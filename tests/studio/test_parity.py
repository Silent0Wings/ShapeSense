"""What the studio shows is exactly what the real pipeline code produces."""

import copy
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pytest
from PIL import Image, ImageDraw
from src.common.config import load_config
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator

from studio.context import config
from studio.inference import arms, predict as studio_predict
from studio.ops import augment, overrides, synth

ROOT = Path(__file__).resolve().parents[2]


def _outline(size=64):
    img = Image.new("L", (size, size), 255)
    ImageDraw.Draw(img).rectangle((14, 20, 50, 44), outline=0, width=2)
    return np.asarray(img, dtype=np.uint8)


def test_augmentation_matches_build_transform():
    image = _outline()
    values = overrides.default_augment_values()
    got = augment.variants(image, 3, values, seed=5, n=3)
    transform = build_transform(load_config())
    want = [transform(image, 3, np.random.default_rng(5 + i)) for i in range(3)]
    assert all(np.array_equal(a, b) for a, b in zip(got, want))


def test_slider_override_changes_only_a_private_copy():
    before = copy.deepcopy(config())
    overrides.augment_config({**overrides.default_augment_values(), "rotate_deg": 0})
    overrides.synth_config({**overrides.default_synth_values(), "radius_lo": 12})
    assert config() == before


def test_same_seed_keeps_other_random_choices_stable():
    image = _outline()
    values = overrides.default_augment_values()
    first = augment.variants(image, 3, values, seed=9, n=1)[0]
    second = augment.variants(image, 3, values, seed=9, n=1)[0]
    assert np.array_equal(first, second)


@pytest.mark.parametrize("label", range(10))
def test_generator_preview_matches_build_generator(label):
    cfg = config()
    image, _ = synth.draw(label, cfg, np.random.default_rng(11))
    want = build_generator(cfg)(label, np.random.default_rng(11))
    assert np.array_equal(image, want)


def _drawing():
    img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
    ImageDraw.Draw(img).ellipse((40, 40, 216, 216), outline=(0, 0, 0, 255), width=8)
    return img


def _bundle():
    return pytest.importorskip("export.predict")


@pytest.mark.skipif(not (ROOT / "export" / "model.onnx").is_file(), reason="needs the Stage 6 bundle")
def test_a0_probabilities_match_the_shipped_bundle():
    bundle = _bundle()
    out = studio_predict.infer(_drawing(), ["A0"])
    assert out["status"] == "ok"
    want = bundle.predict_proba(bundle.preprocess(_drawing()))
    got = out["results"][0]["all"]
    assert set(got) == set(want)
    assert all(abs(got[k] - want[k]) < 1e-9 for k in want)


@pytest.mark.skipif(not (ROOT / "export" / "model.onnx").is_file(), reason="needs the Stage 6 bundle")
def test_blank_drawing_maps_to_the_demo_message():
    out = studio_predict.infer(Image.new("RGBA", (256, 256), (255, 255, 255, 255)), ["A0"])
    assert out["status"] == "blank" and out["message"] == "Draw a shape first"


@pytest.mark.skipif(not arms.ARMS_MANIFEST.is_file(), reason="needs python -m studio.tools.export_arms")
@pytest.mark.parametrize("arm", ["A1", "B"])
def test_arm_onnx_matches_its_torchscript(arm):
    torch = pytest.importorskip("torch")
    run = json.loads(arms.ARMS_MANIFEST.read_text(encoding="utf-8"))[arm]["run"]
    model = torch.jit.load(str(ROOT / "artifacts" / "stage4" / run / "model.pt"), map_location="cpu")
    model.eval()
    x = np.random.default_rng(0).random((4, 1, 64, 64), dtype=np.float32)
    with torch.no_grad():
        want = model(torch.from_numpy(x)).numpy()
    session = ort.InferenceSession(str(arms.model_path(arm)), providers=["CPUExecutionProvider"])
    got = session.run(None, {session.get_inputs()[0].name: x})[0]
    assert np.max(np.abs(got - want)) < 1e-4
