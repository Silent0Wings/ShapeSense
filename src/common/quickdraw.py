"""Quick, Draw! stroke rendering (public; was the private
build_unified_dataset._qd_loader that audit_dataset.py imported)."""

from typing import Callable

from PIL import Image, ImageDraw

QD_CANVAS_PX = 256   # Quick, Draw! simplified drawings live on 256x256
QD_STROKE_PX = 3     # stroke width used in the Phase 1 build


def quickdraw_loader(rec: dict) -> Callable[[], Image.Image]:
    """Return a zero-arg loader that renders one ndjson record to RGB."""
    def load() -> Image.Image:
        im = Image.new("RGB", (QD_CANVAS_PX, QD_CANVAS_PX), "white")
        d = ImageDraw.Draw(im)
        for xs, ys in rec["drawing"]:
            d.line(list(zip(xs, ys)), fill="black", width=QD_STROKE_PX)
        return im
    return load
