"""Pure classification metrics for Stage 5 (plan 29, stage_5.md R2/R3).

Every function here is a pure NumPy function on arrays: no file I/O, no
global RNG, no config access. Values that belong to the config (class
names, confusion pairs) are passed in by the caller.

Units convention (applies to the whole ``stage5_eval`` package):
  * F1 values (per-class and macro) are reported in **points**, i.e. on a
    0–100 scale, at every public API boundary.
  * Accuracy is reported as a fraction in [0, 1].

Label arrays are integer class indices in ``range(n_classes)``.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence

import numpy as np

F1_POINTS_SCALE = 100.0  # points per unit of F1 fraction


def _as_labels(y: np.ndarray, name: str, n_classes: int) -> np.ndarray:
    """Validate and return ``y`` as a 1-D int64 array of class indices."""
    arr = np.asarray(y)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got shape {arr.shape}")
    arr = arr.astype(np.int64, copy=False)
    if arr.size and (arr.min() < 0 or arr.max() >= n_classes):
        raise ValueError(
            f"{name} contains labels outside range(0, {n_classes})"
        )
    return arr


def confusion(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> np.ndarray:
    """Confusion matrix with rows = true class, columns = predicted class.

    Args:
        y_true: shape (n,), int class indices.
        y_pred: shape (n,), int class indices.
        n_classes: number of classes k.

    Returns:
        int64 array of shape (k, k); ``conf[t, p]`` is the number of
        images of true class ``t`` predicted as ``p``.
    """
    if n_classes <= 0:
        raise ValueError("n_classes must be positive")
    yt = _as_labels(y_true, "y_true", n_classes)
    yp = _as_labels(y_pred, "y_pred", n_classes)
    if yt.shape != yp.shape:
        raise ValueError(
            f"y_true and y_pred differ in length: {yt.shape} vs {yp.shape}"
        )
    codes = yt * n_classes + yp
    return np.bincount(codes, minlength=n_classes * n_classes).reshape(
        n_classes, n_classes
    )


def f1_from_confusion(conf: np.ndarray) -> np.ndarray:
    """Per-class F1 in **points** from one or many confusion matrices.

    Args:
        conf: shape (..., k, k); leading dimensions are independent
            confusion matrices (used by the vectorised bootstrap).

    Returns:
        float64 array of shape (..., k). A class with no true samples and
        no predicted samples (tp = fp = fn = 0) gets F1 = 0 points.
    """
    conf = np.asarray(conf, dtype=np.float64)
    if conf.ndim < 2 or conf.shape[-1] != conf.shape[-2]:
        raise ValueError(f"conf must have shape (..., k, k), got {conf.shape}")
    tp = np.diagonal(conf, axis1=-2, axis2=-1)
    fp = conf.sum(axis=-2) - tp  # column sums minus diagonal
    fn = conf.sum(axis=-1) - tp  # row sums minus diagonal
    denom = 2.0 * tp + fp + fn
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = np.where(denom > 0, 2.0 * tp / np.where(denom > 0, denom, 1.0), 0.0)
    return f1 * F1_POINTS_SCALE


def per_class_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> np.ndarray:
    """Per-class F1 in **points** (0–100).

    Returns:
        float64 array of shape (k,). A class absent from both ``y_true``
        and ``y_pred`` gets F1 = 0 (it has no true positives and the
        0/0 case is defined as 0 so that macro-F1 stays a plain mean).
    """
    return f1_from_confusion(confusion(y_true, y_pred, n_classes))


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    """Macro-F1 in **points**: the plain mean of per-class F1 over all k classes."""
    return float(per_class_f1(y_true, y_pred, n_classes).mean())


def accuracy(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    """Accuracy as a fraction in [0, 1] (trace of the confusion over n)."""
    conf = confusion(y_true, y_pred, n_classes)
    n = conf.sum()
    if n == 0:
        raise ValueError("accuracy is undefined for zero samples")
    return float(np.trace(conf) / n)


def soft_vote(probs: np.ndarray) -> np.ndarray:
    """Soft-vote ensemble: average softmax probabilities over models.

    Args:
        probs: shape (n_models, n_images, k), probabilities per model.

    Returns:
        float64 array of shape (n_images, k) — the mean over axis 0.
        Predictions are ``soft_vote(probs).argmax(axis=1)``.
    """
    arr = np.asarray(probs, dtype=np.float64)
    if arr.ndim != 3:
        raise ValueError(
            f"probs must have shape (n_models, n_images, k), got {arr.shape}"
        )
    if arr.shape[0] == 0:
        raise ValueError("soft_vote needs at least one model")
    return arr.mean(axis=0)


def group_accuracy(
    y_true: np.ndarray, y_pred: np.ndarray, groups: Sequence[Hashable] | np.ndarray
) -> dict[Hashable, float]:
    """Accuracy (fraction in [0, 1]) per group, e.g. per source or domain.

    Args:
        y_true, y_pred: shape (n,).
        groups: length-n sequence of group keys (any hashable).

    Returns:
        dict mapping each distinct group key to its accuracy.
    """
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    g = np.asarray(groups)
    if not (yt.shape == yp.shape == g.shape) or yt.ndim != 1:
        raise ValueError("y_true, y_pred and groups must all be 1-D of equal length")
    correct = yt == yp
    out: dict[Hashable, float] = {}
    for key in np.unique(g):
        mask = g == key
        out[key.item() if hasattr(key, "item") else key] = float(correct[mask].mean())
    return out


def pair_confusions(
    conf: np.ndarray,
    class_names: Sequence[str],
    pairs: Sequence[Sequence[str]],
) -> list[dict]:
    """Report both directions of each named confusion pair (R3).

    Args:
        conf: shape (k, k) confusion matrix (rows true, cols predicted).
        class_names: length-k names indexing ``conf``.
        pairs: iterable of ``(a, b)`` class-name pairs.

    Returns:
        One dict per pair: ``{"a", "b", "a_to_b", "b_to_a"}`` where
        ``a_to_b`` is the count of true ``a`` predicted as ``b``.
    """
    conf = np.asarray(conf)
    if conf.ndim != 2 or conf.shape[0] != conf.shape[1] or conf.shape[0] != len(class_names):
        raise ValueError("conf must be (k, k) and class_names must have length k")
    index = {name: i for i, name in enumerate(class_names)}
    out = []
    for a, b in pairs:
        if a not in index or b not in index:
            raise ValueError(f"unknown class in pair ({a}, {b})")
        ia, ib = index[a], index[b]
        out.append(
            {
                "a": a,
                "b": b,
                "a_to_b": int(conf[ia, ib]),
                "b_to_a": int(conf[ib, ia]),
            }
        )
    return out
