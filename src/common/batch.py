"""Batch format shared by the Stage 4 loader and its data suppliers.

This is the data-stream interface that Stages 2, 3 and 4 agree on at
the Stage 1 handoff. Images produced by Stages 2 and 3 must fit this
format before they enter a batch.
"""

from dataclasses import dataclass

import numpy as np

IMAGE_SIZE = 64           # pixels, square
IMAGE_CHANNELS = 1        # grayscale, black outline on white
SYNTHETIC_FRACTION = 0.3  # share of each training batch from Stage 3


@dataclass
class Batch:
    images: np.ndarray        # (N, 1, 64, 64) float32 in [0, 1]
    labels: np.ndarray        # (N,) int64, index into configs/taxonomy.yaml
    is_synthetic: np.ndarray  # (N,) bool, True for Stage 3 generator output
