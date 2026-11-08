"""Tests for demo/logic.py (E33). Fake bundle only; gradio is never imported here."""

import numpy as np
import pytest

from demo import logic


class Rejected(Exception):
    """Stand-in for export.standardize.Rejected."""


class FakeBundle:
    Rejected = Rejected

    def __init__(self, available=True, probs=None, reject=False):
        self._available = available
        self._probs = probs or {"circle": 0.7, "square": 0.2, "hexagon": 0.1}
        self._reject = reject
        self.preprocess_calls = 0
        self.predict_calls = 0

    def model_available(self):
        return self._available

    def preprocess(self, img):
        self.preprocess_calls += 1
        if self._reject:
            raise Rejected("no_contrast")
        return np.zeros((64, 64), dtype=np.uint8)

    def predict_proba(self, x64):
        self.predict_calls += 1
        return dict(self._probs)


def _ink_canvas():
    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[..., 3] = 255  # opaque white page, as composited by the canvas
    rgba[100:110, 50:200, :3] = 0  # black stroke
    return rgba


def test_blank_canvas_alpha_zero_is_blank():
    blank = np.zeros((256, 256, 4), dtype=np.uint8)
    assert logic.is_blank(blank) is True


def test_none_is_blank():
    assert logic.is_blank(None) is True


def test_blank_does_not_call_model():
    bundle = FakeBundle()
    result = logic.infer(np.zeros((256, 256, 4), dtype=np.uint8), bundle)
    assert result["message"] == logic.BLANK_MESSAGE
    assert bundle.preprocess_calls == 0
    assert bundle.predict_calls == 0


def test_single_dot_rejected_message():
    bundle = FakeBundle(reject=True)
    result = logic.infer(_ink_canvas(), bundle)
    assert result["message"] == logic.BLANK_MESSAGE
    assert result["x64"] is None
    assert result["top3"] == []


def test_missing_model_message():
    bundle = FakeBundle(available=False)
    result = logic.infer(_ink_canvas(), bundle)
    assert result["message"] == logic.NO_MODEL_MESSAGE
    assert bundle.preprocess_calls == 0
    assert bundle.predict_calls == 0


def test_low_confidence_not_sure():
    probs = {"circle": 0.4, "square": 0.3, "hexagon": 0.2, "triangle": 0.1}
    result = logic.infer(_ink_canvas(), FakeBundle(probs=probs))
    assert result["confident"] is False
    assert result["label"] == "not sure"
    assert result["top3"][0] == ("circle", 0.4)


def test_drawing_returns_top3_and_x64():
    probs = {"circle": 0.1, "square": 0.5, "hexagon": 0.2, "triangle": 0.15, "star": 0.05}
    result = logic.infer(_ink_canvas(), FakeBundle(probs=probs))
    assert result["message"] is None
    assert result["confident"] is True
    assert result["label"] == "square"
    assert len(result["top3"]) == logic.TOP_K == 3
    assert [name for name, _ in result["top3"]] == ["square", "hexagon", "triangle"]
    probs_sorted = [p for _, p in result["top3"]]
    assert probs_sorted == sorted(probs_sorted, reverse=True)
    assert result["x64"].shape == (64, 64)
    assert result["x64"].dtype == np.uint8


def test_canvas_to_rgba_accepts_composite_dict_and_rgb():
    rgba = _ink_canvas()
    assert logic.canvas_to_rgba({"composite": rgba, "layers": [], "background": None}) is not None
    assert np.array_equal(logic.canvas_to_rgba({"composite": rgba}), rgba)
    assert np.array_equal(logic.canvas_to_rgba(rgba), rgba)

    rgb = np.full((256, 256, 3), 255, dtype=np.uint8)
    out = logic.canvas_to_rgba(rgb)
    assert out.shape == (256, 256, 4)
    assert out.dtype == np.uint8
    assert np.all(out[..., :3] == 255)
    assert np.all(out[..., 3] == 255)

    assert logic.canvas_to_rgba(None) is None
    assert logic.canvas_to_rgba({"composite": None}) is None
    with pytest.raises(ValueError):
        logic.canvas_to_rgba(np.zeros((256, 256), dtype=np.uint8))


def test_app_starts_without_export_bundle(monkeypatch):
    """R16: with no exported model the app must start and say so."""
    import builtins
    import pytest
    gr = pytest.importorskip("gradio")  # noqa: F841
    real_import = builtins.__import__

    def no_export(name, *args, **kwargs):
        if name == "export" or name.startswith("export."):
            raise ImportError("no bundle")
        return real_import(name, *args, **kwargs)

    from demo import app, logic
    monkeypatch.setattr(builtins, "__import__", no_export)
    stub = app.load_bundle()
    monkeypatch.setattr(builtins, "__import__", real_import)
    assert stub.model_available() is False
    import numpy as np
    canvas = np.zeros((256, 256, 4), np.uint8)
    canvas[100:150, 100:104, :] = 255
    assert logic.infer(canvas, stub)["message"] == logic.NO_MODEL_MESSAGE
