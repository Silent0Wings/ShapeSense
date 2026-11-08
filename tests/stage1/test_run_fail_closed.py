"""Stage 1 run() is fail-closed end to end (stages/stage_1.md R9).

Every check (leakage, noise bands, FDs, source shortcut) runs in
plan_freeze() BEFORE freeze(); a check that fails or raises leaves
configs/splits (here: a tmp splits_dir) without a single manifest.
No data_set/ needed: load_unified, the grouping/split and the image
loader are replaced by synthetic rows.
"""

import copy
import csv
from pathlib import Path

import numpy as np
import pytest

from src.common.config import class_names, load_config
from src.stage1_freeze import run as stage1

ROOT = Path(__file__).resolve().parents[2]
SPLIT_CYCLE = ("train", "val", "test")
META_COLUMNS = ("image_id", "source_id", "domain", "license", "original_label", "label_id",
                "label_name", "path", "split", "native_width", "native_height", "phash")


def _config(tmp_path: Path) -> dict:
    cfg = copy.deepcopy(load_config(ROOT / "configs" / "pipeline.yaml"))
    cfg["exclude_source_labels"] = []  # synthetic rows: the exclusion rule has its own tests
    unified = tmp_path / "unified"
    cfg["paths"].update({
        "unified_dir": str(unified),
        "catalog": str(unified / "catalog.sqlite"),
        "metadata": str(unified / "metadata.csv"),
        "raw_dir": str(tmp_path / "data"),
        "gemstone_ids": str(tmp_path / "configs" / "gemstone_ids.csv"),
        "splits_dir": str(tmp_path / "configs" / "splits"),
        "artifacts_dir": str(tmp_path / "artifacts"),
        "test_access_log": str(tmp_path / "artifacts" / "test_access.log"),
    })
    cfg["filter_gemstones"] = False
    return cfg


def _rows(cfg: dict) -> list[dict]:
    """Three rows per class, one per split, every md5/phash unique."""
    rows = []
    i = 0
    for lab, name in enumerate(class_names(cfg)):
        for split in SPLIT_CYCLE:
            rows.append({"image_id": f"src_{name}_{i:06d}", "label_id": lab, "source_id": "src",
                         "domain": "sketch", "phash": i, "path": f"x/{name}/{i}.png",
                         "md5": f"md5-{i:06d}", "want_split": split})
            i += 1
    return rows


def _write_metadata(cfg: dict, rows: list[dict], names: list[str],
                    domain_of=lambda r: r["domain"]) -> None:
    p = Path(cfg["paths"]["metadata"])
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(META_COLUMNS), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({"image_id": r["image_id"], "source_id": r["source_id"],
                        "domain": domain_of(r), "license": "CC0",
                        "original_label": names[r["label_id"]], "label_id": r["label_id"],
                        "label_name": names[r["label_id"]], "path": r["path"],
                        "split": "train", "native_width": 28, "native_height": 28,
                        "phash": f"{r['phash']:016x}"})


@pytest.fixture()
def harness(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    rows = _rows(cfg)
    names = class_names(cfg)
    _write_metadata(cfg, rows, names)
    side = int(cfg["image_size"])

    monkeypatch.setattr(stage1, "load_unified", lambda config: copy.deepcopy(rows))
    monkeypatch.setattr(stage1, "global_groups", lambda phashes, max_hamming: list(range(len(phashes))))
    monkeypatch.setattr(stage1, "group_split", lambda rs, ratios, seed: [r["want_split"] for r in rs])
    monkeypatch.setattr(stage1, "_load_images",
                        lambda rs, unified_dir: np.full((len(rs), side, side), 255, dtype=np.uint8))
    return cfg, rows, names


def _manifests(cfg: dict) -> list[Path]:
    """Every CSV under the tmp splits_dir plus any leftover .splits_tmp_* directory."""
    splits_dir = Path(cfg["paths"]["splits_dir"])
    found = sorted(splits_dir.glob("*.csv")) if splits_dir.is_dir() else []
    if splits_dir.parent.is_dir():
        found += sorted(p for p in splits_dir.parent.iterdir() if p.name.startswith(".splits_tmp_"))
    return found


def test_clean_run_passes_and_writes_three_manifests(harness):
    cfg, rows, _ = harness
    result = stage1.run(cfg)
    assert result["status"] == "passed"
    assert all(result["checks"].values())
    assert set(result["checks"]) == {"no_id_in_two_splits", "no_md5_in_two_splits",
                                     "no_phash_group_spans", "fd_all_hold"}
    assert [p.name for p in _manifests(cfg)] == ["test.csv", "train.csv", "val.csv"]
    assert result["metrics"]["train"] == result["metrics"]["val"] == result["metrics"]["test"] == 10


def test_noise_band_failure_blocks_manifests(harness, monkeypatch):
    cfg, _, _ = harness

    def boom(*args, **kwargs):
        raise ValueError("class 5 (pentagon) has no rows in the test split")

    monkeypatch.setattr(stage1, "noise_bands", boom)
    with pytest.raises(ValueError, match="no rows in the test split"):
        stage1.run(cfg)
    assert _manifests(cfg) == []


def test_fd_violation_blocks_manifests(harness):
    cfg, rows, names = harness
    # one row of source "src" carries another domain: source_id -> domain is violated
    _write_metadata(cfg, rows, names,
                    domain_of=lambda r: "RENDER" if r["image_id"] == rows[0]["image_id"] else r["domain"])
    result = stage1.run(cfg)
    assert result["status"] == "failed"
    assert result["checks"]["fd_all_hold"] is False
    assert _manifests(cfg) == []
    # the diagnostic artefact is still written so the violation can be read
    fd_check = Path(cfg["paths"]["artifacts_dir"]) / "stage1" / "fd_check.json"
    assert fd_check.is_file()
    assert "fd_check.json" in " ".join(result["outputs"])


def test_leak_blocks_manifests(harness, monkeypatch):
    cfg, rows, _ = harness
    leaked = copy.deepcopy(rows)
    leaked[1]["md5"] = leaked[0]["md5"]          # same md5 in train and val (R5)
    monkeypatch.setattr(stage1, "load_unified", lambda config: copy.deepcopy(leaked))
    result = stage1.run(cfg)
    assert result["status"] == "failed"
    assert result["checks"]["no_md5_in_two_splits"] is False
    assert _manifests(cfg) == []


def test_plan_freeze_writes_nothing(harness):
    cfg, rows, _ = harness
    assigned = copy.deepcopy(rows)
    for i, r in enumerate(assigned):
        r["phash_group"] = f"g{i:06d}"
        r["split"] = r["want_split"]
    checks, artefacts = stage1.plan_freeze(cfg, assigned)
    assert all(checks.values())
    assert set(artefacts) == {"split_stats", "noise_bands", "fd_check", "source_classifier",
                              "source_test_share"}
    assert len(artefacts["noise_bands"]) == len(class_names(cfg))
    assert _manifests(cfg) == []
    assert not (Path(cfg["paths"]["artifacts_dir"]) / "stage1").exists()
