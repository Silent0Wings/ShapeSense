"""Stage 3 public generator: generate(label, rng) -> uint8 (image_size, image_size).

All randomness comes from the rng argument. Nothing is written to disk.
The config is read once when a generator is built, never per call.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from src.common.config import class_names, load_default_config

from .render import render_outline
from .shapes import SUPPORTED_CLASSES, sample_params, vertices

GeneratorCallable = Callable[[int, np.random.Generator], np.ndarray]

_DEFAULT_GENERATOR: GeneratorCallable | None = None


class ParamLog:
    """Running min and max of every sampled parameter, per class.

    Feeds artifacts/stage3/param_ranges.json. Array-valued parameters are
    logged over all their entries.
    """

    def __init__(self) -> None:
        self._ranges: dict[str, dict[str, list[float]]] = {}

    def record(self, name: str, params: dict) -> None:
        """Fold one sampled params dict for class `name` into the ranges."""
        bucket = self._ranges.setdefault(name, {})
        for key, value in params.items():
            arr = np.asarray(value, dtype=np.float64)
            lo, hi = float(arr.min()), float(arr.max())
            if key in bucket:
                old_lo, old_hi = bucket[key]
                bucket[key] = [min(old_lo, lo), max(old_hi, hi)]
            else:
                bucket[key] = [lo, hi]

    def to_dict(self) -> dict[str, dict[str, list[float]]]:
        """{class: {param: [min, max]}} with plain Python floats."""
        return {n: {k: list(v) for k, v in p.items()} for n, p in self._ranges.items()}


def _make_generator(config: dict, log: ParamLog | None) -> GeneratorCallable:
    names = class_names(config)
    unknown = [n for n in names if n not in SUPPORTED_CLASSES]
    if unknown:
        raise ValueError(f"no geometry for classes {unknown}")
    synth = config["synth"]
    margins = config["taxonomy"]["ambiguity_margins"]
    size = int(config["image_size"])
    stroke_px = float(synth["stroke_px"])
    supersample = int(synth["supersample"])
    n_classes = len(names)

    def _generate(label: int, rng: np.random.Generator) -> np.ndarray:
        idx = int(label)
        if not 0 <= idx < n_classes:
            raise ValueError(f"label {label} is outside 0..{n_classes - 1}")
        name = names[idx]
        params = sample_params(name, rng, synth, margins)
        if log is not None:
            log.record(name, params)
        return render_outline(vertices(name, params, size), size, stroke_px, supersample)

    return _generate


def build_generator(config: dict) -> GeneratorCallable:
    """Return generate(label, rng) bound to `config`.

    Args:
        config: merged pipeline config (src.common.config.load_config()).

    Returns:
        Callable taking (label: int, rng: np.random.Generator) and returning
        uint8 (image_size, image_size), values 0 or 255.

    Raises:
        ValueError: a class in the taxonomy has no geometry.
    """
    return _make_generator(config, None)


def build_generator_with_log(config: dict) -> tuple[GeneratorCallable, ParamLog]:
    """Like build_generator, and also return the ParamLog that records every call."""
    log = ParamLog()
    return _make_generator(config, log), log


def generate(label: int, rng: np.random.Generator) -> np.ndarray:
    """Draw one synthetic image of class `label` from the default config.

    Args:
        label: taxonomy index 0..9.
        rng: the only source of randomness.

    Returns:
        uint8 (image_size, image_size) with values 0 (ink) or 255 (background).
    """
    global _DEFAULT_GENERATOR
    if _DEFAULT_GENERATOR is None:
        _DEFAULT_GENERATOR = build_generator(load_default_config())
    return _DEFAULT_GENERATOR(label, rng)
