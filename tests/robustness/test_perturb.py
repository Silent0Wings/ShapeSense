"""The perturbed validation sets are fixed, cover every level, and never touch test data."""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from robustness.run import SPLIT
from src.common import perturb
from src.common.perturb import SETS, build_set
from src.common.robust_summary import family_drop


def _outline(thickness=2):
    img = Image.new("L", (64, 64), 255)
    ImageDraw.Draw(img).rectangle((10, 18, 53, 45), outline=0, width=thickness)
    return np.asarray(img, dtype=np.uint8)


def test_only_the_validation_split_is_used():
    assert SPLIT == "val"


def test_same_seed_gives_identical_bytes_and_a_new_seed_does_not():
    images = np.stack([_outline(), _outline(3)])
    assert np.array_equal(build_set("gauss0.1", images, 1), build_set("gauss0.1", images, 1))
    assert not np.array_equal(build_set("gauss0.1", images, 1), build_set("gauss0.1", images, 2))


def test_every_requested_level_exists():
    names = set(SETS)
    assert {f"rot{a}" for a in (0, 15, 30, 45, 90, 135, 180)} <= names
    assert {f"gauss{s}" for s in (0.02, 0.05, 0.1, 0.2)} <= names
    assert {"jpeg90", "jpeg50", "jpeg20", "blur1", "blur2", "blur3"} <= names
    families = {v[0] for v in SETS.values()}
    assert {"salt_pepper", "brightness", "contrast", "occlusion"} <= families


def test_zero_rotation_is_the_clean_image():
    image = _outline()
    assert np.array_equal(perturb.rotate(image, 0), image)


@pytest.mark.parametrize("angle", [15, 45, 90, 135, 180])
def test_rotation_stays_binary_and_keeps_the_drawing_in_frame(angle):
    image = _outline()
    out = perturb.rotate(image, angle)
    assert set(np.unique(out)) <= {0, 255}
    ink = np.argwhere(out < 128)
    side = (ink.max(0) - ink.min(0)).max() + 1
    assert abs(side - 44) <= 3
    assert ink.min() > 0 and ink.max() < 63


def test_thin_strokes_stay_in_one_piece_after_rotation():
    from scipy import ndimage

    out = perturb.rotate(_outline(1), 30)
    assert ndimage.label(out < 128, structure=np.ones((3, 3)))[1] == 1


def test_family_drop_is_clean_minus_perturbed():
    scores = {"clean": {"accuracy": 90.0}, "a": {"accuracy": 80.0}, "b": {"accuracy": 70.0}}
    assert family_drop(scores, ["a", "b"]) == 15.0
