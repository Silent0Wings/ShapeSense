"""CRISP-DM iteration 2: arm A2 batches, per-arm settings, the search and the transform fixes."""

import copy
import importlib
import random

import numpy as np
import pytest
from PIL import Image, ImageDraw
from scipy import ndimage

from src.common.config import ConfigError, arm_config, load_config, set_dotted, validate_pipeline
from src.stage2_augment import build_transform
from src.stage4_train import run as stage4_run
from src.stage4_train import search
from src.stage4_train.sampling import batch_composition, class_index, clean_count, make_batch

N_CLASSES = 10
SIZE = 16
BATCH = 256
A2 = {"augment": True, "synthetic": True, "clean_fraction": 0.25, "synthetic_fraction": 0.2}
transform_module = importlib.import_module("src.stage2_augment.transform")


def _store():
    labels = np.repeat(np.arange(N_CLASSES, dtype=np.int64), 12)
    return np.full((labels.size, SIZE, SIZE), 255, dtype=np.uint8), labels, class_index(labels, N_CLASSES)


def test_arm_share_overrides_the_global_synthetic_fraction():
    assert batch_composition(A2, BATCH, 0.3) == (205, 51)
    assert batch_composition({"augment": True, "synthetic": True}, BATCH, 0.3) == (179, 77)
    assert clean_count(A2, BATCH) == 64
    assert clean_count({"augment": True, "synthetic": False}, BATCH) == 0


def test_a2_leaves_exactly_the_clean_images_untransformed():
    images, labels, idx = _store()
    calls = []

    def spy(img, label, rng):
        calls.append(int(label))
        return np.zeros_like(img)

    batch = make_batch(images, labels, idx, A2, BATCH, 0.3, N_CLASSES, np.random.default_rng(0),
                       transform=spy, generate=lambda label, rng: np.full((SIZE, SIZE), 255, dtype=np.uint8))
    assert len(calls) == BATCH - clean_count(A2, BATCH)
    untouched = int((batch.images.reshape(BATCH, -1).max(axis=1) > 0).sum())
    assert untouched == clean_count(A2, BATCH)
    assert int(batch.is_synthetic.sum()) == 51


def test_clean_and_augmented_real_images_are_each_class_balanced():
    images, labels, idx = _store()
    seen = []
    make_batch(images, labels, idx, {"augment": True, "synthetic": False, "clean_fraction": 0.5}, 100, 0.3,
               N_CLASSES, np.random.default_rng(0), transform=lambda i, l, r: (seen.append(int(l)), i)[1])
    counts = np.bincount(seen, minlength=N_CLASSES)
    assert counts.min() == 5 and counts.max() == 5


@pytest.mark.parametrize("arm", [
    {"augment": True, "synthetic": True, "clean_fraction": 0.7, "synthetic_fraction": 0.4},
    {"augment": False, "synthetic": False, "clean_fraction": 0.2},
])
def test_invalid_arm_shares_rejected(arm):
    cfg = copy.deepcopy(load_config())
    cfg["arms"]["A2"] = arm
    with pytest.raises(ConfigError):
        validate_pipeline(cfg)


def test_arm_config_applies_overrides_without_touching_the_original():
    cfg = copy.deepcopy(load_config())
    cfg["arms"]["A1"]["overrides"] = {"augment.rotate_deg": 15, "taxonomy.rotate_limit_deg": {"square": 5}}
    tuned = arm_config(cfg, "A1")
    assert tuned["augment"]["rotate_deg"] == 15
    assert tuned["taxonomy"]["rotate_limit_deg"] == {"square": 5}
    assert cfg["augment"]["rotate_deg"] != 15
    assert "rotate_limit_deg" not in cfg["taxonomy"]


def test_set_dotted_reaches_nested_keys():
    cfg = {"a": {"b": {"c": 1}}}
    set_dotted(cfg, "a.b.c", 2)
    assert cfg == {"a": {"b": {"c": 2}}}


def _capture_affine(monkeypatch):
    calls = []
    real = transform_module.compose_affine

    def spy(rot, shear, axis_factors, orient):
        calls.append((float(rot), np.array(axis_factors, dtype=float)))
        return real(rot, shear, axis_factors, orient)

    monkeypatch.setattr(transform_module, "compose_affine", spy)
    return calls


def _triangle():
    img = Image.new("L", (64, 64), 255)
    ImageDraw.Draw(img).polygon([(32, 8), (56, 54), (8, 54)], outline=0, width=2)
    return np.asarray(img, dtype=np.uint8)


def _square():
    img = Image.new("L", (64, 64), 255)
    ImageDraw.Draw(img).rectangle((12, 12, 52, 52), outline=0, width=2)
    return np.asarray(img, dtype=np.uint8)


def test_nonuniform_scale_is_continuous(monkeypatch):
    calls = _capture_affine(monkeypatch)
    cfg = load_config()
    fn = build_transform(cfg)
    for seed in range(30):
        fn(_triangle(), 2, np.random.default_rng(seed))
    values = np.concatenate([a for _, a in calls])
    assert np.unique(np.round(values, 6)).size > 20
    assert values.min() >= 0.9 and values.max() <= 1.1


def test_rotation_cap_applies_only_to_the_listed_class(monkeypatch):
    calls = _capture_affine(monkeypatch)
    cfg = copy.deepcopy(load_config())
    cfg["taxonomy"]["rotate_limit_deg"] = {"square": 5}
    fn = build_transform(cfg)
    for seed in range(40):
        fn(_square(), 3, np.random.default_rng(seed))
    square = np.abs(np.degrees([r for r, _ in calls]))
    calls.clear()
    for seed in range(40):
        fn(_triangle(), 2, np.random.default_rng(seed))
    triangle = np.abs(np.degrees([r for r, _ in calls]))
    assert square.max() <= 5.0 + 1e-6
    assert triangle.max() > 45


def test_thin_sketch_stays_in_one_piece_after_rotation():
    img = Image.new("L", (64, 64), 255)
    ImageDraw.Draw(img).line([(10, 10), (54, 18), (30, 54), (10, 10)], fill=0, width=1)
    cfg = copy.deepcopy(load_config())
    cfg["augment"].update({"noise_p": 0.0, "blur_p": 0.0})
    fn = build_transform(cfg)
    pieces = [ndimage.label(fn(np.asarray(img, dtype=np.uint8), 2, np.random.default_rng(s)) < 128,
                            structure=np.ones((3, 3)))[1] for s in range(40)]
    assert max(pieces) <= 2


def test_augmented_shapes_match_the_real_size_again():
    cfg = copy.deepcopy(load_config())
    cfg["augment"].update({"scale": [1.0, 1.0], "translate_px": 0, "noise_p": 0.0, "blur_p": 0.0})
    fn = build_transform(cfg)
    sides = []
    for seed in range(30):
        ys, xs = np.nonzero(fn(_square(), 3, np.random.default_rng(seed)) < 128)
        sides.append(max(ys.max() - ys.min(), xs.max() - xs.min()) + 1)
    assert 55 <= float(np.mean(sides)) <= 59


def test_release_gpu_empties_the_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(stage4_run.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(stage4_run.torch.cuda, "empty_cache", lambda: calls.append(1))
    stage4_run.release_gpu()
    assert calls == [1]


def test_search_samplers_stay_inside_the_preregistered_ranges():
    rng = random.Random(0)
    for _ in range(200):
        a = search.sample_augment(rng)
        assert a["augment.rotate_deg"] in search.ROTATIONS
        assert 0.75 <= a["augment.scale"][0] <= a["augment.scale"][1] <= 1.1
        assert a["augment.nonuniform_scale"] <= 0.2 and a["augment.shear_deg"] <= 20
        assert a["augment.noise_p"] <= 0.5 and a["augment.blur_p"] <= 0.5
        s = search.sample_synth(rng)
        assert 0.1 <= s["arms.B.synthetic_fraction"] <= 0.5
        assert s["synth.diamond_acute_angle_deg"][1] <= 80 and s["synth.star_inner_ratio"][1] <= 0.6
        shares = search.sample_shares(rng)
        assert shares["arms.A2.clean_fraction"] + shares["arms.A2.synthetic_fraction"] <= 0.8


def test_search_trial_budget_matches_the_preregistration():
    assert (search.N_AUGMENT, search.N_SYNTH, search.N_SHARES, search.TOP_K) == (24, 16, 12, 5)
    assert len(search.GRID_LR) * len(search.GRID_DROPOUT) == 6
    assert len(search.ablation_specs(load_config(), "c")) == 30


def test_top_settings_keeps_distinct_settings_only():
    def row(score, overrides):
        return {"val_macro_f1": score, "settings": {"overrides": overrides, "hparams": {"lr": 0.1}}}
    rows = [row(90.0, {"a": 1}), row(95.0, {"a": 1}), row(92.0, {"a": 2})]
    picked = search.top_settings(rows)
    assert [r["val_macro_f1"] for r in picked] == [95.0, 92.0]
