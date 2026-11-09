"""Live Stage 3 samples: the generator's own steps, keeping the drawn parameters."""

from __future__ import annotations

import numpy as np
from src.stage3_synth.render import render_outline
from src.stage3_synth.shapes import sample_params, vertices

from studio.context import classes
from studio.imaging import to_b64_png
from studio.ops.overrides import synth_config


def _plain(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def draw(label: int, cfg: dict, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
    """One image and its parameters, in the same steps as ``build_generator``."""
    name = classes()[int(label)]
    synth = cfg["synth"]
    params = sample_params(name, rng, synth, cfg["taxonomy"]["ambiguity_margins"])
    size = int(cfg["image_size"])
    image = render_outline(vertices(name, params, size), size, float(synth["stroke_px"]),
                           int(synth["supersample"]))
    return image, {k: _plain(v) for k, v in params.items()}


def preview(label: int, values: dict, seed: int, n: int) -> list[dict]:
    cfg = synth_config(values)
    out = []
    for i in range(n):
        image, params = draw(label, cfg, np.random.default_rng(seed + i))
        out.append({"image": to_b64_png(image), "params": params})
    return out
