"""Tests for dashboard/view_model.py (E31). tmp_path only; no Streamlit, no real artifacts."""

import json
from pathlib import Path

from dashboard import view_model as vm


def _status(stage: str, status: str = "passed", **overrides) -> dict:
    d = {
        "stage": stage,
        "owner": "Owner",
        "run_id": "2026-11-10T09:00:00-05:00/abc123",
        "status": status,
        "started_at": "2026-11-10T09:00:00-05:00",
        "finished_at": "2026-11-10T09:04:12-05:00",
        "inputs": {"configs/pipeline.yaml#split": "sha256:0"},
        "outputs": [],
        "metrics": {},
        "checks": {},
    }
    d.update(overrides)
    return d


def _write(artifacts: Path, stage: str, payload: dict) -> Path:
    path = artifacts / stage / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return path


def _row(rows: list[dict], stage: str) -> dict:
    return next(r for r in rows if r["stage"] == stage)


def test_missing_status_is_grey_not_run(tmp_path):
    assert vm.light(None) == "grey"
    rows = vm.overview_rows(vm.load_statuses(tmp_path))
    assert len(rows) == 7
    assert all(r["light"] == "grey" for r in rows)
    assert all(r["status"] == "not_run" for r in rows)


def test_failed_is_red(tmp_path):
    _write(tmp_path, "stage2", _status("stage2", status="failed"))
    _write(tmp_path, "stage3", _status("stage3", status="passed"))
    statuses = vm.load_statuses(tmp_path)
    assert vm.light(statuses["stage2"]) == "red"
    assert vm.light(statuses["stage3"]) == "green"
    rows = vm.overview_rows(statuses)
    assert _row(rows, "stage2")["light"] == "red"
    assert _row(rows, "stage2")["status"] == "failed"


def test_verdict_separate_from_light(tmp_path):
    _write(tmp_path, "stage5", _status("stage5", status="passed",
                                       metrics={"verdict": "fail"}))
    rows = vm.overview_rows(vm.load_statuses(tmp_path))
    row = _row(rows, "stage5")
    assert row["light"] == "green"
    assert row["status"] == "passed"
    assert row["verdict"] == "fail"
    assert _row(rows, "stage4")["verdict"] is None


def test_only_stage1_run_one_green_six_grey(tmp_path):
    _write(tmp_path, "stage1", _status("stage1"))
    rows = vm.overview_rows(vm.load_statuses(tmp_path))
    lights = [r["light"] for r in rows]
    assert lights.count("green") == 1
    assert lights.count("grey") == 6
    assert _row(rows, "stage1")["light"] == "green"


def test_eight_tabs_seven_stages(tmp_path):
    assert len(vm.TAB_NAMES) == 8
    assert len(vm.STAGES) == 7
    assert vm.TAB_NAMES[0] == "Overview"
    # Tabs 1..7 map one-to-one onto stage0..stage6 by their leading digit.
    assert [name[0] for name in vm.TAB_NAMES[1:]] == [s[-1] for s in vm.STAGES]
    assert len(vm.overview_rows(vm.load_statuses(tmp_path))) == 7


def test_corrupt_status_json_does_not_crash(tmp_path):
    bad = _write(tmp_path, "stage2", {})
    bad.write_text("{not json", encoding="utf-8")
    not_object = _write(tmp_path, "stage3", {})
    not_object.write_text("[1, 2]", encoding="utf-8")
    undecodable = tmp_path / "stage4" / "status.json"
    undecodable.parent.mkdir(parents=True, exist_ok=True)
    undecodable.write_bytes(b"\xff\xfe\x00")

    statuses = vm.load_statuses(tmp_path)
    assert statuses["stage2"] is None
    assert statuses["stage3"] is None
    assert statuses["stage4"] is None

    notes = vm.status_notes(tmp_path)
    assert set(notes) == {"stage2", "stage3", "stage4"}

    rows = vm.overview_rows(statuses)
    assert [r["light"] for r in rows] == ["grey"] * 7
    assert _row(rows, "stage2")["status"] == "not_run"


def test_test_reads_for_run_counts_only_that_run(tmp_path):
    log = tmp_path / "test_access.log"
    log.write_text(
        "2026-11-10T09:00:00-05:00,run-A,src.stage5_eval.run,test,572\n"
        "2026-11-10T09:01:00-05:00,run-B,src.stage5_eval.run,test,572\n"
        "2026-11-10T09:02:00-05:00,run-A,src.stage5_eval.run,test,572\n"
        "not a valid line\n",
        encoding="utf-8",
    )
    assert vm.test_reads_for_run(log, "run-A") == 2
    assert vm.test_reads_for_run(log, "run-B") == 1
    assert vm.test_reads_for_run(log, "run-C") == 0
    assert vm.test_reads_for_run(tmp_path / "missing.log", "run-A") == 0


def test_stage4_ignores_stage5_reads(tmp_path):
    """One pipeline invocation shares a run_id: Stage 5's legitimate reads must
    not light the Stage 4 leak check, and the Stage 5 tab shows only its own."""
    log = tmp_path / "test_access.log"
    log.write_text(
        "2026-11-10T09:00:00-05:00,run-A,src.stage5_eval.run,test,572\n"
        "2026-11-10T09:01:00-05:00,run-A,src.stage5_eval.evaluate,test,572\n"
        "2026-11-10T09:02:00-05:00,run-A,src.stage4_train.run,test,572\n"
        "2026-11-10T09:03:00-05:00,run-B,src.stage4_train.run,test,572\n",
        encoding="utf-8",
    )
    assert vm.leaked_test_reads(log, "run-A") == 1
    assert vm.stage5_test_reads(log, "run-A") == 2
    assert vm.test_reads_for_run(log, "run-A") == 3
    assert vm.leaked_test_reads(log, "run-B") == 1
    assert vm.stage5_test_reads(log, "run-B") == 0
    # A run with Stage 5 reads only is clean for the Stage 4 check.
    log.write_text("2026-11-10T09:00:00-05:00,run-C,src.stage5_eval.run,test,572\n",
                   encoding="utf-8")
    assert vm.leaked_test_reads(log, "run-C") == 0
    assert vm.stage5_test_reads(log, "run-C") == 1
    assert vm.leaked_test_reads(tmp_path / "missing.log", "run-C") == 0


def test_stage_files_missing_are_none(tmp_path):
    files = vm.stage_files(tmp_path, "stage1", repo_root=tmp_path)
    assert files
    assert all(path is None for path in files.values())

    pdf = vm.stage_files(tmp_path, "stage6", repo_root=tmp_path)
    assert pdf == {vm.REPORT_PDF: None}

    csv_path = tmp_path / "stage1" / "split_stats.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("class,n\nellipse,150\n", encoding="utf-8")
    assert vm.stage_files(tmp_path, "stage1", repo_root=tmp_path)["split_stats.csv"] == csv_path
