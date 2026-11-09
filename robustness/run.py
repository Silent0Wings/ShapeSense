"""Build the perturbed validation sets once, then score every trained model on them.

    python -m robustness.run

Validation data only: the sets are saved under artifacts/robustness/val_sets and
never regenerated, so every model scores identical images. The summary goes to
docs/crisp_dm/iteration_2/robustness/. This is a descriptive check made after
iteration 2 closed, and it changes no verdict.
"""

from __future__ import annotations

import json

import numpy as np
import torch
from PIL import Image, ImageDraw
from src.common.config import REPO_ROOT, class_names, load_config, resolve
from src.common.hashing import sha256_path
from src.common.perturb import SETS, build_set
from src.common.robust_summary import summarise
from src.stage4_train.data import ImageStore
from src.stage4_train.sampling import to_float
from src.stage4_train.train import macro_f1_points


SPLIT = "val"
SEED = 20261109
ARMS = ("A0", "A1", "B", "A2")
BATCH = 1024
EXAMPLE_CLASSES = ("square", "star")
RECORDED_TOLERANCE = 0.01
NOTE = "Validation images only, perturbed once with a fixed seed. Descriptive; made after iteration 2 closed; changes no verdict."
OUT = REPO_ROOT / "docs" / "crisp_dm" / "iteration_2" / "robustness"


def build_all(store: ImageStore, sets_dir) -> dict[str, np.ndarray]:
    """Create any missing set; an existing set is read back and checked, never rewritten."""
    sets_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = sets_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    out = {}
    for name in SETS:
        path = sets_dir / f"{name}.npz"
        if name in manifest:
            if sha256_path(path) != manifest[name]:
                raise RuntimeError(f"saved set {name} changed on disk")
        else:
            np.savez_compressed(path, images=build_set(name, store.images, SEED))
            manifest[name] = sha256_path(path)
        with np.load(path) as saved:
            out[name] = saved["images"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out


def predict(model, images: np.ndarray, device: str) -> np.ndarray:
    out = []
    with torch.no_grad():
        for start in range(0, len(images), BATCH):
            x = torch.from_numpy(to_float(images[start:start + BATCH])).to(device)
            out.append(model(x).argmax(1).cpu().numpy())
    return np.concatenate(out)


def confusion(labels: np.ndarray, preds: np.ndarray, n: int) -> np.ndarray:
    return np.bincount(labels * n + preds, minlength=n * n).reshape(n, n)


def score(store: ImageStore, sets: dict[str, np.ndarray], seeds: list[int], stage4, device: str) -> dict:
    labels, n = store.labels, store.n_classes
    per_run: dict[str, dict[int, dict[str, dict]]] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        for seed in seeds:
            run = f"{arm}_{seed}"
            model = torch.jit.load(str(stage4 / run / "model.pt"), map_location=device).eval()
            scores = {}
            for name, images in sets.items():
                preds = predict(model, images, device)
                matrix = confusion(labels, preds, n)
                support = matrix.sum(1)
                scores[name] = {"accuracy": 100.0 * float((preds == labels).mean()),
                                "macro_f1": macro_f1_points(labels, preds, n), "matrix": matrix,
                                "recall": 100.0 * np.diag(matrix) / np.maximum(support, 1)}
            recorded = json.loads((stage4 / run / "run.json").read_text(encoding="utf-8"))["val_macro_f1"]
            if abs(scores["clean"]["macro_f1"] - recorded) > RECORDED_TOLERANCE:
                raise RuntimeError(f"{run}: clean {scores['clean']['macro_f1']} differs from recorded {recorded}")
            per_run[arm][seed] = scores
            print(f"{run}: clean accuracy {scores['clean']['accuracy']:.2f}", flush=True)
    return per_run


def example_sheet(store: ImageStore, sets: dict[str, np.ndarray], labels: list[str], path) -> None:
    """One column per set, one row per example class, labelled above each column."""
    cell, head = 72, 18
    columns = list(SETS)
    sheet = Image.new("L", (len(columns) * cell, head + cell * len(EXAMPLE_CLASSES)), 255)
    draw = ImageDraw.Draw(sheet)
    for x, name in enumerate(columns):
        draw.text((x * cell + 2, 3), name.replace("saltpepper", "s&p ")[:11], fill=0)
        for y, label in enumerate(EXAMPLE_CLASSES):
            index = int(store.class_idx[labels.index(label)][0])
            sheet.paste(Image.fromarray(sets[name][index]), (x * cell + 4, head + y * cell + 4))
    sheet.save(path)


def main() -> None:
    config = load_config()
    store = ImageStore.from_split(config, SPLIT)
    artifacts = resolve(config["paths"]["artifacts_dir"])
    sets = build_all(store, artifacts / "robustness" / "val_sets")
    seeds = [int(s) for s in config["seed_set"]]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    labels = class_names(config)
    per_run = score(store, sets, seeds, artifacts / "stage4", device)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(summarise(per_run, seeds, labels, len(store), SPLIT, SEED, NOTE), indent=1) + "\n", encoding="utf-8")
    example_sheet(store, sets, labels, OUT / "examples.png")
    print(f"wrote {OUT / 'results.json'}")


if __name__ == "__main__":
    main()
