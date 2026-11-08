"""Paired statistics for Stage 5 (plan 29, stage_5.md R5/R6, Decision 9).

Pure functions: the RNG is injected, nothing is read from disk or config.
F1 quantities are in **points** (0–100); see ``metrics`` for the
package-wide units convention.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

from src.stage5_eval.metrics import f1_from_confusion

BOOT_CHUNK = 256  # bootstrap iterations processed per vectorised block


def _confusions_at(
    codes: np.ndarray, idx: np.ndarray, n_classes: int
) -> np.ndarray:
    """Confusion matrices for many resamples at once.

    Args:
        codes: shape (n,), ``y_true * k + y_pred`` per image.
        idx: shape (n_iter, n), resampled image indices.
        n_classes: k.

    Returns:
        int64 array (n_iter, k, k).
    """
    n_iter = idx.shape[0]
    kk = n_classes * n_classes
    offsets = (np.arange(n_iter, dtype=np.int64) * kk)[:, None]
    flat = (codes[idx] + offsets).ravel()
    return np.bincount(flat, minlength=n_iter * kk).reshape(n_iter, n_classes, n_classes)


def paired_bootstrap(
    y: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    n_classes: int,
    n_boot: int,
    rng: np.random.Generator,
    ci_level: float,
) -> dict:
    """Paired bootstrap of the macro-F1 difference (b minus a) in points.

    Both models are scored on the **same** resampled indices in every
    iteration — that pairing is what makes the CI of the difference
    valid (stage_5.md pitfall "comparing unpaired runs").

    Args:
        y: shape (n,) true labels.
        pred_a, pred_b: shape (n,) predictions of the reference model (a)
            and the candidate model (b).
        n_classes: k.
        n_boot: number of bootstrap resamples (e.g. 2000).
        rng: injected ``np.random.Generator``.
        ci_level: e.g. 0.95 for a 95% percentile interval.

    Returns:
        dict with keys
          ``delta``: observed macro-F1(b) − macro-F1(a), points;
          ``ci``: [lo, hi] percentile CI of the bootstrap delta, points;
          ``half_width``: (hi − lo) / 2, points;
          ``drop_observed``: per-class F1(a) − F1(b), points, shape (k,);
          ``drop_ci_lo`` / ``drop_ci_hi``: per-class percentile bounds of
          the bootstrap drop, shape (k,);
          ``n_boot``, ``ci_level`` echoed back.
    """
    y = np.asarray(y, dtype=np.int64)
    pa = np.asarray(pred_a, dtype=np.int64)
    pb = np.asarray(pred_b, dtype=np.int64)
    if not (y.shape == pa.shape == pb.shape) or y.ndim != 1 or y.size == 0:
        raise ValueError("y, pred_a and pred_b must be non-empty 1-D arrays of equal length")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    if not 0.0 < ci_level < 1.0:
        raise ValueError("ci_level must lie strictly between 0 and 1")

    n = y.size
    codes_a = y * n_classes + pa
    codes_b = y * n_classes + pb

    # Observed statistics.
    f1_a = f1_from_confusion(
        np.bincount(codes_a, minlength=n_classes**2).reshape(n_classes, n_classes)
    )
    f1_b = f1_from_confusion(
        np.bincount(codes_b, minlength=n_classes**2).reshape(n_classes, n_classes)
    )
    delta = float(f1_b.mean() - f1_a.mean())
    drop_observed = f1_a - f1_b

    # Bootstrap: one index draw per iteration, shared by both models.
    deltas = np.empty(n_boot, dtype=np.float64)
    drops = np.empty((n_boot, n_classes), dtype=np.float64)
    start = 0
    while start < n_boot:
        stop = min(start + BOOT_CHUNK, n_boot)
        idx = rng.integers(0, n, size=(stop - start, n))
        fa = f1_from_confusion(_confusions_at(codes_a, idx, n_classes))
        fb = f1_from_confusion(_confusions_at(codes_b, idx, n_classes))
        deltas[start:stop] = fb.mean(axis=1) - fa.mean(axis=1)
        drops[start:stop] = fa - fb
        start = stop

    alpha = 1.0 - ci_level
    q_lo, q_hi = 100.0 * alpha / 2.0, 100.0 * (1.0 - alpha / 2.0)
    lo, hi = np.percentile(deltas, [q_lo, q_hi])
    drop_lo = np.percentile(drops, q_lo, axis=0)
    drop_hi = np.percentile(drops, q_hi, axis=0)

    return {
        "delta": delta,
        "ci": [float(lo), float(hi)],
        "half_width": float((hi - lo) / 2.0),
        "drop_observed": drop_observed,
        "drop_ci_lo": drop_lo,
        "drop_ci_hi": drop_hi,
        "n_boot": int(n_boot),
        "ci_level": float(ci_level),
    }


def mcnemar_test(correct_a: np.ndarray, correct_b: np.ndarray) -> dict:
    """McNemar's test on paired per-image correctness (stage_5.md M2).

    Uses the chi-square approximation with continuity correction:
    statistic = (|b − c| − 1)² / (b + c).

    Args:
        correct_a, correct_b: shape (n,) booleans, one entry per image.

    Returns:
        dict with ``b`` (a right, b wrong), ``c`` (a wrong, b right),
        ``both_right``, ``both_wrong``, ``statistic`` and ``p_value``.
        If no image is discordant (b + c = 0) the statistic is 0 and the
        p-value is 1.
    """
    ca = np.asarray(correct_a, dtype=bool)
    cb = np.asarray(correct_b, dtype=bool)
    if ca.shape != cb.shape or ca.ndim != 1:
        raise ValueError("correct_a and correct_b must be 1-D of equal length")
    both_right = int(np.sum(ca & cb))
    b = int(np.sum(ca & ~cb))
    c = int(np.sum(~ca & cb))
    both_wrong = int(np.sum(~ca & ~cb))
    if b + c == 0:
        statistic, p_value = 0.0, 1.0
    else:
        res = mcnemar([[both_right, b], [c, both_wrong]], exact=False, correction=True)
        statistic, p_value = float(res.statistic), float(res.pvalue)
    return {
        "b": b,
        "c": c,
        "both_right": both_right,
        "both_wrong": both_wrong,
        "statistic": statistic,
        "p_value": p_value,
    }


def holm(pvals: Mapping[str, float]) -> dict[str, float]:
    """Holm–Bonferroni adjusted p-values.

    Sort the m p-values ascending, multiply the i-th (1-based) by
    ``m − i + 1``, enforce monotonicity with a running maximum and cap
    at 1. Returns a dict with the same keys.
    """
    if not pvals:
        return {}
    keys = list(pvals.keys())
    p = np.asarray([pvals[k] for k in keys], dtype=np.float64)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("p-values must lie in [0, 1]")
    m = p.size
    order = np.argsort(p, kind="stable")
    multipliers = m - np.arange(m)
    adjusted_sorted = np.minimum(1.0, np.maximum.accumulate(p[order] * multipliers))
    adjusted = np.empty(m, dtype=np.float64)
    adjusted[order] = adjusted_sorted
    return {k: float(v) for k, v in zip(keys, adjusted)}


def per_seed_differences(
    scores_a: Mapping[int, float], scores_b: Mapping[int, float]
) -> dict:
    """Paired per-seed differences (seed k of b minus seed k of a).

    Args:
        scores_a, scores_b: mapping seed → score (same unit, e.g. macro-F1
            points). The key sets must match exactly.

    Returns:
        dict with ``seeds`` (sorted), ``diffs`` (seed → b − a), ``mean``,
        ``std`` (ddof=1 when n > 1, else 0) and ``same_sign`` (True when
        every difference is strictly positive or every one is strictly
        negative).
    """
    if set(scores_a) != set(scores_b):
        raise ValueError(
            f"seed sets differ: {sorted(scores_a)} vs {sorted(scores_b)}"
        )
    if not scores_a:
        raise ValueError("at least one seed is required")
    seeds = sorted(scores_a)
    diffs = np.asarray([scores_b[s] - scores_a[s] for s in seeds], dtype=np.float64)
    ddof = 1 if diffs.size > 1 else 0
    same_sign = bool(np.all(diffs > 0) or np.all(diffs < 0))
    return {
        "seeds": seeds,
        "diffs": {s: float(d) for s, d in zip(seeds, diffs)},
        "mean": float(diffs.mean()),
        "std": float(diffs.std(ddof=ddof)),
        "same_sign": same_sign,
    }
