"""The trained CNN as a layer table, from the same config keys that build it."""

from __future__ import annotations

from studio.context import classes, config


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
