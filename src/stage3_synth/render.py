"""Rasterise a closed polygon as a black outline on white (no fill).

Output format matches the real data (stages/stage_3.md R2): single channel,
uint8, pure 0 ink on 255 background, no grey anti-aliased edge pixels.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

WHITE = 255  # pixel value of background
BLACK = 0  # pixel value of ink
MAX_CAPPED_VERTICES = 16  # polygons with more vertices are curves (no corner caps)
BINARY_THRESHOLD = 128  # grey level; after downsampling, >= this becomes white


def render_outline(vertices: np.ndarray, size: int, stroke_px: float,
                   supersample: int) -> np.ndarray:
    """Draw the closed outline of `vertices` and return a binary image.

    Args:
        vertices: float (K, 2), columns (x, y) in pixels of a `size` canvas,
            boundary order, not repeated at the end.
        size: output side in pixels (> 0).
        stroke_px: outline width in output pixels (>= 1).
        supersample: integer factor; drawing happens at size * supersample.

    Returns:
        uint8 (size, size), values only 0 (ink) or 255 (background).
    """
    hi = size * supersample
    pts = np.asarray(vertices, dtype=np.float64) * supersample
    canvas = Image.new("L", (hi, hi), WHITE)
    draw = ImageDraw.Draw(canvas)
    # A closed line, not polygon(width=): Pillow's wide polygon outline fills
    # concave shapes such as the star. No joint="curve": it adds a pie slice
    # at every vertex (64 per circle) and halves throughput (R8).
    coords = pts.ravel().tolist()  # flat [x0, y0, x1, y1, ...]; the first point closes the line
    width = max(1, round(stroke_px * supersample))
    draw.line(coords + coords[:2], fill=BLACK, width=width)
    # square caps at real corners so joins have no notch; smooth curves
    # (circle/ellipse polygons) have tiny turning angles and need none
    if len(pts) <= MAX_CAPPED_VERTICES:
        r = width / 2.0
        for x, y in pts.tolist():
            draw.rectangle((x - r, y - r, x + r, y + r), fill=BLACK)
    small = canvas.resize((size, size), Image.Resampling.BOX)
    arr = np.asarray(small, dtype=np.uint8)
    return BLACK + (arr >= BINARY_THRESHOLD).astype(np.uint8) * (WHITE - BLACK)
