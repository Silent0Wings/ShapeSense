"""Stage 5 runner helpers (audit findings 2, 5, 10): arm membership of config
runs, gallery images without an unaccounted test read, and the noise-band
threshold check derived from the file actually read.

tmp_path and synthetic arrays only; the real test split is never read.
"""

import csv
import json

import numpy as np
import pytest

from src.common.hashing import sha256_path
from src.stage5_eval import evaluate
from src.stage5_eval import run as s5

K = 3
N = 10


def _config(tmp_path, runs):
    art = tmp_path / "artifacts"
    (art / "stage4" / "baselines").mkdir(parents=True)
    (art / "stage4" / "baselines" / "baselines.json").write_text("{}", encoding="utf-8")
    return {
        "paths": {"artifacts_dir": str(art), "test_access_log": str(tmp_path / "log.csv"),
                  "splits_dir": str(tmp_path / "splits")},
        "runs": runs,
        "seed_set": [0, 1],
    }


def _spec(name, arm, seed, **extra):
    return evaluate.ModelSpec(name=name, kind=evaluate.KIND_CNN, path=f"{name}.pt",
                              fingerprint="fp", extra={"arm": arm, "seed": seed, **extra})


def test_named_run_not_in_arm_ensemble(tmp_path):
    runs = [{"arm": "A1", "seed": 0}, {"arm": "B", "seed": 0},
            {"arm": "B", "seed": 0, "name": "B_equalreal"},
            {"arm": "A1", "seed": 1, "holdout_source": "github_handdrawn"}]
    config = _config(tmp_path, runs)

    assert s5.is_arm_member(runs[0]) and s5.is_arm_member(runs[1])
    assert not s5.is_arm_member(runs[2]) and not s5.is_arm_member(runs[3])
    assert s5.run_name(runs[2]) == "B_equalreal_0"
    assert s5.run_name(runs[3]) == f"A1_{s5.LOSO_TAG}_1"  # Stage 4 sweep.run_name spelling
    # Power check and ensembles see plain runs only.
    assert s5.arm_run_names(config, ("A1", "B")) == {"A1": ["A1_0"], "B": ["B_0"]}

    specs = s5.build_specs(config, shortcut_detected=False)
    by_name = {s.name: s for s in specs}
    # Every config run is still evaluated (one counted test read each), plus two baselines.
    assert len(specs) == len(runs) + len(s5.BASELINE_KINDS)
    assert s5._arm_of(by_name["B_0"]) == "B"
    assert s5._arm_of(by_name["B_equalreal_0"]) is None
    assert by_name["B_equalreal_0"].extra["ablation"] is True
    assert by_name["B_equalreal_0"].extra["name"] == "B_equalreal"
    holdout = by_name[f"A1_{s5.LOSO_TAG}_1"]
    assert s5._arm_of(holdout) is None
    assert holdout.extra["ablation"] is True
    assert holdout.source_filter == "github_handdrawn"
    assert not s5.is_full_split_spec(holdout)
    assert s5.is_full_split_spec(by_name["B_0"])
    members_b = [s.name for s in specs if s5._arm_of(s) == "B"]
    assert members_b == ["B_0"]


def test_no_unaccounted_gallery_read(tmp_path, monkeypatch):
    """Galleries never trigger a read of their own: they use the fresh read of
    an evaluated model (one B cache is invalidated) or the error cache, or are skipped."""
    def _forbidden(_config):
        raise AssertionError("a test read not tied to an evaluated model was attempted")
    monkeypatch.setattr(s5.evaluate, "default_test_reader", _forbidden)

    specs = [_spec("A1_0", "A1", 0), _spec("B_0", "B", 0), _spec("B_1", "B", 1),
             evaluate.ModelSpec(name="baseline_x", kind=evaluate.KIND_BASELINE,
                                path="b.joblib", fingerprint="fp", extra={"baseline": "x"})]
    err_path = tmp_path / "predictions" / s5.ERRORS_CACHE
    # Error cache missing: re-evaluate one B member so its counted read brings the images.
    assert s5.gallery_refresh_name(specs, err_path) == "B_0"
    assert s5.gallery_refresh_name([specs[0], specs[3]], err_path) is None

    rng = np.random.default_rng(0)
    y = rng.integers(0, K, size=N).astype(np.int64)
    pred = y.copy()
    pred[::3] = (pred[::3] + 1) % K
    ids = np.array([f"img_{i}" for i in range(N)])
    images = rng.integers(0, 256, size=(N, 4, 4)).astype(np.uint8)

    # Nothing available: skipped, no read.
    assert s5.gallery_errors(None, err_path, y, pred, ids) is None
    assert not err_path.is_file()
    # Fresh images: used and cached.
    fresh = s5.gallery_errors(images, err_path, y, pred, ids)
    assert fresh is not None and err_path.is_file()
    wrong = pred != y
    assert np.array_equal(fresh[0], images[wrong]) and np.array_equal(fresh[1], y[wrong])
    # Cache present: nothing to refresh, cache reused.
    assert s5.gallery_refresh_name(specs, err_path) is None
    cached = s5.gallery_errors(None, err_path, y, pred, ids)
    assert cached is not None and np.array_equal(cached[0], fresh[0])
    assert np.array_equal(cached[2], pred[wrong])

    # Accounting: an unaccounted read fails the check even when the counts agree.
    assert s5.test_reads_ok(3, 3, 0) is True
    assert s5.test_reads_ok(3, 3, 1) is False
    assert s5.test_reads_ok(4, 3, 0) is False


def test_thresholds_check_derived_from_noise_bands_file(tmp_path):
    path = tmp_path / s5.NOISE_BANDS_FILE
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label_id", "class", "n_test", "noise_band_points",
                                          "threshold_points"])
        w.writeheader()
        for c in range(K):
            w.writerow({"label_id": c, "class": f"c{c}", "n_test": 100 + c,
                        "noise_band_points": 1.5 + c, "threshold_points": 2.0 + c})
    bands = s5.read_noise_bands(path, K)
    assert bands["source_sha256"] == sha256_path(path)
    assert bands["source_path"].endswith(s5.NOISE_BANDS_FILE)
    assert np.array_equal(bands["threshold_points"], [2.0, 3.0, 4.0])
    assert s5.thresholds_from_noise_bands(bands) is True
    assert s5.thresholds_from_noise_bands({**bands, "source_sha256": s5.MISSING_HASH}) is False
    assert s5.thresholds_from_noise_bands({**bands, "source_sha256": ""}) is False
    assert s5.thresholds_from_noise_bands(
        {**bands, "threshold_points": np.array([np.nan, 1.0, 2.0])}) is False
    with pytest.raises(ValueError):
        s5.read_noise_bands(path, K + 1)  # a class without a row


def test_build_specs_reads_baseline_meta(tmp_path):
    config = _config(tmp_path, [{"arm": "A1", "seed": 0}, {"arm": "B", "seed": 0}])
    bdir = tmp_path / "artifacts" / "stage4" / "baselines"
    (bdir / "baselines.json").write_text(json.dumps(
        {"svm_hog": {"features": "hog", "hog_pixels_per_cell": 8}}), encoding="utf-8")
    specs = s5.build_specs(config, shortcut_detected=False)
    hog = next(s for s in specs if s.name == f"{s5.BASELINE_PREFIX}svm_hog")
    assert hog.features == "hog" and hog.hog_pixels_per_cell == 8
    assert s5._arm_of(hog) is None
