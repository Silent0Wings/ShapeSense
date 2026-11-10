"""Deterministic content hashes for the pipeline's input cache.

Every stage records the hash of each input it read in status.json →
inputs; a stage whose recorded hashes all still match is skipped. Hashes
depend on content and relative paths only, never on mtimes or on the
order in which the OS lists a directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Collection, Iterator, Sequence

CHUNK_BYTES = 1 << 20          # read files in 1 MiB chunks
READERS = 8                    # threads reading a tree ahead of the hash
READ_BATCH = 64                # files read ahead at once (at most 64 MiB in memory)
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


def scan_files(root: str | Path, skip: Collection[str] = ()) -> Iterator[tuple[str, os.DirEntry]]:
    """(relative posix path, DirEntry) of every file under root, in no set order.

    The same files as ``Path.rglob("*")`` filtered by ``is_file()``: hidden
    names included, symlinked directories not entered, unreadable or missing
    directories skipped. os.scandir already knows each entry's type (and, on
    Windows, its size), so a large tree costs no stat per file. A file or
    directory whose name is in ``skip`` is left out at every depth.
    """
    stack = [(os.fspath(root), "")]
    while stack:
        folder, prefix = stack.pop()
        try:
            with os.scandir(folder) as it:
                entries = list(it)
        except OSError:
            continue
        for entry in entries:
            if entry.name in skip:
                continue
            rel = prefix + entry.name
            if entry.is_dir(follow_symlinks=False):
                stack.append((entry.path, rel + "/"))
            elif entry.is_file():
                yield rel, entry


def _tree_files(root: Path) -> list[tuple[str, str]]:
    return sorted((rel, entry.path) for rel, entry in scan_files(root, skip=IGNORED_DIRS)
                  if Path(entry.name).suffix not in IGNORED_SUFFIXES)


def _read_head(path: str) -> bytes:
    """A file's first CHUNK_BYTES, which is the whole of nearly every file in a tree."""
    with open(path, "rb") as f:
        return f.read(CHUNK_BYTES)


def hash_named_files(files: Sequence[tuple[str, str]]) -> str:
    """Hash (relative path, file) pairs in list order: path, NUL, content, NUL.

    Threads only read ahead, because opening many small files is what costs
    time. The digest is still fed one file at a time, in list order, so it
    does not depend on how the reads interleave.
    """
    h = hashlib.sha256()
    with ThreadPoolExecutor(READERS) as pool:
        for start in range(0, len(files), READ_BATCH):
            batch = files[start:start + READ_BATCH]
            for (rel, p), head in zip(batch, pool.map(_read_head, [p for _, p in batch])):
                h.update(rel.encode("utf-8") + b"\0")
                h.update(head)
                if len(head) == CHUNK_BYTES:  # a big file: stream the rest of it
                    with open(p, "rb") as f:
                        f.seek(CHUNK_BYTES)
                        for chunk in iter(lambda: f.read(CHUNK_BYTES), b""):
                            h.update(chunk)
                h.update(b"\0")
    return _prefixed(h)


def sha256_tree(root: str | Path) -> str:
    """Hash every file under root: sorted relative path + content."""
    return hash_named_files(_tree_files(Path(root)))


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
