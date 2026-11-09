"""Turn the browser's base64 PNG into a PIL image, with hard size limits."""

from __future__ import annotations

import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

from studio.settings import MAX_PNG_BYTES, MAX_PNG_SIDE

PNG_PREFIX = "data:image/png;base64,"


class BadDrawing(ValueError):
    """The upload is not a PNG of an accepted size."""


def decode_png(payload: str) -> Image.Image:
    if not payload.startswith(PNG_PREFIX):
        raise BadDrawing("expected a PNG data URL")
    try:
        data = base64.b64decode(payload[len(PNG_PREFIX):], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BadDrawing("invalid base64") from exc
    if len(data) > MAX_PNG_BYTES:
        raise BadDrawing("drawing is too large")
    try:
        image = Image.open(io.BytesIO(data))
        if image.format != "PNG":
            raise BadDrawing("not a PNG")
        if max(image.size) > MAX_PNG_SIDE:
            raise BadDrawing("drawing is too large")
        return image.convert("RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        raise BadDrawing("not a readable PNG") from exc
