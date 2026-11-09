"""B-ensemble mistakes Stage 5 stored, limited to the configured confusable pairs.

The file holds every B mistake. Only the three pairs the report already shows
are displayed, in both directions; image ids are never read.
"""

from __future__ import annotations

import numpy as np

from studio.allowlist import prediction_path
from studio.context import classes, confusion_pairs
from studio.imaging import to_b64_png
from studio.settings import MAX_ERRORS_PAGE


def allowed_cells() -> set[tuple[int, int]]:
    """(true, predicted) class indices that may show images."""
    index = {name: i for i, name in enumerate(classes())}
    cells: set[tuple[int, int]] = set()
    for a, b in confusion_pairs():
        cells.add((index[a], index[b]))
        cells.add((index[b], index[a]))
    return cells


def page(true: int, pred: int, offset: int) -> dict | None:
    """One page of stored errors for an allowed cell. None if nothing is stored."""
    path = prediction_path("errors")
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=False) as z:
        images, labels, preds = z["images"], z["labels"], z["preds"]
    hits = np.flatnonzero((labels == true) & (preds == pred))
    chosen = hits[offset: offset + MAX_ERRORS_PAGE]
    return {"total": int(hits.size), "offset": int(offset),
            "images": [to_b64_png(images[int(i)]) for i in chosen]}
