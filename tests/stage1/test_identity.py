"""E20: catalog + metadata join with md5 (stages/stage_1.md R1)."""

from src.stage1_freeze.identity import ROW_FIELDS, join_rows


def test_join_rows_md5_and_types():
    catalog = [
        {"image_id": "b_002", "source_id": "qd", "label_id": "9", "path": "x/b.png", "domain": "sketch"},
        {"image_id": "a_001", "source_id": "ek", "label_id": 5, "path": "x/a.png", "domain": "render"},
    ]
    metadata = [
        {"image_id": "a_001", "phash": "00000000000000ff", "split": "test"},
        {"image_id": "b_002", "phash": "8000000000000000", "split": "train"},
    ]
    rows = join_rows(catalog, metadata, md5_of=lambda p: "md5-of-" + p)

    assert [r["image_id"] for r in rows] == ["a_001", "b_002"]  # sorted by image_id
    assert all(tuple(r) == ROW_FIELDS for r in rows)
    a, b = rows
    assert a["label_id"] == 5 and b["label_id"] == 9 and isinstance(b["label_id"], int)
    assert a["phash"] == 0xFF and b["phash"] == 1 << 63 and isinstance(a["phash"], int)
    assert a["md5"] == "md5-of-x/a.png" and b["md5"] == "md5-of-x/b.png"
    assert a["domain"] == "render" and b["source_id"] == "qd"
    assert "split" not in a  # Phase 1 split is never carried (Decision 15)
