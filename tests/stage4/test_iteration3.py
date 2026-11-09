"""Iteration 3 training options: equal real images, data fraction, pretraining, folds, BatchNorm."""

import numpy as np
import pytest
import torch

from src.common.config import ConfigError, load_config, validate_pipeline
from src.stage4_train import bn, sampling
from src.stage4_train.data import ImageStore
from src.stage4_train.folds import grouped_folds, pooled
from src.stage4_train.model import build_model
from src.stage4_train.train import train_one


def _store(n=200, k=2, seed=0):
    rng = np.random.default_rng(seed)
    images = rng.integers(0, 256, (n, 64, 64)).astype(np.uint8)
    labels = np.arange(n) % k
    groups = np.array([f"g{labels[i]}_{i // (2 * k)}" for i in range(n)])
    return ImageStore(images=images, labels=labels, source_ids=np.array(["s"] * n), n_classes=k, group_ids=groups)


def test_equal_real_keeps_a_full_real_batch_and_adds_synthetic():
    base = {"augment": False, "synthetic": True, "synthetic_fraction": 0.25}
    assert sampling.batch_composition(base, 256, 0.3) == (192, 64)
    assert sampling.batch_composition({**base, "equal_real": True}, 256, 0.3) == (256, 64)


def test_equal_real_batch_has_every_image():
    store = _store()
    arm = {"augment": False, "synthetic": True, "synthetic_fraction": 0.25, "equal_real": True}
    batch = sampling.make_batch(store.images, store.labels, store.class_idx, arm, 16, 0.3, 2,
                                np.random.default_rng(0), generate=lambda c, r: np.full((64, 64), 255, np.uint8))
    assert batch.images.shape[0] == 20 and batch.is_synthetic.sum() == 4


def test_a_synthetic_only_batch_uses_no_real_image():
    store = _store()
    arm = {"augment": False, "synthetic": True, "synthetic_fraction": 1.0}
    batch = sampling.make_batch(store.images, store.labels, store.class_idx, arm, 8, 0.3, 2,
                                np.random.default_rng(0), generate=lambda c, r: np.full((64, 64), 255, np.uint8))
    assert batch.is_synthetic.all() and batch.images.shape[0] == 8


def test_real_subset_is_repeatable_group_safe_and_per_class():
    store = _store()
    one, two = store.real_subset(0.25, 3), store.real_subset(0.25, 3)
    assert np.array_equal(one.group_ids, two.group_ids)
    assert 45 <= len(one) <= 60
    assert set(np.unique(one.labels)) == {0, 1}
    kept = set(one.group_ids)
    assert np.isin(store.group_ids, sorted(kept)).sum() == len(one)
    assert store.real_subset(1.0, 3) is store


def test_folds_keep_groups_whole_and_cover_every_image():
    store = pooled(_store(120), _store(90, seed=1))
    folds = grouped_folds(store, 3, 7)
    assert len(folds) == 3
    assert sorted(np.concatenate([v for _, v in folds]).tolist()) == list(range(len(store)))
    for tr, va in folds:
        assert not set(store.group_ids[tr]) & set(store.group_ids[va])


def _config():
    return load_config()


def test_config_rejects_a_bad_pretrain_share():
    cfg = _config()
    cfg["arms"]["P"]["pretrain_fraction"] = 1.0
    with pytest.raises(ConfigError, match="pretrain_fraction"):
        validate_pipeline(cfg)


def test_config_rejects_a_bad_data_fraction():
    cfg = _config()
    cfg["train"]["real_fraction"] = 0.0
    with pytest.raises(ConfigError, match="real_fraction"):
        validate_pipeline(cfg)


def test_pretraining_sees_only_synthetic_and_never_picks_a_best_epoch(tmp_path):
    cfg = _config()
    cfg["train"].update(max_epochs=4, steps_per_epoch=2, batch_size=8, device="cpu", early_stopping_patience=1)
    cfg["arms"]["T"] = {"augment": False, "synthetic": True, "synthetic_fraction": 0.0, "pretrain_fraction": 0.5}
    train = _store(40, k=10)
    val = _store(20, k=10, seed=1)
    seen = []

    def generate(label, rng):
        seen.append(int(label))
        return np.full((64, 64), 255, np.uint8)

    scores = iter([99.0, 99.0, 1.0, 2.0])
    info = train_one("T_0", "T", 0, cfg, train, val, None, generate, {"lr": 0.001, "dropout": 0.2}, tmp_path,
                     steps_per_epoch=2, val_scorer=lambda *_: next(scores))
    assert info["pretrain_epochs"] == 2 and len(seen) == 2 * 2 * 8
    assert info["epochs_run"] == 4 and info["best_epoch"] == 4


def test_batchnorm_recalibration_changes_only_the_averages(tmp_path):
    cfg = _config()
    model = build_model(cfg, 10, 0.2).eval()
    path = tmp_path / "m.pt"
    torch.jit.script(model).save(str(path))
    images = np.random.default_rng(0).integers(0, 256, (32, 64, 64)).astype(np.uint8)
    out = bn.recalibrated(path, cfg, 10, 0.2, images, "cpu")
    before, after = model.state_dict(), out.state_dict()
    for name, value in before.items():
        if "running" in name or "num_batches" in name:
            continue
        assert torch.equal(value, after[name]), name
    assert any(not torch.equal(before[n], after[n]) for n in before if "running_mean" in n)
    assert not out.training
