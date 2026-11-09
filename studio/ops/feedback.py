"""Save a drawing the user says was predicted wrongly, always under FEEDBACK_DIR."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from PIL import Image

from studio import settings

NOTE = "Informal feedback for a future CRISP-DM iteration; not test data."


def save(image: Image.Image, strokes: list, results: list[dict]) -> str:
    """Write ``<name>.png`` and ``<name>.json``; the name is never taken from the request."""
    now = datetime.now()
    name = f"{now:%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    settings.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    image.save(settings.FEEDBACK_DIR / f"{name}.png")
    record = {"saved_at": now.isoformat(timespec="seconds"), "note": NOTE, "strokes": strokes, "results": results}
    (settings.FEEDBACK_DIR / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return f"{settings.FEEDBACK_LABEL}/{name}.png"
