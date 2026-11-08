"""QA-review regressions (stages/stage_2.md Should 2): thin sketch outlines
must survive blur, and noise must never punch holes in the outline."""

import copy

import numpy as np

from src.common.config import load_config
from src.stage2_augment import build_transform

SEEDS = 100


def _thin_circle(size=64, radius=22):
    yy, xx = np.mgrid[:size, :size]
    img = np.full((size, size), 255, np.uint8)
    img[np.abs(np.hypot(yy - size / 2, xx - size / 2) - radius) < 0.6] = 0  # ~1-px line
    return img


def _cfg(**augment):
    cfg = copy.deepcopy(load_config())
    cfg["augment"].update(augment)
    return cfg


def test_one_pixel_sketch_survives_strongest_blur():
    cfg = _cfg(blur_p=1.0, blur_sigma=[cfg_max := load_config()["augment"]["blur_sigma"][1]] * 2,
               noise_p=0.0)
    fn = build_transform(cfg)
    ref = _thin_circle()
    n_in = int((ref == 0).sum())
    for seed in range(SEEDS):
        out = fn(ref, 0, np.random.default_rng(seed))
        assert (out == 0).sum() >= 0.6 * n_in, (seed, cfg_max)


def test_noise_only_adds_ink():
    """The noise step only adds ink next to the outline, never removes it."""
    import sys
    tmod = sys.modules[build_transform.__module__]
    ref = _thin_circle() == 0
    ring = tmod._outer_ring(ref.shape[0], tmod.FRAME_MARGIN_PX)
    for seed in range(SEEDS):
        out = tmod._flip_near_outline(ref, ring, 0.004, np.random.default_rng(seed))
        assert np.all(out[ref]), seed          # every original ink pixel kept
        assert out.sum() > ref.sum()           # and some ink was added
        assert not out[ring].any()


def _long_side(img):
    ys, xs = np.nonzero(img == 0)
    return max(ys.max() - ys.min(), xs.max() - xs.min()) + 1


def test_augmented_shapes_keep_standardized_size():
    """P-55: after rotation/shear the shape is re-framed like Stage 1
    (bbox + margin), so augmented training shapes are not systematically
    smaller than the standardized validation/test images."""
    cfg = load_config()
    aug = cfg["augment"]
    fn = build_transform(cfg)
    size = cfg["image_size"]
    target = size / (1 + 2 * aug["frame_margin"])
    ref = _thin_circle(size, radius=int(target / 2) - 1)
    square = np.full((size, size), 255, np.uint8)
    lo, hi = int(size / 2 - target / 2) + 1, int(size / 2 + target / 2) - 1
    square[lo:hi, lo:lo + 2] = square[lo:hi, hi - 2:hi] = 0
    square[lo:lo + 2, lo:hi] = square[hi - 2:hi, lo:hi] = 0
    for img, label in ((ref, 0), (square, 3)):
        sides = [_long_side(fn(img, label, np.random.default_rng(s))) for s in range(SEEDS)]
        expected = target * float(np.mean(aug["scale"]))   # bbox like Stage 1 x mean jitter
        assert abs(np.mean(sides) - expected) <= 3.0, (label, np.mean(sides), expected)
        assert max(sides) <= size - 2
