"""One ONNX Runtime session per arm: A0 from export/, A1 and B from studio/out/arms."""

from __future__ import annotations

import json
from pathlib import Path

import onnxruntime as ort
from src.common.config import REPO_ROOT

from studio.settings import ARMS, ARMS_DIR, ARMS_MANIFEST

_sessions: dict[str, ort.InferenceSession] = {}


def model_path(arm: str) -> Path:
    if arm == "A0":
        return REPO_ROOT / "export" / "model.onnx"
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
    out: dict[str, dict] = {}
    card = REPO_ROOT / "export" / "model_card.json"
    if card.is_file():
        info = json.loads(card.read_text(encoding="utf-8"))
        out["A0"] = {"run": info["run_name"], "val_macro_f1": info["val_macro_f1"]}
    if ARMS_MANIFEST.is_file():
        out.update(json.loads(ARMS_MANIFEST.read_text(encoding="utf-8")))
    return out
