"""CRISP-DM iteration 2 part of the report: generated numbers and the findings table."""

import json

from src.common.config import load_config
from src.stage6_report.iteration2 import MACRO_NAMES, change_tables, collect, failure_tables, log_table


def _artifacts(tmp_path):
    art = tmp_path / "artifacts"
    (art / "stage5").mkdir(parents=True)
    (art / "stage4" / "tuning_iter2").mkdir(parents=True)
    metrics = {"primary": {"label": "A2 vs A0"}, "delta": 1.5, "ci": [0.5, 2.5], "verdict": "pass",
               "ensembles": {"A0": {"macro_f1": 90.0}, "A2": {"macro_f1": 91.5}},
               "fresh_holdout": {"n": 4500, "delta": 2.0, "ci": [1.0, 3.0], "verdict": "pass",
                                 "arms": {"A2": {"macro_f1": 96.0}}},
               "loso": [{"arm": "A2", "accuracy": 0.7}, {"arm": "A2", "accuracy": 0.8}]}
    (art / "stage5" / "status.json").write_text(json.dumps({"metrics": metrics, "checks": {"test_reads": 37}}),
                                                encoding="utf-8")
    winners = {"winners": {"A2": {"mean_val_macro_f1": 95.17}}, "trials_per_arm": {"A0": 6, "A2": 18}}
    (art / "stage4" / "tuning_iter2" / "winners.json").write_text(json.dumps(winners), encoding="utf-8")
    return art


def test_macros_come_from_the_artifacts(tmp_path):
    macros = collect(load_config(), _artifacts(tmp_path))
    assert set(macros) == set(MACRO_NAMES)
    assert macros["ItwoPrimary"] == "A2 vs A0" and macros["ItwoDelta"] == "1.50"
    assert macros["ItwoReads"] == "37" and macros["ItwoFreshN"] == "4,500"
    assert macros["ItwoFreshAtwo"] == "96.0" and macros["ItwoValAtwo"] == "95.2"
    assert macros["ItwoLosoAtwo"] == "75.0" and macros["ItwoTrialsA0".replace("A0", "Azero")] == "6"


def test_missing_inputs_show_a_dash(tmp_path):
    macros = collect(load_config(), tmp_path)
    assert macros["ItwoDelta"] == "--" and macros["ItwoFreshVerdict"] == "--"


def test_findings_table_lists_every_step_of_the_iteration():
    table = log_table()
    for step in ("Data Understanding", "Data Preparation", "Modeling", "Evaluation"):
        assert step in table
    assert "\\begin{tabular}" in table


def test_failure_tables_list_each_group_and_escape_text():
    tables = failure_tables()
    for group in ("1. Dropping the diamonds", "3. Finding out why", "Before this timeline"):
        assert group in tables
    assert "Still open" in tables and "91.7\\%" in tables


def test_change_tables_group_changes_and_review_by_step():
    tables = change_tables()
    assert "Modeling: changes" in tables and "Evaluation: outside review" in tables
    assert "Does not stand" in tables
