"""E20: md5-keyed gemstone filter (stages/stage_1.md R2, Decision 1)."""

import pytest

from src.stage1_freeze.gemstones import (GemstoneMatchError, apply_gemstone_filter,
                                         read_exclusions)


def _rows():
    return [
        {"image_id": "quickdraw_diamond_000001", "md5": "aaa", "label_id": 9},
        {"image_id": "quickdraw_diamond_000002", "md5": "bbb", "label_id": 9},
        {"image_id": "quickdraw_diamond_000003", "md5": "ccc", "label_id": 9},
    ]


def test_removes_exact_md5_matches():
    kept, removed = apply_gemstone_filter(_rows(), [{"image_id": "x", "md5": "bbb"}])
    assert removed == 1
    assert [r["md5"] for r in kept] == ["aaa", "ccc"]


def test_zero_match_fails():
    with pytest.raises(GemstoneMatchError, match="matched 0"):
        apply_gemstone_filter(_rows(), [{"image_id": "x", "md5": "zzz"}])


def test_duplicate_match_fails():
    rows = _rows() + [{"image_id": "quickdraw_diamond_000004", "md5": "aaa", "label_id": 9}]
    with pytest.raises(GemstoneMatchError, match="matched 2"):
        apply_gemstone_filter(rows, [{"image_id": "x", "md5": "aaa"}])


def test_empty_list_removes_nothing(tmp_path):
    kept, removed = apply_gemstone_filter(_rows(), [])
    assert removed == 0 and len(kept) == 3
    header_only = tmp_path / "gemstone_ids.csv"
    header_only.write_text("image_id,md5\n", encoding="utf-8")
    assert read_exclusions(header_only) == []
    assert read_exclusions(tmp_path / "missing.csv") == []


def test_matches_on_md5_not_image_id():
    # Same positional id as a real row but a different md5: the id must not match.
    exclusions = [{"image_id": "quickdraw_diamond_000001", "md5": "not-aaa"}]
    with pytest.raises(GemstoneMatchError, match="matched 0"):
        apply_gemstone_filter(_rows(), exclusions)


def test_read_exclusions_parses_rows(tmp_path):
    p = tmp_path / "gemstone_ids.csv"
    p.write_text("image_id,md5\nquickdraw_diamond_000007,abc123\n", encoding="utf-8")
    assert read_exclusions(p) == [{"image_id": "quickdraw_diamond_000007", "md5": "abc123"}]


def test_blank_md5_row_fails(tmp_path):
    """An image_id without an md5 can never match: fail, never drop it silently."""
    p = tmp_path / "gemstone_ids.csv"
    p.write_text("image_id,md5\n"
                 "quickdraw_diamond_000007,abc123\n"
                 "quickdraw_diamond_000008,\n", encoding="utf-8")
    with pytest.raises(GemstoneMatchError, match="quickdraw_diamond_000008"):
        read_exclusions(p)
    # whitespace-only md5 is blank too
    p.write_text("image_id,md5\nquickdraw_diamond_000009,   \n", encoding="utf-8")
    with pytest.raises(GemstoneMatchError, match="empty md5"):
        read_exclusions(p)


def test_fully_blank_lines_are_skipped(tmp_path):
    p = tmp_path / "gemstone_ids.csv"
    p.write_text("image_id,md5\n\n,\nquickdraw_diamond_000007,abc123\n   \n", encoding="utf-8")
    assert read_exclusions(p) == [{"image_id": "quickdraw_diamond_000007", "md5": "abc123"}]
