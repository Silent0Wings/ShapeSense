"""Recalibrate BatchNorm statistics on real images, leaving every weight unchanged."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch import nn

from src.stage4_train.model import build_model
from src.stage4_train.sampling import to_float

CHUNK = 256


def recalibrated(model_path: str | Path, config: dict, n_classes: int, dropout: float,
                 images_u8: np.ndarray, device: str) -> nn.Module:
    """A copy of the saved model whose BatchNorm averages come from ``images_u8`` only."""
    model = build_model(config, n_classes, dropout)
    model.load_state_dict(torch.jit.load(str(model_path), map_location="cpu").state_dict())
    model.to(device).eval()
    norms = [m for m in model.modules() if isinstance(m, nn.BatchNorm2d)]
    for norm in norms:
        norm.reset_running_stats()
        norm.momentum = None    # a plain cumulative average
        norm.train()
    with torch.no_grad():
        for start in range(0, len(images_u8), CHUNK):
            model(torch.from_numpy(to_float(images_u8[start:start + CHUNK])).to(device))
    return model.eval()
