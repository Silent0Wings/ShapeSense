"""Live Stage 2 previews, produced by the real ``build_transform``."""

from __future__ import annotations

import numpy as np
from src.stage2_augment import build_transform

from studio.imaging import to_b64_png
from studio.ops.overrides import augment_config


def variants(image: np.ndarray, label: int, values: dict, seed: int, n: int,
             uncapped: bool = False) -> list[np.ndarray]:
    """``n`` augmented versions of one image; each variant has its own seed.

    The draw order inside the transform is fixed, so moving one slider with the
    same seed leaves the other random choices where they were.
    """
    transform = build_transform(augment_config(values, uncapped))
    return [transform(image, int(label), np.random.default_rng(seed + i)) for i in range(n)]


def preview(image: np.ndarray, label: int, values: dict, seed: int, n: int, uncapped: bool = False) -> dict:
    out = variants(image, label, values, seed, n, uncapped)
    return {"original": to_b64_png(image), "variants": [to_b64_png(v) for v in out]}
