"""E23: source-shortcut check on train/val only (R13, Decision 12)."""

import numpy as np

from src.stage1_freeze.source_check import POOL_SIDE_PX, downsample, shortcut_check

SIDE = 64
TRIGGER = 10.0   # evaluation.shortcut_trigger_points
SEED = 0


def _noise_images(rng, n, speckle=0.02):
    img = np.full((n, SIDE, SIDE), 255, dtype=np.uint8)
    img[rng.random((n, SIDE, SIDE)) < speckle] = 0
    return img


def _dataset(rng, n, plant_corner):
    X = _noise_images(rng, n)
    y = np.array([i % 2 for i in range(n)])                  # two classes
    s = np.array([("src_a", "src_b")[(i // 2) % 2] for i in range(n)])  # both sources in both classes
    if plant_corner:
        X[s == "src_b", :4, :4] = 0                           # black corner block for one source
    return X, y, s


def test_downsample_shape_and_range():
    X = np.full((3, SIDE, SIDE), 255, dtype=np.uint8)
    f = downsample(X)
    assert f.shape == (3, POOL_SIDE_PX * POOL_SIDE_PX)
    assert np.allclose(f, 1.0)


def test_detects_planted_source_signal():
    rng = np.random.default_rng(SEED)
    Xtr, ytr, s_tr = _dataset(rng, 200, plant_corner=True)
    Xva, yva, s_va = _dataset(rng, 100, plant_corner=True)
    result = shortcut_check(Xtr, ytr, s_tr, Xva, yva, s_va, TRIGGER, SEED)
    assert result["shortcut_detected"] is True
    assert result["pooled_accuracy"] > result["pooled_majority_rate"] + TRIGGER / 100
    assert set(result["classes"]) == {"0", "1"}
    assert result["splits_used"] == ["train", "val"]


def test_no_signal_not_detected():
    rng = np.random.default_rng(SEED)
    Xtr, ytr, s_tr = _dataset(rng, 200, plant_corner=False)
    Xva, yva, s_va = _dataset(rng, 300, plant_corner=False)
    result = shortcut_check(Xtr, ytr, s_tr, Xva, yva, s_va, TRIGGER, SEED)
    assert result["shortcut_detected"] is False
    assert result["gain_points"] <= TRIGGER
    assert result["pooled_majority_rate"] > 0           # baseline is the majority rate, not 0


def test_single_source_classes_skipped():
    rng = np.random.default_rng(SEED)
    Xtr, ytr, s_tr = _dataset(rng, 200, plant_corner=True)
    Xva, yva, s_va = _dataset(rng, 100, plant_corner=True)
    s_tr = np.where(ytr == 1, "only_src", s_tr)         # class 1 has one source in train
    s_va = np.where(yva == 1, "only_src", s_va)
    result = shortcut_check(Xtr, ytr, s_tr, Xva, yva, s_va, TRIGGER, SEED,
                            class_names=["circle", "ellipse"])
    assert result["skipped_classes"] == ["ellipse"]
    assert list(result["classes"]) == ["circle"]
    assert result["n_val_evaluated"] == int((yva == 0).sum())
