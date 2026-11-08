"""Contract tests for stage2_augment.transform(img, label, rng).

Reference images are drawn procedurally with Pillow, so no data_set/ is needed.
"""

import math

import numpy as np
from PIL import Image, ImageDraw

from src.common.config import load_config
from src.stage2_augment.transform import build_transform, transform

OUTLINE_PX = 2          # reference outline width, pixels
SEEDS = 20             # seeds per label for the contract checks
POLY_RADIUS_PX = 26     # circumradius of the regular polygon references, pixels


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


def test_output_shape_dtype_binary():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    labels = _label_of(config)
    assert len(labels) == 10
    for name, label in labels.items():
        ref = render_reference(name, size)
        for seed in range(SEEDS):
            out = fn(ref, label, np.random.default_rng(seed))
            assert out.shape == (size, size), name
            assert out.dtype == np.uint8, name
            assert set(np.unique(out).tolist()) <= {0, 255}, name


def test_deterministic_same_seed():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    for name, label in _label_of(config).items():
        ref = render_reference(name, size)
        a = fn(ref, label, np.random.default_rng(7))
        b = fn(ref, label, np.random.default_rng(7))
        assert np.array_equal(a, b), name


def test_different_seeds_differ():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    label = _label_of(config)["circle"]
    ref = render_reference("circle", size)
    outs = [fn(ref, label, np.random.default_rng(seed)) for seed in range(SEEDS)]
    assert any(not np.array_equal(outs[0], other) for other in outs[1:])


def test_input_not_mutated():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    for name, label in _label_of(config).items():
        ref = render_reference(name, size)
        before = ref.copy()
        fn(ref, label, np.random.default_rng(3))
        assert np.array_equal(ref, before), name


def test_returns_array_not_tuple():
    config = load_config()
    size = int(config["image_size"])
    fn = build_transform(config)
    ref = render_reference("hexagon", size)
    out = fn(ref, _label_of(config)["hexagon"], np.random.default_rng(0))
    assert isinstance(out, np.ndarray)
    assert not isinstance(out, tuple)
    module_out = transform(ref, _label_of(config)["hexagon"], np.random.default_rng(0))
    assert isinstance(module_out, np.ndarray)
    assert module_out.shape == out.shape
