"""Standardize a drawing with the shipped code, then score it with each arm."""

from __future__ import annotations

import time

import numpy as np

from studio.imaging import to_b64_png
from studio.inference import arms as arm_models
from studio.settings import ARMS, NOT_SURE_BELOW, TOP_K

MISSING = "No exported model yet. Run: python run_pipeline.py --stages 6"


def _bundle():
    """export.predict, imported late because its generated files may not exist yet."""
    try:
        from export import predict as bundle
    except ImportError:
        return None
    return bundle if bundle.model_available() else None


def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits.astype(np.float64) - logits.max()
    e = np.exp(z)
    return e / e.sum()


def _score(arm: str, x64: np.ndarray, labels: tuple[str, ...], scale: float) -> dict:
    session = arm_models.session(arm)
    x = (x64.astype(np.float32) / scale).reshape(1, 1, *x64.shape)
    started = time.perf_counter()
    logits = session.run(None, {session.get_inputs()[0].name: x})[0][0]
    latency_ms = (time.perf_counter() - started) * 1000.0
    probs = softmax(logits)
    order = np.argsort(-probs)
    top = [{"label": labels[int(i)], "p": float(probs[i])} for i in order[:TOP_K]]
    return {"arm": arm, "label": top[0]["label"], "top": top, "latency_ms": latency_ms,
            "not_sure": top[0]["p"] < NOT_SURE_BELOW,
            "all": {labels[i]: float(p) for i, p in enumerate(probs)}}


def infer(image, requested: list[str]) -> dict:
    """Result for one PIL drawing. Reports problems as messages, never as a crash."""
    bundle = _bundle()
    if bundle is None:
        return {"status": "no_model", "message": MISSING}
    try:
        x64 = bundle.preprocess(image)
    except bundle.Rejected as exc:
        return {"status": "blank", "message": "Draw a shape first", "reason": str(exc)}
    labels = tuple(bundle._labels())
    have = arm_models.available()
    chosen = [arm for arm in ARMS if arm in requested and arm in have]
    return {"status": "ok", "seen": to_b64_png(x64),
            "results": [_score(arm, x64, labels, bundle.PIXEL_SCALE) for arm in chosen],
            "missing": [arm for arm in requested if arm not in have]}
