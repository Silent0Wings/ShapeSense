"""demo/app.py message formatting (audit finding 11): the "not sure" text takes
its threshold from demo.logic, never from a literal. Skips when gradio or the
export bundle is not importable on this machine."""

import pytest

from demo import logic

pytest.importorskip("gradio")
try:
    from demo import app
except ImportError as exc:  # export/standardize.py not generated yet
    pytest.skip(f"demo app not importable here ({exc})", allow_module_level=True)


def _not_sure(best=("circle", 0.4)):
    return {"message": None, "label": logic.NOT_SURE_LABEL, "confident": False,
            "top3": [best, ("square", 0.3), ("hexagon", 0.2)], "x64": None}


def test_not_sure_message_uses_threshold(monkeypatch):
    text = app._markdown(_not_sure())
    assert "Not sure" in text and "circle" in text and "40%" in text
    assert f"below {logic.NOT_SURE_THRESHOLD:.0%}" in text

    # The wording follows the constant: no "50%" literal survives a changed threshold.
    monkeypatch.setattr(logic, "NOT_SURE_THRESHOLD", 0.6)
    text = app._markdown(_not_sure())
    assert "below 60%" in text
    assert "50%" not in text


def test_markdown_other_branches():
    assert app._markdown({"message": "Draw a shape first"}) == "**Draw a shape first**"
    confident = {"message": None, "confident": True, "label": "square", "top3": [("square", 0.9)]}
    assert app._markdown(confident) == "**Prediction: square**"
