"""Pure geometry for the Stage 3 generator (NumPy only, no I/O, no global RNG).

Two steps per image:
  sample_params(name, rng, synth_cfg, margins) -> dict of scalars / small arrays
  vertices(name, params, size)                 -> float64 (K, 2), canvas pixels

Columns of the vertex arrays are (x, y). The canvas is `size` x `size` and its
centre is (size/2, size/2) plus the sampled centre offset. Class names come from
configs/taxonomy.yaml; every number that is a setting is read from the config
values passed in. Only geometric definitions (vertex counts, angle sums) and
rule ceilings are named constants here.
"""

from __future__ import annotations

import functools
import math

import numpy as np

RATIO_RENDER_CUSHION = 0.05  # ratio units added to the taxonomy margin: 64-px
#   aliasing of a small, slightly rotated outline can read ~0.05 low
PIXEL_EXTENT_HALF = 0.5  # px; a rendered extent counts whole pixels (max - min + 1)
FRAME_MARGIN_PX = 1   # pixels kept white between the outline and the frame edge
TWO_PI = 2.0 * math.pi  # radians
RIGHT_ANGLE_DEG = 90.0  # degrees
ANGLE_SUM_TRIANGLE_DEG = 180.0  # degrees, interior angles of a Euclidean triangle
CIRCLE_POINTS = 64  # vertices; contract requires >= 64 for a smooth curve
ELLIPSE_POINTS = 64  # vertices; contract requires >= 64
STAR_TIPS = 5  # points of the star; the outline has 2 * STAR_TIPS vertices
STAR_INNER_RATIO_CEILING = 0.6  # inner / outer radius; stages/stage_3.md Should 2
TRIANGLE_MIN_ANGLE_DEG = 25.0  # degrees; every interior angle of a triangle
TRIANGLE_MAX_JITTER_TRIES = 50  # attempts to keep the triangle angle rule after jitter
ANGLE_EPS_DEG = 1e-6  # degrees; float tolerance for angle comparisons
REGULAR_SIDES = {"pentagon": 5, "hexagon": 6, "octagon": 8}  # vertex counts
UNIT_POLYGON_CACHE_SIZE = 8  # distinct (vertex count, phase) pairs; the classes use five
SUPPORTED_CLASSES = frozenset({
    "circle", "ellipse", "triangle", "square", "rectangle",
    "pentagon", "hexagon", "octagon", "star", "diamond",
})


def _uniform(rng: np.random.Generator, lo: float, hi: float, what: str) -> float:
    """rng.uniform(lo, hi) that refuses an empty range instead of sampling outside it."""
    if hi < lo:
        raise ValueError(f"{what}: upper bound {hi} is below lower bound {lo}")
    return float(rng.uniform(lo, hi))


@functools.lru_cache(maxsize=UNIT_POLYGON_CACHE_SIZE)
def _unit_polygon(n: int, phase: float) -> np.ndarray:
    """(n, 2) float64 vertices of the regular n-gon of radius 1, first at `phase`. Read-only."""
    ang = phase + np.arange(n) * (TWO_PI / n)
    pts = np.column_stack([np.cos(ang), np.sin(ang)])
    pts.setflags(write=False)
    return pts


def _regular_polygon(n: int, radius: float, phase: float = -math.pi / 2) -> np.ndarray:
    """Regular n-gon centred at the origin.

    Args:
        n: number of vertices (>= 3).
        radius: circumradius in pixels (> 0).
        phase: angle of the first vertex in radians.

    Returns:
        float64 (n, 2), x/y in pixels, every vertex at distance `radius`.
    """
    return radius * _unit_polygon(n, phase)


def _rotate(pts: np.ndarray, theta: float) -> np.ndarray:
    """Rotate (K, 2) points by theta radians about the origin."""
    c, s = math.cos(theta), math.sin(theta)
    return pts @ np.array([[c, s], [-s, c]])


def _triangle_base(angles_deg: np.ndarray, radius: float) -> np.ndarray:
    """Triangle inscribed in a circle of radius `radius`, with interior angles A, B, C.

    Vertex P0 has angle A, P1 has angle B, P2 has angle C. The central angle
    over an arc equals twice the inscribed angle opposite that arc.
    """
    a, _b, c = (math.radians(float(x)) for x in angles_deg)
    t = np.array([0.0, 2.0 * c, 2.0 * c + 2.0 * a])
    return radius * np.column_stack([np.cos(t), np.sin(t)])


def _base_outline(name: str, params: dict) -> np.ndarray:
    """Unrotated, unjittered outline centred at the origin, float64 (K, 2)."""
    r = params["radius_px"]
    if name == "circle":
        return _regular_polygon(CIRCLE_POINTS, r)
    # The drawn outline adds half a stroke on each side, which pulls the
    # visible ratio of a thin shape toward 1. The margin is therefore
    # applied to the OUTER (stroke-inclusive) extents, so the rendered image
    # meets it, and the centreline ratio is strictly larger.
    half = 0.5 * params.get("stroke_px", 0.0) + PIXEL_EXTENT_HALF
    if name == "ellipse":
        ratio = params["axis_ratio"]
        minor = (r + half) / ratio - half
        return _regular_polygon(ELLIPSE_POINTS, 1.0) * np.array([r, minor])
    if name == "triangle":
        return _triangle_base(params["interior_angles_deg"], r)
    if name == "square":
        return _regular_polygon(4, r, phase=math.pi / 4)
    if name == "rectangle":
        # Half-diagonal is `radius_px`; w / h = side_ratio.
        ratio = params["side_ratio"]
        h = r / math.sqrt(1.0 + ratio * ratio)
        w = ratio * (h + half) - half
        return np.array([[w, h], [-w, h], [-w, -h], [w, -h]], dtype=np.float64)
    if name == "diamond":
        # Rhombus with long half-diagonal p = radius_px. Interior angle at the
        # tips on the long axis is 2 * atan(q / p) = acute_angle_deg.
        p = r
        q = p * math.tan(math.radians(params["acute_angle_deg"]) / 2.0)
        return np.array([[p, 0.0], [0.0, q], [-p, 0.0], [0.0, -q]], dtype=np.float64)
    if name in REGULAR_SIDES:
        return _regular_polygon(REGULAR_SIDES[name], r)
    if name == "star":
        k = np.arange(2 * STAR_TIPS)
        ang = -math.pi / 2 + k * (math.pi / STAR_TIPS)
        rad = np.where(k % 2 == 0, r, r * params["inner_ratio"])
        return np.column_stack([rad * np.cos(ang), rad * np.sin(ang)])
    raise ValueError(f"no geometry for class {name!r}")


def _outline(name: str, params: dict) -> np.ndarray:
    """Final outline before the canvas offset: base + vertex jitter, then rotation."""
    pts = _base_outline(name, params)
    jitter = params.get("vertex_jitter_px")
    if jitter is not None:
        pts = pts + jitter
    return _rotate(pts, params["rotation_rad"])


def _attach_jitter(name: str, rng: np.random.Generator, params: dict, amp: float) -> None:
    """Store uniform +/- amp pixel jitter per vertex in params["vertex_jitter_px"]."""
    shape = _base_outline(name, params).shape
    params["vertex_jitter_px"] = rng.uniform(-amp, amp, size=shape)


def interior_angles_deg(vertices_: np.ndarray) -> np.ndarray:
    """Unsigned angle at each vertex, between its two incident edges.

    Args:
        vertices_: float (K, 2) polygon vertices in boundary order.

    Returns:
        float64 (K,) degrees in (0, 180]. For a rhombus the acute angle is the
        minimum; the obtuse one is 180 minus it.
    """
    pts = np.asarray(vertices_, dtype=np.float64)
    prev = np.roll(pts, 1, axis=0) - pts
    nxt = np.roll(pts, -1, axis=0) - pts
    dot = np.sum(prev * nxt, axis=1)
    norms = np.linalg.norm(prev, axis=1) * np.linalg.norm(nxt, axis=1)
    cos = np.clip(dot / norms, -1.0, 1.0)
    return np.degrees(np.arccos(cos))


def sample_params(name: str, rng: np.random.Generator, synth_cfg: dict,
                  margins: dict) -> dict:
    """Draw one set of render parameters for class `name`.

    Args:
        name: class name from configs/taxonomy.yaml (e.g. "ellipse").
        rng: the only source of randomness.
        synth_cfg: the `synth` section of configs/pipeline.yaml.
        margins: `ambiguity_margins` from configs/taxonomy.yaml.

    Returns:
        dict of Python floats (scalars) and float64 arrays. Keys always include
        radius_px, rotation_rad (radians, [0, 2pi)), dx_px, dy_px (pixels) and
        the class-specific ratios or angles (axis_ratio, side_ratio,
        acute_angle_deg, inner_ratio, interior_angles_deg, vertex_jitter_px).

    Raises:
        ValueError: unknown class, or a configured range that is empty.
    """
    if name not in SUPPORTED_CLASSES:
        raise ValueError(f"no geometry for class {name!r}")
    jitter_px = float(synth_cfg["center_jitter_px"])
    params: dict = {
        "stroke_px": float(synth_cfg["stroke_px"]),
        "radius_px": _uniform(rng, *synth_cfg["radius_px"], "synth.radius_px"),
        "rotation_rad": float(rng.uniform(0.0, TWO_PI)),
        "dx_px": _uniform(rng, -jitter_px, jitter_px, "synth.center_jitter_px"),
        "dy_px": _uniform(rng, -jitter_px, jitter_px, "synth.center_jitter_px"),
    }
    vertex_amp = float(synth_cfg["vertex_jitter_px"])

    if name == "ellipse":
        params["axis_ratio"] = _uniform(
            rng, margins["ellipse_min_axis_ratio"] + RATIO_RENDER_CUSHION,
            synth_cfg["ellipse_max_axis_ratio"], "ellipse axis ratio")
    elif name == "rectangle":
        params["side_ratio"] = _uniform(
            rng, margins["rectangle_min_side_ratio"] + RATIO_RENDER_CUSHION,
            synth_cfg["rectangle_max_side_ratio"], "rectangle side ratio")
    elif name == "diamond":
        lo, hi = synth_cfg["diamond_acute_angle_deg"]
        angle = _uniform(rng, lo, hi, "synth.diamond_acute_angle_deg")
        # Clamp so that |angle - 90| >= the taxonomy margin (acute side only).
        params["acute_angle_deg"] = min(
            angle, RIGHT_ANGLE_DEG - float(margins["diamond_min_angle_offset_deg"]))
    elif name == "star":
        lo, hi = synth_cfg["star_inner_ratio"]
        params["inner_ratio"] = _uniform(
            rng, lo, min(hi, STAR_INNER_RATIO_CEILING), "synth.star_inner_ratio")
        _attach_jitter(name, rng, params, vertex_amp)
    elif name == "triangle":
        # Dirichlet(1, 1, 1) on the simplex, scaled so every angle is >= the
        # minimum and the three sum to 180 deg.
        u = rng.dirichlet(np.ones(3))
        params["interior_angles_deg"] = (
            TRIANGLE_MIN_ANGLE_DEG
            + (ANGLE_SUM_TRIANGLE_DEG - 3.0 * TRIANGLE_MIN_ANGLE_DEG) * u)
        for _ in range(TRIANGLE_MAX_JITTER_TRIES):
            _attach_jitter(name, rng, params, vertex_amp)
            if (interior_angles_deg(_outline(name, params)).min()
                    >= TRIANGLE_MIN_ANGLE_DEG - ANGLE_EPS_DEG):
                break
        else:
            params["vertex_jitter_px"] = np.zeros((3, 2))
    elif name in REGULAR_SIDES:
        _attach_jitter(name, rng, params, vertex_amp)
    # circle, square: no class-specific draw. Circle, square, rectangle and
    # diamond get no vertex jitter, so their margins hold exactly.
    return params


def vertices(name: str, params: dict, size: int) -> np.ndarray:
    """Closed-polygon vertices on a canvas of `size` pixels.

    Args:
        name: class name.
        params: dict from sample_params for the same class.
        size: canvas side in pixels (> 0).

    Returns:
        float64 (K, 2), columns (x, y) in canvas pixels, boundary order, not
        closed (the first vertex is not repeated). Circle and ellipse have
        CIRCLE_POINTS / ELLIPSE_POINTS vertices.
    """
    pts = _outline(name, params)
    half = 0.5 * params.get("stroke_px", 0.0)
    lo_edge, hi_edge = FRAME_MARGIN_PX + half, size - 1 - FRAME_MARGIN_PX - half
    span = (pts.max(axis=0) - pts.min(axis=0)).max()
    room = hi_edge - lo_edge
    if span > room:
        # Too big for the frame: shrink uniformly (label-safe), never clip.
        pts = pts * (room / span)
    centre = np.array([size / 2.0 + params["dx_px"], size / 2.0 + params["dy_px"]])
    out = pts + centre
    # Shift (not clip) so the whole outline stays inside the frame margin.
    out = out + np.maximum(lo_edge - out.min(axis=0), 0.0)
    out = out - np.maximum(out.max(axis=0) - hi_edge, 0.0)
    return out


def check_params(name: str, params: dict, margins: dict, synth_cfg: dict) -> list[str]:
    """List the stage 3 rules that a parameter set breaks (empty list = valid).

    Args:
        name: class name.
        params: dict in the canonical keys of sample_params (axis_ratio,
            side_ratio, acute_angle_deg, inner_ratio).
        margins: `ambiguity_margins` from configs/taxonomy.yaml.
        synth_cfg: the `synth` section of configs/pipeline.yaml.

    Returns:
        Human-readable violation messages; empty when every rule holds.
    """
    problems: list[str] = []
    if name == "ellipse":
        low = float(margins["ellipse_min_axis_ratio"])
        if params["axis_ratio"] < low:
            problems.append(f"ellipse axis ratio {params['axis_ratio']:.3f} < {low}")
    elif name == "rectangle":
        low = float(margins["rectangle_min_side_ratio"])
        if params["side_ratio"] < low:
            problems.append(f"rectangle side ratio {params['side_ratio']:.3f} < {low}")
    elif name == "diamond":
        acute = float(params["acute_angle_deg"])
        offset = float(margins["diamond_min_angle_offset_deg"])
        if acute >= RIGHT_ANGLE_DEG:
            problems.append(f"diamond acute angle {acute} is not acute")
        elif RIGHT_ANGLE_DEG - acute < offset - ANGLE_EPS_DEG:
            problems.append(f"diamond angle {acute} is within {offset} deg of 90")
    elif name == "star":
        ratio = float(params["inner_ratio"])
        low, high = (float(x) for x in synth_cfg["star_inner_ratio"])
        if ratio > min(high, STAR_INNER_RATIO_CEILING) or ratio < low:
            problems.append(f"star inner/outer {ratio:.3f} outside [{low}, {high}] "
                            f"capped at {STAR_INNER_RATIO_CEILING}")
    return problems
