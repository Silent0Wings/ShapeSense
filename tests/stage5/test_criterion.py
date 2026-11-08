"""E29: the locked success criterion (R7, Decision 10, Mission M3). Points."""

import numpy as np
import pytest

from src.stage5_eval import criterion

K = 4
MIN_GAIN = 1.0  # points, mirrors success_criterion.macro_f1_min_gain_points
MIN_DROP = 2.0  # points, mirrors success_criterion.max_class_f1_drop_points
NOISE_ACC = 0.9  # mirrors evaluation.noise_band_accuracy


def _boot(delta, ci, drop=None, drop_lo=None, drop_hi=None) -> dict:
    """Build a paired_bootstrap-shaped dict with neutral per-class drops."""
    return {
        "delta": delta,
        "ci": list(ci),
        "drop_observed": np.asarray(drop if drop is not None else np.zeros(K), dtype=float),
        "drop_ci_lo": np.asarray(drop_lo if drop_lo is not None else -np.ones(K), dtype=float),
        "drop_ci_hi": np.asarray(drop_hi if drop_hi is not None else np.ones(K), dtype=float),
    }


def test_noise_band_decision_10_table():
    assert criterion.noise_band_points(150, NOISE_ACC) == pytest.approx(2.4495, abs=1e-4)
    assert round(criterion.noise_band_points(150, NOISE_ACC), 1) == 2.4
    assert criterion.noise_band_points(572, NOISE_ACC) == pytest.approx(1.254, abs=1e-3)
    assert criterion.noise_band_points(375, NOISE_ACC) == pytest.approx(1.549, abs=1e-3)
    with pytest.raises(ValueError):
        criterion.noise_band_points(0, NOISE_ACC)


def test_class_thresholds_max_of_floor_and_band():
    bands = np.array([2.45, 1.25, 1.55])
    np.testing.assert_allclose(criterion.class_thresholds(bands, MIN_DROP), [2.45, 2.0, 2.0])


def test_small_gain_fails():
    res = criterion.verdict(_boot(0.6, [0.1, 1.1]), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "fail"
    assert any(r.startswith("gain") for r in res["reasons"])
    assert not any("CI includes 0" in r for r in res["reasons"])
    assert res["harmful_classes"] == []
    assert res["delta"] == 0.6 and res["ci"] == [0.1, 1.1]


def test_ci_including_zero_fails():
    res = criterion.verdict(_boot(1.8, [-0.2, 3.8]), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "fail"
    assert any("CI includes 0" in r for r in res["reasons"])
    assert not any(r.startswith("gain") for r in res["reasons"])
    # A CI touching exactly 0 also fails ("excludes 0" is strict).
    res0 = criterion.verdict(_boot(1.8, [0.0, 3.8]), np.full(K, MIN_DROP), MIN_GAIN)
    assert res0["verdict"] == "fail"


def test_drop_inside_band_does_not_fail():
    # Class 2 is the small class (n = 150 -> band 2.45); drop 2.2 with CI > 0.
    thresholds = criterion.class_thresholds(
        [1.5, 1.5, criterion.noise_band_points(150, NOISE_ACC), 1.5], MIN_DROP
    )
    drop = [0.0, 0.0, 2.2, 0.0]
    drop_lo = [-1.0, -1.0, 0.5, -1.0]
    res = criterion.verdict(_boot(1.8, [0.6, 3.0], drop, drop_lo), thresholds, MIN_GAIN)
    assert res["verdict"] == "pass"
    assert res["harmful_classes"] == []
    assert res["reported_drops"] == [2]
    assert res["reasons"] == []


def test_flat_threshold_makes_small_class_fail():
    # Same numbers as above, but a flat 2.0-point rule -> class 2 fails on noise (M3).
    drop = [0.0, 0.0, 2.2, 0.0]
    drop_lo = [-1.0, -1.0, 0.5, -1.0]
    res = criterion.verdict(_boot(1.8, [0.6, 3.0], drop, drop_lo), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "fail"
    assert res["harmful_classes"] == [2]
    assert res["reported_drops"] == []
    assert any(r.startswith("class 2:") and "CI excludes 0" in r for r in res["reasons"])


def test_large_drop_with_ci_including_zero_reported_not_failing():
    drop = [0.0, 3.0, 0.0, 0.0]
    drop_lo = [-1.0, -0.4, -1.0, -1.0]
    res = criterion.verdict(_boot(1.8, [0.6, 3.0], drop, drop_lo), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "pass"
    assert res["harmful_classes"] == []
    assert res["reported_drops"] == [1]


def test_report_drop_points_adds_small_drops_to_report():
    drop = [0.0, 1.5, 0.0, 0.0]  # below threshold, CI includes 0 -> normally silent
    res = criterion.verdict(_boot(1.8, [0.6, 3.0], drop), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["reported_drops"] == []
    res2 = criterion.verdict(
        _boot(1.8, [0.6, 3.0], drop), np.full(K, MIN_DROP), MIN_GAIN, report_drop_points=1.0
    )
    assert res2["reported_drops"] == [1]
    assert res2["verdict"] == "pass"


def test_pass_case():
    res = criterion.verdict(_boot(1.8, [0.6, 3.0]), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "pass"
    assert res["reasons"] == []
    assert res["harmful_classes"] == []
    assert res["reported_drops"] == []
    # Gain exactly at the minimum passes (>=).
    assert criterion.verdict(_boot(1.0, [0.2, 1.8]), np.full(K, MIN_DROP), MIN_GAIN)["verdict"] == "pass"


def test_multiple_reasons_accumulate():
    drop = [2.5, 0.0, 0.0, 0.0]
    drop_lo = [0.3, -1.0, -1.0, -1.0]
    res = criterion.verdict(_boot(0.4, [-0.5, 1.3], drop, drop_lo), np.full(K, MIN_DROP), MIN_GAIN)
    assert res["verdict"] == "fail"
    assert len(res["reasons"]) == 3
    assert res["harmful_classes"] == [0]


def test_verdict_shape_mismatch_raises():
    with pytest.raises(ValueError):
        criterion.verdict(_boot(1.8, [0.6, 3.0]), np.full(K + 1, MIN_DROP), MIN_GAIN)
