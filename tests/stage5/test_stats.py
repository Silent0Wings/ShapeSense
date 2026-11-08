"""E29: paired bootstrap, McNemar, Holm, per-seed differences (R5/R6, M2)."""

import numpy as np
import pytest

from src.stage5_eval import stats

K = 3
N_BOOT = 300
CI_LEVEL = 0.95


def _synthetic(n: int = 300, seed: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """y and a prediction that is wrong on ~30% of the images."""
    rng = np.random.default_rng(seed)
    y = rng.integers(0, K, size=n)
    pred = y.copy()
    wrong = rng.random(n) < 0.3
    pred[wrong] = (y[wrong] + 1) % K
    return y, pred


def test_mcnemar_mission_m2():
    # 30 images "a right, b wrong", 50 "a wrong, b right", plus concordant pairs.
    both = 2700
    correct_a = np.array([True] * both + [True] * 30 + [False] * 50 + [False] * 20)
    correct_b = np.array([True] * both + [False] * 30 + [True] * 50 + [False] * 20)
    res = stats.mcnemar_test(correct_a, correct_b)
    assert res["b"] == 30 and res["c"] == 50
    assert res["both_right"] == both and res["both_wrong"] == 20
    assert res["statistic"] == pytest.approx((abs(30 - 50) - 1) ** 2 / 80)
    assert res["statistic"] == pytest.approx(4.5125)
    assert res["p_value"] == pytest.approx(0.0336, abs=5e-4)


def test_mcnemar_no_discordant_pairs():
    ok = np.array([True, False, True])
    res = stats.mcnemar_test(ok, ok)
    assert res["b"] == 0 and res["c"] == 0
    assert res["statistic"] == 0.0 and res["p_value"] == 1.0


def test_holm_known_values():
    adj = stats.holm({"a": 0.01, "b": 0.04})
    assert adj["a"] == pytest.approx(0.02)
    assert adj["b"] == pytest.approx(0.04)
    # Monotone: the smaller raw p cannot end up with a larger adjusted p.
    adj2 = stats.holm({"a": 0.03, "b": 0.02})
    assert adj2["b"] == pytest.approx(0.04)
    assert adj2["a"] == pytest.approx(0.04)
    assert adj2["b"] <= adj2["a"]
    # Capped at 1.
    adj3 = stats.holm({"x": 0.7, "y": 0.9, "z": 0.95})
    assert all(v <= 1.0 for v in adj3.values())
    assert adj3["x"] == pytest.approx(1.0)
    assert stats.holm({}) == {}


def test_bootstrap_paired_same_indices():
    y, pred_a = _synthetic()
    pred_b = pred_a.copy()
    boot = stats.paired_bootstrap(
        y, pred_a, pred_b, K, N_BOOT, np.random.default_rng(0), CI_LEVEL
    )
    # Identical models on identical resamples -> every delta is exactly 0.
    assert boot["delta"] == 0.0
    assert boot["ci"] == [0.0, 0.0]
    assert boot["half_width"] == 0.0
    np.testing.assert_array_equal(boot["drop_observed"], np.zeros(K))
    np.testing.assert_array_equal(boot["drop_ci_lo"], np.zeros(K))
    np.testing.assert_array_equal(boot["drop_ci_hi"], np.zeros(K))


def test_bootstrap_detects_real_gain():
    y, pred_a = _synthetic()
    pred_b = y.copy()  # b is perfect, a is wrong on ~30%
    boot = stats.paired_bootstrap(
        y, pred_a, pred_b, K, N_BOOT, np.random.default_rng(0), CI_LEVEL
    )
    assert boot["delta"] > 0
    assert boot["ci"][0] > 0
    assert boot["ci"][0] <= boot["delta"] <= boot["ci"][1]
    assert boot["half_width"] == pytest.approx((boot["ci"][1] - boot["ci"][0]) / 2)
    # Every class improved under b, so drops (a - b) are negative with CIs < 0.
    assert np.all(boot["drop_observed"] < 0)
    assert np.all(boot["drop_ci_hi"] < 0)
    assert boot["drop_observed"].shape == (K,)


def test_bootstrap_deterministic_for_rng_seed():
    y, pred_a = _synthetic()
    _, pred_b = _synthetic(seed=7)
    b1 = stats.paired_bootstrap(y, pred_a, pred_b, K, N_BOOT, np.random.default_rng(3), CI_LEVEL)
    b2 = stats.paired_bootstrap(y, pred_a, pred_b, K, N_BOOT, np.random.default_rng(3), CI_LEVEL)
    assert b1["ci"] == b2["ci"]
    np.testing.assert_array_equal(b1["drop_ci_lo"], b2["drop_ci_lo"])
    b3 = stats.paired_bootstrap(y, pred_a, pred_b, K, N_BOOT, np.random.default_rng(4), CI_LEVEL)
    assert b3["ci"] != b1["ci"]
    # The observed delta does not depend on the RNG.
    assert b3["delta"] == b1["delta"]


def test_bootstrap_rejects_bad_inputs():
    y, pred_a = _synthetic()
    with pytest.raises(ValueError):
        stats.paired_bootstrap(y, pred_a[:-1], pred_a, K, 10, np.random.default_rng(0), CI_LEVEL)
    with pytest.raises(ValueError):
        stats.paired_bootstrap(y, pred_a, pred_a, K, 0, np.random.default_rng(0), CI_LEVEL)
    with pytest.raises(ValueError):
        stats.paired_bootstrap(y, pred_a, pred_a, K, 10, np.random.default_rng(0), 1.5)


def test_per_seed_differences_same_sign():
    a = {1: 80.0, 2: 81.0, 3: 79.5}
    b = {1: 81.5, 2: 82.0, 3: 80.0}
    res = stats.per_seed_differences(a, b)
    assert res["seeds"] == [1, 2, 3]
    assert res["diffs"] == {1: pytest.approx(1.5), 2: pytest.approx(1.0), 3: pytest.approx(0.5)}
    assert res["mean"] == pytest.approx(1.0)
    assert res["std"] == pytest.approx(0.5)  # ddof=1
    assert res["same_sign"] is True
    mixed = stats.per_seed_differences(a, {1: 81.5, 2: 80.0, 3: 80.0})
    assert mixed["same_sign"] is False
    single = stats.per_seed_differences({1: 80.0}, {1: 82.0})
    assert single["std"] == 0.0 and single["mean"] == pytest.approx(2.0)


def test_per_seed_requires_matching_seeds():
    with pytest.raises(ValueError):
        stats.per_seed_differences({1: 80.0, 2: 81.0}, {1: 81.0, 3: 82.0})
    with pytest.raises(ValueError):
        stats.per_seed_differences({1: 80.0}, {1: 81.0, 2: 82.0})
