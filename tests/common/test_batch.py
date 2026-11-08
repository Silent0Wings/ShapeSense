"""E12: batch format reads its sizes from config (stages/stage_0.md R5)."""

import numpy as np
import pytest

from src.common import batch as batch_mod
from src.common.batch import Batch, BatchFormatError, validate_batch


def _good(n=4, size=64):
    return Batch(images=np.zeros((n, 1, size, size), np.float32),
                 labels=np.arange(n, dtype=np.int64),
                 is_synthetic=np.zeros(n, bool))


def test_no_hardcoded_constants():
    for name in ("SYNTHETIC_FRACTION", "IMAGE_SIZE", "IMAGE_CHANNELS"):
        assert not hasattr(batch_mod, name), f"{name} duplicates configs/pipeline.yaml"


def test_validate_batch_shape_dtype_range():
    validate_batch(_good(), image_size=64, channels=1)
    with pytest.raises(BatchFormatError, match="shape"):
        validate_batch(_good(size=32), image_size=64, channels=1)
    b = _good()
    b.images = b.images.astype(np.float64)
    with pytest.raises(BatchFormatError, match="dtype"):
        validate_batch(b, image_size=64, channels=1)
    b = _good()
    b.images[0, 0, 0, 0] = 2.0
    with pytest.raises(BatchFormatError, match="range"):
        validate_batch(b, image_size=64, channels=1)


def test_validate_batch_rejects_mask_length_mismatch():
    b = _good()
    b.is_synthetic = np.zeros(3, bool)
    with pytest.raises(BatchFormatError, match="is_synthetic"):
        validate_batch(b, image_size=64, channels=1)
