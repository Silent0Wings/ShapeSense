"""The iteration 3 search: arm P, generator search per arm and grouped CV."""

import random

import pytest

from src.common.config import load_config
from src.stage4_train import search


def test_generator_search_targets_the_arm_it_is_given():
    drawn = search.sample_synth(random.Random(0), "A2")
    assert "arms.A2.synthetic_fraction" in drawn and "arms.B.synthetic_fraction" not in drawn


def test_pretrain_search_keeps_fine_tuning_on_real_images():
    drawn = search.sample_pretrain(random.Random(0))
    assert 0.1 <= drawn["arms.P.pretrain_fraction"] <= 0.6
    assert not any(k.endswith("synthetic_fraction") for k in drawn)


def test_cv_covers_every_fold_of_every_setting_at_the_short_budget():
    settings = [{"settings": {"overrides": {"a": i}, "hparams": {"lr": 0.1, "dropout": 0.2}}} for i in range(2)]
    specs = search.cv_specs(load_config(), "c", "A1", settings)
    assert len(specs) == 2 * search.N_FOLDS
    assert [s["fold"][1] for s in specs] == [0, 1, 2, 0, 1, 2]
    assert all(s["overrides"]["train.max_epochs"] == search.CV_EPOCHS for s in specs)


def test_search_refuses_to_start_before_the_budget_rule_has_run(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "BUDGET_RESULT", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError, match="budget rule"):
        search.adopted_budget()


def test_execute_reuses_only_a_trial_with_identical_settings(monkeypatch):
    config = load_config()
    same = search._spec(config, "c", "grid", "same", "A1", 0, {"a": 1}, {"lr": 0.1, "dropout": 0.2})
    other = search._spec(config, "c", "grid", "other", "A1", 0, {"a": 2}, {"lr": 0.1, "dropout": 0.2})
    finished = [{"name": "t00", "settings": search._settings(same), "val_macro_f1": 90.0}]
    trained = []

    def fake_run_specs(_config, specs, job_runner):
        trained.extend(s["run_name"] for s in specs)
        return {s["run_name"]: {"name": s["run_name"], "settings": search._settings(s), "val_macro_f1": 50.0} for s in specs}

    monkeypatch.setattr(search, "run_specs", fake_run_specs)
    out = search.execute(config, [same, other], finished=finished)
    assert trained == [other["run_name"]]
    assert [r["val_macro_f1"] for r in out] == [90.0, 50.0]
    assert out[0]["name"] == same["run_name"] and out[1]["name"] == other["run_name"]
