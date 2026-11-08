"""E28: the Decision 8 SmallCNN — size, output shape, TorchScript round trip."""

import numpy as np
import pytest
import torch

from src.stage4_train.model import SmallCNN, count_params

CHANNELS = (32, 64, 128)    # Decision 8 architecture (test fixture, mirrors train.channels)
N_CLASSES = 10              # taxonomy size for the parameter-count check
SIZE = 64                   # input side, pixels (mirrors image_size)
PARAMS_LO, PARAMS_HI = 80_000, 130_000  # "about 100k parameters" (Decision 8)


def test_param_count_about_100k():
    model = SmallCNN(channels=CHANNELS, dropout=0.2, n_classes=N_CLASSES)
    n = count_params(model)
    assert PARAMS_LO <= n <= PARAMS_HI, n


def test_output_shape():
    model = SmallCNN(channels=CHANNELS, dropout=0.2, n_classes=3)
    model.eval()
    x = torch.rand(5, 1, SIZE, SIZE)
    with torch.no_grad():
        logits = model(x)
    assert logits.shape == (5, 3)
    assert logits.dtype == torch.float32
    assert torch.isfinite(logits).all()


def test_rejects_bad_arguments():
    with pytest.raises(ValueError):
        SmallCNN(channels=(), n_classes=3)
    with pytest.raises(ValueError):
        SmallCNN(channels=CHANNELS, dropout=1.0, n_classes=3)
    with pytest.raises(ValueError):
        SmallCNN(channels=CHANNELS, n_classes=0)


def test_torchscript_roundtrip(tmp_path):
    torch.manual_seed(0)
    model = SmallCNN(channels=(8, 16, 32), dropout=0.3, n_classes=4)
    model.eval()
    x = torch.from_numpy(np.random.default_rng(0).random((6, 1, SIZE, SIZE), dtype=np.float32))
    with torch.no_grad():
        expected = model(x)
    path = tmp_path / "model.pt"
    torch.jit.script(model).save(str(path))
    loaded = torch.jit.load(str(path))
    loaded.eval()
    with torch.no_grad():
        got = loaded(x)
    assert got.shape == expected.shape
    assert torch.allclose(got, expected, atol=1e-6)
