"""Stage 3 public API: generate(label, rng) and its factory build_generator(config)."""

from .generate import build_generator, generate

__all__ = ["build_generator", "generate"]
