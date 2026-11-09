"""Summary of the test-access log: counts only, never modified."""

from __future__ import annotations

from collections import Counter

from studio.data.tables import read_text


def summary() -> dict:
    text = read_text("access_log")
    if text is None:
        return {"total": 0, "callers": {}, "run_ids": []}
    rows = [line.split(",") for line in text.splitlines() if line.strip()]
    return {"total": len(rows), "callers": dict(Counter(r[2] for r in rows)),
            "run_ids": sorted({r[1] for r in rows})}
