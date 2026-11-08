"""Batch format shared by the Stage 4 loader and its data suppliers.

This is the data-stream interface that Stages 2, 3 and 4 agree on at
the Stage 1 handoff. Images produced by Stages 2 and 3 must fit this
format before they enter a batch. Sizes come from configs/pipeline.yaml
(`image_size`, `image_channels`); nothing here duplicates them.
"""

from dataclasses import dataclass

import numpy as np


class BatchFormatError(ValueError):
    """Raised when a batch does not match the shared format."""


@dataclass
class Batch:
    images: np.ndarray        # (N, C, S, S) float32 in [0, 1]
    labels: np.ndarray        # (N,) int64, index into configs/taxonomy.yaml
    is_synthetic: np.ndarray  # (N,) bool, True for Stage 3 generator output


def validate_batch(batch: Batch, image_size: int, channels: int) -> None:
    """Raise BatchFormatError unless `batch` matches the shared format."""
    imgs = batch.images
    n = len(batch.labels)
    if imgs.shape != (n, channels, image_size, image_size):
        raise BatchFormatError(
            f"images shape {imgs.shape}, expected {(n, channels, image_size, image_size)}")
    if imgs.dtype != np.float32:
        raise BatchFormatError(f"images dtype {imgs.dtype}, expected float32")
    if imgs.size and (imgs.min() < 0.0 or imgs.max() > 1.0):
        raise BatchFormatError("images range must be [0, 1]")
    if batch.labels.dtype != np.int64:
        raise BatchFormatError(f"labels dtype {batch.labels.dtype}, expected int64")
    if batch.is_synthetic.shape != (n,) or batch.is_synthetic.dtype != bool:
        raise BatchFormatError("is_synthetic must be a bool array with one entry per image")
