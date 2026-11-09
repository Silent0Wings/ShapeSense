"""The evaluation repairs of iteration 3: each test fails without its fix."""

import json

import numpy as np
import pytest

from src.common.features import PIXEL_SCALE
from src.common.splits import reads_outside
from src.stage4_train import sampling
from src.stage4_train.model import SmallCNN
from src.stage5_eval import criterion, evaluate, robust
from src.stage5_eval import run as s5
from src.stage5_eval.stats import analysis_rng, cluster_bootstrap, mcnemar_test

K = 3


def _data(n=300, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, K, n)
    a, b = y.copy(), y.copy()
    a[rng.random(n) < 0.15] = 0
    b[rng.random(n) < 0.15] = 1
    return y, a, b


def test_clusters_widen_the_interval_when_images_are_near_duplicates():
    y, a, b = _data()
    many = 8
    tiled = [np.tile(x, many) for x in (y, a, b)]
    unique = np.arange(tiled[0].size)
    copies = np.tile(np.arange(y.size), many)
    args = (K, 400, analysis_rng(1, "x"), 0.95)
    as_single = cluster_bootstrap(*tiled, unique, *args)
    as_groups = cluster_bootstrap(*tiled, copies, K, 400, analysis_rng(1, "x"), 0.95)
    assert as_groups["half_width"] > 1.8 * as_single["half_width"]
    assert as_groups["n_clusters"] == y.size


def test_levels_are_averaged_and_scored_on_the_same_resample():
    y, a, b = _data()
    groups = np.arange(y.size)
    one = cluster_bootstrap(y, a, b, groups, K, 200, analysis_rng(2, "x"), 0.95)
    two = cluster_bootstrap(y, np.stack([a, a]), np.stack([b, b]), groups, K, 200, analysis_rng(2, "x"), 0.95)
    assert one["delta"] == pytest.approx(two["delta"])
    assert one["ci"] == pytest.approx(two["ci"])


def test_named_generators_do_not_depend_on_the_order_of_analyses():
    first = analysis_rng(0, "secondary/a").random(3)
    analysis_rng(0, "something new").random(100)
    assert np.array_equal(first, analysis_rng(0, "secondary/a").random(3))
    assert not np.array_equal(first, analysis_rng(0, "secondary/b").random(3))


def test_mcnemar_is_exact_for_few_discordant_pairs():
    a = np.array([True] * 10 + [False] * 0 + [True] * 90)
    b = np.array([False] * 10 + [True] * 90)
    assert mcnemar_test(a, b)["p_value"] == pytest.approx(2 * 0.5 ** 10)


def _boot(delta, ci, drop=None, se=None, adj=None):
    n = K
    return {"delta": delta, "ci": ci, "drop_observed": np.array(drop if drop is not None else [0.0] * n),
            "drop_se": np.array(se if se is not None else [0.5] * n),
            "drop_ci_lo_adj": np.array(adj if adj is not None else [-1.0] * n)}


def test_robust_rule_needs_gain_and_interval():
    assert criterion.robust_verdict(_boot(1.5, [0.5, 2.5]), 2.0, 1.0)["verdict"] == "pass"
    assert criterion.robust_verdict(_boot(0.5, [0.1, 0.9]), 2.0, 1.0)["verdict"] == "fail"
    assert criterion.robust_verdict(_boot(1.5, [-0.1, 2.5]), 2.0, 1.0)["verdict"] == "fail"


def test_robust_rule_reports_the_strict_reading_without_requiring_it():
    loose = criterion.robust_verdict(_boot(1.5, [0.5, 2.5]), 2.0, 1.0)
    assert loose["verdict"] == "pass" and loose["strict_pass"] is False
    assert criterion.robust_verdict(_boot(2.5, [1.2, 3.5]), 2.0, 1.0)["strict_pass"] is True


def test_harm_needs_the_corrected_interval_and_the_standard_error_floor():
    harmful = _boot(1.5, [0.5, 2.5], drop=[3.0, 0, 0], se=[1.0, 0.5, 0.5], adj=[0.2, -1, -1])
    assert criterion.robust_verdict(harmful, 2.0, 1.0)["harmful_classes"] == [0]
    not_corrected = _boot(1.5, [0.5, 2.5], drop=[3.0, 0, 0], se=[1.0, 0.5, 0.5], adj=[-0.2, -1, -1])
    assert criterion.robust_verdict(not_corrected, 2.0, 1.0)["harmful_classes"] == []
    wide = _boot(1.5, [0.5, 2.5], drop=[3.0, 0, 0], se=[4.0, 0.5, 0.5], adj=[0.2, -1, -1])
    assert criterion.robust_verdict(wide, 2.0, 1.0)["harmful_classes"] == []


def test_reads_by_another_module_count_as_extra(tmp_path):
    log = tmp_path / "log"
    log.write_text("t,run,src.stage5_eval.evaluate,test,5\nt,run,src.other,test,5\nt,old,src.other,test,5\n", encoding="utf-8")
    assert reads_outside("run", s5.READER, log_path=log) == 1


def test_stale_error_images_are_not_reused(tmp_path):
    path = tmp_path / "errors.npz"
    images, y, pred, ids = np.zeros((4, 8, 8), np.uint8), np.array([0, 1, 2, 0]), np.array([1, 1, 2, 2]), np.array(list("abcd"))
    s5.gallery_errors(images, path, y, pred, ids, "models-1")
    assert s5.gallery_errors(None, path, y, pred, ids, "models-1") is not None
    assert s5.gallery_errors(None, path, y, pred, ids, "models-2") is None


def test_wrong_class_counts_stop_the_analysis():
    s5.check_class_counts(np.array([0, 0, 1]), np.array([2, 1, 0]))
    with pytest.raises(ValueError, match="noise_bands"):
        s5.check_class_counts(np.array([0, 1, 1]), np.array([2, 1, 0]))


def test_preprocessing_code_is_part_of_the_prediction_key(tmp_path):
    model = tmp_path / "m.pt"
    model.write_bytes(b"x")
    assert "+" in evaluate.model_fingerprint(model)


def test_training_and_evaluation_share_one_scaling_constant():
    assert sampling.UINT8_MAX is PIXEL_SCALE


def test_the_network_default_is_four_blocks():
    assert sum(1 for m in SmallCNN().modules() if m.__class__.__name__ == "Conv2d") == 4


def test_perturbed_sets_are_built_once_and_checked(tmp_path):
    images = np.full((3, 64, 64), 255, dtype=np.uint8)
    images[:, 20:40, 20] = 0
    out = robust.sets_for(images, ["gauss0.1"], 7, tmp_path, "h1")
    again = robust.sets_for(None, ["gauss0.1"], 7, tmp_path, "h1")
    assert np.array_equal(out["gauss0.1"], again["gauss0.1"])
    with pytest.raises(RuntimeError, match="another holdout"):
        robust.sets_for(None, ["gauss0.1"], 7, tmp_path, "h2")
    stored = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    (tmp_path / "gauss0.1.npz").write_bytes(b"changed")
    assert stored["sets"]["gauss0.1"]
    with pytest.raises(RuntimeError, match="changed on disk"):
        robust.sets_for(None, ["gauss0.1"], 7, tmp_path, "h1")


def test_a_missing_set_needs_a_holdout_read(tmp_path):
    with pytest.raises(RuntimeError, match="no holdout read"):
        robust.sets_for(None, ["blur1"], 7, tmp_path, "h1")
