"""Gemstone-diamond exclusion list (Decision 1, stages/stage_1.md R2).

The list in configs/gemstone_ids.csv is written by human reviewers from
the contact sheet. Matching is on `md5` ONLY: `image_id` is positional
(`f"{source}_{label}_{i:06d}"`) and shifts whenever the build is rerun,
so it is recorded for the reviewers' convenience but never used to match.
A listed md5 that matches zero images or more than one fails the stage.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable

EXCLUSION_COLUMNS = ("image_id", "md5")


class GemstoneMatchError(ValueError):
    """A listed md5 matched zero images or more than one (R2)."""


def read_exclusions(path: str | Path) -> list[dict]:
    """Rows of the exclusion CSV (header `image_id,md5`); [] if missing or header-only."""
    p = Path(path)
    if not p.is_file():
        return []
    with open(p, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        if header is None:          # empty file: treat like a header-only template
            return []
        missing = [c for c in EXCLUSION_COLUMNS if c not in header]
        if missing:
            raise GemstoneMatchError(f"{p}: missing column(s) {missing}; "
                                     f"expected header {','.join(EXCLUSION_COLUMNS)}")
        rows = []
        for line_no, r in enumerate(reader, start=2):   # line 1 is the header
            values = {c: (r.get(c) or "").strip() for c in EXCLUSION_COLUMNS}
            if not any(values.values()):
                continue                                 # fully blank line: skipped
            if not values["md5"]:
                # A reviewer wrote an image_id but no md5: the row can never
                # match, so dropping it silently would hide a missed exclusion.
                raise GemstoneMatchError(f"{p}:{line_no}: image_id {values['image_id']!r} "
                                         "has an empty md5; matching is on md5 only")
            rows.append(values)
    return rows


def apply_gemstone_filter(rows: list[dict], exclusions: Iterable[dict]
                          ) -> tuple[list[dict], int]:
    """Drop every row whose md5 is listed; return (kept_rows, n_removed).

    Raises GemstoneMatchError when any listed md5 matches 0 or >1 rows.
    Duplicate md5 entries in the list are reported as an error too, so a
    reviewer's copy-paste slip never hides a missing match.
    """
    listed = [e["md5"] for e in exclusions]
    if not listed:
        return list(rows), 0
    repeated = sorted(m for m, n in Counter(listed).items() if n > 1)
    if repeated:
        raise GemstoneMatchError(f"md5 listed more than once in the exclusion list: {repeated}")
    counts = Counter(r["md5"] for r in rows)
    problems = []
    for m in listed:
        n = counts.get(m, 0)
        if n != 1:
            problems.append(f"{m} matched {n} image(s)")
    if problems:
        raise GemstoneMatchError("gemstone list must match exactly one image per md5: "
                                 + "; ".join(problems))
    wanted = set(listed)
    kept = [r for r in rows if r["md5"] not in wanted]
    return kept, len(rows) - len(kept)
