"""Read-only access to the unified catalog and its standardized PNGs.

The SQLite catalog (data_set/unified/catalog.sqlite) is the authority on
paths, labels and sources; split membership comes ONLY from the Stage 1
manifests through common.load_split (Decision 15). Every connection is
opened read-only (`mode=ro`), one per process (Windows-safe).
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from src.common.config import resolve
from src.common.splits import load_split

PNG_READERS = 8  # threads reading PNGs; file opens and zlib run outside the GIL


def connect_readonly(catalog_path: str | Path) -> sqlite3.Connection:
    uri = Path(catalog_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def image_paths(config: dict) -> dict[str, str]:
    """image_id -> PNG path relative to paths.unified_dir."""
    con = connect_readonly(resolve(config["paths"]["catalog"]))
    try:
        return dict(con.execute("SELECT image_id, path FROM Image"))
    finally:
        con.close()


def read_png(path: str | Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("L"), dtype=np.uint8)


def load_split_rows(config: dict, split: str) -> list[dict]:
    """Manifest rows of a split (goes through the test-split guard)."""
    return load_split(split, splits_dir=resolve(config["paths"]["splits_dir"]),
                      log_path=resolve(config["paths"]["test_access_log"]))


def load_images(config: dict, image_ids: list[str]) -> np.ndarray:
    """uint8 (N, S, S) images for the given ids, in order."""
    paths = image_paths(config)
    root = resolve(config["paths"]["unified_dir"])
    size = config["image_size"]
    out = np.empty((len(image_ids), size, size), dtype=np.uint8)
    files = [root / paths[iid] for iid in image_ids]
    with ThreadPoolExecutor(PNG_READERS) as pool:
        for i, image in enumerate(pool.map(read_png, files)):
            out[i] = image
    return out


def load_fresh_images(config: dict, rows: list[dict], folder: str = "fresh_holdout") -> tuple[np.ndarray, np.ndarray]:
    """Images + labels of a fresh holdout, from the PNGs named in its manifest rows."""
    root = resolve(config["paths"]["raw_dir"]) / folder
    size = config["image_size"]
    images = np.empty((len(rows), size, size), dtype=np.uint8)
    for i, row in enumerate(rows):
        images[i] = read_png(root / row["path"])
    return images, np.array([int(r["label_id"]) for r in rows], dtype=np.int64)


def load_split_images(config: dict, split: str, per_class: int | None = None,
                      seed: int = 0, rows: list[dict] | None = None
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Images + labels of one split; optionally `per_class` random images per class.

    The split is read through common.load_split, so a test read outside
    src.stage5_eval raises and every test read is logged. Pass `rows` to
    reuse manifest rows already read (no second log line).
    """
    if rows is None:
        rows = load_split_rows(config, split)
    if per_class is not None:
        rng = np.random.default_rng(seed)
        by_label: dict[int, list[dict]] = {}
        for r in rows:
            by_label.setdefault(int(r["label_id"]), []).append(r)
        picked = []
        for label in sorted(by_label):
            group = by_label[label]
            idx = rng.choice(len(group), size=min(per_class, len(group)), replace=False)
            picked.extend(group[i] for i in sorted(idx))
        rows = picked
    images = load_images(config, [r["image_id"] for r in rows])
    labels = np.array([int(r["label_id"]) for r in rows], dtype=np.int64)
    return images, labels
