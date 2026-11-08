"""E25: public generate(label, rng) contract (stages/stage_3.md R1-R5)."""

import copy
import random

import numpy as np
import pytest

from src.common.config import class_names, load_config
from src.stage3_synth.generate import build_generator_with_log, generate


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_output_shape_dtype_binary(cfg):
    size = cfg["image_size"]
    for label in range(len(class_names(cfg))):
        img = generate(label, np.random.default_rng(label))
        assert img.shape == (size, size)
        assert img.dtype == np.uint8
        assert set(np.unique(img).tolist()) <= {0, 255}


def test_deterministic_same_seed(cfg):
    for label in range(len(class_names(cfg))):
        a = generate(label, np.random.default_rng(7))
        b = generate(label, np.random.default_rng(7))
        assert np.array_equal(a, b)


def test_different_seeds_differ(cfg):
    for label in range(len(class_names(cfg))):
        imgs = [generate(label, np.random.default_rng(s)) for s in range(5)]
        assert any(not np.array_equal(imgs[0], other) for other in imgs[1:])


def test_white_background_black_ink(cfg):
    for label in range(len(class_names(cfg))):
        for seed in range(10):
            img = generate(label, np.random.default_rng(seed))
            assert img[0, 0] == 255 and img[0, -1] == 255
            assert img[-1, 0] == 255 and img[-1, -1] == 255
            assert img.min() == 0


def test_no_global_rng(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("global RNG used")

    monkeypatch.setattr(np.random, "seed", boom)
    monkeypatch.setattr(random, "random", boom)
    for label in range(10):
        generate(label, np.random.default_rng(label))


def test_log_records_every_class(cfg):
    gen, log = build_generator_with_log(cfg)
    for label in range(len(class_names(cfg))):
        gen(label, np.random.default_rng(label))
    ranges = log.to_dict()
    assert set(ranges) == set(class_names(cfg))
    for name, params in ranges.items():
        assert "radius_px" in params, name
        lo, hi = params["radius_px"]
        assert lo <= hi
