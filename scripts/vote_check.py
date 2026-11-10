"""Compare equal-weight and per-class-weight voting on validation only.

``python -m scripts.vote_check`` uses the saved validation probabilities of
the exported runs, learns per-class weights on one half of validation and scores
on the other half, with each near-duplicate group kept in one half. Writes
docs/crisp_dm/iteration_3/experiments/vote_check.json. Validation was already
used for tuning, so these scores are optimistic and say nothing about test data.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from studio.settings import ARMS, ARMS_MANIFEST, PACKAGE_DIR

REPO = PACKAGE_DIR.parent
OUT = REPO / "docs" / "crisp_dm" / "iteration_3" / "experiments" / "vote_check.json"
SPLIT_SEED = 20261109
ADOPT_MARGIN = 0.5   # points; the margin iteration 3 used for its budget rule


def macro_f1(labels: np.ndarray, predicted: np.ndarray, n_classes: int) -> np.ndarray:
    """F1 per class, in points."""
    out = np.zeros(n_classes)
    for c in range(n_classes):
        tp = np.sum((labels == c) & (predicted == c))
        denom = 2 * tp + np.sum((labels != c) & (predicted == c)) + np.sum((labels == c) & (predicted != c))
        out[c] = 200.0 * tp / denom if denom else 0.0
    return out


def split_groups(labels: np.ndarray, groups: np.ndarray, seed: int = SPLIT_SEED) -> np.ndarray:
    """True for images in the first half, balanced by class; every group stays whole."""
    folds = StratifiedGroupKFold(n_splits=2, shuffle=True, random_state=seed)
    _, first = next(folds.split(np.zeros(len(labels)), labels, groups))
    half = np.zeros(len(labels), dtype=bool)
    half[first] = True
    return half


def _score(labels: np.ndarray, predicted: np.ndarray, n_classes: int) -> float:
    """Macro-F1 over the classes present, so an absent class is not counted as a zero."""
    return float(macro_f1(labels, predicted, n_classes)[np.unique(labels)].mean())


def _class_weights(labels: np.ndarray, predicted: np.ndarray, n_classes: int) -> np.ndarray:
    """F1 per class on the learning half; a class it lacks gets the same weight for every arm."""
    weights = macro_f1(labels, predicted, n_classes)
    weights[np.setdiff1d(np.arange(n_classes), labels)] = 1.0
    return weights


def scores_on(probs: np.ndarray, labels: np.ndarray, learn: np.ndarray, hold: np.ndarray, names: list[str]) -> dict[str, float]:
    """Held-apart macro-F1 of each arm, the equal vote and the per-class vote. probs: (arms, n, k)."""
    k = probs.shape[2]
    out = {name: _score(labels[hold], p[hold].argmax(1), k) for name, p in zip(names, probs)}
    out["equal"] = _score(labels[hold], probs[:, hold].mean(0).argmax(1), k)
    weights = np.stack([_class_weights(labels[learn], p[learn].argmax(1), k) for p in probs])   # (arms, k)
    weighted = (weights[:, None, :] * probs[:, hold]).sum(0)
    out["per_class"] = _score(labels[hold], weighted.argmax(1), k)
    return out


def compare(probs: np.ndarray, labels: np.ndarray, groups: np.ndarray, names: list[str]) -> dict:
    half = split_groups(labels, groups)
    folds = [scores_on(probs, labels, half, ~half, names), scores_on(probs, labels, ~half, half, names)]
    mean = {key: float(np.mean([f[key] for f in folds])) for key in folds[0]}
    gain = mean["per_class"] - mean["equal"]
    return {"held_apart_macro_f1": mean, "folds": folds, "per_class_gain_over_equal": gain,
            "margin": ADOPT_MARGIN, "keep": "per_class" if gain >= ADOPT_MARGIN else "equal"}


def main() -> None:
    manifest = json.loads(ARMS_MANIFEST.read_text(encoding="utf-8"))
    with open(REPO / "configs" / "splits" / "val.csv", encoding="utf-8", newline="") as f:
        group_of = {r["image_id"]: r["phash_group"] for r in csv.DictReader(f)}
    names = [arm for arm in ARMS if arm in manifest]
    probs, labels, ids = [], None, None
    for arm in names:
        with np.load(Path(REPO / "artifacts" / "stage4" / manifest[arm]["run"] / "val_probs.npz"), allow_pickle=False) as z:
            probs.append(z["probs"].astype(np.float64))
            if ids is None:
                labels, ids = z["labels"], z["image_ids"].astype(str)
            elif not np.array_equal(ids, z["image_ids"].astype(str)):
                raise ValueError(f"{arm} scored its validation images in a different order")
    groups = np.array([group_of[i] for i in ids])
    result = compare(np.stack(probs), labels, groups, names)
    result.update(runs={arm: manifest[arm]["run"] for arm in names}, note="Validation only, reused from tuning, so scores are optimistic.")
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
