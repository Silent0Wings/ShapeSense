"""The Stage 4 CNN (implementation.md Decision 8).

``SmallCNN``: one block of [Conv2d 3x3 (pad 1) -> BatchNorm2d -> ReLU ->
MaxPool2d 2] per entry of ``train.channels`` (four: 32 / 64 / 128 / 128),
global average pooling, Dropout and one Linear layer to the classes. About
242k parameters at 10 classes.

Input contract: float32 (N, 1, 64, 64) in [0, 1], white background = 1.0,
ink = 0.0 (``sampling.to_float`` = uint8 / 255). Output: logits (N, k).

Every architectural number (channels, dropout, input channels, class
count) is passed in by the caller from ``configs/pipeline.yaml#train``
and the taxonomy; nothing is hard-coded here except the kernel geometry
below, which is part of the Decision 8 architecture itself.
"""

from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import nn

CONV_KERNEL = 3   # pixels; Decision 8 "Conv 3x3"
CONV_PADDING = 1  # pixels; keeps the spatial size before the pool
POOL_SIZE = 2     # MaxPool2d factor per block
GAP_OUTPUT = 1    # AdaptiveAvgPool2d target: 1x1 (global average pool)


class SmallCNN(nn.Module):
    """Decision 8 CNN: 3 x [Conv-BN-ReLU-MaxPool] -> GAP -> Dropout -> Linear.

    Args:
        channels: output channels per block, e.g. ``(32, 64, 128, 128)``.
        dropout: dropout probability before the classifier.
        n_classes: number of output logits.
        in_channels: input image channels (``image_channels`` in config).

    ``forward(x)`` takes float32 (N, in_channels, S, S) and returns
    logits float32 (N, n_classes). TorchScript-compatible.
    """

    def __init__(self, channels: Sequence[int] = (32, 64, 128, 128), dropout: float = 0.2,
                 n_classes: int = 10, in_channels: int = 1) -> None:
        super().__init__()
        if len(channels) < 1:
            raise ValueError("channels must name at least one block")
        if not 0.0 <= float(dropout) < 1.0:
            raise ValueError(f"dropout must be in [0, 1), got {dropout}")
        if n_classes < 1:
            raise ValueError(f"n_classes must be >= 1, got {n_classes}")
        layers: list[nn.Module] = []
        c_in = int(in_channels)
        for c_out in channels:
            c_out = int(c_out)
            layers += [
                nn.Conv2d(c_in, c_out, kernel_size=CONV_KERNEL, padding=CONV_PADDING),
                nn.BatchNorm2d(c_out),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(POOL_SIZE),
            ]
            c_in = c_out
        self.features = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool2d(GAP_OUTPUT)
        self.dropout = nn.Dropout(float(dropout))
        self.classifier = nn.Linear(c_in, int(n_classes))
        self.n_classes = int(n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """(N, C, S, S) float32 in [0, 1] -> logits (N, n_classes)."""
        h = self.features(x)
        h = self.pool(h)
        h = torch.flatten(h, 1)
        h = self.dropout(h)
        return self.classifier(h)


def count_params(model: nn.Module, trainable_only: bool = True) -> int:
    """Number of (trainable) parameters in ``model``."""
    return int(sum(p.numel() for p in model.parameters()
                   if p.requires_grad or not trainable_only))


def build_model(config: dict, n_classes: int, dropout: float) -> SmallCNN:
    """``SmallCNN`` from ``config["train"]["channels"]`` and ``config["image_channels"]``.

    ``dropout`` is passed separately because it is a Decision 7 tuning
    hyperparameter (``hparams["dropout"]``), not a fixed config value.
    """
    return SmallCNN(channels=tuple(int(c) for c in config["train"]["channels"]),
                    dropout=float(dropout), n_classes=int(n_classes),
                    in_channels=int(config["image_channels"]))
