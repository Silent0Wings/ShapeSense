"""The trained CNN as a layer table, from the same config keys that build it."""

from __future__ import annotations

from studio.context import classes, config


CONV_KERNEL = 3    # mirrors src/stage4_train/model.py; a test ties them together
POOL_SIZE = 2


def network() -> list[dict]:
    """Every operation of the real model, in order, with its shapes and learned numbers."""
    cfg = config()
    channels = [int(c) for c in cfg["train"]["channels"]]
    size = int(cfg["image_size"])
    c_in = int(cfg["image_channels"])
    seen, jump = 1, 1
    ops = [{"id": "input", "group": "Input", "kind": "input", "name": "Image", "input": None,
            "output": [c_in, size, size], "params": 0, "sees": seen}]

    def add(block: str, kind: str, name: str, before: list[int], after: list[int], params: int) -> None:
        ops.append({"id": f"{block}-{kind}", "group": block, "kind": kind, "name": name, "input": before,
                    "output": after, "params": params, "sees": seen})

    for n, c_out in enumerate(channels, start=1):
        block = f"Block {n}"
        seen += (CONV_KERNEL - 1) * jump
        add(block, "conv", "Conv 3x3", [c_in, size, size], [c_out, size, size], c_in * c_out * CONV_KERNEL ** 2 + c_out)
        add(block, "batchnorm", "BatchNorm", [c_out, size, size], [c_out, size, size], 2 * c_out)
        add(block, "relu", "ReLU", [c_out, size, size], [c_out, size, size], 0)
        seen += (POOL_SIZE - 1) * jump
        jump *= POOL_SIZE
        add(block, "maxpool", "MaxPool 2", [c_out, size, size], [c_out, size // POOL_SIZE, size // POOL_SIZE], 0)
        size //= POOL_SIZE
        c_in = c_out
    seen = None
    add("Global pool", "globalpool", "Average pool", [c_in, size, size], [c_in], 0)
    add("Dropout", "dropout", "Dropout", [c_in], [c_in], 0)
    n_classes = len(classes())
    add("Classifier", "linear", "Linear", [c_in], [n_classes], c_in * n_classes + n_classes)
    return ops


def recipes() -> list[dict]:
    """What each arm's training batch holds, mirroring src/stage4_train/sampling.py."""
    cfg = config()
    train = cfg["train"]
    batch = int(train["batch_size"])
    out = []
    for arm, arm_cfg in cfg["arms"].items():
        share = float(arm_cfg.get("synthetic_fraction", cfg["synthetic_fraction"]))
        synthetic = int(round(batch * share)) if arm_cfg["synthetic"] else 0
        real = batch - synthetic
        clean = int(round(batch * float(arm_cfg.get("clean_fraction", 0.0)))) if arm_cfg["augment"] else real
        pretrain = int(float(arm_cfg.get("pretrain_fraction", 0.0)) * int(train["max_epochs"]))
        out.append({"arm": arm, "clean": clean, "augmented": real - clean, "synthetic": synthetic,
                    "pretrain_epochs": pretrain, "pretrain_synthetic": batch if pretrain else 0,
                    "lr": arm_cfg["hparams"]["lr"], "dropout": arm_cfg["hparams"]["dropout"]})
    return out


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
