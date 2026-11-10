"""The report's iteration 3 macros come from the artifacts, and show a dash when one is absent."""

import json
from pathlib import Path

from src.stage6_report.iteration3 import MACRO_NAMES, collect


def _artifacts(tmp: Path) -> Path:
    robust = {
        "label": "A2 vs A0", "delta": 9.2, "ci": [8.9, 9.5], "verdict": "pass", "strict_pass": True,
        "ci_clustered_by_source": [3.9, 9.4], "n": 4500, "levels": ["a", "b"],
        "clean": {"A2 vs A0": {"delta": 0.64, "ci": [0.19, 1.07]}},
        "secondary": {"A1 vs A0": {"delta": 7.0, "p_holm": 0.004}},
        "ensembles": {"A2": {"clean_macro_f1": 98.5, "perturbed_macro_f1": 84.8}},
    }
    metrics = {"robust": robust, "reused_test": {"delta": 0.5, "ci": [-0.2, 1.2], "verdict": "fail"},
               "fresh_holdout": {"delta": 0.54, "ci": [0.1, 1.0], "verdict": "fail"},
               "loso": [{"arm": "A2", "accuracy": 0.7}, {"arm": "A2", "accuracy": 0.8}]}
    (tmp / "stage5").mkdir(parents=True)
    (tmp / "stage5" / "status.json").write_text(json.dumps({"metrics": metrics, "checks": {"test_reads": 92, "test_reads_expected": 92}}), encoding="utf-8")
    winners = {"winners": {"A2": {"mean_val_macro_f1": 95.8}}, "trials_per_arm": {"A2": 34}}
    (tmp / "stage4" / "tuning_iter3").mkdir(parents=True)
    (tmp / "stage4" / "tuning_iter3" / "winners.json").write_text(json.dumps(winners), encoding="utf-8")
    return tmp


def test_macros_come_from_the_artifacts(tmp_path):
    macros = collect(_artifacts(tmp_path))
    assert set(macros) == set(MACRO_NAMES)
    assert macros["IthreePrimary"] == "A2 vs A0" and macros["IthreeDelta"] == "9.20" and macros["IthreeVerdict"] == "pass"
    assert macros["IthreeStrict"] == "yes" and macros["IthreeN"] == "4,500" and macros["IthreeLevels"] == "2"
    assert macros["IthreeDamagedAtwo"] == "84.8" and macros["IthreeCleanAtwo"] == "98.5" and macros["IthreeValAtwo"] == "95.8"
    assert macros["IthreeTrialsAtwo"] == "34" and macros["IthreeLosoAtwo"] == "75.0"
    assert macros["IthreeSecAoneAzeroDelta"] == "7.00" and macros["IthreeSecAoneAzeroP"] == "0.004"
    assert macros["IthreeTestVerdict"] == "fail" and macros["IthreeFreshDelta"] == "0.54" and macros["IthreeCleanCIHi"] == "1.07"


def test_missing_inputs_show_a_dash(tmp_path):
    macros = collect(tmp_path)
    assert set(macros) == set(MACRO_NAMES)
    assert macros["IthreeDelta"] == "--" and macros["IthreeVerdict"] == "--" and macros["IthreeTrialsP"] == "--"
