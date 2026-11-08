"""E15: migration equivalence comparison (stages/stage_0.md R2, D3)."""

from src.stage0_infra.migration import compare

REC = {"catalog_content": "sha256:a", "rows": 18500, "class_counts": {"0": 2500},
       "phash_groups": "sha256:g", "metadata_content": "sha256:m"}


def test_identical_records_pass():
    assert compare(REC, dict(REC))["equal"] is True


def test_any_count_difference_fails():
    for key, value in [("rows", 18499), ("class_counts", {"0": 2499}),
                       ("phash_groups", "sha256:other"), ("catalog_content", "sha256:b")]:
        r = compare(REC, {**REC, key: value})
        assert r["equal"] is False and key in r["differences"]
