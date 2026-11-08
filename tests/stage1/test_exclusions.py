"""CRISP-DM iteration 1: (source, class) exclusions before the split."""

import pytest

from src.stage1_freeze.exclusions import apply_source_label_exclusions

NAMES = ["circle", "ellipse", "triangle", "square", "rectangle", "pentagon",
         "hexagon", "octagon", "star", "diamond"]


def _rows():
    return [{"image_id": "q1", "source_id": "quickdraw", "label_id": 9},
            {"image_id": "q2", "source_id": "quickdraw", "label_id": 9},
            {"image_id": "q3", "source_id": "quickdraw", "label_id": 0},
            {"image_id": "r1", "source_id": "kaggle_reevald", "label_id": 9}]


def test_drops_only_the_listed_source_class_pair():
    kept, removed = apply_source_label_exclusions(_rows(), [["quickdraw", "diamond"]], NAMES)
    assert [r["image_id"] for r in kept] == ["q3", "r1"]   # other QD classes and
    assert removed == {"quickdraw/diamond": 2}               # other diamond sources kept


def test_empty_rule_list_keeps_everything():
    kept, removed = apply_source_label_exclusions(_rows(), [], NAMES)
    assert len(kept) == 4 and removed == {}


def test_pair_matching_nothing_fails():
    with pytest.raises(ValueError, match="github_handdrawn/diamond"):
        apply_source_label_exclusions(_rows(), [["github_handdrawn", "diamond"]], NAMES)
