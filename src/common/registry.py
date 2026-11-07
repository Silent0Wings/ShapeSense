"""Name-based registry: stages look each other up by config name, never
by import. Stage 4 asks for the names listed in configs/pipeline.yaml
("augment", "synthetic"), so arms A0/A1/B differ only in config.
"""

from typing import Any, Callable

_REGISTRY: dict[str, Callable[..., Any]] = {}


def register(name: str, factory: Callable[..., Any]) -> None:
    """Register a factory (e.g. stage2's build_transform) under a name."""
    _REGISTRY[name] = factory


def get(name: str) -> Callable[..., Any]:
    if name not in _REGISTRY:
        raise KeyError(
            f"nothing registered as {name!r}; available: {available()}"
        )
    return _REGISTRY[name]


def available() -> list[str]:
    return sorted(_REGISTRY)
