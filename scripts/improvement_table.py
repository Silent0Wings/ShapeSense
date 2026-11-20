"""The course improvement table: baseline, then cleaning, transformation and
feature selection, each scored by test macro-F1 on the same 2,776 images.

    python -m scripts.improvement_table replay     # raw images for every catalog id
    python -m scripts.improvement_table train      # baseline + cleaning runs (A0 recipe)
    python -m scripts.improvement_table fs         # feature selection, validation only
    python -m scripts.improvement_table evaluate   # one logged test read, writes results/

Rows (every model: SmallCNN, the arm's tuned lr/dropout, the frozen 49 steps
x 60 epochs, seeds 0-4; only the data changes):

  baseline        raw collected images, only decoded and resized to 64x64:
                  transparency flattened onto white, 8-bit grey, plain bilinear
                  resize (no crop, no polarity fix, no outline redraw). The
                  train set keeps what cleaning removes: the 350 Quick, Draw!
                  "diamonds" Phase 1 had put in train, the exact duplicates
                  whose twin is in train, and the blank image Stage 1 rejected.
  + cleaning      the same raw decoding, on the cleaned train split (12,405).
  + transformation  Stage 1 standardization (A0, existing runs) and then
                  augmentation + synthetic shapes (A2, the final model).
  + feature selection  input resolution chosen on validation for the A2 recipe.

The test split (configs/splits/test.csv) is the same for every row; each row
reads it with its own preprocessing (raw decode or standardized PNG). Only the
``evaluate`` step reads it, through src.stage5_eval's logged reader. Outputs:
artifacts/improvement/ (runs, git-ignored) and results/improvement_table.{json,csv}.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.common.config import arm_config, load_config, resolve

OUT = resolve("artifacts") / "improvement"
RAW_NPZ = OUT / "raw_images.npz"
RESULTS_JSON = resolve("results") / "improvement_table.json"
RESULTS_CSV = resolve("results") / "improvement_table.csv"
SEEDS = (0, 1, 2, 3, 4)
FS_SEEDS = (0, 1, 2)          # validation-only search seeds
FS_SIZES = (32, 48)           # candidate input resolutions; 64 is the existing A2
SIZE = 64
_RAW: dict = {}


def _raw() -> dict:
    """The replay arrays, decompressed once (indexing an npz decompresses on every access)."""
    if not _RAW:
        with np.load(RAW_NPZ) as z:
            _RAW.update({k: z[k] for k in z.files})
    return _RAW


# --------------------------------------------------------------------------- #
# Raw decoding and the Stage 1 replay
# --------------------------------------------------------------------------- #

def raw_decode(im) -> np.ndarray:
    """uint8 (64, 64): the least needed to stack one image into a tensor."""
    from PIL import Image
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    return np.asarray(im.convert("L").resize((SIZE, SIZE), Image.BILINEAR), dtype=np.uint8)


def replay() -> None:
    """Re-run Stage 1's candidate loop (same seed and order) without writing the
    dataset, keeping each image's raw decoding and the items cleaning dropped."""
    from PIL import Image
    from src.common.imaging import md5
    from src.stage1_freeze import build_unified_dataset as b
    from src.stage1_freeze.standardize import Rejected, standardize
    from src.stage1_freeze.taxonomy import TAXONOMY

    rng = random.Random(b.SEED)
    groups = defaultdict(list)
    for src, orig, ref, loader in b.candidates(b.DATA):
        label = b.LABEL_MAP[src].get(orig)
        if label is not None:
            groups[(src, label)].append((orig, ref, loader))

    kept, extra = [], []      # extra: duplicates and rejects (cleaning removes them)
    seen = {}
    for key in sorted(groups):
        src, label = key
        items = groups[key]
        rng.shuffle(items)
        n_kept = 0
        for orig, ref, loader in items[:b.CANDIDATES_PER_GROUP]:
            im = loader() if callable(loader) else Image.open(loader)
            raw = raw_decode(im)
            try:
                arr, _ = standardize(im)
            except Rejected as e:
                extra.append(dict(kind="rejected", source_id=src, label=label, ref=ref, raw=raw,
                                  twin_md5=""))
                continue
            h = md5(arr)
            if h in seen:
                extra.append(dict(kind="duplicate", source_id=src, label=label, ref=ref, raw=raw,
                                  twin_md5=h))
                continue
            seen[h] = True
            kept.append(dict(source_id=src, label=label, ref=ref, raw=raw, md5=h))
            n_kept += 1
            if n_kept >= b.MAX_PER_GROUP:
                break
        print(f"{src:18s} {label:10s} kept {n_kept}", flush=True)

    for i, r in enumerate(sorted(kept, key=lambda r: (r["source_id"], r["label"], r["ref"]))):
        r["image_id"] = f"{r['source_id']}_{r['label']}_{i:06d}"
    rows = kept + extra
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        RAW_NPZ,
        image_id=np.array([r.get("image_id", "") for r in rows]),
        kind=np.array([r.get("kind", "kept") for r in rows]),
        source_id=np.array([r["source_id"] for r in rows]),
        label_id=np.array([TAXONOMY.index(r["label"]) for r in rows], dtype=np.int64),
        md5=np.array([r.get("md5", "") for r in rows]),
        twin_md5=np.array([r.get("twin_md5", "") for r in rows]),
        ref=np.array([str(r["ref"]) for r in rows]),
        raw=np.stack([r["raw"] for r in rows]))
    print(f"kept {len(kept)}, extra {len(extra)} -> {RAW_NPZ}")
    _check_replay()


def _manifest(split: str) -> list[dict]:
    with open(resolve("configs/splits") / f"{split}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _check_replay() -> None:
    """Every train and val id must exist with the same md5 and label (test is checked at evaluate)."""
    z = _raw()
    by_id = {iid: i for i, iid in enumerate(z["image_id"]) if iid}
    for split in ("train", "val"):
        for row in _manifest(split):
            i = by_id.get(row["image_id"])
            if i is None or z["md5"][i] != row["md5"] or int(z["label_id"][i]) != int(row["label_id"]):
                raise SystemExit(f"replay mismatch for {split} {row['image_id']}")
    print("replay check passed: train and val ids, md5 and labels match the frozen manifests")


# --------------------------------------------------------------------------- #
# Stores
# --------------------------------------------------------------------------- #

def _raw_store(ids: list[str], extra_idx: list[int] | None = None):
    from src.stage4_train.data import ImageStore
    z = _raw()
    by_id = {iid: i for i, iid in enumerate(z["image_id"]) if iid}
    idx = [by_id[i] for i in ids] + list(extra_idx or [])
    return ImageStore(images=z["raw"][idx], labels=z["label_id"][idx], source_ids=z["source_id"][idx],
                      n_classes=10)


def baseline_extras() -> tuple[list[int], dict]:
    """Raw items the baseline trains on that cleaning removes."""
    z = _raw()
    split_of = {}
    for split in ("train", "val"):
        for row in _manifest(split):
            split_of[row["md5"]] = split
    meta = {r["image_id"]: r["split"] for r in csv.DictReader(
        open(resolve("data_set/unified/metadata.csv"), encoding="utf-8"))}
    idx, counts = [], defaultdict(int)
    for i in range(len(z["image_id"])):
        kind, iid = str(z["kind"][i]), str(z["image_id"][i])
        if kind == "kept" and z["source_id"][i] == "quickdraw" and int(z["label_id"][i]) == 9:
            if meta.get(iid) == "train":         # Phase 1 split; its val/test share stays out
                idx.append(i); counts["quickdraw_diamond"] += 1
        elif kind == "duplicate" and split_of.get(str(z["twin_md5"][i])) == "train":
            idx.append(i); counts["exact_duplicate"] += 1
        elif kind == "rejected":
            idx.append(i); counts["rejected_blank"] += 1
    return idx, dict(counts)


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #

def _train(name: str, arm: str, seed: int, config: dict, train_store, val_store, val_ids,
           transform=None, generate=None) -> dict:
    from src.stage4_train.train import completed_run, train_one
    cfg = arm_config(config, arm)
    hp = {k: float(v) for k, v in cfg["arms"][arm]["hparams"].items()}
    run_dir = OUT / name
    done = completed_run(run_dir, hp, int(cfg["train"]["steps_per_epoch"]))
    if done is not None:
        print(f"{name}: reused (val {done['val_macro_f1']:.2f})", flush=True)
        return done
    info = train_one(name, arm, seed, cfg, train_store, val_store, transform, generate, hp, run_dir,
                     steps_per_epoch=int(cfg["train"]["steps_per_epoch"]), val_image_ids=val_ids,
                     prep_workers=int(cfg["train"].get("prep_workers", 0)))
    print(f"{name}: val macro-F1 {info['val_macro_f1']:.2f} in {info['seconds']:.0f} s", flush=True)
    return info


def train() -> None:
    config = load_config()
    val_ids = [r["image_id"] for r in _manifest("val")]
    train_ids = [r["image_id"] for r in _manifest("train")]
    val_store = _raw_store(val_ids)
    extras, counts = baseline_extras()
    print(f"baseline extras: {counts}", flush=True)
    stores = {"baseline": _raw_store(train_ids, extras), "cleaning": _raw_store(train_ids)}
    for row, store in stores.items():
        print(f"{row}: {len(store.labels)} training images", flush=True)
        for seed in SEEDS:
            _train(f"{row}_{seed}", "A0", seed, config, store, val_store, np.array(val_ids))


def _resized_model(size: int):
    """build_model with a fixed area-downsampling layer in front (feature selection)."""
    import torch
    from torch import nn
    from src.stage4_train import model as model_mod

    class Resized(nn.Module):
        def __init__(self, inner: nn.Module, side: int) -> None:
            super().__init__()
            self.inner = inner
            self.side = int(side)
            self.n_classes = int(inner.n_classes)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # Rebuild plain strides first: to_float's [:, None] gives the channel axis
            # stride 0, and the CUDA area kernel then reads the wrong pixels (CPU is fine).
            n, c, h, w = x.shape[0], x.shape[1], x.shape[2], x.shape[3]
            x = torch.flatten(x, 1).view(n, c, h, w)
            x = nn.functional.interpolate(x, size=[self.side, self.side], mode="area")
            return self.inner(x)

    def build(config: dict, n_classes: int, dropout: float) -> nn.Module:
        return Resized(model_mod.build_model(config, n_classes, dropout), size)
    return build


def fs() -> None:
    """Input resolution for the A2 recipe, chosen on validation (3 seeds)."""
    from src.stage2_augment import build_transform
    from src.stage3_synth import build_generator
    from src.stage4_train import train as train_mod
    from src.stage4_train.sweep import load_stores
    config = load_config()
    cfg = arm_config(config, "A2")
    train_store, val_store, val_ids = load_stores(cfg)
    transform, generate = build_transform(cfg), build_generator(cfg)
    original = train_mod.build_model
    scores = {}
    try:
        for size in FS_SIZES:
            train_mod.build_model = _resized_model(size)
            scores[size] = [_train(f"fs{size}_{seed}", "A2", seed, config, train_store, val_store, val_ids,
                                   transform, generate)["val_macro_f1"] for seed in FS_SEEDS]
    finally:
        train_mod.build_model = original
    stage4 = resolve("artifacts/stage4")
    scores[SIZE] = [json.loads((stage4 / f"A2_{s}" / "run.json").read_text())["val_macro_f1"]
                    for s in FS_SEEDS]
    means = {size: float(np.mean(v)) for size, v in scores.items()}
    winner = max(means, key=means.get)
    out = {"candidates": {str(k): v for k, v in scores.items()},
           "mean": {str(k): v for k, v in means.items()}, "winner": int(winner), "seeds": list(FS_SEEDS)}
    (OUT / "feature_selection.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    if winner != SIZE:
        train_mod.build_model = _resized_model(winner)
        try:
            for seed in SEEDS:
                _train(f"fs{winner}_{seed}", "A2", seed, config, train_store, val_store, val_ids,
                       transform, generate)
        finally:
            train_mod.build_model = original


# --------------------------------------------------------------------------- #
# Evaluation: the only test read
# --------------------------------------------------------------------------- #

def evaluate() -> None:
    from src.stage4_train.train import macro_f1_points
    from src.stage5_eval.evaluate import default_test_reader, predict_torchscript
    config = load_config()
    rows, std_images, labels = default_test_reader(config)()   # one logged read
    z = _raw()
    by_id = {iid: i for i, iid in enumerate(z["image_id"]) if iid}
    idx = [by_id[r["image_id"]] for r in rows]
    if any(z["md5"][i] != r["md5"] for i, r in zip(idx, rows)):
        raise SystemExit("raw replay does not match the test manifest")
    raw_images = z["raw"][idx]
    fs_info = json.loads((OUT / "feature_selection.json").read_text())

    def score(model_dir: Path, images: np.ndarray) -> float:
        preds = predict_torchscript(model_dir / "model.pt", images).argmax(axis=1)
        return macro_f1_points(labels, preds, 10)

    stage4 = resolve("artifacts/stage4")
    fs_dir = (lambda s: OUT / f"fs{fs_info['winner']}_{s}") if fs_info["winner"] != SIZE else (lambda s: stage4 / f"A2_{s}")
    steps = [
        ("Baseline (raw images, only resized)", lambda s: OUT / f"baseline_{s}", raw_images),
        ("+ Cleaning (drop off-definition diamonds, duplicates, blank image)", lambda s: OUT / f"cleaning_{s}", raw_images),
        ("+ Transformation, part 1: standardization (A0)", lambda s: stage4 / f"A0_{s}", std_images),
        ("+ Transformation, part 2: augmentation + synthetic shapes (A2)", lambda s: stage4 / f"A2_{s}", std_images),
        (f"+ Feature selection: input resolution {fs_info['winner']} px (chosen on validation)", fs_dir, std_images),
    ]
    table = []
    for name, dir_of, images in steps:
        per_seed = [score(dir_of(s), images) for s in SEEDS]
        table.append({"step": name, "per_seed": per_seed, "mean": float(np.mean(per_seed)),
                      "std": float(np.std(per_seed, ddof=1))})
        print(f"{name}: {table[-1]['mean']:.2f} ± {table[-1]['std']:.2f}", flush=True)
    base = table[0]["mean"]
    for row in table:
        row["delta_vs_baseline"] = row["mean"] - base

    # The 200 images of the direct-LLM benchmark: baseline and final model, seed 0.
    with open(resolve("results/direct_llm_prediction/sample_ids.csv"), encoding="utf-8", newline="") as f:
        sample = [r["image_id"] for r in csv.DictReader(f)]
    pos = {r["image_id"]: i for i, r in enumerate(rows)}
    sel = np.array([pos[i] for i in sample])
    sample_labels = labels[sel]

    def score_sample(model_dir: Path, images: np.ndarray) -> float:
        preds = predict_torchscript(model_dir / "model.pt", images[sel]).argmax(axis=1)
        return macro_f1_points(sample_labels, preds, 10)
    llm_subset = {"n": len(sample), "baseline_0": score_sample(OUT / "baseline_0", raw_images),
                  "final_A2_0": score_sample(stage4 / "A2_0", std_images)}
    print(f"200-image benchmark subset: {llm_subset}", flush=True)
    out = {"metric": "test macro-F1 (points), mean over seeds 0-4", "n_test": len(rows),
           "baseline_extras": baseline_extras()[1], "feature_selection": fs_info, "rows": table,
           "direct_llm_subset": llm_subset}
    RESULTS_JSON.write_text(json.dumps(out, indent=2) + "\n")
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "mean", "std", "delta_vs_baseline"] + [f"seed{s}" for s in SEEDS])
        for row in table:
            w.writerow([row["step"], f"{row['mean']:.2f}", f"{row['std']:.2f}",
                        f"{row['delta_vs_baseline']:+.2f}"] + [f"{v:.2f}" for v in row["per_seed"]])
    print(f"-> {RESULTS_JSON}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["replay", "train", "fs", "evaluate"])
    step = parser.parse_args().step
    {"replay": replay, "train": train, "fs": fs, "evaluate": evaluate}[step]()


if __name__ == "__main__":
    sys.exit(main())
