"""Stage 4 data access: the in-memory image store for one split.

Stage 4 loads every image of the train or val split once (uint8
(N, 64, 64) plus labels and source ids) and samples batches from memory
(``sampling.make_batch``). That is the simplest way to reach CPU
training throughput (plan 26 § 6) and it keeps the hot path NumPy-only.

Test-split hygiene (stage_4.md R8): ``ImageStore.from_split`` accepts
only "train" and "val" and raises ``ValueError`` for anything else, so
Stage 4 cannot even ask for the test split; ``common.load_split`` guards
it a second time underneath.

The catalog readers come from ``src.common.catalog``::

    load_split_images(config, split, per_class=None, seed=0, rows=None)
        -> (uint8 (N, 64, 64), int64 (N,))
    load_split_rows(config, split) -> list[dict]   # manifest rows

Both are injectable (``loader=`` / ``rows_loader=``) so tests run on
synthetic arrays without ``data_set/``. The manifest is read once and its
rows are handed to the image loader, so images and source ids line up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from src.stage4_train.sampling import class_index, to_float

__all__ = ["ImageStore", "to_float", "ALLOWED_SPLITS"]

ALLOWED_SPLITS = ("train", "val")  # Stage 4 never reads "test" (R8)
SOURCE_COLUMN = "source_id"       # manifest column holding the source id

ImagesLoader = Callable[..., tuple[np.ndarray, np.ndarray]]
RowsLoader = Callable[[dict, str], list[dict]]


def _default_images_loader(config: dict, split: str,
                           rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    from src.common.catalog import load_split_images  # data-access layer, lazy
    return load_split_images(config, split, rows=rows)


def _default_rows_loader(config: dict, split: str) -> list[dict]:
    from src.common.catalog import load_split_rows  # data-access layer, lazy
    return load_split_rows(config, split)


@dataclass
class ImageStore:
    """All images of one split held in memory.

    Attributes:
        images: uint8 (N, S, S), black outline on white.
        labels: int64 (N,), taxonomy label index.
        source_ids: str array (N,), manifest ``source_id`` per image.
        n_classes: number of classes (taxonomy size).
        class_idx: per-class index lists, ``sampling.class_index``.
    """

    images: np.ndarray
    labels: np.ndarray
    source_ids: np.ndarray
    n_classes: int
    class_idx: list[np.ndarray] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.images = np.asarray(self.images)
        self.labels = np.asarray(self.labels, dtype=np.int64)
        self.source_ids = np.asarray(self.source_ids).astype(str)
        n = self.images.shape[0]
        if self.labels.shape != (n,) or self.source_ids.shape != (n,):
            raise ValueError(f"images ({n}), labels ({self.labels.shape}) and source_ids "
                             f"({self.source_ids.shape}) must have one entry per image")
        if self.images.dtype != np.uint8:
            raise ValueError(f"images must be uint8, got {self.images.dtype}")
        self.class_idx = class_index(self.labels, self.n_classes)

    def __len__(self) -> int:
        return int(self.images.shape[0])

    @classmethod
    def from_split(cls, config: dict, split: str, *,
                   loader: ImagesLoader | None = None,
                   rows_loader: RowsLoader | None = None) -> "ImageStore":
        """Load every image of ``split`` ("train" or "val" only).

        Raises ValueError for any other split name, in particular "test"
        (stage_4.md R8). ``n_classes`` comes from the merged taxonomy
        (``config["taxonomy"]["classes"]``).
        """
        if split not in ALLOWED_SPLITS:
            raise ValueError(f"Stage 4 may only load {ALLOWED_SPLITS}, not {split!r} "
                             "(the test split belongs to Stage 5; stage_4.md R8)")
        load_images = loader or _default_images_loader
        load_rows = rows_loader or _default_rows_loader
        rows = load_rows(config, split)  # read once: images and ids share these rows
        images, labels = load_images(config, split, rows=rows)
        if len(rows) != len(labels):
            raise ValueError(f"{split}: {len(rows)} manifest rows but {len(labels)} images")
        source_ids = np.array([row[SOURCE_COLUMN] for row in rows], dtype=str)
        n_classes = len(config["taxonomy"]["classes"])
        return cls(images=images, labels=labels, source_ids=source_ids, n_classes=n_classes)

    def filter_out_source(self, source_id: str) -> "ImageStore":
        """Return a new store without the images of ``source_id``.

        Used for the Hand-Drawn leave-one-source-out runs (Decision 12).
        The original store is left unchanged.
        """
        keep = self.source_ids != str(source_id)
        return ImageStore(images=self.images[keep], labels=self.labels[keep],
                          source_ids=self.source_ids[keep], n_classes=self.n_classes)

    def class_counts(self) -> np.ndarray:
        """int64 (n_classes,) number of stored images per class."""
        return np.array([len(ix) for ix in self.class_idx], dtype=np.int64)
