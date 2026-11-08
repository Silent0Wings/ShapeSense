"""Tests for the export bundle (plan 32, R12).

Covers preprocessing (must be the training standardize), the labels file,
prediction on a fresh image of any size, validation-only model selection and
the ONNX-vs-TorchScript check. Tests that need the generated bundle skip with
a reason until the Stage 6 export has run.
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pytest
import torch
from PIL import Image, ImageDraw

from src.common.config import class_names, load_config
from src.stage1_freeze import standardize as std_mod
from src.stage6_report import export as export_mod

EXPORT_DIR = Path(__file__).resolve().parents[2] / "export"


def _fresh_hexagon(size: tuple[int, int] = (300, 200),
                   colour: tuple[int, int, int] = (0, 0, 255),
                   width: int = 12) -> Image.Image:
    """Procedural fresh RGB image: a thick coloured hexagon outline on white."""
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    cx, cy, r = w / 2, h / 2, 0.4 * min(w, h)
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    draw.line(pts + pts[:1], fill=colour, width=width, joint="curve")
    return img


def _predict_module():
    """Import export.predict, or skip while the bundle's standardize.py is not generated."""
    try:
        return importlib.import_module("export.predict")
    except ImportError as exc:
        pytest.skip(f"export bundle not generated yet ({exc}); run the Stage 6 export first")


def test_preprocess_uses_standardize():
    predict = _predict_module()
    img = _fresh_hexagon()
    expected, _info = std_mod.standardize(img)
    np.testing.assert_array_equal(predict.preprocess(img), expected)


def test_preprocess_output_format():
    predict = _predict_module()
    side = load_config()["image_size"]
    x = predict.preprocess(_fresh_hexagon())
    assert x.dtype == np.uint8
    assert x.shape == (side, side)
    assert set(np.unique(x).tolist()) == {0, 255}


def test_labels_json_matches_taxonomy():
    path = EXPORT_DIR / "labels.json"
    if not path.is_file():
        pytest.skip("export/labels.json not generated yet; run the Stage 6 export first")
    labels = json.loads(path.read_text(encoding="utf-8"))
    assert labels == class_names(load_config())


def test_predict_on_fresh_rgb_image_any_size():
    if not (EXPORT_DIR / "model.onnx").is_file():
        pytest.skip("export/model.onnx not generated yet; run the Stage 6 export first")
    predict = _predict_module()
    labels = class_names(load_config())
    assert predict.model_available()
    for size, colour in [((300, 200), (0, 0, 255)), ((128, 256), (200, 40, 40))]:
        img = _fresh_hexagon(size=size, colour=colour)
        assert predict.predict(img) in labels
        probs = predict.predict_proba(predict.preprocess(img))
        assert set(probs) == set(labels)
        assert sum(probs.values()) == pytest.approx(1.0, abs=1e-5)


def _write_run(root: Path, name: str, val: float, test: float) -> None:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    arm, seed = name.split("_")
    (run_dir / "run.json").write_text(json.dumps({
        "run_name": name, "arm": arm, "seed": int(seed),
        "val_macro_f1": val, "test_macro_f1": test,  # test value must be ignored
    }), encoding="utf-8")
    (run_dir / "model.pt").write_bytes(b"")


def test_select_model_uses_validation(tmp_path):
    stage4 = tmp_path / "stage4"
    _write_run(stage4, "A0_0", val=0.70, test=0.99)  # best on TEST only: must lose
    _write_run(stage4, "A1_0", val=0.90, test=0.10)  # best on VALIDATION: must win
    _write_run(stage4, "B_0", val=0.85, test=0.95)
    sel = export_mod.select_model(stage4, ["A0_0", "A1_0", "B_0"])
    assert sel["run_name"] == "A1_0"
    assert sel["val_macro_f1"] == 0.90
    assert sel["model_path"] == str(stage4 / "A1_0" / "model.pt")

    tie = tmp_path / "tie"
    _write_run(tie, "A1_1", val=0.80, test=0.5)
    _write_run(tie, "A1_2", val=0.80, test=0.5)
    assert export_mod.select_model(tie, ["A1_2", "A1_1"])["run_name"] == "A1_2"


def test_select_model_honours_run_name(tmp_path):
    """A named run lives in <name>_<seed>/ (Stage 4 naming); artifacts_dir resolves
    against the repo root, not the CWD."""
    assert export_mod.run_name({"arm": "B", "seed": 0}) == "B_0"
    assert export_mod.run_name({"arm": "B", "seed": 0, "name": "B_equalreal"}) == "B_equalreal_0"
    assert export_mod.run_name({"arm": "A1", "seed": 2, "name": None}) == "A1_2"

    config = {"paths": {"artifacts_dir": "artifacts"},
              "runs": [{"arm": "A1", "seed": 0},
                       {"arm": "B", "seed": 0, "name": "B_equalreal"},
                       {"arm": "B", "seed": 0, "holdout_source": "github_handdrawn"}]}
    assert export_mod.export_candidates(config) == ["A1_0", "B_equalreal_0"]
    stage4 = export_mod.stage4_dir(config)
    assert stage4.is_absolute()
    assert stage4 == export_mod.REPO_ROOT / "artifacts" / "stage4"
    absolute = {"paths": {"artifacts_dir": str(tmp_path / "art")}}
    assert export_mod.stage4_dir(absolute) == tmp_path / "art" / "stage4"

    # The named run's directory is what select_model opens.
    stage4 = tmp_path / "stage4"
    _write_run(stage4, "A1_0", val=0.70, test=0.99)
    named = stage4 / "B_equalreal_0"
    named.mkdir(parents=True)
    (named / "run.json").write_text(json.dumps({
        "run_name": "B_equalreal_0", "arm": "B", "seed": 0,
        "val_macro_f1": 0.95, "test_macro_f1": 0.0}), encoding="utf-8")
    (named / "model.pt").write_bytes(b"")
    sel = export_mod.select_model(stage4, export_mod.export_candidates(config))
    assert sel["run_name"] == "B_equalreal_0"
    assert sel["model_path"] == str(named / "model.pt")


def test_export_onnx_matches_torchscript(tmp_path):
    side = 8
    torch.manual_seed(0)
    net = torch.nn.Sequential(
        torch.nn.Conv2d(1, 4, kernel_size=3, padding=1),
        torch.nn.ReLU(),
        torch.nn.AdaptiveAvgPool2d(1),
        torch.nn.Flatten(),
        torch.nn.Linear(4, 10),
    )
    ts_path = tmp_path / "tiny.pt"
    torch.jit.script(net.eval()).save(str(ts_path))
    onnx_path = tmp_path / "tiny.onnx"
    export_mod.export_onnx(ts_path, onnx_path, image_size=side)

    x = np.random.default_rng(1).random((3, 1, side, side), dtype=np.float32)
    with torch.no_grad():
        expected = torch.jit.load(str(ts_path))(torch.from_numpy(x)).numpy()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    got = session.run(None, {input_name: x})[0]
    assert got.shape == (3, 10)
    np.testing.assert_allclose(got, expected, atol=1e-4)
    # dynamic batch axis: a batch of one also runs
    assert session.run(None, {input_name: x[:1]})[0].shape == (1, 10)
