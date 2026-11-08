"""Stage 4 — scikit-learn baselines (Decision 14, R13).

Logistic regression on raw pixels and a linear SVM on HOG features, both
trained on the same class-balanced real stream as arm A0 and selected on
the validation split only. Stage 5 evaluates the saved models on test; this
module never sees the test split.

Feature contracts:
  pixel_features: uint8 (N, 64, 64) -> float32 (N, 4096), values in [0, 1]
  hog_features:   uint8 (N, 64, 64) -> float32 (N, D), D = 1764 at ppc 8
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.svm import LinearSVC

from src.common.features import (CELLS_PER_BLOCK, ORIENTATIONS, PIXEL_SCALE,  # noqa: F401
                                 hog_features, pixel_features)

KIND_LOGREG = "logreg_pixels"
KIND_SVM = "svm_hog"
FEATURE_PIXELS = "pixels"
FEATURE_HOG = "hog"
MAX_ITER = 1000  # LogisticRegression solver iterations
MAX_ITER_SVM = 5000  # LinearSVC solver iterations
PERCENT = 100.0  # macro-F1 is stored in points (0-100)


def balanced_subset(labels: np.ndarray, per_class: int, rng: np.random.Generator) -> np.ndarray:
    """Indices with min(per_class, count) draws without replacement per class.

    The returned indices are shuffled with `rng`, so the order is a stream,
    not a block per class.
    """
    labels = np.asarray(labels)
    picked = []
    for cls in np.unique(labels):
        idx = np.flatnonzero(labels == cls)
        take = min(per_class, idx.size)
        picked.append(rng.choice(idx, size=take, replace=False))
    if not picked:
        return np.empty(0, dtype=np.int64)
    chosen = np.concatenate(picked).astype(np.int64)
    return chosen[rng.permutation(chosen.size)]


def _make_estimator(kind: str, C: float) -> Any:
    """Default sklearn estimator for a baseline kind."""
    if kind == KIND_LOGREG:
        return LogisticRegression(C=C, max_iter=MAX_ITER)
    if kind == KIND_SVM:
        return LinearSVC(C=C, max_iter=MAX_ITER_SVM)
    raise ValueError(f"unknown baseline kind: {kind!r}")


def fit_select(
    kind: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    C_grid: list[float],
    n_classes: int,
    estimator_factory: Callable[[str, float], Any] | None = None,
) -> dict:
    """Fit one estimator per C on train, pick the C with best validation macro-F1.

    Selection uses the validation split only. The score is macro-F1 in points
    (0-100) over labels 0..n_classes-1. Ties go to the earlier C in the grid.
    `estimator_factory(kind, C)` defaults to the real sklearn estimators.
    """
    if not C_grid:
        raise ValueError("C_grid must not be empty")
    factory = estimator_factory or _make_estimator
    labels = list(range(n_classes))
    grid: dict[str, float] = {}
    best_model: Any = None
    best_C = float(C_grid[0])
    best_score = -np.inf
    for C in C_grid:
        model = factory(kind, float(C))
        model.fit(X_train, y_train)
        pred = np.asarray(model.predict(X_val))
        score = float(f1_score(y_val, pred, average="macro", labels=labels)) * PERCENT
        grid[str(C)] = score
        if score > best_score:
            best_score = score
            best_C = float(C)
            best_model = model
    return {
        "model": best_model,
        "best_C": best_C,
        "val_macro_f1": best_score,
        "grid": grid,
    }


def save_baseline(model: Any, path: Path) -> None:
    """Persist a fitted baseline with joblib, creating the parent folder."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_baseline(path: Path) -> Any:
    """Load a baseline saved by save_baseline."""
    return joblib.load(Path(path))


def _features_for(kind: str, images_u8: np.ndarray, hog_pixels_per_cell: int | None) -> np.ndarray:
    if kind == KIND_LOGREG:
        return pixel_features(images_u8)
    if kind == KIND_SVM:
        if hog_pixels_per_cell is None:
            raise ValueError("hog_pixels_per_cell is required for the HOG baseline")
        return hog_features(images_u8, hog_pixels_per_cell)
    raise ValueError(f"unknown baseline kind: {kind!r}")


def predict_baseline(
    kind: str,
    model: Any,
    images_u8: np.ndarray,
    hog_pixels_per_cell: int | None,
) -> np.ndarray:
    """Predicted integer labels for uint8 (N, 64, 64) images."""
    features = _features_for(kind, images_u8, hog_pixels_per_cell)
    return np.asarray(model.predict(features))


def train_baselines(
    train_images: np.ndarray,
    train_labels: np.ndarray,
    val_images: np.ndarray,
    val_labels: np.ndarray,
    cfg_baselines: dict,
    n_classes: int,
    rng: np.random.Generator,
    out_dir: Path,
) -> dict:
    """Train both baselines on the balanced real stream and write their artifacts.

    Saves `<kind>.joblib` for each kind and `baselines.json` (utf-8) under
    `out_dir`. Returns the same dict that is written to the JSON file.
    """
    out_dir = Path(out_dir)
    per_class = int(cfg_baselines["per_class"])
    ppc = int(cfg_baselines["hog_pixels_per_cell"])
    val_labels = np.asarray(val_labels)

    idx = balanced_subset(train_labels, per_class, rng)
    sub_images = np.asarray(train_images)[idx]
    sub_labels = np.asarray(train_labels)[idx]

    feature_specs = {
        KIND_LOGREG: (FEATURE_PIXELS, None, [float(c) for c in cfg_baselines["logreg_C"]]),
        KIND_SVM: (FEATURE_HOG, ppc, [float(c) for c in cfg_baselines["svm_C"]]),
    }
    summary: dict[str, dict] = {}
    for kind, (feature, kind_ppc, C_grid) in feature_specs.items():
        X_train = _features_for(kind, sub_images, kind_ppc)
        X_val = _features_for(kind, np.asarray(val_images), kind_ppc)
        result = fit_select(kind, X_train, sub_labels, X_val, val_labels, C_grid, n_classes)
        save_baseline(result["model"], out_dir / f"{kind}.joblib")
        summary[kind] = {
            "features": feature,
            "hog_pixels_per_cell": kind_ppc,
            "best_C": result["best_C"],
            "val_macro_f1": result["val_macro_f1"],
            "grid": result["grid"],
            "n_train": int(idx.size),
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baselines.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
