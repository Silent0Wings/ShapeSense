"""E29: pure metrics (stage_5.md R2/R3, Mission M1). F1 in points."""

import numpy as np
import pytest

from src.stage5_eval import metrics

# Mission M1 matrix: rows true (square, diamond, rectangle), cols predicted.
M1_CONF = np.array([[8, 1, 1], [2, 8, 0], [0, 0, 10]], dtype=np.int64)


def _labels_from_confusion(conf: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expand a confusion matrix into (y_true, y_pred) arrays."""
    k = conf.shape[0]
    y_true, y_pred = [], []
    for t in range(k):
        for p in range(k):
            y_true.extend([t] * int(conf[t, p]))
            y_pred.extend([p] * int(conf[t, p]))
    return np.asarray(y_true), np.asarray(y_pred)


def test_mission_m1_values():
    y, pred = _labels_from_confusion(M1_CONF)
    assert metrics.accuracy(y, pred, 3) == pytest.approx(26 / 30)
    f1 = metrics.per_class_f1(y, pred, 3)
    # square: tp 8, fp 2, fn 2 -> 16/20; diamond: tp 8, fp 1, fn 2 -> 16/19;
    # rectangle: tp 10, fp 1, fn 0 -> 20/21. All in points.
    expected = 100.0 * np.array([16 / 20, 16 / 19, 20 / 21])
    np.testing.assert_allclose(f1, expected)
    assert f1[0] == pytest.approx(80.0)
    assert f1[1] == pytest.approx(84.2105, abs=1e-3)
    assert f1[2] == pytest.approx(95.2381, abs=1e-3)
    assert metrics.macro_f1(y, pred, 3) == pytest.approx(expected.mean())
    assert metrics.macro_f1(y, pred, 3) == pytest.approx(86.48, abs=0.01)


def test_confusion_rows_true_cols_pred():
    y, pred = _labels_from_confusion(M1_CONF)
    conf = metrics.confusion(y, pred, 3)
    assert conf.dtype == np.int64
    np.testing.assert_array_equal(conf, M1_CONF)
    # Direct asymmetric check: one true-0 image predicted as 2.
    conf2 = metrics.confusion(np.array([0]), np.array([2]), 3)
    assert conf2[0, 2] == 1 and conf2[2, 0] == 0


def test_confusion_rejects_out_of_range_labels():
    with pytest.raises(ValueError):
        metrics.confusion(np.array([0, 3]), np.array([0, 0]), 3)
    with pytest.raises(ValueError):
        metrics.confusion(np.array([0, 1]), np.array([0]), 3)


def test_soft_vote_averages():
    probs = np.array(
        [
            [[0.8, 0.2], [0.1, 0.9]],
            [[0.4, 0.6], [0.3, 0.7]],
        ]
    )
    out = metrics.soft_vote(probs)
    assert out.shape == (2, 2)
    np.testing.assert_allclose(out, [[0.6, 0.4], [0.2, 0.8]])
    # Soft vote can differ from the first model's argmax.
    assert out.argmax(axis=1).tolist() == [0, 1]


def test_soft_vote_shape_validation():
    with pytest.raises(ValueError):
        metrics.soft_vote(np.zeros((4, 3)))  # missing model axis
    with pytest.raises(ValueError):
        metrics.soft_vote(np.zeros((0, 4, 3)))  # no models


def test_empty_class_f1_zero():
    # Class 2 never appears in truth or predictions -> F1 = 0, macro over 3.
    y = np.array([0, 0, 1, 1])
    pred = np.array([0, 0, 1, 1])
    f1 = metrics.per_class_f1(y, pred, 3)
    np.testing.assert_allclose(f1, [100.0, 100.0, 0.0])
    assert metrics.macro_f1(y, pred, 3) == pytest.approx(200.0 / 3)
    assert np.all(np.isfinite(f1))


def test_group_accuracy():
    y = np.array([0, 1, 0, 1, 2, 2])
    pred = np.array([0, 1, 1, 1, 2, 0])
    groups = np.array(["render", "render", "sketch", "sketch", "sketch", "sketch"])
    acc = metrics.group_accuracy(y, pred, groups)
    assert acc == {"render": pytest.approx(1.0), "sketch": pytest.approx(0.5)}


def test_pair_confusions_both_directions():
    names = ["square", "diamond", "rectangle"]
    out = metrics.pair_confusions(M1_CONF, names, [["square", "diamond"], ["square", "rectangle"]])
    assert out[0] == {"a": "square", "b": "diamond", "a_to_b": 1, "b_to_a": 2}
    assert out[1] == {"a": "square", "b": "rectangle", "a_to_b": 1, "b_to_a": 0}
    with pytest.raises(ValueError):
        metrics.pair_confusions(M1_CONF, names, [["square", "circle"]])
