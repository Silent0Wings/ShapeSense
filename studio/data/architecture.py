"""The trained CNN as a layer table, from the same config keys that build it."""

from __future__ import annotations

from studio.context import classes, config


def layers() -> list[dict]:
    """Shape after each block for the real model (src/stage4_train/model.py)."""
    train = config()["train"]
    size = int(config()["image_size"])
    out = [{"layer": "Input", "detail": "grayscale, white background", "shape": f"1 x {size} x {size}"}]
    for i, channels in enumerate(train["channels"], start=1):
        size //= 2
        out.append({"layer": f"Block {i}", "detail": "Conv 3x3, BatchNorm, ReLU, MaxPool 2",
                    "shape": f"{channels} x {size} x {size}"})
    out.append({"layer": "Global average pool", "detail": "drops position", "shape": str(train["channels"][-1])})
    out.append({"layer": "Dropout + linear", "detail": f"{train['dropout']} config default, tuned per Decision 7",
                "shape": f"{len(classes())} logits"})
    return out
