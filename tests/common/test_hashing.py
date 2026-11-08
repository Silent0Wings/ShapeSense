"""E13: deterministic hashing of files, trees and config subtrees."""

from src.common import hashing


def test_file_hash_prefix_and_change(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x", encoding="utf-8")
    h1 = hashing.sha256_file(p)
    assert h1.startswith("sha256:")
    p.write_text("y", encoding="utf-8")
    assert hashing.sha256_file(p) != h1


def test_tree_hash_order_independent_of_listing(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for root, order in ((a, ["z", "m", "c"]), (b, ["c", "z", "m"])):
        (root / "sub").mkdir(parents=True)
        for name in order:
            (root / "sub" / name).write_bytes(name.encode())
    assert hashing.sha256_tree(a) == hashing.sha256_tree(b)
    (b / "sub" / "m").write_bytes(b"changed")
    assert hashing.sha256_tree(a) != hashing.sha256_tree(b)


def test_tree_hash_ignores_pycache(tmp_path):
    (tmp_path / "m.py").write_text("x = 1", encoding="utf-8")
    h = hashing.sha256_tree(tmp_path)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "m.pyc").write_bytes(b"junk")
    assert hashing.sha256_tree(tmp_path) == h


def test_config_subtree_hash_changes_with_value():
    cfg = {"split": {"ratios": [0.7, 0.15, 0.15], "seed": 42}, "other": 1}
    h = hashing.config_subtree_hash(cfg, "split")
    assert hashing.config_subtree_hash({**cfg, "other": 2}, "split") == h
    cfg2 = {"split": {"ratios": [0.7, 0.15, 0.15], "seed": 43}, "other": 1}
    assert hashing.config_subtree_hash(cfg2, "split") != h


def test_obj_hash_key_order_independent():
    assert hashing.sha256_obj({"a": 1, "b": 2}) == hashing.sha256_obj({"b": 2, "a": 1})
