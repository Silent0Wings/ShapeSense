"""The committed pipeline config, loaded once and never mutated."""

from __future__ import annotations

import functools

from src.common.config import class_names, load_config


@functools.lru_cache(maxsize=1)
def config() -> dict:
    """Merged, validated configs/pipeline.yaml. Deep-copy before changing anything."""
    return load_config()


@functools.lru_cache(maxsize=1)
def classes() -> tuple[str, ...]:
    return tuple(class_names(config()))


def no_shear_classes() -> tuple[str, ...]:
    """Classes where shear and non-uniform scale would change the label."""
    return tuple(config()["taxonomy"]["no_shear_no_nonuniform_scale"])


def confusion_pairs() -> tuple[tuple[str, str], ...]:
    return tuple((a, b) for a, b in config()["evaluation"]["confusion_pairs"])
