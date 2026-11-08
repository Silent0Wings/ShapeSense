"""Manifest contract (stages/stage_1.md R10, Done-when D6).

Reads train.csv and val.csv through common.load_split only. The test
manifest is NEVER read here; test-split overlap is asserted inside Stage 1
and recorded in its status checks (plan 21).
"""

import pytest

from src.common.config import REPO_ROOT
from src.common.splits import MANIFEST_COLUMNS, load_split

SPLITS_DIR = REPO_ROOT / "configs" / "splits"


def _rows_or_skip(name):
    if not (SPLITS_DIR / f"{name}.csv").is_file():
        pytest.skip(f"{name}.csv not written yet (run python run_pipeline.py --stages 1)")
    return load_split(name, splits_dir=SPLITS_DIR)


def test_schema_and_no_overlap_train_val():
    train, val = _rows_or_skip("train"), _rows_or_skip("val")
    assert train and val
    for rows, name in ((train, "train"), (val, "val")):
        assert list(rows[0].keys()) == MANIFEST_COLUMNS
        assert all(r["split"] == name for r in rows)
    for key in ("image_id", "md5", "phash_group"):
        shared = {r[key] for r in train} & {r[key] for r in val}
        assert not shared, f"{key} shared between train and val: {sorted(shared)[:5]}"
