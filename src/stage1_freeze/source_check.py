"""Source-shortcut check (stages/stage_1.md R13, Decision 12).

Is the image source guessable from standardized pixels? For every class
with two or more sources in train, a logistic regression on mean-pooled
pixels is fit on train and scored on val. Pooled accuracy is compared
with the pooled majority-source rate; a gain above the trigger sets
`shortcut_detected`. Train and val only: the signature has no test input.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression

POOL_SIDE_PX = 16          # downsampled side, pixels (64 -> 16 is 4x4 mean pooling)
PIXEL_MAX = 255.0          # uint8 range -> [0, 1]
LOGREG_MAX_ITER = 1000     # lbfgs iterations
POINTS_PER_UNIT = 100.0    # fraction -> percentage points
MIN_SOURCES = 2            # classes with fewer train sources are skipped


def downsample(images: np.ndarray) -> np.ndarray:
    """uint8 (N, S, S) -> float64 (N, POOL_SIDE_PX**2) mean-pooled, scaled to [0, 1]."""
    n, side, side2 = images.shape
    if side != side2 or side % POOL_SIDE_PX:
        raise ValueError(f"images must be square with side divisible by {POOL_SIDE_PX}, "
                         f"got {images.shape}")
    f = side // POOL_SIDE_PX
    pooled = images.reshape(n, POOL_SIDE_PX, f, POOL_SIDE_PX, f).astype(np.float64)
    return pooled.mean(axis=(2, 4)).reshape(n, -1) / PIXEL_MAX


def shortcut_check(X_train: np.ndarray, y_train: Sequence[int], s_train: Sequence[str],
                   X_val: np.ndarray, y_val: Sequence[int], s_val: Sequence[str],
                   trigger_points: float, rng_seed: int,
                   class_names: Sequence[str] | None = None) -> dict:
    """Per-class source classifiers on train, scored on val; Decision 12 trigger.

    Returns a JSON-ready dict: per-class accuracy, majority source and rate,
    val count; pooled (val-size weighted) accuracy and majority rate;
    gain_points; shortcut_detected; skipped classes (< MIN_SOURCES sources).
    """
    y_tr, y_va = np.asarray(y_train), np.asarray(y_val)
    s_tr, s_va = np.asarray(s_train, dtype=object), np.asarray(s_val, dtype=object)
    f_tr, f_va = downsample(np.asarray(X_train)), downsample(np.asarray(X_val))

    def name(lab: int) -> str:
        return class_names[lab] if class_names is not None else str(lab)

    per_class: dict[str, dict] = {}
    skipped: list[str] = []
    correct = majority = n_val_total = 0
    for lab in sorted(set(int(v) for v in y_tr)):
        tr, va = y_tr == lab, y_va == lab
        train_sources = Counter(s_tr[tr].tolist())
        if len(train_sources) < MIN_SOURCES or not va.any():
            skipped.append(name(lab))
            continue
        majority_source = train_sources.most_common(1)[0][0]
        clf = LogisticRegression(max_iter=LOGREG_MAX_ITER, random_state=rng_seed)
        clf.fit(f_tr[tr], s_tr[tr].astype(str))
        pred = clf.predict(f_va[va])
        truth = s_va[va].astype(str)
        n_c = int(va.sum())
        hit = int((pred == truth).sum())
        maj = int((truth == majority_source).sum())
        correct += hit
        majority += maj
        n_val_total += n_c
        per_class[name(lab)] = {
            "label_id": lab,
            "sources": sorted(train_sources),
            "n_train": int(tr.sum()),
            "n_val": n_c,
            "accuracy": hit / n_c,
            "majority_source": majority_source,
            "majority_rate": maj / n_c,
        }

    pooled_acc = correct / n_val_total if n_val_total else 0.0
    pooled_maj = majority / n_val_total if n_val_total else 0.0
    gain = POINTS_PER_UNIT * (pooled_acc - pooled_maj)
    return {
        "classes": per_class,
        "skipped_classes": skipped,
        "n_val_evaluated": n_val_total,
        "pooled_accuracy": pooled_acc,
        "pooled_majority_rate": pooled_maj,
        "gain_points": gain,
        "trigger_points": float(trigger_points),
        "shortcut_detected": bool(gain > float(trigger_points)),
        "features": f"{POOL_SIDE_PX}x{POOL_SIDE_PX} mean-pooled pixels / {int(PIXEL_MAX)}",
        "model": f"LogisticRegression(max_iter={LOGREG_MAX_ITER})",
        "splits_used": ["train", "val"],
    }
