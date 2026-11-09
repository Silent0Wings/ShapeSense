"""The locked success criterion (stage_5.md R7, implementation.md Decision 10).

Pure functions. Thresholds, gains and noise bands are passed in by the
caller (from ``configs/pipeline.yaml`` and ``artifacts/stage1/split_stats.csv``);
nothing is read here. All F1 quantities are in **points** (0–100).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from src.stage5_eval.metrics import F1_POINTS_SCALE


def noise_band_points(n: int, accuracy: float = 0.9) -> float:
    """Sampling noise band of a class's F1 in points.

    ``100 * sqrt(p (1 − p) / n)``: one standard error of recall at
    accuracy ``p`` for a class with ``n`` test images. Example: n = 150
    gives ≈ 2.45 points.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 < accuracy < 1.0:
        raise ValueError("accuracy must lie strictly between 0 and 1")
    return F1_POINTS_SCALE * math.sqrt(accuracy * (1.0 - accuracy) / n)


def class_thresholds(
    noise_bands_points: Sequence[float] | np.ndarray, min_drop_points: float
) -> np.ndarray:
    """Per-class drop threshold ``max(min_drop_points, noise_band_c)`` in points.

    Returns:
        float64 array of shape (k,).
    """
    bands = np.asarray(noise_bands_points, dtype=np.float64)
    if bands.ndim != 1:
        raise ValueError("noise_bands_points must be 1-D")
    return np.maximum(float(min_drop_points), bands)


def verdict(
    boot: dict,
    thresholds_points: Sequence[float] | np.ndarray,
    min_gain_points: float,
    report_drop_points: float | None = None,
) -> dict:
    """Apply the locked criterion to a paired-bootstrap result.

    Pass iff
      1. ``boot["delta"] >= min_gain_points`` (ensemble macro-F1 gain), and
      2. ``boot["ci"][0] > 0`` (CI excludes 0), and
      3. no class has both ``drop_observed > threshold_c`` and
         ``drop_ci_lo > 0`` (harmful class drop).

    Args:
        boot: output of ``stats.paired_bootstrap`` (points).
        thresholds_points: shape (k,) per-class drop thresholds from
            ``class_thresholds`` (points).
        min_gain_points: minimum macro-F1 gain (points).
        report_drop_points: optional; when given, any class whose observed
            drop exceeds this value is also listed in ``reported_drops``
            even if its CI includes 0 and it is within its threshold.

    Returns:
        dict with ``verdict`` ("pass"/"fail"), ``delta``, ``ci``,
        ``reasons`` (human-readable failure reasons, empty on pass),
        ``harmful_classes`` (indices failing rule 3) and
        ``reported_drops`` (indices with a notable drop that does **not**
        fail: observed drop above threshold with CI including 0, or a
        drop with CI excluding 0 that stays within the threshold, or a
        drop above ``report_drop_points``).
    """
    thresholds = np.asarray(thresholds_points, dtype=np.float64)
    drop = np.asarray(boot["drop_observed"], dtype=np.float64)
    drop_lo = np.asarray(boot["drop_ci_lo"], dtype=np.float64)
    if not (thresholds.shape == drop.shape == drop_lo.shape) or thresholds.ndim != 1:
        raise ValueError("thresholds, drop_observed and drop_ci_lo must share shape (k,)")

    delta = float(boot["delta"])
    ci_lo, ci_hi = (float(v) for v in boot["ci"])

    reasons: list[str] = []
    if delta < min_gain_points:
        reasons.append(f"gain {delta:.2f} < {float(min_gain_points):.2f} points")
    if ci_lo <= 0.0:
        reasons.append(f"CI includes 0 ([{ci_lo:.2f}, {ci_hi:.2f}])")

    above = drop > thresholds
    significant = drop_lo > 0.0
    harmful = above & significant
    for c in np.flatnonzero(harmful):
        reasons.append(
            f"class {int(c)}: drop {drop[c]:.2f} > {thresholds[c]:.2f} and CI excludes 0"
        )

    reported = (above & ~significant) | (significant & ~above)
    if report_drop_points is not None:
        reported |= drop > float(report_drop_points)
    reported &= ~harmful

    return {
        "verdict": "pass" if not reasons else "fail",
        "delta": delta,
        "ci": [ci_lo, ci_hi],
        "reasons": reasons,
        "harmful_classes": [int(c) for c in np.flatnonzero(harmful)],
        "reported_drops": [int(c) for c in np.flatnonzero(reported)],
    }


def robust_verdict(boot: dict, min_drop_points: float, min_gain_points: float) -> dict:
    """The pre-registered iteration 3 rule, applied to a ``cluster_bootstrap`` result.

    Pass iff the gain reaches ``min_gain_points``, the CI excludes 0, and no class
    has a mean drop above max(``min_drop_points``, one bootstrap standard error of
    that drop) with a Bonferroni-corrected CI excluding 0. ``strict_pass`` also
    needs the CI to clear the minimum gain; it is reported and not required.
    """
    drop = np.asarray(boot["drop_observed"], dtype=np.float64)
    thresholds = np.maximum(float(min_drop_points), np.asarray(boot["drop_se"], dtype=np.float64))
    significant = np.asarray(boot["drop_ci_lo_adj"], dtype=np.float64) > 0.0
    harmful = (drop > thresholds) & significant
    delta = float(boot["delta"])
    ci_lo, ci_hi = (float(v) for v in boot["ci"])
    reasons: list[str] = []
    if delta < min_gain_points:
        reasons.append(f"gain {delta:.2f} < {float(min_gain_points):.2f} points")
    if ci_lo <= 0.0:
        reasons.append(f"CI includes 0 ([{ci_lo:.2f}, {ci_hi:.2f}])")
    for c in np.flatnonzero(harmful):
        reasons.append(f"class {int(c)}: drop {drop[c]:.2f} > {thresholds[c]:.2f} and corrected CI excludes 0")
    return {"verdict": "pass" if not reasons else "fail", "delta": delta, "ci": [ci_lo, ci_hi],
            "reasons": reasons, "harmful_classes": [int(c) for c in np.flatnonzero(harmful)],
            "strict_pass": not reasons and ci_lo >= float(min_gain_points)}
