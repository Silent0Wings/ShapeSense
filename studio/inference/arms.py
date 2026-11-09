"""One ONNX Runtime session per arm, all from studio/out/arms."""

from __future__ import annotations

import json
from pathlib import Path

import onnxruntime as ort

from studio.settings import ARMS, ARMS_DIR, ARMS_MANIFEST

_sessions: dict[str, ort.InferenceSession] = {}


def model_path(arm: str) -> Path:
    return ARMS_DIR / arm / "model.onnx"


def available() -> list[str]:
    return [arm for arm in ARMS if model_path(arm).is_file()]


def session(arm: str) -> ort.InferenceSession:
    if arm not in _sessions:
        _sessions[arm] = ort.InferenceSession(str(model_path(arm)),
                                              providers=["CPUExecutionProvider"])
    return _sessions[arm]


def provenance() -> dict[str, dict]:
    """Which run each arm's live model came from."""
    return json.loads(ARMS_MANIFEST.read_text(encoding="utf-8")) if ARMS_MANIFEST.is_file() else {}
