"""Stage 0 migration equivalence (stages/stage_0.md R2, Done-when D3).

Proves that moving the Phase 1 scripts from scripts/ into src/ changed
nothing: the pre-move unified dataset (data_set/unified/, built by the
original scripts) and a rebuild by the moved code must agree on

- catalog content hash (every row of every table, sorted),
- row count and class counts,
- per-(source, label) pHash near-duplicate groups (the Phase 1 scope),
- metadata.csv content hash.

This checks only the move. Decision 15's global regrouping happens in
Stage 1 and is expected to change the split numbers.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from src.common.hashing import sha256_file, sha256_obj
from src.common.neardup import near_dup_groups

TABLES = ["Source", "Label", "LabelMapping", "Image", "AugmentationRecord"]
COMPARED = ["catalog_content", "rows", "class_counts", "phash_groups", "metadata_content"]


def _catalog_rows(catalog: Path) -> dict[str, list]:
    con = sqlite3.connect(Path(catalog).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return {t: sorted(map(list, con.execute(f"SELECT * FROM {t}")), key=repr)
                for t in TABLES}
    finally:
        con.close()


def _phash_groups(meta_rows: list[dict], max_hamming: int) -> list[list[str]]:
    by_key = defaultdict(list)
    for r in meta_rows:
        by_key[(r["source_id"], r["label_name"])].append(r)
    groups = []
    for key in sorted(by_key):
        rows = by_key[key]
        gid = near_dup_groups([int(r["phash"], 16) for r in rows], max_hamming)
        clusters = defaultdict(list)
        for r, g in zip(rows, gid):
            clusters[g].append(r["image_id"])
        groups.extend(sorted(c) for c in clusters.values() if len(c) > 1)
    return sorted(groups)


def record(unified_dir: str | Path, max_hamming: int) -> dict:
    """Summary of one unified dataset build."""
    d = Path(unified_dir)
    rows = _catalog_rows(d / "catalog.sqlite")
    with open(d / "metadata.csv", encoding="utf-8", newline="") as f:
        meta = list(csv.DictReader(f))
    groups = _phash_groups(meta, max_hamming)
    return {
        "catalog_content": sha256_obj(rows),
        "catalog_file": sha256_file(d / "catalog.sqlite"),
        "rows": len(rows["Image"]),
        "class_counts": {str(k): v for k, v in sorted(Counter(r[2] for r in rows["Image"]).items())},
        "phash_groups": sha256_obj(groups),
        "phash_group_count": len(groups),
        "metadata_content": sha256_obj(sorted(map(lambda r: sorted(r.items()), meta))),
    }


def compare(before: dict, after: dict) -> dict:
    """Field-by-field comparison; `equal` only if every compared field matches."""
    diffs = {k: {"before": before.get(k), "after": after.get(k)}
             for k in COMPARED if before.get(k) != after.get(k)}
    return {"equal": not diffs, "compared": COMPARED, "differences": diffs,
            "before": before, "after": after}


def write_check(result: dict, out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return p
