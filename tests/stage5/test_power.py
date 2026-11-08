"""E30: Decision 10 power check on validation probabilities (stage_5.md R8)."""

import math

import numpy as np
import pytest

from src.stage5_eval import power

K = 4
N_BOOT = 200  # small for test speed; evaluation.n_boot in production
CI = 0.95  # mirrors success_criterion.ci_level
LIMIT = 1.0  # mirrors evaluation.power_halfwidth_limit_points


def _probs_for(preds: np.ndarray, n_seeds: int, k: int, rng: np.random.Generator) -> np.ndarray:
    """(n_seeds, n, k) probabilities whose soft-vote argmax equals ``preds``."""
    out = rng.uniform(0.0, 0.2, size=(n_seeds, preds.size, k))
    out[:, np.arange(preds.size), preds] += 1.0
    return out / out.sum(axis=2, keepdims=True)


def test_rescale_factor():
    assert power.rescale_factor(3000, 2900) == pytest.approx(math.sqrt(3000 / 2900))
    assert power.rescale_factor(100, 100) == 1.0
    with pytest.raises(ValueError):
        power.rescale_factor(0, 10)


def test_identical_arms_zero_halfwidth():
    rng = np.random.default_rng(0)
    y = rng.integers(0, K, size=300)
    preds = y.copy()
    preds[::7] = (preds[::7] + 1) % K  # some shared errors
    probs = _probs_for(preds, 2, K, rng)
    res = power.power_check(y, probs, probs.copy(), n_test=300, n_classes=K, n_boot=N_BOOT,
                            rng=np.random.default_rng(1), ci_level=CI, limit_points=LIMIT)
    assert res["half_width_val"] == 0.0
    assert res["expected_test_half_width"] == 0.0
    assert res["underpowered"] is False
    assert res["factor"] == pytest.approx(1.0)
    assert res["n_val"] == 300 and res["n_test"] == 300


def test_underpowered_flag():
    rng = np.random.default_rng(0)
    n = 60  # tiny validation set -> wide CI
    y = rng.integers(0, K, size=n)
    noisy_a = np.where(rng.random(n) < 0.35, (y + 1) % K, y)
    noisy_b = np.where(rng.random(n) < 0.35, (y + 2) % K, y)
    probs_a = _probs_for(noisy_a, 2, K, rng)
    probs_b = _probs_for(noisy_b, 2, K, rng)
    res = power.power_check(y, probs_a, probs_b, n_test=n, n_classes=K, n_boot=N_BOOT,
                            rng=np.random.default_rng(1), ci_level=CI, limit_points=LIMIT)
    assert res["half_width_val"] > LIMIT
    assert res["underpowered"] is True
    # A generous limit flips the flag without touching the numbers.
    res2 = power.power_check(y, probs_a, probs_b, n_test=n, n_classes=K, n_boot=N_BOOT,
                             rng=np.random.default_rng(1), ci_level=CI,
                             limit_points=res["expected_test_half_width"] + 1.0)
    assert res2["underpowered"] is False
    assert res2["half_width_val"] == pytest.approx(res["half_width_val"])
    # The rescale factor is applied: a larger test set shrinks the expectation.
    res3 = power.power_check(y, probs_a, probs_b, n_test=4 * n, n_classes=K, n_boot=N_BOOT,
                             rng=np.random.default_rng(1), ci_level=CI, limit_points=LIMIT)
    assert res3["expected_test_half_width"] == pytest.approx(res["half_width_val"] / 2.0)


def test_misaligned_ids_raise():
    n = 20
    ids = np.array([f"img_{i:03d}" for i in range(n)])
    labels = np.arange(n) % K
    rec_a = {"probs": np.full((n, K), 1.0 / K), "labels": labels, "image_ids": ids}
    rec_b = {"probs": np.full((n, K), 1.0 / K), "labels": labels, "image_ids": ids[::-1]}
    with pytest.raises(ValueError, match="image ids"):
        power.align_validation_probs([rec_a, rec_b])
    y, probs, out_ids = power.align_validation_probs([rec_a, dict(rec_a)])
    assert probs.shape == (2, n, K)
    assert np.array_equal(out_ids, ids) and np.array_equal(y, labels)


def test_power_arms_require_identical_ids():
    """A1 and B must list the same validation images, not just the same labels."""
    n = 12
    ids = np.array([f"img_{i:03d}" for i in range(n)])
    labels = np.array([0, 1, 2, 3] * (n // 4))
    # Same label array, different image order: labels alone cannot tell them apart.
    permuted_ids = np.concatenate([ids[4:8], ids[0:4], ids[8:]])
    with pytest.raises(ValueError, match="image ids"):
        power.check_arm_alignment(labels, ids, labels, permuted_ids)
    with pytest.raises(ValueError, match="image ids"):
        power.check_arm_alignment(labels, ids, labels, ids[:-1])
    with pytest.raises(ValueError, match="labels"):
        power.check_arm_alignment(labels, ids, (labels + 1) % K, ids)
    power.check_arm_alignment(labels, ids, labels.copy(), ids.copy())  # aligned: no error
