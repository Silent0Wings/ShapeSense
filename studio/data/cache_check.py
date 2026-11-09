"""Compare each stage's recorded input hashes with the files on disk.

Only safe inputs are recomputed. Some recorded inputs cover the test manifest or
whole image folders, so opening them here would read data this tool must not
touch; those rows are shown as recorded only.
"""

from __future__ import annotations

from src.common.config import resolve
from src.common.hashing import config_subtree_hash, sha256_path

from studio.context import config
from studio.data.tables import read_json

STAGE_CODE = {0: "src/stage0_infra", 1: "src/stage1_freeze", 2: "src/stage2_augment",
              3: "src/stage3_synth", 4: "src/stage4_train", 5: "src/stage5_eval",
              6: "src/stage6_report"}
SPLIT_KEYS = {"train_manifest": "train.csv", "val_manifest": "val.csv"}


def _live_hash(stage: int, key: str) -> str | None:
    """Current hash of a safe input, or None if this input is not recomputed."""
    if key == "code":
        return sha256_path(resolve(STAGE_CODE[stage]))
    if key == "common":
        return sha256_path(resolve("src/common"))
    if key.startswith("code."):
        return sha256_path(resolve(f"src/{key[5:]}"))
    if key.startswith("config."):
        return config_subtree_hash(config(), key[7:])
    if key in SPLIT_KEYS:
        return sha256_path(resolve(config()["paths"]["splits_dir"]) / SPLIT_KEYS[key])
    return None


def rows() -> list[dict]:
    out = []
    for stage in range(7):
        status = read_json(f"status{stage}")
        if status is None:
            continue
        for key, recorded in sorted(status.get("inputs", {}).items()):
            live = _live_hash(stage, key)
            state = "recorded" if live is None else ("match" if live == recorded else "changed")
            out.append({"stage": stage, "input": key, "recorded": str(recorded)[:19], "state": state})
    return out
