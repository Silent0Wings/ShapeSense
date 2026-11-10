"""One fair CNN run: ``train_one(arm, seed, ...)`` (stages/stage_4.md M3).

Everything that could differ between arms is read from one place,
``configs/pipeline.yaml#train``, and passed identically to every run:
architecture, optimizer, LR schedule, batch size, step budget, maximum
epochs and the early-stopping rule (R1, R2). The only per-arm inputs are
the two booleans in ``config["arms"][arm]`` that decide whether the
injected ``transform`` / ``generate`` callables are used (R2).

Decision 13 step budget (R2b): an epoch is ``steps_per_epoch`` optimizer
steps, not a pass over the data. ``required_steps_per_epoch`` computes
``ceil(n_train / batch_size)`` from the FULL (arm A0) train store and
refuses to run unless the frozen value in config equals it. ``train_one``
then refuses to train with any other value, so B can never get a larger
budget (Pitfalls: "Different step budgets per arm").

Selection (R5, R12): after every epoch the validation softmax
probabilities are computed; the epoch with the highest validation
macro-F1 (points, 0-100; ties keep the earlier epoch) is kept and saved as
TorchScript together with its probabilities. Early stopping waits
``early_stopping_patience`` epochs without improvement.

Determinism (R9): ``torch.manual_seed(seed)``, NumPy only through
``sampling.step_rng(seed, epoch, step)``, a fixed thread count and
``torch.use_deterministic_algorithms(True, warn_only=True)``.

Stage 4 never touches the test split; the stores it receives were built
with ``data.ImageStore.from_split("train" | "val")`` (R8).
"""

from __future__ import annotations

import copy
import csv
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
from torch import nn

from src.common.config import resolve
from src.common.hashing import sha256_obj, sha256_path
from src.stage4_train.model import build_model, count_params
from src.stage4_train.prep import BatchPool, prepared
from src.stage4_train.sampling import (BatchStream, clean_count, GenerateLike, TransformLike,
                                       batch_composition, to_float)

PERCENT = 100.0            # macro-F1 and accuracy are reported in points (0-100)
EVAL_BATCH_SIZE = 1024     # images per forward pass when scoring validation
RUN_JSON = "run.json"
TRAIN_LOG_CSV = "train_log.csv"
MODEL_FILE = "model.pt"
VAL_PROBS_FILE = "val_probs.npz"
VAL_CURVE_FILE = "val_curve.png"
LOG_COLUMNS = ["epoch", "train_loss", "train_acc_trainmode", "val_loss", "val_acc",
               "val_macro_f1", "lr", "synthetic_share", "seconds"]
FIG_SIZE_IN = (7.0, 4.0)   # inches, val_curve.png
FIG_DPI = 120

# val_scorer(epoch_index, probs (n_val, k) float32, labels (n_val,) int64) -> points
ValScorer = Callable[[int, np.ndarray, np.ndarray], float]


# --------------------------------------------------------------------------- #
# Pure helpers (NumPy only)
# --------------------------------------------------------------------------- #

def macro_f1_points(labels: np.ndarray, preds: np.ndarray, n_classes: int,
                    excluded: tuple[int, ...] = ()) -> float:
    """Macro-F1 in points (0-100) over classes ``0..n_classes-1`` minus ``excluded``.

    Per class F1 = 2tp / (2tp + fp + fn); a class with no support and no
    predictions scores 0 (the scikit-learn ``zero_division=0`` convention
    the baselines use). ``labels`` and ``preds`` are int arrays (N,).
    """
    labels = np.asarray(labels, dtype=np.int64)
    preds = np.asarray(preds, dtype=np.int64)
    if labels.shape != preds.shape:
        raise ValueError(f"labels {labels.shape} and preds {preds.shape} must match")
    f1s = []
    for c in range(n_classes):
        if c in excluded:
            continue
        tp = int(np.sum((preds == c) & (labels == c)))
        fp = int(np.sum((preds == c) & (labels != c)))
        fn = int(np.sum((preds != c) & (labels == c)))
        denom = 2 * tp + fp + fn
        f1s.append((2.0 * tp / denom) if denom else 0.0)
    return float(np.mean(f1s)) * PERCENT


def accuracy_points(labels: np.ndarray, preds: np.ndarray) -> float:
    """Accuracy in points (0-100)."""
    labels = np.asarray(labels)
    preds = np.asarray(preds)
    if labels.size == 0:
        return 0.0
    return float(np.mean(labels == preds)) * PERCENT


def required_steps_per_epoch(config: dict, n_train_a0: int) -> int:
    """Decision 13: ``ceil(n_train / batch_size)`` from arm A0, frozen in config.

    ``n_train_a0`` is the size of the FULL real train split (arm A0's
    stream), never a filtered store. Raises ``ValueError`` when
    ``train.steps_per_epoch`` is null (not frozen yet) or differs from the
    computed value (stale freeze: refuse rather than train an unfair arm).
    Returns the frozen value.
    """
    train_cfg = config["train"]
    batch_size = int(train_cfg["batch_size"])
    if n_train_a0 < 1:
        raise ValueError(f"n_train_a0 must be >= 1, got {n_train_a0}")
    value = int(math.ceil(n_train_a0 / batch_size))
    frozen = train_cfg.get("steps_per_epoch")
    if frozen is None:
        raise ValueError(f"set train.steps_per_epoch: {value} in configs/pipeline.yaml "
                         "(Decision 13: frozen once from arm A0)")
    if int(frozen) != value:
        raise ValueError(f"train.steps_per_epoch is frozen at {frozen} but arm A0 needs "
                         f"ceil({n_train_a0} / {batch_size}) = {value}; refusing to train with a "
                         "mismatched step budget (Decision 13, stage_4.md R2b)")
    return value


def check_frozen_steps(config: dict, steps_per_epoch: int) -> int:
    """Refuse any step budget other than the frozen ``train.steps_per_epoch``."""
    frozen = config["train"].get("steps_per_epoch")
    if frozen is None:
        raise ValueError("train.steps_per_epoch is null; run required_steps_per_epoch first "
                         "and freeze the value in configs/pipeline.yaml (Decision 13)")
    if int(frozen) != int(steps_per_epoch):
        raise ValueError(f"steps_per_epoch {steps_per_epoch} differs from the frozen "
                         f"train.steps_per_epoch {frozen}; every arm must use the same budget")
    return int(frozen)


DEVICE_CHOICES = ("auto", "cpu", "cuda")


def resolve_device(config: dict) -> str:
    """``"cuda"`` or ``"cpu"`` from ``train.device`` (default ``auto``).

    ``auto`` uses a GPU when one is visible. An explicit ``cuda`` without one
    raises, so a run meant for the GPU can never fall back to the CPU silently.
    """
    choice = str(config["train"].get("device", "auto"))
    if choice not in DEVICE_CHOICES:
        raise ValueError(f"train.device must be one of {DEVICE_CHOICES}, got {choice!r}")
    if choice == "cpu":
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if choice == "cuda":
        raise ValueError("train.device is cuda but no CUDA GPU is available; "
                         "install a CUDA build of PyTorch or set it to auto")
    return "cpu"


def runtime_id(config: dict) -> dict:
    """Hardware and torch build a run trains on; part of the recipe.

    CPU and GPU runs are not numerically identical, so a run is reused only
    on the same device, GPU model and torch version.
    """
    device = resolve_device(config)
    name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
    return {"device": device, "device_name": name, "torch": torch.__version__}


RECIPE_TRAIN_KEYS_IGNORED = ("num_threads", "parallel_runs", "prep_workers", "tuned", "benchmark_batches",
                             "device")  # the resolved hardware is hashed via runtime_id
RECIPE_CODE_DIRS = ("src/stage2_augment", "src/stage3_synth", "src/stage4_train")


def recipe_fingerprint(config: dict) -> str:
    """Hash of everything that defines how a run is trained, other than its
    hparams and seed: architecture/optimizer/budget (train, minus scheduling
    knobs that do not change results), augmentation, generator, arms,
    synthetic share, image size, taxonomy and the Stage 2/3/4 code. A
    finished run is reused only when this matches, so a recipe change can
    never silently mix old and new runs across arms."""
    train = {k: v for k, v in config["train"].items() if k not in RECIPE_TRAIN_KEYS_IGNORED}
    parts = {k: config[k] for k in ("augment", "synth", "arms", "synthetic_fraction",
                                    "image_size", "taxonomy")}
    parts["train"] = train
    parts["code"] = {d: sha256_path(resolve(d)) for d in RECIPE_CODE_DIRS}
    parts["runtime"] = runtime_id(config)
    # The data itself: a re-freeze (e.g. CRISP-DM iteration 1) must retrain.
    splits = resolve(config["paths"]["splits_dir"])
    parts["data"] = {s: sha256_path(splits / f"{s}.csv") for s in ("train", "val")}
    return sha256_obj(parts)


def completed_run(run_dir: Path, hparams: dict, steps_per_epoch: int,
                  recipe: str | None = None) -> dict | None:
    """``run.json`` of a finished run with the same hparams, budget and recipe, else None.

    Lets the sweep and the tuning grid resume after an interruption without
    retraining a run that already exists with identical settings. When a
    ``recipe`` fingerprint is given, a run recorded with another one is
    never reused.
    """
    path = Path(run_dir) / RUN_JSON
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        info = json.load(f)
    same_hparams = all(
        math.isclose(float(info.get("hparams", {}).get(k, float("nan"))), float(v))
        for k, v in hparams.items())
    if recipe is not None and info.get("recipe") != recipe:
        return None
    if same_hparams and int(info.get("steps_per_epoch", -1)) == int(steps_per_epoch) \
            and (Path(run_dir) / MODEL_FILE).is_file() \
            and (Path(run_dir) / VAL_PROBS_FILE).is_file():
        return info
    return None


# --------------------------------------------------------------------------- #
# Torch helpers
# --------------------------------------------------------------------------- #

def predict_proba(model: nn.Module, images_u8: np.ndarray, labels: np.ndarray | None = None,
                  batch_size: int = EVAL_BATCH_SIZE,
                  device: str = "cpu") -> tuple[np.ndarray, float]:
    """Softmax probabilities of ``model`` on uint8 (N, S, S) images.

    ``images_u8`` may instead be a float32 tensor already on ``device``.
    Returns ``(probs float32 (N, k), mean cross-entropy)``; the loss is
    ``nan`` when ``labels`` is None. Runs in eval mode without gradients.
    """
    model.eval()
    chunks: list[np.ndarray] = []
    loss_sum = 0.0
    n = int(images_u8.shape[0])
    with torch.no_grad():
        for start in range(0, n, batch_size):
            chunk = images_u8[start:start + batch_size]
            x = chunk if isinstance(chunk, torch.Tensor) else torch.from_numpy(to_float(chunk)).to(device)
            logits = model(x)
            if labels is not None:
                y = torch.from_numpy(np.asarray(labels[start:start + batch_size],
                                                dtype=np.int64)).to(device)
                loss_sum += float(nn.functional.cross_entropy(logits, y, reduction="sum"))
            chunks.append(torch.softmax(logits, dim=1).cpu().numpy().astype(np.float32))
    probs = np.concatenate(chunks, axis=0) if chunks else np.zeros((0, model.n_classes), np.float32)
    loss = (loss_sum / n) if (labels is not None and n) else float("nan")
    return probs, loss


def _seed_everything(seed: int, num_threads: int) -> None:
    # Required by deterministic CuBLAS operations; must be set before first CUDA use.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.backends.cudnn.benchmark = False
    torch.manual_seed(int(seed))
    torch.set_num_threads(int(num_threads))
    torch.use_deterministic_algorithms(True, warn_only=True)


def _save_torchscript(model: nn.Module, path: Path) -> None:
    scripted = torch.jit.script(model.eval())
    scripted.save(str(path))


def _plot_curve(log_rows: list[dict], best_epoch: int, path: Path) -> None:
    """val_curve.png: validation macro-F1 (left axis) and losses (right axis)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    epochs = [r["epoch"] for r in log_rows]
    fig, ax_f1 = plt.subplots(figsize=FIG_SIZE_IN, dpi=FIG_DPI)
    ax_f1.plot(epochs, [r["val_macro_f1"] for r in log_rows], marker="o",
               color="#1f77b4", label="val macro-F1 (points)")
    ax_f1.axvline(best_epoch, color="#1f77b4", linestyle=":", linewidth=1,
                  label=f"selected epoch {best_epoch}")
    ax_f1.set_xlabel("epoch")
    ax_f1.set_ylabel("val macro-F1 (points)")
    ax_loss = ax_f1.twinx()
    ax_loss.plot(epochs, [r["train_loss"] for r in log_rows], color="#7f7f7f",
                 linestyle="--", label="train loss")
    ax_loss.plot(epochs, [r["val_loss"] for r in log_rows], color="#d62728",
                 linestyle="-", label="val loss")
    ax_loss.set_ylabel("cross-entropy")
    handles = ax_f1.get_legend_handles_labels()
    handles2 = ax_loss.get_legend_handles_labels()
    ax_f1.legend(handles[0] + handles2[0], handles[1] + handles2[1], loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _write_log(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in LOG_COLUMNS})


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #

def train_one(run_name: str, arm: str, seed: int, config: dict,
              train_store: Any, val_store: Any,
              transform: TransformLike | None, generate: GenerateLike | None,
              hparams: dict, out_dir: Path, *,
              steps_per_epoch: int,
              val_image_ids: np.ndarray | None = None,
              val_scorer: ValScorer | None = None,
              excluded_classes: tuple[int, ...] = (),
              prep_workers: int = 0,
              save_curve: bool = True) -> dict:
    """Train one (arm, seed) CNN with validation-based early stopping (M3).

    Args:
        run_name: artifact folder name, e.g. ``"A1_0"``.
        arm: key into ``config["arms"]``; decides only whether ``transform``
            / ``generate`` are used (R2).
        seed: run seed (``config["seed_set"]`` entry); fixes torch init and
            every batch via ``sampling.step_rng`` (R9).
        config: merged pipeline config (``load_config()``).
        train_store, val_store: ``data.ImageStore`` (images uint8 (N, S, S),
            labels int64 (N,), class_idx, n_classes). Train may be a
            leave-one-source-out subset; val must match the saved ids.
        transform, generate: Stage 2 / Stage 3 callables (ignored unless the
            arm's flags ask for them).
        hparams: ``{"lr": float, "dropout": float}`` (Decision 7 winner).
        out_dir: ``artifacts/stage4/<run_name>/``.
        steps_per_epoch: the frozen Decision 13 budget computed by the
            caller from the FULL A0 train store; must equal
            ``config["train"]["steps_per_epoch"]`` or ``ValueError``.
        val_image_ids: str array (n_val,) stored in ``val_probs.npz``;
            defaults to ``"0".."n_val-1"``.
        val_scorer: optional selection hook ``fn(epoch_idx, probs, labels)
            -> points``; defaults to validation macro-F1. Tests inject a
            preset sequence to pin the selected epoch.
        excluded_classes: classes never sampled and left out of validation
            macro-F1 (P-61, leave-one-source-out runs only).
        prep_workers: CPU processes preparing the batches. They rebuild
            ``transform`` and ``generate`` from ``config``, so pass more than
            1 only when both were built from this same ``config``.
        save_curve: write ``val_curve.png``; search trials skip the plot.

    Writes ``model.pt`` (TorchScript, best epoch), ``train_log.csv``,
    ``val_curve.png``, ``val_probs.npz`` (probs float32 (n_val, k), labels
    int64, image_ids str) and ``run.json``. Returns the ``run.json`` dict.
    """
    t_start = time.perf_counter()
    train_cfg = config["train"]
    arm_cfg = config["arms"][arm]
    steps_per_epoch = check_frozen_steps(config, steps_per_epoch)
    batch_size = int(train_cfg["batch_size"])
    max_epochs = int(train_cfg["max_epochs"])
    patience = int(train_cfg["early_stopping_patience"])
    synthetic_fraction = float(config["synthetic_fraction"])
    n_classes = int(train_store.n_classes)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    excluded = tuple(sorted(int(c) for c in excluded_classes))
    device = resolve_device(config)
    _seed_everything(seed, train_cfg["num_threads"])
    model = build_model(config, n_classes, hparams["dropout"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(hparams["lr"]),
                                  weight_decay=float(train_cfg["weight_decay"]))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max_epochs * steps_per_epoch)
    stream = BatchStream(train_store.images, train_store.labels, arm_cfg, batch_size,
                         synthetic_fraction, n_classes, seed=seed, steps=steps_per_epoch,
                         transform=transform if arm_cfg["augment"] else None,
                         generate=generate if arm_cfg["synthetic"] else None,
                         class_idx=getattr(train_store, "class_idx", None),
                         excluded_classes=excluded)
    n_real, n_syn = batch_composition(arm_cfg, batch_size, synthetic_fraction)
    # Arm P: the first epochs see synthetic images only, then real images take over.
    pretrain_epochs = int(float(arm_cfg.get("pretrain_fraction", 0.0)) * max_epochs)
    pretrain_stream = None
    if pretrain_epochs:
        pretrain_stream = BatchStream(train_store.images, train_store.labels,
                                      {**arm_cfg, "synthetic_fraction": 1.0, "clean_fraction": 0.0}, batch_size,
                                      synthetic_fraction, n_classes, seed=seed, steps=steps_per_epoch,
                                      transform=transform if arm_cfg["augment"] else None, generate=generate,
                                      class_idx=getattr(train_store, "class_idx", None),
                                      excluded_classes=excluded)
    val_labels = np.asarray(val_store.labels, dtype=np.int64)
    n_val = int(val_labels.shape[0])
    val_images = torch.from_numpy(to_float(val_store.images)).to(device)
    # Exact CPU uint8 -> float32 values: dividing on the GPU rounds 126 of the 256 levels differently.
    pixel_values = torch.from_numpy(to_float(np.arange(256, dtype=np.uint8).reshape(1, 1, 256))).reshape(-1).to(device)
    if val_image_ids is None:
        val_image_ids = np.array([str(i) for i in range(n_val)], dtype=str)
    val_image_ids = np.asarray(val_image_ids).astype(str)
    if val_image_ids.shape != (n_val,):
        raise ValueError(f"val_image_ids {val_image_ids.shape} must match n_val {n_val}")

    best_score = -math.inf
    best_epoch = 0
    best_state: dict | None = None
    best_probs: np.ndarray | None = None
    best_val_f1 = float("nan")
    wait = 0
    log_rows: list[dict] = []
    syn_total = 0
    img_total = 0
    optimizer_steps = 0

    pretrain_batches = prepared(pretrain_stream, config, prep_workers) if pretrain_stream else None
    batches = None if pretrain_stream else prepared(stream, config, prep_workers)
    try:
        for epoch_idx in range(max_epochs):
            t_epoch = time.perf_counter()
            model.train()
            loss_total = torch.zeros((), dtype=torch.float64, device=device)   # read once per epoch, no GPU sync per step
            correct_total = torch.zeros((), dtype=torch.int64, device=device)
            seen = 0
            if pretrain_stream and epoch_idx == pretrain_epochs:
                if isinstance(pretrain_batches, BatchPool):
                    pretrain_batches.close()   # one pool at a time
                batches = prepared(stream, config, prep_workers)
            source = pretrain_batches if epoch_idx < pretrain_epochs else batches
            for batch in source.epoch(epoch_idx):
                x = torch.from_numpy(batch.images).to(device)
                if batch.images.dtype == np.uint8:
                    x = pixel_values[x.long()]
                y = torch.from_numpy(batch.labels).to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(x)
                loss = nn.functional.cross_entropy(logits, y)
                loss.backward()
                optimizer.step()
                scheduler.step()
                optimizer_steps += 1
                loss_total += loss.detach().double() * int(y.shape[0])
                correct_total += (logits.argmax(dim=1) == y).sum()
                seen += int(y.shape[0])
                syn_total += int(batch.is_synthetic.sum())
                img_total += int(batch.is_synthetic.shape[0])

            loss_sum, correct = float(loss_total), int(correct_total)
            probs, val_loss = predict_proba(model, val_images, val_labels, device=device)
            preds = probs.argmax(axis=1)
            val_f1 = macro_f1_points(val_labels, preds, n_classes, excluded=excluded)
            val_acc = accuracy_points(val_labels, preds)
            score = float(val_scorer(epoch_idx, probs, val_labels)) if val_scorer else val_f1
            epoch = epoch_idx + 1  # 1-based in logs and run.json
            log_rows.append({
                "epoch": epoch,
                "train_loss": loss_sum / seen if seen else float("nan"),
                "train_acc_trainmode": PERCENT * correct / seen if seen else float("nan"),
                "val_loss": val_loss,
                "val_acc": val_acc,
                "val_macro_f1": val_f1,
                "lr": float(scheduler.get_last_lr()[0]),
                "synthetic_share": syn_total / img_total if img_total else 0.0,
                "seconds": time.perf_counter() - t_epoch,
            })
            if epoch_idx < pretrain_epochs:
                continue                # the real-image phase decides the best epoch and patience
            if score > best_score:  # strict: ties keep the earlier epoch
                best_score = score
                best_epoch = epoch
                best_state = copy.deepcopy(model.state_dict())
                best_probs = probs
                best_val_f1 = val_f1
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    break
    finally:
        for prepared_batches in (pretrain_batches, batches):   # also when training raises
            if isinstance(prepared_batches, BatchPool):
                prepared_batches.close()

    assert best_state is not None and best_probs is not None  # max_epochs >= 1 by config
    model.load_state_dict(best_state)
    model.cpu()  # saved models stay device-neutral for Stages 5 and 6
    _save_torchscript(model, out_dir / MODEL_FILE)
    np.savez(out_dir / VAL_PROBS_FILE, probs=best_probs.astype(np.float32),
             labels=val_labels, image_ids=val_image_ids)
    _write_log(log_rows, out_dir / TRAIN_LOG_CSV)
    if save_curve:
        _plot_curve(log_rows, best_epoch, out_dir / VAL_CURVE_FILE)

    info = {
        "run_name": run_name,
        "arm": arm,
        "seed": int(seed),
        "hparams": {"lr": float(hparams["lr"]), "dropout": float(hparams["dropout"])},
        "steps_per_epoch": int(steps_per_epoch),
        "recipe": recipe_fingerprint(config),
        "device": device,
        "device_name": runtime_id(config)["device_name"],
        "excluded_classes": list(excluded),
        "max_epochs": max_epochs,
        "batch_size": batch_size,
        "early_stopping_patience": patience,
        "selection_metric": str(train_cfg["selection_metric"]),
        "best_epoch": int(best_epoch),
        "val_macro_f1": float(best_val_f1),
        "selection_score": float(best_score),
        "epochs_run": len(log_rows),
        "pretrain_epochs": pretrain_epochs,
        "optimizer_steps": int(optimizer_steps),
        "realized_synthetic_share": syn_total / img_total if img_total else 0.0,
        "real_draws_per_step": int(n_real),
        "clean_per_step": clean_count(arm_cfg, batch_size),
        "synthetic_per_step": int(n_syn),
        "n_train": int(len(train_store.labels)),
        "n_val": n_val,
        "n_params": count_params(model),
        "seconds": time.perf_counter() - t_start,
    }
    with open(out_dir / RUN_JSON, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
        f.write("\n")
    return info
