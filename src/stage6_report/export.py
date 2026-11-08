"""Stage 6 export bundle builder (R12, plan 32).

Builds export/ from the Stage 4 artifacts: picks the run with the best
VALIDATION macro-F1, converts its TorchScript model to ONNX, checks the
ONNX output against torch, and writes the files the bundle needs next to
it (standardize.py copied verbatim, labels.json, model_card.json).

Contract:
  Input:  artifacts/stage4/<arm>_<seed>/model.pt and run.json
          (run.json: val_macro_f1, arm, seed, run_name)
          model.pt: TorchScript, input float32 (N, 1, S, S) = uint8 / 255,
          output logits (N, 10)
  Output: export/model.onnx, export/standardize.py, export/labels.json,
          export/model_card.json
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import torch

from src.common.config import class_names, resolve

REPO_ROOT = Path(__file__).resolve().parents[2]
STANDARDIZE_SRC = REPO_ROOT / "src" / "stage1_freeze" / "standardize.py"

STAGE4_SUBDIR = "stage4"
MODEL_TS_NAME = "model.pt"      # Stage 4 TorchScript model, inside each run dir
RUN_JSON_NAME = "run.json"      # Stage 4 per-run summary, inside each run dir
ONNX_NAME = "model.onnx"
STANDARDIZE_NAME = "standardize.py"
LABELS_NAME = "labels.json"
MODEL_CARD_NAME = "model_card.json"

ONNX_OPSET = 17                 # ONNX opset version used for export
INPUT_NAME = "image"
OUTPUT_NAME = "logits"
PIXEL_SCALE = 255.0             # model input = uint8 pixel / 255 (unitless)
VERIFY_SEED = 0                 # np.random seed for the ORT-vs-torch check
VERIFY_BATCH = 4                # random inputs in the ORT-vs-torch check
VERIFY_ATOL = 1e-4              # max abs logit difference allowed
SELECTION_RULE = "validation macro-F1"


def run_name(run: dict[str, Any]) -> str:
    """Run name for one configs/pipeline.yaml#runs entry: ``<name-or-arm>_<seed>``.

    Same rule as Stage 4 (sweep.run_name) and Stage 5 (run.run_name): a named
    run such as ``{arm: B, seed: 0, name: B_equalreal}`` lives in
    ``artifacts/stage4/B_equalreal_0/``, not ``B_0/``.
    """
    return f"{run.get('name') or run['arm']}_{run['seed']}"


def export_candidates(config: dict[str, Any]) -> list[str]:
    """Run names eligible for export, config order.

    Held-out-source runs are excluded: their validation macro-F1 is measured
    on a filtered validation split and is not comparable with the others.
    """
    return [run_name(run) for run in config["runs"] if not run.get("holdout_source")]


def stage4_dir(config: dict[str, Any]) -> Path:
    """``artifacts/stage4`` resolved against the repo root, never the CWD."""
    return resolve(config["paths"]["artifacts_dir"]) / STAGE4_SUBDIR


def select_model(stage4_dir: Path, run_names: list[str]) -> dict[str, Any]:
    """Pick the run with the highest VALIDATION macro-F1.

    Only val_macro_f1 is read; test metrics never enter the choice. Ties go
    to the earlier name in run_names (config order). Returns the run.json
    dict plus "model_path" (str), the TorchScript model of the chosen run.
    """
    stage4_dir = Path(stage4_dir)
    best: dict[str, Any] | None = None
    for name in run_names:
        run_dir = stage4_dir / name
        run_json = run_dir / RUN_JSON_NAME
        model_ts = run_dir / MODEL_TS_NAME
        if not run_json.is_file() or not model_ts.is_file():
            raise FileNotFoundError(
                f"run {name} is incomplete under {run_dir}: Stage 4 must finish it first")
        info = json.loads(run_json.read_text(encoding="utf-8"))
        if best is None or info["val_macro_f1"] > best["val_macro_f1"]:
            best = dict(info, model_path=str(model_ts))
    if best is None:
        raise ValueError("select_model needs at least one run name")
    return best


def export_onnx(torchscript_path: Path, onnx_path: Path, image_size: int) -> None:
    """Export a TorchScript classifier to ONNX and verify it against torch.

    The batch axis is dynamic. Raises RuntimeError if ONNX Runtime and torch
    disagree on the logits for VERIFY_BATCH random inputs (max abs difference
    above VERIFY_ATOL).
    """
    model = torch.jit.load(str(torchscript_path), map_location="cpu")
    model.eval()
    dummy = torch.zeros(1, 1, image_size, image_size, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy,
        str(onnx_path),
        input_names=[INPUT_NAME],
        output_names=[OUTPUT_NAME],
        dynamic_axes={INPUT_NAME: {0: "batch"}, OUTPUT_NAME: {0: "batch"}},
        opset_version=ONNX_OPSET,
        dynamo=False,
    )

    rng = np.random.default_rng(VERIFY_SEED)
    batch = rng.random((VERIFY_BATCH, 1, image_size, image_size), dtype=np.float32)
    with torch.no_grad():
        expected = model(torch.from_numpy(batch)).numpy()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    got = session.run([OUTPUT_NAME], {INPUT_NAME: batch})[0]
    if got.shape != expected.shape:
        raise RuntimeError(
            f"ONNX logits shape {got.shape} != torch logits shape {expected.shape}")
    worst = float(np.max(np.abs(got - expected)))
    if worst > VERIFY_ATOL:
        raise RuntimeError(
            f"ONNX and torch logits differ by {worst:.3g} (limit {VERIFY_ATOL:g})")


def build_bundle(config: dict[str, Any], export_dir: Path) -> dict[str, Any]:
    """Write the export bundle into export_dir and return its paths and selection.

    The model is chosen by validation macro-F1 among config["runs"]. The
    standardize.py copy is byte-for-byte the training file.
    """
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    selection = select_model(stage4_dir(config), export_candidates(config))
    image_size = int(config["image_size"])

    onnx_path = export_dir / ONNX_NAME
    export_onnx(Path(selection["model_path"]), onnx_path, image_size)

    standardize_path = export_dir / STANDARDIZE_NAME
    shutil.copyfile(STANDARDIZE_SRC, standardize_path)

    labels = class_names(config)
    labels_path = export_dir / LABELS_NAME
    labels_path.write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")

    card = {
        "run_name": selection["run_name"],
        "arm": selection["arm"],
        "seed": selection["seed"],
        "val_macro_f1": selection["val_macro_f1"],
        "selection": SELECTION_RULE,
        "input": {
            "name": INPUT_NAME,
            "dtype": "float32",
            "shape": ["batch", 1, image_size, image_size],
            "scale": f"uint8 / {PIXEL_SCALE:g}",
            "background": "white = 1.0",
            "ink": "black = 0.0",
            "preprocess": f"standardize.py -> uint8 {image_size}x{image_size}",
        },
        "output": {
            "name": OUTPUT_NAME,
            "dtype": "float32",
            "shape": ["batch", len(labels)],
            "meaning": "logits in labels.json index order",
        },
    }
    card_path = export_dir / MODEL_CARD_NAME
    card_path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")

    return {
        "onnx": onnx_path,
        "standardize": standardize_path,
        "labels": labels_path,
        "model_card": card_path,
        "selection": selection,
    }
