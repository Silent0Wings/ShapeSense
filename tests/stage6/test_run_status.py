"""Stage 6 fails when a traceability or attribution check fails, and its cache sees every config key."""

from pathlib import Path

import pytest

from src.stage6_report import export as export_module
from src.stage6_report import run as stage6


def _stub_stage(monkeypatch, tmp_path, *, traceable=True, attribution=True):
    bundle = {"selection": {}, "onnx": tmp_path / "m", "standardize": tmp_path / "s", "labels": tmp_path / "l",
              "model_card": tmp_path / "c"}
    monkeypatch.setattr(export_module, "build_bundle", lambda *_: bundle)
    monkeypatch.setattr(stage6, "stage5_status", lambda _: {})
    monkeypatch.setattr(stage6, "write_snippets", lambda *_: {"missing": [], "param_ranges": tmp_path / "p", "pipeline_facts": tmp_path / "f"})
    monkeypatch.setattr(stage6, "draw_hexagon", lambda path: Path(path))
    monkeypatch.setattr(stage6, "smoke_test", lambda *_: {"ok": True, "predicted": "hexagon", "matches_expected": True, "output": ""})
    monkeypatch.setattr(stage6, "build_report", lambda: {"ok": True, "pdf": "r.pdf", "exe": "pwsh", "output": ""})
    monkeypatch.setattr(stage6, "check_report", lambda *_: {"ok": traceable, "placeholders": [], "findings": [], "n_failing": 0 if traceable else 3, "missing_inputs": []})
    monkeypatch.setattr(stage6, "attribution_present", lambda *_: attribution)
    return {"paths": {"artifacts_dir": str(tmp_path)}}


def test_all_checks_passing_sets_no_failure(monkeypatch, tmp_path):
    assert "status" not in stage6.run(_stub_stage(monkeypatch, tmp_path))


@pytest.mark.parametrize("kwargs, words", [({"traceable": False}, "traceability"), ({"attribution": False}, "attribution")])
def test_a_failing_report_check_fails_the_stage(monkeypatch, tmp_path, kwargs, words):
    result = stage6.run(_stub_stage(monkeypatch, tmp_path, **kwargs))
    assert result["status"] == "failed" and words in result["error"]


def test_any_config_change_invalidates_the_cache(tmp_path):
    config = {"paths": {"artifacts_dir": str(tmp_path)}, "runs": [], "image_size": 64}
    before = stage6.inputs(config)
    config["image_size"] = 32
    assert stage6.inputs(config) != before


def test_cache_tracks_preprocessing_and_generator_status(tmp_path):
    config = {"paths": {"artifacts_dir": str(tmp_path)}, "runs": []}
    keys = stage6.inputs(config)
    assert "standardize" in keys and "stage3_status" in keys
