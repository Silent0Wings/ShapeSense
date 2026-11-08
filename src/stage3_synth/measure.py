"""Pure measurement helpers used by the Stage 3 tests (NumPy only).

They measure what the generator produced, independently of the parameters
that produced it, so a test can check the rendered image as well as the
sampled numbers.
"""

from __future__ import annotations

import numpy as np

from .shapes import interior_angles_deg

INK_THRESHOLD = 128  # grey level; pixels below this count as ink
PIXEL_SPAN_OFFSET = 1.0  # pixels; span of a run of pixels is max - min + 1


def axis_ratio(img: np.ndarray) -> float:
    """Ratio of the major to the minor extent of the ink pixels.

    Principal axes come from the PCA of the ink pixel coordinates. The extent
    along each axis is max - min + 1 pixels.

    Args:
        img: uint8 (H, W), ink below INK_THRESHOLD.

    Returns:
        float >= 1.0. NaN when the image has fewer than two ink pixels.
    """
    arr = np.asarray(img)
    ys, xs = np.nonzero(arr < INK_THRESHOLD)
    if xs.size < 2:
        return float("nan")
    pts = np.column_stack([xs, ys]).astype(np.float64)
    centred = pts - pts.mean(axis=0)
    cov = centred.T @ centred / pts.shape[0]
    _, vecs = np.linalg.eigh(cov)
    proj = centred @ vecs
    spans = proj.max(axis=0) - proj.min(axis=0) + PIXEL_SPAN_OFFSET
    return float(spans.max() / spans.min())


def min_interior_angle_deg(vertices: np.ndarray) -> float:
    """Smallest unsigned interior angle of a polygon.

    Args:
        vertices: float (K, 2) in boundary order.

    Returns:
        float degrees in (0, 180]. For a rhombus this is the acute angle.
    """
    return float(np.min(interior_angles_deg(vertices)))
