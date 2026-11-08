"""E16: runner dependency closure, hash cache, fail-stop, shared run_id."""

import types

import pytest

import run_pipeline as rp
from src.common import status


def _fake_stage(name, inputs, result=None, raises=None, calls=None):
    mod = types.ModuleType(name)
    mod.STAGE = name

    def run(config):
        if calls is not None:
            calls.append(name)
        if raises:
            raise raises
        return result or {}

    mod.inputs = lambda config: dict(inputs)
    mod.run = run
    return mod


@pytest.fixture()
def stages(monkeypatch):
    monkeypatch.setenv(status.RUN_ID_ENV, "run-1")
    calls = []
    mods = {"m0": _fake_stage("stage0", {"a": "1"}, calls=calls),
            "m1": _fake_stage("stage1", {"b": "1"}, calls=calls),
            "m2": _fake_stage("stage2", {"c": "1"}, calls=calls)}
    monkeypatch.setattr(rp, "STAGES", {0: "m0", 1: "m1", 2: "m2"})
    return mods, calls


def test_dependency_closure():
    deps = {0: [], 1: [0], 2: [0, 1], 3: [0], 4: [0, 1, 2, 3]}
    assert rp.dependency_closure([3], deps) == [0, 3]
    assert rp.dependency_closure([4], deps) == [0, 1, 2, 3, 4]
    assert rp.dependency_closure([2, 3], deps) == [0, 1, 2, 3]


def test_cached_stage_skipped(stages, tmp_path):
    mods, calls = stages
    rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                  artifacts_dir=tmp_path, log=lambda s: None)
    assert calls == ["stage0", "stage1", "stage2"]
    out = rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                        artifacts_dir=tmp_path, log=lambda s: None)
    assert out == {0: "cached", 1: "cached", 2: "cached"}
    assert calls == ["stage0", "stage1", "stage2"]


def test_changed_input_reruns_only_that_stage(stages, tmp_path):
    mods, calls = stages
    rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                  artifacts_dir=tmp_path, log=lambda s: None)
    mods["m1"].inputs = lambda config: {"b": "2"}
    out = rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                        artifacts_dir=tmp_path, log=lambda s: None)
    assert out[1] == "passed" and out[0] == "cached"


def test_failed_prior_status_not_cached(stages, tmp_path):
    mods, calls = stages
    mods["m1"].run = lambda config: {"status": "failed"}
    rp.run_stages({}, [1], force=False, load=mods.__getitem__,
                  artifacts_dir=tmp_path, log=lambda s: None)
    mods["m1"].run = lambda config: calls.append("again") or {}
    out = rp.run_stages({}, [1], force=False, load=mods.__getitem__,
                        artifacts_dir=tmp_path, log=lambda s: None)
    assert out == {1: "passed"} and calls == ["again"]


def test_force_ignores_cache(stages, tmp_path):
    mods, calls = stages
    for _ in range(2):
        rp.run_stages({}, [0], force=True, load=mods.__getitem__,
                      artifacts_dir=tmp_path, log=lambda s: None)
    assert calls == ["stage0", "stage0"]


def test_failed_stage_stops_pipeline(stages, tmp_path):
    mods, calls = stages
    mods["m1"].run = lambda config: {"status": "failed"}
    out = rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                        artifacts_dir=tmp_path, log=lambda s: None)
    assert out == {0: "passed", 1: "failed"}
    assert "stage2" not in calls


def test_stub_stage_is_not_run(stages, tmp_path):
    mods, calls = stages
    mods["m2"] = _fake_stage("stage2", {"c": "1"}, raises=status.StageNotReady("stub"))
    out = rp.run_stages({}, [2], force=False, load=mods.__getitem__,
                        artifacts_dir=tmp_path, log=lambda s: None)
    assert out == {2: "not_run"}
    assert rp.exit_code(out) == 1


def test_exit_code_zero_only_when_every_stage_ran():
    assert rp.exit_code({0: "passed", 1: "cached"}) == 0
    assert rp.exit_code({0: "passed", 1: "failed"}) == 1


def test_run_id_shared_by_all_stages(stages, tmp_path):
    mods, _ = stages
    rp.run_stages({}, [0, 1, 2], force=False, load=mods.__getitem__,
                  artifacts_dir=tmp_path, log=lambda s: None)
    ids = {status.read_status(f"stage{i}", tmp_path)["run_id"] for i in range(3)}
    assert ids == {"run-1"}
