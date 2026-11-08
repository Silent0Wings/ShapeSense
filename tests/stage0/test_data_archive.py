"""E19: raw-data archive hash is deterministic (stages/stage_0.md R12)."""

import os
import time

from src.stage0_infra.data_archive import archive_sha256


def _tree(root, order):
    for name in order:
        p = root / "src" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(name.encode())


def test_tree_hash_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _tree(a, ["x.png", "y.png", "z.png"])
    _tree(b, ["z.png", "x.png", "y.png"])
    os.utime(b / "src" / "x.png", (time.time() - 1e5, time.time() - 1e5))
    assert archive_sha256(a) == archive_sha256(b)


def test_hash_changes_when_file_changes(tmp_path):
    _tree(tmp_path, ["x.png"])
    before = archive_sha256(tmp_path)
    (tmp_path / "src" / "x.png").write_bytes(b"other")
    assert archive_sha256(tmp_path) != before


def test_excluded_top_level_dir_ignored(tmp_path):
    _tree(tmp_path, ["x.png"])
    before = archive_sha256(tmp_path, exclude=["unified"])
    (tmp_path / "unified").mkdir()
    (tmp_path / "unified" / "built.png").write_bytes(b"derived")
    assert archive_sha256(tmp_path, exclude=["unified"]) == before
