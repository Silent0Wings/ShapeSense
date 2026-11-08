"""Pure geometry helpers for Stage 2 (NumPy only: no file I/O, no RNG, no config).

Coordinates are float pixel positions as (row, col), matching image layout.
"""

from __future__ import annotations

import numpy as np

BLACK_LEVEL = 0                                  # grey level of ink (uint8)
WHITE_LEVEL = 255                                # grey level of paper (uint8)
MIDGREY_LEVEL = (BLACK_LEVEL + WHITE_LEVEL) / 2  # grey level splitting ink from paper (127.5)
FIT_ANGLE_STEP_DEG = 0.5                         # degrees between candidate rectangle orientations
QUARTER_TURN_DEG = 90.0                          # degrees; a rectangle repeats every quarter turn
MIN_INK_PIXELS = 2                               # pixels needed for a defined extent


def ink_coords(img: np.ndarray, ink_level: float = MIDGREY_LEVEL) -> np.ndarray:
    """Positions of ink pixels.

    img: any 2-D array of grey levels (uint8 in practice).
    Returns (N, 2) float64 (row, col) for every pixel with value < ink_level;
    N may be 0.
    """
    rows, cols = np.nonzero(np.asarray(img) < ink_level)
    return np.column_stack((rows, cols)).astype(np.float64)


def fitted_ratio(img: np.ndarray) -> float:
    """Long/short side of the minimum-area rectangle around the ink of img.

    img: (H, W) uint8, ink darker than MIDGREY_LEVEL, paper white.
    Returns a float >= 1.0 (inf if the ink is collinear).

    The rectangle is searched over orientations (FIT_ANGLE_STEP_DEG steps over
    a quarter turn) and the minimum-area one is kept. This is NOT the axis-
    aligned bounding box, so a rotated rectangle keeps its ratio. A pure PCA
    axis choice is not used because a square has isotropic second moments,
    so its PCA axes are arbitrary and would report ratios up to sqrt(2).
    """
    pts = ink_coords(img)
    if pts.shape[0] < MIN_INK_PIXELS:
        raise ValueError("fitted_ratio needs at least 2 ink pixels")
    pts = pts - pts.mean(axis=0)
    theta = np.deg2rad(np.arange(0.0, QUARTER_TURN_DEG, FIT_ANGLE_STEP_DEG))
    c, s = np.cos(theta), np.sin(theta)
    along = np.outer(pts[:, 0], c) + np.outer(pts[:, 1], s)     # (N, A)
    across = np.outer(pts[:, 1], c) - np.outer(pts[:, 0], s)    # (N, A)
    w_along = along.max(axis=0) - along.min(axis=0)
    w_across = across.max(axis=0) - across.min(axis=0)
    k = int(np.argmin(w_along * w_across))
    short, long_ = sorted((float(w_along[k]), float(w_across[k])))
    if short <= 0.0:
        return float("inf")
    return long_ / short


def _rot(angle_rad: float) -> np.ndarray:
    """2x2 rotation matrix for angle_rad (radians)."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def compose_affine(rotation_rad: float, shear_rad: float,
                   axis_factors: np.ndarray, orient_rad: float) -> np.ndarray:
    """Unit-scale linear part R(rot) @ Shear(shear) @ R(orient) diag(f) R(-orient).

    axis_factors: (2,) float per-axis stretch factors, applied along the axes
    rotated by orient_rad. Returns (2, 2) float64. The caller multiplies by
    the uniform scale.
    """
    shear = np.array([[1.0, np.tan(shear_rad)], [0.0, 1.0]], dtype=np.float64)
    stretch = _rot(orient_rad) @ np.diag(axis_factors) @ _rot(-orient_rad)
    return _rot(rotation_rad) @ shear @ stretch


def within_frame(points: np.ndarray, matrix: np.ndarray, center: np.ndarray,
                 shift: np.ndarray, size: int, margin: float) -> bool:
    """True if the forward-mapped points keep `margin` pixels to every frame edge.

    The forward map is x -> matrix @ (x - center) + center + shift.
    points: (N, 2) float (row, col), N >= 1. size: frame side in pixels.
    margin: pixels. Returns a Python bool.
    """
    moved = (points - center) @ matrix.T + center + shift
    return bool(moved.min() >= margin and moved.max() <= size - 1 - margin)
