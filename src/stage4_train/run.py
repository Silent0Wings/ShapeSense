"""Stage 4 — training: baselines + arms A0 / A1 / B. Owner: ______

Contract (implementation.md § Stage 4, stages/stage_4.md):
  Input:  train/val manifests (Stage 1, never test.csv), ``build_transform``
          (Stage 2 package API), ``build_generator`` (Stage 3 package API),
          configs/pipeline.yaml#runs, #arms, #train, #synthetic_fraction,
          #seed_set, artifacts/stage1/source_classifier.json (Decision 12).
  Output: artifacts/stage4/baselines/, loader_benchmark.json, tuning.json,
          <arm>_<seed>/{model.pt, train_log.csv, val_curve.png,
          val_probs.npz, run.json}, seed_disagreement.json.
  Order:  baselines first (Should 1) -> loader benchmark (R10) -> Decision 7
          tuning on A1 (R4) -> arm x seed sweep (+ LOSO if triggered, R14)
          -> seed disagreement (R11).
  Fairness: ``steps_per_epoch`` is frozen once from arm A0 (Decision 13) and
          ``train.train_one`` refuses any other budget (R1, R2b).
  Hygiene: Stage 4 never reads the test split; the stage fails if the
          access log carries this run's run_id (R8).
Does not write status.json; the runner does that through common.status.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits
from torch import nn

from src.common.batch import Batch
from src.common.config import DEFAULT_CONFIG, load_config, resolve
from src.common.hashing import config_subtree_hash, sha256_obj, sha256_path
from src.common.splits import count_test_reads
from src.common.status import current_run_id
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.baselines import train_baselines
from src.stage4_train.benchmark import benchmark, est_all_runs_s, est_run_s
from src.stage4_train.model import build_model, count_params
from src.stage4_train.sampling import batch_composition
from src.stage4_train.sweep import (LOSO_ARMS, LOSO_HOLDOUT_SOURCE, STAGE_DIR_NAME,
                                    load_stores, run_specs, run_sweep,
                                    write_seed_disagreement)
from src.stage4_train.train import (MODEL_FILE, VAL_PROBS_FILE, required_steps_per_epoch,
                                    resolve_device)
from src.stage4_train.tuning import TUNING_JSON, grid_points, run_tuning

STAGE = "stage4"
DEPENDS = ["stage0", "stage1", "stage2", "stage3"]
TRAIN_MANIFEST = "train.csv"
VAL_MANIFEST = "val.csv"
BASELINES_DIR = "baselines"
BASELINES_JSON = "baselines.json"
LOADER_BENCHMARK_JSON = "loader_benchmark.json"
BENCHMARK_ARM = "B"                      # the heaviest stream: augmentation + generator
SOURCE_CLASSIFIER_JSON = "source_classifier.json"   # Stage 1 output (plan 23)
SHORTCUT_KEY = "shortcut_detected"
N_LOSO_RUNS = len(LOSO_ARMS)             # Decision 6 budget: 2 leave-one-source-out runs
EQUAL_COMPUTE_NOTE = ("B substitutes 30% of each batch: ~0.7 x batch_size real draws per step "
                      "vs batch_size for A1 at the same step budget (Decision 13)")
CONFIG_SUBTREES = ("runs", "arms", "train", "synthetic_fraction", "seed_set", "augment", "synth")
CODE_DIRS = ("src/stage4_train", "src/stage2_augment", "src/stage3_synth", "src/common")


def inputs(config: dict) -> dict[str, str]:
    """Content hashes of everything this stage's outputs depend on (never test.csv)."""
    splits_dir = resolve(config["paths"]["splits_dir"])
    stage1_dir = resolve(config["paths"]["artifacts_dir"]) / "stage1"
    hashes: dict[str, str] = {
        "train_manifest": sha256_path(splits_dir / TRAIN_MANIFEST),
        "val_manifest": sha256_path(splits_dir / VAL_MANIFEST),
        "taxonomy": sha256_obj(config["taxonomy"]),
        "source_classifier": sha256_path(stage1_dir / SOURCE_CLASSIFIER_JSON),
    }
    for key in CONFIG_SUBTREES:
        hashes[f"config.{key}"] = config_subtree_hash(config, key)
    for code_dir in CODE_DIRS:
        hashes[f"code.{Path(code_dir).name}"] = sha256_path(resolve(code_dir))
    return hashes


def shortcut_detected(config: dict) -> bool:
    """Decision 12 trigger from artifacts/stage1/source_classifier.json (False if absent)."""
    path = resolve(config["paths"]["artifacts_dir"]) / "stage1" / SOURCE_CLASSIFIER_JSON
    if not path.is_file():
        return False
    with open(path, encoding="utf-8") as f:
        return bool(json.load(f).get(SHORTCUT_KEY, False))


def sgd_step_fn(config: dict, n_classes: int, hparams: dict):
    """``fn(batch)`` doing one AdamW step of a fresh ``SmallCNN`` (benchmark timing only)."""
    torch.manual_seed(int(config["seed_set"][0]))
    torch.set_num_threads(int(config["train"]["num_threads"]))
    device = resolve_device(config)
    model = build_model(config, n_classes, hparams["dropout"]).to(device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(hparams["lr"]),
                                  weight_decay=float(config["train"]["weight_decay"]))

    def step(batch: Batch) -> None:
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(torch.from_numpy(batch.images).to(device)),
                                           torch.from_numpy(batch.labels).to(device))
        loss.backward()
        optimizer.step()

    return step


def release_gpu() -> None:
    """Free the parent's GPU memory, so the training workers have the whole card."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def tuned_hparams(config: dict, stage_dir: Path) -> tuple[dict, dict]:
    """(A1's winner, a tuning.json-shaped record) from the iteration 2 search."""
    winners = json.loads((stage_dir / "tuning_iter3" / "winners.json").read_text(encoding="utf-8"))
    hparams = dict(config["arms"]["A1"]["hparams"])
    return hparams, {"arm": "A1", "seed": int(config["seed_set"][0]), "grid": winners["grid"]["A1"],
                     "winner": hparams, "grid_by_arm": winners["grid"],
                     "trials_per_arm": winners["trials_per_arm"]}


def _write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def run(config: dict, *, config_path: str | Path = DEFAULT_CONFIG) -> dict:
    """Baselines, benchmark, tuning, sweep, seed disagreement; returns the status payload."""
    train_cfg = config["train"]
    # Cap BLAS/OpenMP pools: with two OpenBLAS copies + OpenMP all defaulting
    # to every core, the logistic-regression baseline ran ~12x slower
    # (oversubscription). Stays in force for this process.
    threadpool_limits(int(train_cfg["num_threads"]))
    stage_dir = resolve(config["paths"]["artifacts_dir"]) / STAGE_DIR_NAME
    stage_dir.mkdir(parents=True, exist_ok=True)
    seed0 = int(config["seed_set"][0])
    batch_size = int(train_cfg["batch_size"])
    synthetic_fraction = float(config["synthetic_fraction"])

    train_store, val_store, val_ids = load_stores(config)
    n_classes = int(train_store.n_classes)
    transform = build_transform(config)
    generate = build_generator(config)

    # Decision 13: frozen budget from the full A0 train store (raises if not frozen).
    steps_per_epoch = required_steps_per_epoch(config, len(train_store))

    # Should 1: baselines first (minutes, not hours).
    baselines_dir = stage_dir / BASELINES_DIR
    baselines_summary = train_baselines(train_store.images, train_store.labels,
                                        val_store.images, val_store.labels,
                                        train_cfg["baselines"], n_classes,
                                        rng=np.random.default_rng(seed0), out_dir=baselines_dir)

    # R10: loader + one SGD step benchmark on the heaviest arm, with the budget estimate.
    default_hparams = {"lr": float(train_cfg["lr"]), "dropout": float(train_cfg["dropout"])}
    n_bench = int(train_cfg["benchmark_batches"])
    bench = benchmark(train_store, config["arms"][BENCHMARK_ARM], batch_size, synthetic_fraction,
                      n_classes, n_batches=n_bench, rng=np.random.default_rng(seed0),
                      transform=transform, generate=generate,
                      step_time_fn=sgd_step_fn(config, n_classes, default_hparams),
                      min_batches=n_bench)
    n_grid = len(grid_points(train_cfg["tuning"]))
    n_loso = N_LOSO_RUNS * int(config["evaluation"].get("loso_seeds", 1))
    n_runs_budget = len(config["runs"]) + n_grid + n_loso
    max_epochs = int(train_cfg["max_epochs"])
    bench.update({
        "arm": BENCHMARK_ARM,
        "device": resolve_device(config),
        "num_threads": int(train_cfg["num_threads"]),
        "parallel_runs": int(train_cfg["parallel_runs"]),
        "steps_per_epoch": steps_per_epoch,
        "max_epochs": max_epochs,
        "n_params": count_params(build_model(config, n_classes, default_hparams["dropout"])),
        "est_run_s": est_run_s(steps_per_epoch, max_epochs, bench["per_step_s"]),
        "n_runs_budget": n_runs_budget,
        "est_all_runs_s": est_all_runs_s(n_runs_budget, steps_per_epoch, max_epochs,
                                         bench["per_step_s"]),
    })
    bench_path = stage_dir / LOADER_BENCHMARK_JSON
    _write_json(bench, bench_path)
    release_gpu()

    # R4: Decision 7 grid on A1 validation, once.
    if train_cfg.get("tuned"):   # iteration 2: chosen by src/stage4_train/search.py
        hparams, tuning = tuned_hparams(config, stage_dir)
        _write_json(tuning, stage_dir / TUNING_JSON)
    else:
        tuning = run_tuning(config, train_store, val_store, transform, generate, steps_per_epoch,
                            stage_dir, val_image_ids=val_ids,
                            batch_runner=lambda specs: run_specs(config, specs),
                            config_path=config_path)
        hparams = dict(tuning["winner"])

    # R14: leave-one-source-out runs only when Stage 1's trigger fired.
    loso = shortcut_detected(config)
    results = run_sweep(config, steps_per_epoch, hparams, loso,
                        config_path=config_path, out_dir=stage_dir)

    # R11: robustness number (not the power check).
    disagreement, disagreement_path = write_seed_disagreement(
        stage_dir, [{"run_name": r["run_name"], "arm": r["arm"], "seed": r["seed"],
                     "holdout_source": r.get("holdout_source")} for r in results])

    # R8: the access log must carry no line with this run's run_id.
    test_reads = count_test_reads(current_run_id(),
                                  log_path=resolve(config["paths"]["test_access_log"]))
    no_test_reads = test_reads == 0

    same_steps = all(int(r["steps_per_epoch"]) == steps_per_epoch
                     and int(r["optimizer_steps"]) == steps_per_epoch * int(r["epochs_run"])
                     for r in results)
    all_present = all((stage_dir / r["run_name"] / MODEL_FILE).is_file()
                      and (stage_dir / r["run_name"] / VAL_PROBS_FILE).is_file()
                      for r in results)
    composition = {arm: batch_composition(spec, batch_size, synthetic_fraction)
                   for arm, spec in config["arms"].items()}

    outputs = [str(baselines_dir / BASELINES_JSON), str(bench_path),
               str(stage_dir / TUNING_JSON), str(disagreement_path)]
    outputs += [str(stage_dir / r["run_name"] / MODEL_FILE) for r in results]
    result = {
        "outputs": outputs,
        "metrics": {
            "steps_per_epoch": steps_per_epoch,
            "hparams": hparams,
            "arm_hparams": {arm: spec.get("hparams", hparams) for arm, spec in config["arms"].items()},
            "tuning_grid": tuning["grid"],
            "runs": [{"name": r["run_name"], "arm": r["arm"], "seed": r["seed"],
                      "best_epoch": r["best_epoch"], "val_macro_f1": r["val_macro_f1"],
                      "epochs_run": r["epochs_run"],
                      "realized_synthetic_share": r["realized_synthetic_share"],
                      "holdout_source": r.get("holdout_source")} for r in results],
            "real_draws_per_step": {arm: n_real for arm, (n_real, _) in composition.items()},
            "synthetic_per_step": {arm: n_syn for arm, (_, n_syn) in composition.items()},
            "equal_compute_note": EQUAL_COMPUTE_NOTE,
            "loso_required": loso,
            "loso_holdout_source": LOSO_HOLDOUT_SOURCE if loso else None,
            "baselines": baselines_summary,
            "loader_benchmark": {k: bench[k] for k in ("per_step_s", "images_per_s",
                                                       "est_run_s", "est_all_runs_s",
                                                       "n_runs_budget")},
            "seed_disagreement": {arm: v["mean_pairwise_disagreement"]
                                  for arm, v in disagreement["per_arm"].items()},
        },
        "checks": {
            "same_steps_every_run": same_steps,
            "all_runs_present": all_present,
            "test_reads_this_run": int(test_reads),
            "no_test_reads": no_test_reads,
        },
    }
    if not no_test_reads:
        result["status"] = "failed"
        result["error"] = (f"{test_reads} test-split read(s) logged under this run_id; "
                           "Stage 4 must never read the test split (stage_4.md R8)")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    config_path = resolve(args.config)
    run(load_config(config_path), config_path=config_path)


if __name__ == "__main__":
    main()
