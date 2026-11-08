"""E22: split stats, Decision 10 noise bands and the FD frame (R8, R12)."""

import pytest

from src.stage1_freeze.check_fds import check_rows
from src.stage1_freeze.stats import fd_rows, noise_band_points, noise_bands, split_stats

NAMES = ["circle", "ellipse", "triangle"]
ACCURACY = 0.9        # evaluation.noise_band_accuracy
FLOOR = 2.0           # success_criterion.max_class_f1_drop_points


def _rows_with_test_counts(counts):
    rows = []
    for lab, n in enumerate(counts):
        rows += [{"label_id": lab, "source_id": "s", "split": "test"} for _ in range(n)]
    return rows


def test_noise_band_matches_decision_10_table():
    assert noise_band_points(150, ACCURACY) == pytest.approx(2.449, abs=5e-4)
    assert noise_band_points(572, ACCURACY) == pytest.approx(1.254, abs=5e-4)
    assert noise_band_points(375, ACCURACY) == pytest.approx(1.549, abs=5e-4)
    bands = noise_bands(_rows_with_test_counts([375, 150, 572]), NAMES, ACCURACY, FLOOR)
    assert [b["n_test"] for b in bands] == [375, 150, 572]
    assert bands[1]["label_name"] == "ellipse"
    assert bands[1]["noise_band_points"] == pytest.approx(2.449, abs=5e-4)


def test_threshold_is_max_of_floor_and_band():
    bands = noise_bands(_rows_with_test_counts([375, 150, 572]), NAMES, ACCURACY, FLOOR)
    by_name = {b["label_name"]: b for b in bands}
    assert by_name["ellipse"]["threshold_points"] == pytest.approx(2.449, abs=5e-4)  # band wins
    assert by_name["circle"]["threshold_points"] == FLOOR                            # floor wins
    assert by_name["triangle"]["threshold_points"] == FLOOR


def test_noise_band_rejects_missing_class():
    with pytest.raises(ValueError, match="no rows in the test split"):
        noise_bands(_rows_with_test_counts([10, 0, 10]), NAMES, ACCURACY, FLOOR)


def test_counts_sum_to_rows():
    rows = []
    for i in range(120):
        rows.append({"label_id": i % 3, "source_id": f"s{i % 2}",
                     "split": ("train", "val", "test")[i % 7 % 3]})
    stats = split_stats(rows, NAMES)
    assert sum(s["n"] for s in stats) == len(rows)
    assert all(s["label_name"] == NAMES[s["label_id"]] for s in stats)
    keys = [(s["split"], s["label_id"], s["source_id"]) for s in stats]
    assert keys == sorted(keys) and len(keys) == len(set(keys))


def test_fd_rows_use_filtered_rows_and_new_split():
    metadata = [
        {"image_id": "a", "source_id": "s1", "domain": "sketch", "path": "train/x/a.png", "split": "train"},
        {"image_id": "b", "source_id": "s1", "domain": "sketch", "path": "test/x/b.png", "split": "test"},
        {"image_id": "c", "source_id": "s1", "domain": "RENDER", "path": "val/x/c.png", "split": "val"},
    ]
    filtered = [{"image_id": "a"}, {"image_id": "b"}]          # c was filtered out
    frame = fd_rows(filtered, metadata, {"a": "val", "b": "train"})
    assert [r["image_id"] for r in frame] == ["a", "b"]
    assert [r["split"] for r in frame] == ["val", "train"]       # NEW split, not metadata's
    assert frame[0]["path"] == "train/x/a.png"                   # other columns untouched
    checks = [("source_id -> domain", ["source_id"], ["domain"]),
              ("image_id -> (path, split)", ["image_id"], ["path", "split"])]
    results = check_rows(frame, checks)
    assert results["source_id -> domain"][1] == {}               # c's conflict is gone
    assert results["image_id -> (path, split)"][1] == {}
    assert check_rows(metadata, checks)["source_id -> domain"][1] != {}  # unfiltered would fail
