"""The all-models vote averages probabilities, and its validation check keeps groups whole."""

import numpy as np

from studio.inference.predict import vote
from scripts.vote_check import _score, compare, split_groups

LABELS = ("circle", "square", "star")


def _result(arm, *probs):
    return {"arm": arm, "all": dict(zip(LABELS, probs)), "latency_ms": 2.0}


def test_vote_averages_probabilities_with_equal_weight():
    out = vote([_result("A0", 0.9, 0.1, 0.0), _result("A1", 0.3, 0.6, 0.1)], LABELS)
    assert out["arm"] == "vote" and out["label"] == "circle"
    assert out["top"][0]["p"] == 0.6 and round(out["top"][1]["p"], 6) == 0.35
    assert out["arms"] == ["A0", "A1"] and out["latency_ms"] == 4.0


def test_a_confident_model_counts_for_more_than_an_unsure_one():
    out = vote([_result("A0", 0.98, 0.01, 0.01), _result("A1", 0.45, 0.5, 0.05)], LABELS)
    assert out["label"] == "circle"


def test_a_tie_is_broken_the_same_way_every_time():
    out = vote([_result("A0", 0.5, 0.5, 0.0)], LABELS)
    assert out["label"] == "circle"


def test_an_unsure_average_is_marked_not_sure():
    out = vote([_result("A0", 0.4, 0.3, 0.3), _result("A1", 0.3, 0.4, 0.3)], LABELS)
    assert out["not_sure"] is True


def test_no_results_means_no_vote():
    assert vote([], LABELS) is None


def test_validation_halves_keep_each_group_whole():
    groups = np.array(["a", "a", "b", "b", "c", "c", "d", "d"])
    labels = np.array([0, 0, 1, 1, 0, 0, 1, 1])
    half = split_groups(labels, groups)
    for group in np.unique(groups):
        assert len(set(half[groups == group])) == 1
    assert half.any() and (~half).any()


def test_a_class_missing_from_a_half_is_not_scored_as_zero():
    labels = np.array([0, 0, 1, 1])
    assert _score(labels, labels, 3) == 100.0


def _probs(n):
    labels = np.arange(n) % 3
    good = np.eye(3)[labels] * 0.9 + 0.1 / 3
    return labels, good


def test_compare_reports_every_arm_and_keeps_equal_weights_without_a_clear_win():
    labels, good = _probs(60)
    groups = np.array([f"g{i}" for i in range(60)])
    out = compare(np.stack([good, good]), labels, groups, ["A0", "A1"])
    assert set(out["held_apart_macro_f1"]) == {"A0", "A1", "equal", "per_class"}
    assert out["per_class_gain_over_equal"] == 0.0 and out["keep"] == "equal"
