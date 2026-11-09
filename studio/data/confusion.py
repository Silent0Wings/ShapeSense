"""Confusion counts from Stage 5's cached ensemble predictions (no test read).

Only the ``preds`` and ``labels`` arrays are loaded; no image and no image id
leaves this module.
"""

from __future__ import annotations

import numpy as np

from studio.allowlist import prediction_path
from studio.context import classes


def counts(arm: str) -> list[list[int]] | None:
    """(k, k) counts, rows are the true class. None when Stage 5 has not run."""
    path = prediction_path(arm)
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=False) as z:
        preds, labels = z["preds"], z["labels"]
    k = len(classes())
    matrix = np.zeros((k, k), dtype=np.int64)
    np.add.at(matrix, (labels.astype(np.int64), preds.astype(np.int64)), 1)
    return matrix.tolist()
