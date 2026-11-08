"""Baseline feature extractors shared by Stage 4 (training) and Stage 5
(evaluation), so Stage 5 can predict with the saved baselines without
importing Stage 4 (implementation.md § Separation of concerns 1)."""

import numpy as np
from skimage.feature import hog

ORIENTATIONS = 9  # HOG orientation bins
CELLS_PER_BLOCK = 2  # HOG cells per block side
PIXEL_SCALE = 255.0  # uint8 range -> [0, 1]


def pixel_features(images_u8: np.ndarray) -> np.ndarray:
    """Flatten uint8 (N, H, W) images to float32 (N, H*W) scaled to [0, 1]."""
    n, height, width = images_u8.shape
    return images_u8.reshape(n, height * width).astype(np.float32) / np.float32(PIXEL_SCALE)


def hog_features(images_u8: np.ndarray, pixels_per_cell: int) -> np.ndarray:
    """HOG descriptor per uint8 (N, H, W) image, returned as float32 (N, D).

    Each image is scaled to [0, 1] before skimage.feature.hog.
    """
    if images_u8.shape[0] == 0:
        return np.empty((0, 0), dtype=np.float32)
    cell = (pixels_per_cell, pixels_per_cell)
    block = (CELLS_PER_BLOCK, CELLS_PER_BLOCK)
    rows = [
        hog(
            img.astype(np.float32) / PIXEL_SCALE,
            orientations=ORIENTATIONS,
            pixels_per_cell=cell,
            cells_per_block=block,
            feature_vector=True,
        )
        for img in images_u8
    ]
    return np.asarray(rows, dtype=np.float32)
