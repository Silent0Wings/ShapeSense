"""Stage 2 — augmentation pipeline. Owner: ______

Contract (implementation.md, Stage 2):
  Input:  configs/splits/train.txt, configs/taxonomy.yaml
  Output: a TransformFn factory registered as "augment",
          artifacts/stage2/qa/ sample sheet
  Done when: zero label-changing artifacts in QA, and the per-class
             transform exclusions are enforced by config (shear and
             non-uniform scaling off for circle, ellipse, square,
             rectangle, diamond). Runs in parallel with Stage 3.
"""

import argparse

import numpy as np

from src.common.catalog import load_split_images
from src.common.config import class_names, load_config, resolve
from src.common.hashing import config_subtree_hash, sha256_obj, sha256_path
from src.common.registry import register
from src.stage2_augment.qa import QA_COLS, qa_sheet
from src.stage2_augment.transform import build_transform

STAGE = "stage2"
DEPENDS = ["stage0", "stage1"]


def inputs(config: dict) -> dict[str, str]:
    """Content hashes of everything this stage's outputs depend on."""
    return {
        "code": sha256_path(resolve("src/stage2_augment")),
        "common": sha256_path(resolve("src/common")),
        "config.augment": config_subtree_hash(config, "augment"),
        "taxonomy": sha256_obj(config["taxonomy"]),
        "train_manifest": sha256_path(resolve(config["paths"]["splits_dir"]) / "train.csv"),
    }


def run(config: dict) -> dict:
    """Register "augment", render the QA sheet and return outputs and metrics.

    Does not write status.json; the runner does. The QA verdict is set by the
    orchestrator after visual review, so it is reported as "pending_review".
    """
    register("augment", build_transform)
    transform_fn = build_transform(config)
    seed = config["seed_set"][0]
    names = class_names(config)

    images, labels = load_split_images(config, "train", per_class=QA_COLS, seed=seed)
    images_by_label = {label: list(images[labels == label]) for label in range(len(names))}

    qa_path = resolve(config["paths"]["artifacts_dir"]) / STAGE / "qa" / "qa_sheet.png"
    out = qa_sheet(images_by_label, names, transform_fn, np.random.default_rng(seed), qa_path)

    disabled_for = list(config["taxonomy"]["no_shear_no_nonuniform_scale"])
    return {
        "outputs": [out.as_posix()],
        "metrics": {
            "rules_in_force": {
                "disabled_for": disabled_for,
                "disabled_transforms": ["shear", "non_uniform_scale"],
            },
            "qa": "pending_review",
        },
        "checks": {"disable_list_from_config": True},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
