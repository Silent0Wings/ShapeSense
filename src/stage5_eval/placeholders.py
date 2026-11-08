"""Placeholder LaTeX tables so the Phase 2 report compiles before Stage 5 runs
(stages/stage_0.md R10). build.ps1 runs pdflatex with -halt-on-error, so a
missing \\input file would stop the report; each placeholder is a single
dash. Real tables written by Stage 5 are never overwritten, and Stage 6's
traceability check flags any placeholder left in place.
"""

from __future__ import annotations

from pathlib import Path

TABLE_NAMES = ("metrics", "per_class", "comparisons", "per_source", "power", "verdict",
               "test_reads")
PLACEHOLDER_MARK = "% PLACEHOLDER (Stage 0): Stage 5 has not run yet"
PLACEHOLDER_TEXT = PLACEHOLDER_MARK + "\n--\n"


def is_placeholder(path: str | Path) -> bool:
    p = Path(path)
    return p.is_file() and p.read_text(encoding="utf-8").startswith(PLACEHOLDER_MARK)


def write_placeholders(tables_dir: str | Path) -> list[Path]:
    """Write a dash table for every missing name; return the files written."""
    d = Path(tables_dir)
    d.mkdir(parents=True, exist_ok=True)
    written = []
    for name in TABLE_NAMES:
        p = d / f"{name}.tex"
        if not p.exists():
            p.write_text(PLACEHOLDER_TEXT, encoding="utf-8")
            written.append(p)
    return written
