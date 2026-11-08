"""E21: leakage assertions and the fail-closed freeze (R4, R5, R9; Missions M1, M3)."""

import csv

from src.common.splits import MANIFEST_COLUMNS
from src.stage1_freeze.leakage import freeze, leakage_checks, write_manifests

M1_TABLE = """image_id,md5,label_id,source_id,phash_group,split
img_001,a1b2,5,2,g010,train
img_002,c3d4,5,2,g010,test
img_003,e5f6,0,4,g011,val
img_003,e5f6,0,4,g011,train
img_004,a1b2,9,1,g012,test
img_005,0a9f,3,3,g013,val
"""


def _m1_rows():
    return list(csv.DictReader(M1_TABLE.splitlines()))


def test_mission_m1_rows_flagged():
    checks = leakage_checks(_m1_rows())
    assert checks == {"no_id_in_two_splits": False,     # img_003 in val and train (R5)
                      "no_md5_in_two_splits": False,    # img_004 carries img_001's md5 (R5)
                      "no_phash_group_spans": False}    # g010 in train and test (R4)
    clean = [r for r in _m1_rows() if r["image_id"] == "img_005"]
    clean.append({"image_id": "img_006", "md5": "ffff", "label_id": "1", "source_id": "2",
                  "phash_group": "g014", "split": "train"})
    assert all(leakage_checks(clean).values())


def test_injected_leak_writes_no_manifests(tmp_path):
    splits_dir = tmp_path / "splits"
    rows = _m1_rows()
    result = freeze(rows, splits_dir)
    assert result["status"] == "failed"
    assert result["checks"]["no_id_in_two_splits"] is False
    assert list(tmp_path.rglob("*.csv")) == []           # nothing written, no temp leftovers
    assert not any(p.name.startswith(".splits_tmp_") for p in tmp_path.iterdir())


def test_clean_freeze_writes_three_manifests(tmp_path):
    splits_dir = tmp_path / "splits"
    rows = [r for r in _m1_rows() if r["image_id"] in ("img_001", "img_005")]
    result = freeze(rows, splits_dir)
    assert result["status"] == "passed" and all(result["checks"].values())
    assert sorted(p.name for p in splits_dir.glob("*.csv")) == ["test.csv", "train.csv", "val.csv"]
    with open(splits_dir / "train.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        train = list(reader)
    assert reader.fieldnames == MANIFEST_COLUMNS
    assert [r["image_id"] for r in train] == ["img_001"]
    assert (splits_dir / "test.csv").read_text(encoding="utf-8") == ",".join(MANIFEST_COLUMNS) + "\n"


def test_write_manifests_sorted_and_schema_only(tmp_path):
    rows = [
        {"image_id": "b", "md5": "2", "label_id": 1, "source_id": "s", "phash_group": "g2",
         "split": "val", "path": "ignored", "phash": 7},
        {"image_id": "a", "md5": "1", "label_id": 0, "source_id": "s", "phash_group": "g1",
         "split": "val"},
    ]
    write_manifests(rows, tmp_path)
    text = (tmp_path / "val.csv").read_text(encoding="utf-8")
    assert text == ("image_id,md5,label_id,source_id,phash_group,split\n"
                    "a,1,0,s,g1,val\n"
                    "b,2,1,s,g2,val\n")
