"""Shared contracts between pipeline stages.

Stages communicate only through these protocols and through artifacts on
disk (configs/, artifacts/). No stage imports another stage's internals;
Stage 4 depends on TransformFn and GeneratorFn, not on stage2 or stage3
code.
"""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class TransformFn(Protocol):
    """Stage 2 contract: class-safe augmentation of one image."""

    def __call__(self, image: np.ndarray, label: int) -> np.ndarray:
        """Return an augmented copy of image (64x64, single channel).

        Must never change the label: shear and non-uniform scaling are
        disabled for circle, ellipse, square, rectangle and diamond.
        """
        ...


@runtime_checkable
class GeneratorFn(Protocol):
    """Stage 3 contract: render one synthetic image of a class."""

    def sample(self, label: int, rng: np.random.Generator) -> np.ndarray:
        """Return a synthetic 64x64 single-channel image for label.

        Must respect the ambiguity margins in configs/taxonomy.yaml
        (ellipse axis ratio >= 1.2, rectangle side ratio >= 1.2,
        diamond angles clearly off 90 deg).
        """
        ...


class ModelHandle(Protocol):
    """Stage 4 contract: a trained model Stage 5 can evaluate."""

    def predict(self, images: np.ndarray) -> np.ndarray:
        """Return predicted label indices for an (N, 1, 64, 64) batch."""
        ...
