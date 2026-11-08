"""Internal behaviour of the Stage 2 transform: label safety, outline survival,
frame containment, config-driven disable list, and no global RNG.

Reference images are drawn procedurally with Pillow (no data_set/ needed).
"""

import copy
import math
import random

import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.common.config import load_config
from src.stage2_augment.geometry import fitted_ratio
from src.stage2_augment.transform import build_transform

OUTLINE_PX = 2           # reference outline width, pixels
INK_GREY = 128           # reference pixels darker than this count as ink
SEEDS = 200              # seeds per check (plan 24)
RATIO_REL_TOL = 0.08     # relative tolerance on fitted_ratio for disabled classes
ENABLED_MIN_DEV = 0.05   # an enabled class must deviate by more than this at least once
POLY_RADIUS_PX = 26      # circumradius of the regular polygon references, pixels
BORDER_PX = 1            # outermost frame ring that must stay white


def _regular_polygon(n: int, cx: float, cy: float, r: float, start_deg: float = -90.0):
    return [(cx + r * math.cos(math.radians(start_deg + 360.0 * k / n)),
             cy + r * math.sin(math.radians(start_deg + 360.0 * k / n))) for k in range(n)]


def _closed_line(draw: ImageDraw.ImageDraw, pts: list) -> None:
    draw.line(pts + [pts[0]], fill=0, width=OUTLINE_PX, joint="curve")


def render_reference(name: str, size: int) -> np.ndarray:
    """Clean 2-px black outline on white, uint8 (size, size), for a class name."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)
    c = size / 2
    if name == "circle":
        draw.ellipse([8, 8, 56, 56], outline=0, width=OUTLINE_PX)
    elif name == "ellipse":                       # axis ratio 52/32 = 1.6
        draw.ellipse([6, 16, 58, 48], outline=0, width=OUTLINE_PX)
    elif name == "square":
        draw.rectangle([12, 12, 52, 52], outline=0, width=OUTLINE_PX)
    elif name == "rectangle":                     # side ratio 46/26 = 1.77
        draw.rectangle([9, 19, 55, 45], outline=0, width=OUTLINE_PX)
    elif name == "diamond":                       # rhombus, acute angle 60 deg
        _closed_line(draw, [(32, 6), (47, 32), (32, 58), (17, 32)])
    elif name == "triangle":
        _closed_line(draw, _regular_polygon(3, c, c, POLY_RADIUS_PX))
    elif name == "pentagon":
        _closed_line(draw, _regular_polygon(5, c, c, POLY_RADIUS_PX))
    elif name == "hexagon":
        _closed_line(draw, _regular_polygon(6, c, c, POLY_RADIUS_PX))
    elif name == "octagon":
        _closed_line(draw, _regular_polygon(8, c, c, POLY_RADIUS_PX))
    elif name == "star":
        outer = _regular_polygon(5, c, c, 28, -90.0)
        inner = _regular_polygon(5, c, c, 12, -54.0)
        pts = [p for pair in zip(outer, inner) for p in pair]
        _closed_line(draw, pts)
    else:
        raise KeyError(name)
    return np.asarray(img, dtype=np.uint8)


def _label_of(config: dict) -> dict[str, int]:
    return {name: int(idx) for idx, name in config["taxonomy"]["classes"].items()}


def _rotated_reference(name: str, size: int, degrees: float) -> np.ndarray:
    """Reference rotated about the frame centre, re-binarised to 0/255."""
    ref = Image.fromarray(render_reference(name, size), mode="L")
    rotated = ref.rotate(degrees, resample=Image.Resampling.BILINEAR, fillcolor=255)
    arr = np.asarray(rotated, dtype=np.float64)
    return np.where(arr < INK_GREY, 0, 255).astype(np.uint8)


ROUND_TOL = 0.10           # circle/square: fitted ratio may not exceed 1 + this


def _record_linear(monkeypatch):
    """Capture every unit-scale linear part the transform composes."""
    import sys
    tmod = sys.modules[build_transform.__module__]  # the package re-exports a
    # function named `transform`, which shadows the submodule attribute
    seen = []
    real = tmod.compose_affine

    def spy(*args, **kwargs):
        m = real(*args, **kwargs)
        seen.append(m)
        return m

    monkeypatch.setattr(tmod, "compose_affine", spy)
    return seen


@pytest.mark.parametrize("name", ["circle", "ellipse", "square", "rectangle", "diamond"])
def test_disabled_linear_part_is_pure_rotation(name, monkeypatch):
    """Exact label-safety property (R4): for a disabled class the sampled
    linear map is a rotation (times the uniform scale applied later), so
    no shear and no non-uniform scale can reach the image."""
    seen = _record_linear(monkeypatch)
    config = load_config()
    fn = build_transform(config)
    label = _label_of(config)[name]
    ref = render_reference(name, int(config["image_size"]))
    for seed in range(SEEDS):
        fn(ref, label, np.random.default_rng(seed))
    assert len(seen) == SEEDS
    for m in seen:
        np.testing.assert_allclose(m.T @ m, np.eye(2), atol=1e-12)


def test_enabled_linear_part_can_shear(monkeypatch):
    seen = _record_linear(monkeypatch)
    config = load_config()
    fn = build_transform(config)
    ref = render_reference("hexagon", int(config["image_size"]))
    for seed in range(SEEDS):
        fn(ref, _label_of(config)["hexagon"], np.random.default_rng(seed))
    assert max(np.abs(m.T @ m - np.eye(2)).max() for m in seen) > 0.05


@pytest.mark.parametrize("name", ["circle", "ellipse", "square", "rectangle", "diamond"])
def test_disabled_classes_stay_on_their_side_of_the_margin(name):
    """Image-level check (Mission M3 idea): a circle/square stays round/square,
    an ellipse/rectangle/diamond stays clearly elongated (>= taxonomy margin).
    The fitted ratio is measured on the 2-px outline, so uniform shrinking
    moves it a little (stroke width is constant); the class boundary is what
    must hold."""
    config = load_config()
    margins = config["taxonomy"]["ambiguity_margins"]
    floor = {"ellipse": margins["ellipse_min_axis_ratio"],
             "rectangle": margins["rectangle_min_side_ratio"],
             "diamond": margins["rectangle_min_side_ratio"]}
    fn = build_transform(config)
    label = _label_of(config)[name]
    ref = render_reference(name, int(config["image_size"]))
    for seed in range(SEEDS):
        r = fitted_ratio(fn(ref, label, np.random.default_rng(seed)))
        if name in ("circle", "square"):
            assert r <= 1.0 + ROUND_TOL, (seed, r)
        else:
            assert r >= floor[name], (seed, r)


def test_rotated_rectangle_ratio_preserved():
    """A rectangle pre-rotated by 45 deg keeps its ratio (bbox would not)."""
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)["rectangle"]
    ref = _rotated_reference("rectangle", size, 45.0)
    ref_ratio = fitted_ratio(ref)
    assert ref_ratio > 1.5
    for seed in range(SEEDS):
        out = fn(ref, label, np.random.default_rng(seed))
        assert fitted_ratio(out) >= config["taxonomy"]["ambiguity_margins"]["rectangle_min_side_ratio"]


def test_enabled_class_can_shear():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)["hexagon"]
    ref = render_reference("hexagon", size)
    ref_ratio = fitted_ratio(ref)
    deviations = [abs(fitted_ratio(fn(ref, label, np.random.default_rng(seed))) / ref_ratio - 1.0)
                  for seed in range(SEEDS)]
    assert max(deviations) > ENABLED_MIN_DEV


def test_disable_list_read_from_config():
    config = copy.deepcopy(load_config())
    config["taxonomy"]["no_shear_no_nonuniform_scale"] = [
        name for name in config["taxonomy"]["no_shear_no_nonuniform_scale"] if name != "square"]
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)["square"]
    ref = render_reference("square", size)
    ref_ratio = fitted_ratio(ref)
    deviations = [abs(fitted_ratio(fn(ref, label, np.random.default_rng(seed))) / ref_ratio - 1.0)
                  for seed in range(SEEDS)]
    assert max(deviations) > RATIO_REL_TOL


@pytest.mark.parametrize("name", list(_label_of(load_config()).keys()))
def test_thin_outline_survives(name):
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)[name]
    ref = render_reference(name, size)
    in_ink = int((ref < INK_GREY).sum())
    for seed in range(100):
        out = fn(ref, label, np.random.default_rng(seed))
        out_ink = int((out == 0).sum())
        assert out_ink >= 0.5 * in_ink, (name, seed)


@pytest.mark.parametrize("name", list(_label_of(load_config()).keys()))
def test_shape_stays_in_frame(name):
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)[name]
    ref = render_reference(name, size)
    for seed in range(SEEDS):
        out = fn(ref, label, np.random.default_rng(seed))
        ring = np.ones((size, size), dtype=bool)
        ring[BORDER_PX:size - BORDER_PX, BORDER_PX:size - BORDER_PX] = False
        assert (out[ring] == 255).all(), (name, seed)


def test_no_global_rng(monkeypatch):
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("global RNG used")

    monkeypatch.setattr(np.random, "seed", _forbidden)
    monkeypatch.setattr(random, "random", _forbidden)
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    labels = _label_of(config)
    for name in ("circle", "hexagon", "star"):
        out = fn(render_reference(name, size), labels[name], np.random.default_rng(0))
        assert out.shape == (size, size)
        assert out.dtype == np.uint8
