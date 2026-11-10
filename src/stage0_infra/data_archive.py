"""Deterministic SHA-256 of the raw data tree (stages/stage_0.md R12).

The hash covers every file's relative path and bytes, in sorted order, so
two machines holding the same raw archive get the same digest whatever
their file timestamps or directory listing order.
"""

from __future__ import annotations

from pathlib import Path

from src.common.hashing import hash_named_files, scan_files


def archive_sha256(root: str | Path, exclude: list[str] | None = None) -> tuple[str, int]:
    """(\"sha256:<hex>\", file count) over root, skipping top-level names in exclude."""
    root = Path(root)
    skip = set(exclude or [])
    files = sorted((rel, entry.path) for rel, entry in scan_files(root)
                   if rel.split("/", 1)[0] not in skip)
    return hash_named_files(files), len(files)
