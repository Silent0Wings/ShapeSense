"""The Evaluation and hash views agree with what Stages 0-6 recorded."""

import json
from pathlib import Path

import pytest

from studio.context import classes
from studio.data import cache_check, confusion, errors, whatif
from studio.data.tables import read_csv, read_json
from studio.settings import ARMS, ERRORS_ARM

ROOT = Path(__file__).resolve().parents[2]
needs_stage5 = pytest.mark.skipif(not (ROOT / "artifacts" / "stage5" / "status.json").is_file(),
                                  reason="needs a finished Stage 5")


@needs_stage5
@pytest.mark.parametrize("arm", ARMS)
def test_confusion_matches_the_metrics_table(arm):
    matrix = confusion.counts(arm)
    total = sum(map(sum, matrix))
    assert total == 2776
    accuracy = 100.0 * sum(matrix[i][i] for i in range(len(matrix))) / total
    row = next(r for r in read_csv("metrics") if r["kind"] == "ensemble" and r["arm"] == arm)
    assert accuracy == pytest.approx(float(row["accuracy_pct"]), abs=0.05)


@needs_stage5
def test_stored_errors_equal_the_candidate_confusion_cells():
    matrix = confusion.counts(ERRORS_ARM)
    for true, pred in errors.allowed_cells():
        assert errors.page(true, pred, 0)["total"] == matrix[true][pred]


def test_only_configured_pairs_may_show_images():
    names = classes()
    cells = {(names[t], names[p]) for t, p in errors.allowed_cells()}
    assert cells == {("square", "diamond"), ("diamond", "square"), ("square", "rectangle"),
                     ("rectangle", "square"), ("circle", "ellipse"), ("ellipse", "circle")}


@needs_stage5
def test_whatif_at_locked_values_reproduces_the_verdict():
    locked = json.loads((ROOT / "artifacts" / "stage5" / "status.json").read_text(encoding="utf-8"))["metrics"]
    out = whatif.evaluate(1.0, 2.0, True)
    assert out["verdict"] == locked["verdict"]
    assert out["reasons"] == locked["reasons"]
    assert out["harmful_classes"] == locked["harmful_classes"]


@needs_stage5
def test_whatif_can_flip_only_the_copy():
    before = read_json("status5")
    assert whatif.evaluate(-5.0, 2.0, False)["verdict"] == "pass"
    assert read_json("status5") == before


@needs_stage5
def test_safe_hashes_all_match_the_recorded_inputs():
    rows = cache_check.rows()
    assert rows and not [r for r in rows if r["state"] == "changed"]
    assert any(r["state"] == "match" for r in rows)
