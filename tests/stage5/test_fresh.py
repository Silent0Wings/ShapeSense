"""CRISP-DM iteration 2: the fresh holdout and config-driven comparisons in Stage 5."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from src.common.config import load_config
from src.common.splits import TestSplitAccessError, load_split
from src.stage5_eval import fresh
from src.stage5_eval import run as s5

K = 3
NAMES = ["a", "b", "c"]


def test_primary_and_secondary_come_from_the_config():
    cfg = copy.deepcopy(load_config())
    assert s5.primary_roles(cfg) == ("A0", "A2")
    assert s5.secondary_pairs(cfg) == (("A0", "A1"), ("A0", "B"), ("B", "A2"))
    del cfg["evaluation"]["primary"], cfg["evaluation"]["secondary"]
    assert s5.primary_roles(cfg) == ("A1", "B")
    assert s5.secondary_pairs(cfg) == s5.SECONDARY_PAIRS


def test_hold_out_runs_cover_every_arm_and_the_configured_seeds():
    cfg = load_config()
    runs = s5.loso_runs(cfg)
    assert len(runs) == 12
    assert {arm for arm, _, _ in runs} == {"A0", "A1", "B", "A2"}
    assert {seed for _, seed, _ in runs} == {0, 1, 2}
    assert ("A2", 1, "A2_loso_handdrawn_1") in runs


def test_fresh_holdout_is_sealed_like_the_test_split(tmp_path):
    (tmp_path / "fresh_holdout.csv").write_text("image_id\nx\n", encoding="utf-8")
    log = tmp_path / "log"
    with pytest.raises(TestSplitAccessError):
        load_split("fresh_holdout", splits_dir=tmp_path, log_path=log)
    assert not log.exists()


def test_stage5_reads_of_the_fresh_holdout_are_logged(tmp_path, monkeypatch):
    (tmp_path / "fresh_holdout.csv").write_text("image_id\nx\n", encoding="utf-8")
    log = tmp_path / "log"
    monkeypatch.setattr("src.common.splits._allowed_test_reader", lambda *a: True)
    rows = load_split("fresh_holdout", splits_dir=tmp_path, log_path=log)
    assert rows == [{"image_id": "x"}]
    assert log.read_text(encoding="utf-8").count("fresh_holdout") == 1


def _record(preds, y, ids):
    probs = np.eye(K)[preds].astype(np.float32)
    return {"probs": probs, "preds": preds, "labels": y, "image_ids": ids,
            "source_ids": np.array(["s"] * len(y))}


def test_analyse_applies_the_locked_rule_to_the_fresh_holdout(tmp_path):
    y = np.array([0, 1, 2] * 20)
    ids = np.array([str(i) for i in range(y.size)])
    good = y.copy()
    worse = y.copy()
    worse[:12] = (worse[:12] + 1) % K
    models = {"A0_0": _record(worse, y, ids), "A2_0": _record(good, y, ids)}
    specs = [SimpleNamespace(name="A0_0", arm="A0"), SimpleNamespace(name="A2_0", arm="A2")]
    result, outputs = fresh.analyse(models, specs, ["A0", "A2"], lambda s: s.arm, NAMES, "A0", "A2", 1.0, 2.0,
                                    200, np.random.default_rng(0), 0.95, {"noise_band_accuracy": 0.9}, tmp_path)
    assert result["label"] == "A2 vs A0" and result["verdict"] == "pass"
    assert result["delta"] > 1.0
    assert result["arms"]["A2"]["macro_f1"] == pytest.approx(100.0)
    assert result["n"] == y.size
    assert {p.name for p in outputs} >= {"fresh_metrics.csv", "fresh_per_class.csv"}
