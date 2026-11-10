"""The main finding lists the other arms, and P carries no invented interval."""

from studio.data import lights


def _status():
    return {"metrics": {
        "verdict": "pass", "delta": 9.2, "ci": [8.9, 9.5], "reasons": [], "primary": {"label": "A2 vs A0"},
        "robust": {
            "secondary": {"A1 vs A0": {"delta": 7.0, "ci": [6.6, 7.3]}, "B vs A0": {"delta": 7.5, "ci": [7.2, 7.9]},
                          "A2 vs A1": {"delta": 2.2, "ci": [2.0, 2.4]}},
            "ensembles": {"A0": {"perturbed_macro_f1": 75.0}, "P": {"perturbed_macro_f1": 83.5}},
        },
    }}


def test_other_arms_are_all_against_the_same_reference_and_ordered(monkeypatch):
    monkeypatch.setattr(lights, "read_json", lambda name: _status())
    rows = lights.verdict()["others"]
    assert [r["label"] for r in rows] == ["P vs A0", "B vs A0", "A1 vs A0"]


def test_p_has_a_score_difference_but_no_interval(monkeypatch):
    monkeypatch.setattr(lights, "read_json", lambda name: _status())
    p = lights.verdict()["others"][0]
    assert p["delta"] == 8.5 and p["ci"] is None


def test_older_results_without_robust_fields_list_no_other_arms(monkeypatch):
    status = _status()
    del status["metrics"]["robust"]
    monkeypatch.setattr(lights, "read_json", lambda name: status)
    assert lights.verdict()["others"] == []


def test_each_iteration_reports_its_own_result_and_a_missing_record_is_skipped(monkeypatch):
    records = {"iter1_status": _status(), "status5": _status()}
    monkeypatch.setattr(lights, "read_json", lambda name: records.get(name))
    out = lights.iteration_results()
    assert sorted(out) == [1, 3] and out[1] == {"verdict": "pass", "delta": 9.2, "ci": [8.9, 9.5], "label": "A2 vs A0"}
