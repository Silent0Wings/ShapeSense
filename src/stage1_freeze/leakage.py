"""Leakage assertions and fail-closed manifest writing (R4, R5, R9, R10).

`leakage_checks` is pure. `write_manifests` writes the three CSVs to a
temporary directory first and moves them into place, so a failure half
way leaves no partial manifest behind. `freeze` is the fail-closed
composition (Mission M3): checks first, manifests only if every check
holds, otherwise `status: failed` and nothing written.
"""

from __future__ import annotations

import csv
import os
import shutil
import tempfile
from pathlib import Path

from src.common.splits import MANIFEST_COLUMNS, SPLITS

CHECK_KEYS = {
    "no_id_in_two_splits": "image_id",
    "no_md5_in_two_splits": "md5",
    "no_phash_group_spans": "phash_group",
}
LINE_TERMINATOR = "\n"   # LF so the committed manifests diff cleanly on every OS


def _spans_two_splits(rows: list[dict], key: str) -> bool:
    seen: dict[str, str] = {}
    for r in rows:
        value, split = str(r[key]), str(r["split"])
        if seen.setdefault(value, split) != split:
            return True
    return False


def leakage_checks(manifest_rows: list[dict]) -> dict[str, bool]:
    """R4/R5: no image_id, md5 or phash_group appears in two splits."""
    return {name: not _spans_two_splits(manifest_rows, key)
            for name, key in CHECK_KEYS.items()}


def manifest_row(row: dict) -> dict:
    """Project a row onto the shared manifest schema (R10)."""
    return {c: row[c] for c in MANIFEST_COLUMNS}


def write_manifests(rows: list[dict], splits_dir: str | Path) -> list[Path]:
    """Write train.csv, val.csv, test.csv under splits_dir, atomically as a set.

    Columns exactly MANIFEST_COLUMNS, rows sorted by image_id, utf-8, LF.
    """
    splits_dir = Path(splits_dir)
    splits_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".splits_tmp_", dir=splits_dir.parent))
    try:
        ordered = sorted(rows, key=lambda r: r["image_id"])
        written: list[Path] = []
        for name in SPLITS:
            p = tmp / f"{name}.csv"
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS,
                                   lineterminator=LINE_TERMINATOR)
                w.writeheader()
                for r in ordered:
                    if r["split"] == name:
                        w.writerow(manifest_row(r))
            written.append(p)
        final = []
        for p in written:
            dest = splits_dir / p.name
            os.replace(p, dest)
            final.append(dest)
        return final
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def freeze(rows: list[dict], splits_dir: str | Path) -> dict:
    """Run the leakage checks; write manifests only if all hold (R9, M3).

    Returns {"status": "passed"|"failed", "checks": {...}, "outputs": [Path, ...]}.
    """
    checks = leakage_checks(rows)
    if not all(checks.values()):
        return {"status": "failed", "checks": checks, "outputs": []}
    return {"status": "passed", "checks": checks, "outputs": write_manifests(rows, splits_dir)}
