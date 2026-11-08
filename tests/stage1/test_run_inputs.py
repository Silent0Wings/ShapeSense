"""Stage 1 input hashes: creating the header-only gemstone template is not a change."""

import copy
from pathlib import Path

from src.common.config import load_config
from src.stage1_freeze.contact_sheet import write_template
from src.stage1_freeze.run import inputs

ROOT = Path(__file__).resolve().parents[2]


def _config(tmp_path: Path) -> dict:
    cfg = copy.deepcopy(load_config(ROOT / "configs" / "pipeline.yaml"))
    cfg["paths"].update({
        "unified_dir": str(tmp_path / "unified"),
        "catalog": str(tmp_path / "unified" / "catalog.sqlite"),
        "metadata": str(tmp_path / "unified" / "metadata.csv"),
        "gemstone_ids": str(tmp_path / "configs" / "gemstone_ids.csv"),
        "splits_dir": str(tmp_path / "configs" / "splits"),
        "artifacts_dir": str(tmp_path / "artifacts"),
    })
    return cfg


def test_template_creation_does_not_change_inputs(tmp_path):
    cfg = _config(tmp_path)
    gemstone_path = Path(cfg["paths"]["gemstone_ids"])
    before = inputs(cfg)
    assert write_template(gemstone_path) is True          # run() does this on every fresh checkout
    after = inputs(cfg)
    assert after == before
    assert after["gemstone_ids"] == before["gemstone_ids"]


def test_filled_exclusion_list_changes_inputs(tmp_path):
    cfg = _config(tmp_path)
    gemstone_path = Path(cfg["paths"]["gemstone_ids"])
    write_template(gemstone_path)
    before = inputs(cfg)
    with open(gemstone_path, "a", encoding="utf-8", newline="") as f:
        f.write("quickdraw_diamond_000007,abc123\n")
    after = inputs(cfg)
    assert after["gemstone_ids"] != before["gemstone_ids"]
    assert {k for k in after if after[k] != before[k]} == {"gemstone_ids"}
