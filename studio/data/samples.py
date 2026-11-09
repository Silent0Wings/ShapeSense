"""The browsable image pool: train and val only, chosen through the manifests.

This is the only module that imports the catalog. Manifests are the authority on
which split an image belongs to, because the folders under data_set/unified are
named after an older split. Any image stored in the old ``test/`` folder is also
dropped, so this module never opens a file in that folder at all.
"""

from __future__ import annotations

import functools

import numpy as np
from src.common.catalog import image_paths, load_images, load_split_rows

from studio.context import config
from studio.settings import POOL_SPLITS


class SplitNotAllowed(ValueError):
    """A caller asked for a split other than train or val."""


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


@functools.lru_cache(maxsize=2)
def _pool(split: str) -> tuple[dict, ...]:
    """Manifest rows of one split whose image is not stored under the old test folder."""
    if split not in POOL_SPLITS:
        raise SplitNotAllowed(split)
    paths = image_paths(config())
    rows = load_split_rows(config(), split)
    return tuple(r for r in rows if not _norm(paths[r["image_id"]]).startswith("test/"))


def pool_counts(split: str) -> dict:
    rows = _pool(split)
    return {"kept": len(rows), "total_manifest": len(load_split_rows(config(), split))}


def _class_rows(split: str, label: int) -> list[dict]:
    return [r for r in _pool(split) if int(r["label_id"]) == int(label)]


def pick(split: str, label: int, n: int, seed: int) -> tuple[np.ndarray, list[dict]]:
    """``n`` random images of a class; returns (images, their manifest rows)."""
    rows = _class_rows(split, label)
    if not rows:
        return np.empty((0, 64, 64), dtype=np.uint8), []
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(rows), size=min(n, len(rows)), replace=False)
    chosen = [rows[int(i)] for i in idx]
    return load_images(config(), [r["image_id"] for r in chosen]), chosen


def nth(split: str, label: int, index: int) -> tuple[np.ndarray, dict] | None:
    """The image at a stable position of a class, wrapping around; None when empty."""
    rows = _class_rows(split, label)
    if not rows:
        return None
    row = rows[int(index) % len(rows)]
    return load_images(config(), [row["image_id"]])[0], row


def class_stats(split: str, label: int, n: int, seed: int) -> dict | None:
    """Mean and spread of up to ``n`` images of a class, for the Stage 1 page."""
    images, rows = pick(split, label, n, seed)
    if not rows:
        return None
    stack = images.astype(np.float32)
    return {"mean": stack.mean(axis=0).astype(np.uint8),
            "std": np.clip(stack.std(axis=0) * 2.0, 0, 255).astype(np.uint8),
            "n": len(rows)}


def largest_groups(split: str, top: int) -> list[dict]:
    """The ``top`` largest near-duplicate groups in the pool, largest first."""
    counts: dict[str, int] = {}
    label: dict[str, str] = {}
    for r in _pool(split):
        counts[r["phash_group"]] = counts.get(r["phash_group"], 0) + 1
        label[r["phash_group"]] = r["label_id"]
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [{"group": g, "size": n, "label": int(label[g])} for g, n in ranked]


def group_images(split: str, group: str, n: int) -> np.ndarray:
    rows = [r for r in _pool(split) if r["phash_group"] == group][:n]
    return load_images(config(), [r["image_id"] for r in rows])
