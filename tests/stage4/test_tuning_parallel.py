"""Decision 7 grid points are independent, so they train through the
shared process-pool runner (one batch), not one after another."""

import copy

from src.common.config import load_config
from src.stage4_train.tuning import grid_points, run_tuning


def test_grid_goes_to_batch_runner_once(tmp_path):
    cfg = copy.deepcopy(load_config())
    calls = []

    def batch_runner(specs):
        calls.append(specs)
        return {s["run_name"]: {"val_macro_f1": 50.0 + 10 * s["hparams"]["lr"] * 1000
                                if s["hparams"]["dropout"] == 0.2 else 1.0,
                                "best_epoch": 3} for s in specs}

    result = run_tuning(cfg, None, None, None, None, 50, tmp_path,
                        batch_runner=batch_runner, config_path="configs/pipeline.yaml")
    assert len(calls) == 1
    assert len(calls[0]) == len(grid_points(cfg["train"]["tuning"]))
    assert {s["arm"] for s in calls[0]} == {cfg["train"]["tuning"]["arm"]}
    assert {s["seed"] for s in calls[0]} == {cfg["seed_set"][0]}
    assert result["winner"] == {"lr": 0.003, "dropout": 0.2}
