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

from src.common.config import load_config
from src.common.registry import register


def build_transform(config: dict):
    """Return a TransformFn (see src/common/interfaces.py)."""
    raise NotImplementedError("Stage 2 not implemented yet")


def run(config: dict) -> None:
    register("augment", build_transform)
    raise NotImplementedError("Stage 2 QA not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
