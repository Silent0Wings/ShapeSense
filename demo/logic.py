"""
Pure logic for the draw-and-infer demo (plan 33, E33). No Gradio import here.

Drawings made in the demo are informal evidence only (R17): they are not
test data, they are never used for training, and they never change the
Stage 5 verdict. Nothing in this module writes to disk or to any dataset.

The model bundle is injected (``export.predict`` in production, a fake in
tests). Only the ``export`` package may be imported by the demo (R15).
"""
import numpy as np
from PIL import Image

BLANK_MESSAGE = "Draw a shape first"
NO_MODEL_MESSAGE = "No exported model yet — run the pipeline (python run_pipeline.py)"
NOT_SURE_THRESHOLD = 0.5  # top-class probability below this is shown as "not sure"
NOT_SURE_LABEL = "not sure"
TOP_K = 3  # number of confidences shown


def is_blank(rgba):
    """True if there is no canvas or nothing is painted.

    Tests the ALPHA channel. Unpainted canvas pixels are (0, 0, 0, 0), so an
    RGB-darkness test would read a blank canvas as solid ink (R16).
    """
    return rgba is None or bool(rgba[..., 3].sum() == 0)


def canvas_to_rgba(value):
    """Convert a Gradio Sketchpad value to an H x W x 4 uint8 RGBA array, or None.

    Accepts the dict form (key "composite", an array or None) or a bare array
    with 3 or 4 channels. RGB input gets alpha 255.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("composite")
        if value is None:
            return None
    arr = np.asarray(value)
    if arr.ndim != 3 or arr.shape[2] not in (3, 4):
        raise ValueError(f"expected an H x W x 3 or H x W x 4 array, got shape {arr.shape}")
    arr = arr.astype(np.uint8, copy=False)
    if arr.shape[2] == 3:
        alpha = np.full(arr.shape[:2] + (1,), 255, dtype=np.uint8)
        arr = np.concatenate([arr, alpha], axis=2)
    return arr


def _message(text):
    return {"message": text, "label": None, "confident": False, "top3": [], "x64": None}


def infer(rgba, bundle):
    """Run the demo prediction for one canvas.

    Order: blank canvas -> BLANK_MESSAGE (model not called); no model ->
    NO_MODEL_MESSAGE; ``bundle.Rejected`` from preprocessing (a dot, a stray
    mark) -> BLANK_MESSAGE; otherwise top-3 classes and the 64x64 image the
    model saw. A top probability below NOT_SURE_THRESHOLD gives label
    "not sure" with confident False.
    """
    if is_blank(rgba):
        return _message(BLANK_MESSAGE)
    if not bundle.model_available():
        return _message(NO_MODEL_MESSAGE)
    try:
        x64 = bundle.preprocess(Image.fromarray(np.asarray(rgba, dtype=np.uint8)))
    except bundle.Rejected:
        return _message(BLANK_MESSAGE)
    probs = bundle.predict_proba(x64)
    top3 = sorted(((str(name), float(p)) for name, p in probs.items()),
                  key=lambda kv: kv[1], reverse=True)[:TOP_K]
    best_name, best_p = top3[0]
    confident = best_p >= NOT_SURE_THRESHOLD
    return {
        "message": None,
        "label": best_name if confident else NOT_SURE_LABEL,
        "confident": confident,
        "top3": top3,
        "x64": np.asarray(x64, dtype=np.uint8),
    }
