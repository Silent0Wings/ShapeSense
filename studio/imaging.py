"""uint8 image arrays as base64 PNG strings for the browser."""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image


def to_b64_png(image: np.ndarray) -> str:
    """Encode a (H, W) uint8 array. The browser scales it up without smoothing."""
    arr = np.asarray(image, dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(arr).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
