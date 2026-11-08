"""Stage 0 input hashes cover what the checks depend on and never Stage 0's own outputs."""

import copy
from pathlib import Path

from src.common.config import load_config
from src.stage0_infra import run as stage0

ROOT = Path(__file__).resolve().parents[2]


def _config(tmp_path: Path) -> dict:
    cfg = copy.deepcopy(load_config(ROOT / "configs" / "pipeline.yaml"))
    raw = tmp_path / "data"
    (raw / "unified").mkdir(parents=True)
    (raw / "source_a").mkdir()
    (raw / "source_a" / "img.png").write_bytes(b"raw-bytes")
    (raw / "unified" / "catalog.sqlite").write_bytes(b"catalog-v1")
    cfg["paths"].update({
        "raw_dir": str(raw),
        "unified_dir": str(raw / "unified"),
        "catalog": str(raw / "unified" / "catalog.sqlite"),
        "metadata": str(raw / "unified" / "metadata.csv"),
        "artifacts_dir": str(tmp_path / "artifacts"),
    })
    return cfg


def _code_dirs(tmp_path: Path) -> dict:
    dirs = {}
    for key in stage0.CODE_DIRS:
        d = tmp_path / "code" / key
        d.mkdir(parents=True)
        (d / "mod.py").write_text(f"# {key}\n", encoding="utf-8")
        dirs[key] = str(d)
    return dirs


def test_inputs_exclude_self_created_files(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(stage0, "CODE_DIRS", _code_dirs(tmp_path))
    before = stage0.inputs(cfg)
    stage_dir = Path(cfg["paths"]["artifacts_dir"]) / stage0.STAGE
    stage_dir.mkdir(parents=True)
    (stage_dir / "migration_check.json").write_text('{"equal": true}\n', encoding="utf-8")
    (stage_dir / "data_archive_sha256.txt").write_text("sha256:abc  1 files\n", encoding="utf-8")
    assert stage0.inputs(cfg) == before
    assert not any("migration" in k or "archive" in k for k in before)


def test_inputs_change_when_build_code_changes(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    dirs = _code_dirs(tmp_path)
    monkeypatch.setattr(stage0, "CODE_DIRS", dirs)
    before = stage0.inputs(cfg)
    (Path(dirs["build_code"]) / "mod.py").write_text("# changed build\n", encoding="utf-8")
    after = stage0.inputs(cfg)
    assert {k for k in after if after[k] != before[k]} == {"build_code"}


def test_inputs_track_catalog_and_raw_tree(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    monkeypatch.setattr(stage0, "CODE_DIRS", _code_dirs(tmp_path))
    before = stage0.inputs(cfg)
    raw = Path(cfg["paths"]["raw_dir"])
    (raw / "unified" / "catalog.sqlite").write_bytes(b"catalog-v2")
    after_catalog = stage0.inputs(cfg)
    assert after_catalog["catalog"] != before["catalog"]
    assert after_catalog["raw_data"] == before["raw_data"]       # unified/ is not raw data
    (raw / "source_a" / "img2.png").write_bytes(b"more")
    with_file = stage0.inputs(cfg)["raw_data"]
    assert with_file != before["raw_data"]
    assert with_file == "files=2;bytes=13"                      # "raw-bytes" (9) + "more" (4)
    # same count and bytes -> same fingerprint: a cheap size fingerprint, not a content hash
    (raw / "source_a" / "img2.png").write_bytes(b"MORE")
    assert stage0.inputs(cfg)["raw_data"] == with_file
    assert stage0.raw_fingerprint(tmp_path / "nowhere") == "files=0;bytes=0"


def test_run_recomputes_checks_every_time(tmp_path, monkeypatch):
    """A stale migration_check.json / archive file is never reused."""
    cfg = _config(tmp_path)
    stage_dir = Path(cfg["paths"]["artifacts_dir"]) / stage0.STAGE
    stage_dir.mkdir(parents=True)
    (stage_dir / "migration_check.json").write_text('{"equal": false, "stale": true}\n',
                                                    encoding="utf-8")
    (stage_dir / "data_archive_sha256.txt").write_text("sha256:stale  0 files\n", encoding="utf-8")
    calls = []

    def fake_migration(raw, unified, d, max_hamming, out_path):
        calls.append("migration")
        Path(out_path).write_text('{"equal": true, "differences": {}}\n', encoding="utf-8")
        return {"equal": True}

    monkeypatch.setattr(stage0, "migration_check", fake_migration)
    monkeypatch.setattr(stage0, "archive_sha256", lambda root, exclude=None: ("sha256:fresh", 1))
    result = stage0.run(cfg)
    assert calls == ["migration"]
    assert result["checks"]["migration_equivalent"] is True
    assert result["metrics"]["data_archive_sha256"] == "sha256:fresh"
