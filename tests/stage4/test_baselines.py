"""Tests for the Stage 4 scikit-learn baselines (Decision 14, R13).

Synthetic 64x64 toy shapes only: no data_set/, no test split.
"""

import json

import numpy as np
import pytest

from src.stage4_train import baselines as bl

N_CLASSES = 3
TRAIN_GOOD_C = 0.01  # fake estimator: the "best" C on the train set
VAL_GOOD_C = 1.0  # fake estimator: the "best" C on the validation set
HOG_PPC = 8


def _toy_dataset(n_per_class: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Horizontal bar (0), vertical bar (1), diagonal (2) on noisy background."""
    images = []
    labels = []
    for cls in range(N_CLASSES):
        for _ in range(n_per_class):
            base = np.zeros((64, 64), dtype=np.int64)
            if cls == 0:
                base[28:36, :] = 255
            elif cls == 1:
                base[:, 28:36] = 255
            else:
                for i in range(64):
                    base[i, i] = 255
                    if i + 1 < 64:
                        base[i, i + 1] = 255
            noise = rng.integers(0, 40, size=(64, 64))
            images.append(np.clip(base + noise, 0, 255).astype(np.uint8))
            labels.append(cls)
    return np.stack(images), np.asarray(labels, dtype=np.int64)


class _FakeEstimator:
    """Feature column 0 carries the label, column 1 the set id (0 train, 1 val).

    It predicts the true labels only for the C that is "good" for its set,
    and predicts class 0 otherwise, so the C that wins on train differs from
    the C that wins on validation.
    """

    def __init__(self, C: float) -> None:
        self.C = C

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_FakeEstimator":
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        labels = X[:, 0].astype(np.int64)
        is_val = X[0, 1] == 1
        good_C = VAL_GOOD_C if is_val else TRAIN_GOOD_C
        if self.C == good_C:
            return labels
        return np.zeros(len(labels), dtype=np.int64)


def test_pixel_features_shape_range() -> None:
    rng = np.random.default_rng(0)
    imgs = rng.integers(0, 256, size=(5, 64, 64), dtype=np.uint8)
    feats = bl.pixel_features(imgs)
    assert feats.shape == (5, 4096)
    assert feats.dtype == np.float32
    assert feats.min() >= 0.0
    assert feats.max() <= 1.0
    np.testing.assert_allclose(feats[0], imgs[0].reshape(-1) / 255.0, rtol=1e-6)


def test_hog_shape() -> None:
    rng = np.random.default_rng(0)
    imgs = rng.integers(0, 256, size=(3, 64, 64), dtype=np.uint8)
    feats = bl.hog_features(imgs, pixels_per_cell=HOG_PPC)
    # 8x8 cells, 2x2 cells per block -> 7x7 blocks, 9 orientations * 2 * 2 each
    assert feats.shape == (3, 9 * 7 * 7 * 2 * 2)
    assert feats.dtype == np.float32


def test_balanced_subset_counts() -> None:
    labels = np.array([0] * 10 + [1] * 3 + [2] * 7)
    rng = np.random.default_rng(0)
    idx = bl.balanced_subset(labels, per_class=5, rng=rng)
    counts = np.bincount(labels[idx], minlength=3)
    np.testing.assert_array_equal(counts, [5, 3, 5])
    assert len(set(idx.tolist())) == idx.size  # without replacement


def test_selection_uses_val_only() -> None:
    y_train = np.tile(np.arange(N_CLASSES), 10)
    y_val = np.tile(np.arange(N_CLASSES), 4)
    X_train = np.column_stack([y_train, np.zeros_like(y_train)]).astype(np.float64)
    X_val = np.column_stack([y_val, np.ones_like(y_val)]).astype(np.float64)

    res = bl.fit_select(
        bl.KIND_LOGREG,
        X_train,
        y_train,
        X_val,
        y_val,
        C_grid=[TRAIN_GOOD_C, VAL_GOOD_C],
        n_classes=N_CLASSES,
        estimator_factory=lambda kind, C: _FakeEstimator(C),
    )

    assert res["best_C"] == VAL_GOOD_C
    assert res["grid"][str(VAL_GOOD_C)] == pytest.approx(100.0)
    assert res["grid"][str(TRAIN_GOOD_C)] < 100.0
    assert res["model"].C == VAL_GOOD_C


def test_saved_model_reloads_and_predicts(tmp_path) -> None:
    rng = np.random.default_rng(1)
    imgs, labels = _toy_dataset(10, rng)

    X_pix = bl.pixel_features(imgs)
    res_lr = bl.fit_select(bl.KIND_LOGREG, X_pix, labels, X_pix, labels, [1.0], N_CLASSES)
    path_lr = tmp_path / "logreg_pixels.joblib"
    bl.save_baseline(res_lr["model"], path_lr)
    loaded_lr = bl.load_baseline(path_lr)
    np.testing.assert_array_equal(
        bl.predict_baseline(bl.KIND_LOGREG, loaded_lr, imgs, None),
        res_lr["model"].predict(X_pix),
    )

    X_hog = bl.hog_features(imgs, HOG_PPC)
    res_svm = bl.fit_select(bl.KIND_SVM, X_hog, labels, X_hog, labels, [1.0], N_CLASSES)
    path_svm = tmp_path / "svm_hog.joblib"
    bl.save_baseline(res_svm["model"], path_svm)
    loaded_svm = bl.load_baseline(path_svm)
    np.testing.assert_array_equal(
        bl.predict_baseline(bl.KIND_SVM, loaded_svm, imgs, HOG_PPC),
        res_svm["model"].predict(X_hog),
    )


def test_beats_chance_on_toy_data() -> None:
    rng = np.random.default_rng(2)
    train_imgs, train_labels = _toy_dataset(40, rng)
    val_imgs, val_labels = _toy_dataset(20, rng)

    X_pix_tr = bl.pixel_features(train_imgs)
    X_pix_va = bl.pixel_features(val_imgs)
    res_lr = bl.fit_select(bl.KIND_LOGREG, X_pix_tr, train_labels, X_pix_va, val_labels, [1.0], N_CLASSES)
    assert res_lr["val_macro_f1"] > 60.0

    X_hog_tr = bl.hog_features(train_imgs, HOG_PPC)
    X_hog_va = bl.hog_features(val_imgs, HOG_PPC)
    res_svm = bl.fit_select(bl.KIND_SVM, X_hog_tr, train_labels, X_hog_va, val_labels, [1.0], N_CLASSES)
    assert res_svm["val_macro_f1"] > 60.0


def test_train_baselines_writes_json(tmp_path) -> None:
    rng = np.random.default_rng(3)
    train_imgs, train_labels = _toy_dataset(20, rng)
    val_imgs, val_labels = _toy_dataset(10, rng)
    cfg = {
        "per_class": 10,
        "logreg_C": [1.0],
        "svm_C": [1.0],
        "hog_pixels_per_cell": HOG_PPC,
    }
    out_dir = tmp_path / "baselines"

    summary = bl.train_baselines(
        train_imgs,
        train_labels,
        val_imgs,
        val_labels,
        cfg,
        n_classes=N_CLASSES,
        rng=np.random.default_rng(4),
        out_dir=out_dir,
    )

    assert (out_dir / "logreg_pixels.joblib").is_file()
    assert (out_dir / "svm_hog.joblib").is_file()
    written = json.loads((out_dir / "baselines.json").read_text(encoding="utf-8"))
    assert written == summary
    assert written[bl.KIND_LOGREG]["features"] == "pixels"
    assert written[bl.KIND_SVM]["features"] == "hog"
    assert written[bl.KIND_SVM]["hog_pixels_per_cell"] == HOG_PPC
    assert written[bl.KIND_LOGREG]["n_train"] == 30  # 10 per class x 3 classes
    assert written[bl.KIND_SVM]["n_train"] == 30
    for kind in (bl.KIND_LOGREG, bl.KIND_SVM):
        assert set(written[kind]["grid"]) == {"1.0"}
        assert 0.0 <= written[kind]["val_macro_f1"] <= 100.0
