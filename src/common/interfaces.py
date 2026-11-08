"""Shared contracts between pipeline stages (frozen at the Stage 1/2/3 hand-off).

Stages communicate only through these protocols and through artifacts on
disk (configs/, artifacts/). No stage imports another stage's internals;
Stage 4 depends on TransformFn and GeneratorFn, not on stage2 or stage3
code (it looks them up through src/common/registry).

Image format everywhere: uint8 (64, 64), single channel, black (0)
outline on white (255). The label is the index in configs/taxonomy.yaml.
"""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class TransformFn(Protocol):
    """Stage 2 contract: `stage2_augment.transform(img, label, rng)`."""

    def __call__(self, img: np.ndarray, label: int,
                 rng: np.random.Generator) -> np.ndarray:
        """Return an augmented copy of img (uint8 64x64).

        Never changes the label: shear and non-uniform scaling are
        disabled for the classes in taxonomy.no_shear_no_nonuniform_scale.
        All randomness comes from rng.
        """
        ...


@runtime_checkable
class GeneratorFn(Protocol):
    """Stage 3 contract: `stage3_synth.generate(label, rng)`."""

    def __call__(self, label: int, rng: np.random.Generator) -> np.ndarray:
        """Return a synthetic uint8 64x64 image of class `label`.

        Respects taxonomy.ambiguity_margins (ellipse axis ratio >= 1.2,
        rectangle side ratio >= 1.2, diamond angles clearly off 90 deg).
        All randomness comes from rng.
        """
        ...


class ModelHandle(Protocol):
    """Stage 4 contract: a trained model Stage 5 can evaluate."""

    def predict_proba(self, images: np.ndarray) -> np.ndarray:
        """Return (N, n_classes) probabilities for an (N, 1, 64, 64) float batch."""
        ...
