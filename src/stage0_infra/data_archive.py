"""Deterministic SHA-256 of the raw data tree (stages/stage_0.md R12).

The hash covers every file's relative path and bytes, in sorted order, so
two machines holding the same raw archive get the same digest whatever
their file timestamps or directory listing order.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_BYTES = 1 << 20  # 1 MiB


def archive_sha256(root: str | Path, exclude: list[str] | None = None) -> tuple[str, int]:
    """(\"sha256:<hex>\", file count) over root, skipping top-level names in exclude."""
    root = Path(root)
    skip = set(exclude or [])
    files = sorted((p for p in root.rglob("*")
                    if p.is_file() and p.relative_to(root).parts[0] not in skip),
                   key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for p in files:
        h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_BYTES), b""):
                h.update(chunk)
        h.update(b"\0")
    return "sha256:" + h.hexdigest(), len(files)
