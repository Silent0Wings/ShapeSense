"""Deterministic content hashes for the pipeline's input cache.

Every stage records the hash of each input it read in status.json →
inputs; a stage whose recorded hashes all still match is skipped. Hashes
depend on content and relative paths only, never on mtimes or on the
order in which the OS lists a directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CHUNK_BYTES = 1 << 20          # read files in 1 MiB chunks
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc"}


def _prefixed(h: "hashlib._Hash") -> str:
    return "sha256:" + h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return _prefixed(hashlib.sha256(data))


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_BYTES), b""):
            h.update(chunk)
    return _prefixed(h)


def _tree_files(root: Path):
    for p in sorted(root.rglob("*"), key=lambda q: q.relative_to(root).as_posix()):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if p.is_file() and p.suffix not in IGNORED_SUFFIXES:
            yield rel.as_posix(), p


def sha256_tree(root: str | Path) -> str:
    """Hash every file under root: sorted relative path + content."""
    root = Path(root)
    h = hashlib.sha256()
    for rel, p in _tree_files(root):
        h.update(rel.encode("utf-8") + b"\0")
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_BYTES), b""):
                h.update(chunk)
        h.update(b"\0")
    return _prefixed(h)


def sha256_path(path: str | Path) -> str:
    """File or directory hash; a missing path hashes to 'missing'."""
    p = Path(path)
    if p.is_dir():
        return sha256_tree(p)
    if p.is_file():
        return sha256_file(p)
    return "missing"


def sha256_obj(obj: Any) -> str:
    """Canonical JSON hash (sorted keys), for config subtrees."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_bytes(text.encode("utf-8"))


def config_subtree_hash(cfg: dict, dotted: str) -> str:
    cur: Any = cfg
    for part in dotted.split("."):
        cur = cur[part]
    return sha256_obj(cur)
