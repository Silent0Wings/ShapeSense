"""E25: Stage 3 margins, geometry and outline rules (stages/stage_3.md R3, Should 1-2, M1)."""

import copy

import numpy as np
from scipy import ndimage
import pytest

from src.common.config import class_names, load_config
from src.stage3_synth.generate import build_generator_with_log
from src.stage3_synth.measure import axis_ratio, min_interior_angle_deg
from src.stage3_synth.render import render_outline
from src.stage3_synth.shapes import check_params, interior_angles_deg, sample_params, vertices

PARAM_SEEDS = 1000
RENDER_SEEDS = 300
RATIO_RENDER_SLACK = 0.02  # measuring error allowed at 64 px (plan 25 section 6)
ANGLE_TOL_DEG = 1e-6  # float tolerance for angle comparisons
CIRCLE_RENDER_MAX_RATIO = 1.08  # axes equal within measuring error


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def _draw(name, seed, cfg):
    """Sample params, build vertices and render one image for class `name`."""
    size = cfg["image_size"]
    synth = cfg["synth"]
    rng = np.random.default_rng(seed)
    params = sample_params(name, rng, synth, cfg["taxonomy"]["ambiguity_margins"])
    verts = vertices(name, params, size)
    img = render_outline(verts, size, synth["stroke_px"], synth["supersample"])
    return params, verts, img


def test_ellipse_ratio_margin(cfg):
    margin = cfg["taxonomy"]["ambiguity_margins"]["ellipse_min_axis_ratio"]
    for seed in range(PARAM_SEEDS):
        params = sample_params("ellipse", np.random.default_rng(seed),
                               cfg["synth"], cfg["taxonomy"]["ambiguity_margins"])
        assert params["axis_ratio"] >= margin, seed
    for seed in range(RENDER_SEEDS):
        _, _, img = _draw("ellipse", seed, cfg)
        assert axis_ratio(img) >= margin - RATIO_RENDER_SLACK, seed


def test_rectangle_ratio_margin(cfg):
    margin = cfg["taxonomy"]["ambiguity_margins"]["rectangle_min_side_ratio"]
    for seed in range(PARAM_SEEDS):
        params = sample_params("rectangle", np.random.default_rng(seed),
                               cfg["synth"], cfg["taxonomy"]["ambiguity_margins"])
        assert params["side_ratio"] >= margin, seed
    for seed in range(RENDER_SEEDS):
        _, _, img = _draw("rectangle", seed, cfg)
        assert axis_ratio(img) >= margin - RATIO_RENDER_SLACK, seed


def test_diamond_angle_margin(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    margin = margins["diamond_min_angle_offset_deg"]
    for seed in range(PARAM_SEEDS):
        params = sample_params("diamond", np.random.default_rng(seed),
                               cfg["synth"], margins)
        verts = vertices("diamond", params, cfg["image_size"])
        acute = min_interior_angle_deg(verts)
        assert abs(acute - 90.0) >= margin - ANGLE_TOL_DEG, seed


def test_triangle_min_angle(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    for seed in range(PARAM_SEEDS):
        params = sample_params("triangle", np.random.default_rng(seed),
                               cfg["synth"], margins)
        verts = vertices("triangle", params, cfg["image_size"])
        assert min_interior_angle_deg(verts) >= 25.0 - ANGLE_TOL_DEG, seed


def test_circle_axes_equal(cfg):
    for seed in range(RENDER_SEEDS):
        _, _, img = _draw("circle", seed, cfg)
        assert axis_ratio(img) <= CIRCLE_RENDER_MAX_RATIO, seed


def test_circle_and_ellipse_have_at_least_64_points(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    for name in ("circle", "ellipse"):
        params = sample_params(name, np.random.default_rng(0), cfg["synth"], margins)
        assert len(vertices(name, params, cfg["image_size"])) >= 64


def test_square_sides_equal_right_angles(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    for seed in range(RENDER_SEEDS):
        params = sample_params("square", np.random.default_rng(seed),
                               cfg["synth"], margins)
        verts = vertices("square", params, cfg["image_size"])
        sides = np.linalg.norm(np.roll(verts, -1, axis=0) - verts, axis=1)
        assert np.allclose(sides, sides[0], rtol=1e-9), seed
        assert np.allclose(interior_angles_deg(verts), 90.0, atol=ANGLE_TOL_DEG), seed


def test_star_inner_ratio_at_most_0_6(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    for seed in range(PARAM_SEEDS):
        params = sample_params("star", np.random.default_rng(seed), cfg["synth"], margins)
        assert params["inner_ratio"] <= 0.6, seed  # stages/stage_3.md Should 2
        assert params["inner_ratio"] >= cfg["synth"]["star_inner_ratio"][0], seed


def test_outline_not_filled(cfg):
    for name in class_names(cfg):
        for seed in range(20):
            _, _, img = _draw(name, seed, cfg)
            ink = img == 0
            region = ndimage.binary_fill_holes(ink)
            # an outline encloses white interior; a filled shape does not
            assert (region & ~ink).sum() >= 20, (name, seed)  # white interior px
            ink_fraction = float(np.mean(img == 0))
            assert ink_fraction < 0.35, (name, seed)


def test_margins_read_from_taxonomy(cfg):
    raised = copy.deepcopy(cfg)
    raised["taxonomy"]["ambiguity_margins"]["ellipse_min_axis_ratio"] = 1.8
    margins = raised["taxonomy"]["ambiguity_margins"]
    for seed in range(300):
        params = sample_params("ellipse", np.random.default_rng(seed),
                               raised["synth"], margins)
        assert params["axis_ratio"] >= 1.8, seed
    gen, log = build_generator_with_log(raised)
    for seed in range(100):
        gen(1, np.random.default_rng(seed))
    assert log.to_dict()["ellipse"]["axis_ratio"][0] >= 1.8


def test_mission_m1_violations_rejected(cfg):
    margins = cfg["taxonomy"]["ambiguity_margins"]
    synth = cfg["synth"]
    # 1. ellipse 20 x 18: ratio 1.11 < 1.2
    assert check_params("ellipse", {"axis_ratio": 20 / 18}, margins, synth)
    # 2. rectangle 30 x 20: ratio 1.5 is fine
    assert check_params("rectangle", {"side_ratio": 30 / 20}, margins, synth) == []
    # 3. diamond with an 85 deg acute angle: within 10 deg of 90
    assert check_params("diamond", {"acute_angle_deg": 85.0}, margins, synth)
    # 5. star outer 24, inner 20: inner/outer 0.83 > 0.6
    assert check_params("star", {"inner_ratio": 20 / 24}, margins, synth)
    # a clearly valid ellipse passes
    assert check_params("ellipse", {"axis_ratio": 2.0}, margins, synth) == []
