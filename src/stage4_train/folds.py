"""Grouped, stratified folds for the iteration 3 search.

Train and validation are pooled and split so near-duplicate images never straddle
a fold. Folds are grouped on ``phash_group``, not on ``source_id``: ellipse,
pentagon and diamond each come from one source, so source folds would remove a
class from training or validation. The hold-out-source runs test sources instead.
The sealed splits never enter this code.
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from src.stage4_train.data import ImageStore


def pooled(train: ImageStore, val: ImageStore) -> ImageStore:
    return ImageStore(images=np.concatenate([train.images, val.images]),
                      labels=np.concatenate([train.labels, val.labels]),
                      source_ids=np.concatenate([train.source_ids, val.source_ids]),
                      n_classes=train.n_classes,
                      group_ids=np.concatenate([train.group_ids, val.group_ids]))


def grouped_folds(store: ImageStore, n_folds: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """(train positions, validation positions) per fold."""
    splitter = StratifiedGroupKFold(n_splits=int(n_folds), shuffle=True, random_state=int(seed))
    return [(np.asarray(a), np.asarray(b)) for a, b in splitter.split(store.images, store.labels, store.group_ids)]
