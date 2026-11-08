"""Content identity for every unified image (stages/stage_1.md R1, Decision 1).

The catalog's `Image` table carries neither pHash nor any content hash;
pHash lives in metadata.csv and md5 exists only as a function. This
module joins the two files and computes `md5` of the standardized array,
so both become first-class row fields that the manifests carry forward.

Split membership is NOT taken from either file: `Image.split` and the
train/val/test path prefixes are Phase 1 leftovers (Decision 15).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Iterable

from src.common.catalog import connect_readonly, read_png
from src.common.config import resolve
from src.common.imaging import md5

PHASH_HEX_BASE = 16  # metadata.csv stores pHash as a 16-digit hex string

ROW_FIELDS = ("image_id", "label_id", "source_id", "domain", "phash", "path", "md5")

_CATALOG_QUERY = (
    "SELECT i.image_id, i.source_id, i.label_id, i.path, s.domain "
    "FROM Image AS i JOIN Source AS s ON s.source_id = i.source_id"
)


def join_rows(catalog_rows: Iterable[dict], metadata_rows: Iterable[dict],
              md5_of: Callable[[str], str]) -> list[dict]:
    """Join catalog rows with metadata rows on image_id and attach md5.

    catalog_rows:  dicts with image_id, source_id, label_id, path, domain.
    metadata_rows: dicts with at least image_id and phash (hex string).
    md5_of:        path (relative, as stored in the catalog) -> md5 hex.

    Returns one dict per catalog row with the keys in ROW_FIELDS
    (label_id int, phash int), sorted by image_id. Raises KeyError when a
    catalog image has no metadata row, so a stale metadata.csv fails loudly.
    """
    phash_by_id: dict[str, int] = {}
    for m in metadata_rows:
        phash_by_id[m["image_id"]] = int(m["phash"], PHASH_HEX_BASE)
    out: list[dict] = []
    for c in catalog_rows:
        iid = c["image_id"]
        if iid not in phash_by_id:
            raise KeyError(f"metadata.csv has no row for catalog image {iid!r}")
        out.append({
            "image_id": iid,
            "label_id": int(c["label_id"]),
            "source_id": c["source_id"],
            "domain": c["domain"],
            "phash": phash_by_id[iid],
            "path": c["path"],
            "md5": md5_of(c["path"]),
        })
    out.sort(key=lambda r: r["image_id"])
    return out


def read_metadata(path: str | Path) -> list[dict]:
    """All rows of metadata.csv as dicts of strings."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_catalog_rows(catalog_path: str | Path) -> list[dict]:
    """Image rows joined with their Source.domain, read-only."""
    con = connect_readonly(catalog_path)
    try:
        cur = con.execute(_CATALOG_QUERY)
        return [dict(zip(("image_id", "source_id", "label_id", "path", "domain"), r))
                for r in cur]
    finally:
        con.close()


def load_unified(config: dict) -> list[dict]:
    """Catalog + metadata + md5 pass for every image (reads every PNG once)."""
    unified_dir = resolve(config["paths"]["unified_dir"])
    catalog_rows = read_catalog_rows(resolve(config["paths"]["catalog"]))
    metadata_rows = read_metadata(resolve(config["paths"]["metadata"]))

    def md5_of(rel_path: str) -> str:
        return md5(read_png(unified_dir / rel_path))

    return join_rows(catalog_rows, metadata_rows, md5_of)
