"""E13: fail-closed status writer (stages/stage_0.md R8, Mission M2)."""

import json

import pytest

from src.common import status


@pytest.fixture(autouse=True)
def _run_id(monkeypatch):
    monkeypatch.setenv(status.RUN_ID_ENV, "test-run/abc123")


def test_passed_status_validates(tmp_path):
    status.run_stage("stage9", lambda: {"metrics": {"n": 1}, "outputs": ["x"]},
                     inputs={"a": "sha256:1"}, artifacts_dir=tmp_path, owner="me")
    d = status.read_status("stage9", artifacts_dir=tmp_path)
    status.validate_status(d)
    assert d["status"] == "passed"
    assert d["run_id"] == "test-run/abc123"
    assert d["metrics"] == {"n": 1}
    assert d["inputs"] == {"a": "sha256:1"}


def test_raising_stage_writes_failed_and_reraises(tmp_path):
    def boom():
        raise RuntimeError("leak detected")

    with pytest.raises(RuntimeError, match="leak detected"):
        status.run_stage("stage9", boom, inputs={}, artifacts_dir=tmp_path)
    d = status.read_status("stage9", artifacts_dir=tmp_path)
    assert d["status"] == "failed"
    assert "leak detected" in d["error"]


def test_stage_not_ready_writes_not_run(tmp_path):
    def stub():
        raise status.StageNotReady("Stage 9 not implemented yet")

    result = status.run_stage("stage9", stub, inputs={}, artifacts_dir=tmp_path)
    assert result["status"] == "not_run"
    assert status.read_status("stage9", artifacts_dir=tmp_path)["status"] == "not_run"


def test_library_notimplemented_is_failed(tmp_path):
    def stage():
        raise NotImplementedError("raised deep inside a library")

    with pytest.raises(NotImplementedError):
        status.run_stage("stage9", stage, inputs={}, artifacts_dir=tmp_path)
    assert status.read_status("stage9", artifacts_dir=tmp_path)["status"] == "failed"


def test_stage_can_report_its_own_failure(tmp_path):
    status.run_stage("stage9", lambda: {"status": "failed", "checks": {"leak": False}},
                     inputs={}, artifacts_dir=tmp_path)
    assert status.read_status("stage9", artifacts_dir=tmp_path)["status"] == "failed"


def test_stale_passed_overwritten_on_failure(tmp_path):
    status.run_stage("stage9", lambda: {}, inputs={}, artifacts_dir=tmp_path)
    with pytest.raises(ValueError):
        status.run_stage("stage9", lambda: (_ for _ in ()).throw(ValueError("x")),
                         inputs={}, artifacts_dir=tmp_path)
    assert status.read_status("stage9", artifacts_dir=tmp_path)["status"] == "failed"


def test_cache_hit_only_when_all_inputs_match_and_passed(tmp_path):
    inputs = {"a": "sha256:1", "b": "sha256:2"}
    assert not status.is_cached("stage9", inputs, artifacts_dir=tmp_path)
    status.run_stage("stage9", lambda: {}, inputs=inputs, artifacts_dir=tmp_path)
    assert status.is_cached("stage9", inputs, artifacts_dir=tmp_path)
    assert not status.is_cached("stage9", {**inputs, "b": "sha256:3"}, artifacts_dir=tmp_path)
    assert not status.is_cached("stage9", {"a": "sha256:1"}, artifacts_dir=tmp_path)


def test_failed_status_never_cached(tmp_path):
    inputs = {"a": "sha256:1"}
    status.run_stage("stage9", lambda: {"status": "failed"}, inputs=inputs,
                     artifacts_dir=tmp_path)
    assert not status.is_cached("stage9", inputs, artifacts_dir=tmp_path)


def test_schema_rejects_unknown_status(tmp_path):
    with pytest.raises(status.StatusSchemaError):
        status.validate_status({"stage": "s", "status": "ok", "run_id": "r",
                                "started_at": "t", "finished_at": "t", "inputs": {},
                                "outputs": [], "metrics": {}, "checks": {}, "owner": ""})


def test_status_file_is_valid_json_on_disk(tmp_path):
    status.run_stage("stage9", lambda: {}, inputs={}, artifacts_dir=tmp_path)
    json.loads((tmp_path / "stage9" / "status.json").read_text(encoding="utf-8"))


def test_cache_miss_when_output_changed_or_deleted(tmp_path):
    out = tmp_path / "manifest.csv"
    out.write_text("a\n", encoding="utf-8")
    inputs = {"a": "sha256:1"}
    status.run_stage("stage9", lambda: {"outputs": [str(out)]}, inputs=inputs,
                     artifacts_dir=tmp_path)
    assert status.is_cached("stage9", inputs, artifacts_dir=tmp_path)
    out.write_text("tampered\n", encoding="utf-8")
    assert not status.is_cached("stage9", inputs, artifacts_dir=tmp_path)
    out.unlink()
    assert not status.is_cached("stage9", inputs, artifacts_dir=tmp_path)


def test_reserved_result_keys_cannot_break_the_write(tmp_path):
    status.run_stage("stage9", lambda: {"inputs": {"x": 1}, "run_id": "fake", "note": "kept"},
                     inputs={"a": "sha256:1"}, artifacts_dir=tmp_path)
    d = status.read_status("stage9", artifacts_dir=tmp_path)
    assert d["inputs"] == {"a": "sha256:1"} and d["run_id"] == "test-run/abc123"
    assert d["note"] == "kept"
