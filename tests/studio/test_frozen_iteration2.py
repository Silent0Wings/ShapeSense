"""Iteration 2's verdict page reads its frozen record, not the live iteration 3 status."""

from studio.data import pages


def test_iteration2_page_carries_the_frozen_test_and_fresh_intervals():
    metrics = pages.build("iteration2")["metrics"]
    assert metrics["primary"]["label"] == "A2 vs A0"
    assert round(metrics["delta"], 2) == 0.06 and [round(x, 2) for x in metrics["ci"]] == [-0.69, 0.83]
    fresh = metrics["fresh_holdout"]
    assert round(fresh["delta"], 2) == 0.08 and [round(x, 2) for x in fresh["ci"]] == [-0.41, 0.57]


def test_iteration2_page_is_not_the_live_stage5_status():
    live = pages.build("stage5")["metrics"]
    frozen = pages.build("iteration2")["metrics"]
    assert frozen["delta"] != live["delta"]
