"""Predict the class of a fresh image with the exported bundle (R14).

Self-contained: imports only numpy, Pillow, onnxruntime, the standard
library and the sibling standardize.py (a verbatim copy of
src/stage1_freeze/standardize.py, written by the Stage 6 export). No torch
and no src/ imports (import-linter: export imports nothing from the project).

Preprocessing is standardize.standardize(), the same code used for training
images. Never add a plain resize here: it causes train/serve skew.

Usage (from the repository root):
    from export import predict
    predict.predict(Image.open("drawing.png"))          -> "hexagon"
    predict.predict_proba(predict.preprocess(img))      -> {"circle": 0.04, ...}
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

try:
    from . import standardize as _std
except ImportError:  # run as a script: python export/predict.py
    import standardize as _std

Rejected = _std.Rejected

EXPORT_DIR = Path(__file__).resolve().parent
MODEL_NAME = "model.onnx"
LABELS_NAME = "labels.json"
PIXEL_SCALE = 255.0  # model input = uint8 pixel / 255 (unitless)


def model_available() -> bool:
    """True when the exported model and its labels are both on disk."""
    return (EXPORT_DIR / MODEL_NAME).is_file() and (EXPORT_DIR / LABELS_NAME).is_file()


def preprocess(img: Image.Image) -> np.ndarray:
    """Any-size RGB/RGBA image -> uint8 (64, 64), values 0 (ink) or 255 (white).

    Raises Rejected (standardize.Rejected) for blank or contrast-free input.
    """
    x64, _info = _std.standardize(img)
    return x64


@functools.lru_cache(maxsize=1)
def _labels() -> tuple[str, ...]:
    return tuple(json.loads((EXPORT_DIR / LABELS_NAME).read_text(encoding="utf-8")))


@functools.lru_cache(maxsize=1)
def _session() -> ort.InferenceSession:
    return ort.InferenceSession(str(EXPORT_DIR / MODEL_NAME),
                                providers=["CPUExecutionProvider"])


def predict_proba(x64: np.ndarray) -> dict[str, float]:
    """Softmax class probabilities for one preprocessed (64, 64) uint8 image.

    Returns {class name: probability}; probabilities sum to 1.
    Raises FileNotFoundError when the bundle has not been exported yet.
    """
    if not model_available():
        raise FileNotFoundError(
            f"no exported model in {EXPORT_DIR}: run the Stage 6 export first")
    arr = np.asarray(x64)
    if arr.ndim != 2:
        raise ValueError(f"expected a 2-D image array, got shape {arr.shape}")
    session = _session()
    x = (arr.astype(np.float32) / PIXEL_SCALE).reshape(1, 1, *arr.shape)
    logits = session.run(None, {session.get_inputs()[0].name: x})[0][0]
    z = logits.astype(np.float64) - logits.max()
    e = np.exp(z)
    probs = e / e.sum()
    labels = _labels()
    if len(labels) != probs.size:
        raise ValueError("labels.json does not match the model output size")
    return {name: float(p) for name, p in zip(labels, probs)}


def predict(img: Image.Image) -> str:
    """Most probable class name for any-size RGB/RGBA image."""
    probs = predict_proba(preprocess(img))
    return max(probs, key=probs.__getitem__)
