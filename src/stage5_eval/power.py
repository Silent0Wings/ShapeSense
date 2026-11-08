"""Decision 10 power check (stages/stage_5.md R8, plan 30).

Before any test prediction, Stage 5 estimates how wide the primary CI will
be: the same paired bootstrap as the primary comparison, run on A1's and
B's **validation** soft-vote predictions, then rescaled by
``sqrt(n_val / n_test)``. If the expected half-width exceeds the limit,
the stage discloses the limited power without changing the criterion.

Pure functions: validation probabilities, the test-set size and the RNG
are injected; nothing here reads the test split or the config. F1
quantities are in **points** (0-100), as everywhere in ``stage5_eval``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from src.stage5_eval.metrics import soft_vote
from src.stage5_eval.stats import paired_bootstrap


def rescale_factor(n_val: int, n_test: int) -> float:
    """``sqrt(n_val / n_test)``: a CI half-width shrinks with sqrt(n).

    The validation bootstrap half-width times this factor is the expected
    half-width of the same statistic on the test split.
    """
    if n_val <= 0 or n_test <= 0:
        raise ValueError("n_val and n_test must be positive")
    return math.sqrt(n_val / n_test)


def align_validation_probs(
    seed_records: Sequence[dict],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack per-seed ``val_probs.npz`` records into one ``(n_seeds, n, k)`` array.

    Args:
        seed_records: one dict per seed with keys ``probs`` (n, k),
            ``labels`` (n,) and ``image_ids`` (n,), as saved by Stage 4.

    Returns:
        ``(labels, probs, image_ids)``. Raises ``ValueError`` unless every
        seed lists exactly the same image ids in the same order (the
        soft vote averages row by row, so a permuted seed would silently
        vote on the wrong images).
    """
    if not seed_records:
        raise ValueError("at least one validation record is required")
    ref_ids = np.asarray(seed_records[0]["image_ids"]).astype(str)
    ref_labels = np.asarray(seed_records[0]["labels"], dtype=np.int64)
    stacked = []
    for i, rec in enumerate(seed_records):
        ids = np.asarray(rec["image_ids"]).astype(str)
        if ids.shape != ref_ids.shape or not np.array_equal(ids, ref_ids):
            raise ValueError(
                f"validation record {i} lists different image ids (or a different "
                "order) than record 0; seeds must be aligned by image_id"
            )
        labels = np.asarray(rec["labels"], dtype=np.int64)
        if not np.array_equal(labels, ref_labels):
            raise ValueError(f"validation record {i} has different labels than record 0")
        probs = np.asarray(rec["probs"], dtype=np.float64)
        if probs.ndim != 2 or probs.shape[0] != ref_ids.shape[0]:
            raise ValueError(f"validation record {i}: probs must have shape (n, k)")
        stacked.append(probs)
    return ref_labels, np.stack(stacked, axis=0), ref_ids


def check_arm_alignment(y_a: np.ndarray, ids_a: np.ndarray,
                        y_b: np.ndarray, ids_b: np.ndarray) -> None:
    """Both arms' validation records must list the same images in the same order.

    The paired bootstrap pairs row i of A1 with row i of B, so identical
    labels are not enough: two permutations of the same labels can carry the
    same label array while mismatching the images. Raises ``ValueError``.
    """
    ids_a = np.asarray(ids_a).astype(str)
    ids_b = np.asarray(ids_b).astype(str)
    if ids_a.shape != ids_b.shape or not np.array_equal(ids_a, ids_b):
        raise ValueError("A1 and B validation records list different image ids (or order)")
    if not np.array_equal(np.asarray(y_a, dtype=np.int64), np.asarray(y_b, dtype=np.int64)):
        raise ValueError("A1 and B validation records disagree on labels/order")


def power_check(
    y_val: np.ndarray,
    probs_a1: np.ndarray,
    probs_b: np.ndarray,
    n_test: int,
    n_classes: int,
    n_boot: int,
    rng: np.random.Generator,
    ci_level: float,
    limit_points: float,
) -> dict:
    """Expected test half-width of the primary CI from validation predictions.

    Args:
        y_val: shape (n_val,) validation labels.
        probs_a1, probs_b: shape (n_seeds, n_val, k) validation softmax
            probabilities of every A1 / B seed model, aligned by image id.
        n_test: number of test images (from Stage 1's published counts, so
            no test read is needed).
        n_classes: k.
        n_boot, rng, ci_level: bootstrap settings (``evaluation.n_boot``,
            ``evaluation.bootstrap_seed``, ``success_criterion.ci_level``).
        limit_points: ``evaluation.power_halfwidth_limit_points``.

    Returns:
        dict with ``n_val``, ``n_test``, ``factor`` (sqrt(n_val / n_test)),
        ``half_width_val`` (points), ``expected_test_half_width`` (points),
        ``limit_points``, ``underpowered`` (expected > limit),
        ``delta_val`` and ``ci_val`` (the validation B − A1 macro-F1 and
        its CI, for context only).
    """
    y = np.asarray(y_val, dtype=np.int64)
    pa1 = np.asarray(probs_a1, dtype=np.float64)
    pb = np.asarray(probs_b, dtype=np.float64)
    if pa1.ndim != 3 or pb.ndim != 3:
        raise ValueError("probs_a1 and probs_b must have shape (n_seeds, n_val, k)")
    if pa1.shape[1:] != pb.shape[1:] or pa1.shape[1] != y.size:
        raise ValueError("probs_a1, probs_b and y_val disagree on n_val or k")
    pred_a1 = soft_vote(pa1).argmax(axis=1)
    pred_b = soft_vote(pb).argmax(axis=1)
    boot = paired_bootstrap(y, pred_a1, pred_b, n_classes, n_boot, rng, ci_level)
    n_val = int(y.size)
    factor = rescale_factor(n_val, int(n_test))
    half_width_val = float(boot["half_width"])
    expected = half_width_val * factor
    return {
        "n_val": n_val,
        "n_test": int(n_test),
        "factor": factor,
        "half_width_val": half_width_val,
        "expected_test_half_width": float(expected),
        "limit_points": float(limit_points),
        "underpowered": bool(expected > float(limit_points)),
        "delta_val": float(boot["delta"]),
        "ci_val": [float(v) for v in boot["ci"]],
        "n_boot": int(n_boot),
        "ci_level": float(ci_level),
    }
