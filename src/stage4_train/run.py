"""Stage 4 — training: baselines + arms A0 / A1 / B. Owner: ______

Contract (implementation.md, Stage 4):
  Input:  configs/splits/ (Stage 1), "augment" module (Stage 2),
          "synthetic" module (Stage 3) — both via src/common/registry,
          never by direct import
  Output: artifacts/stage4/models/ (all arms x seeds), training logs,
          validation curves
  Done when: every arm x seed is trained with identical architecture,
             optimizer and seed set; validation-based selection
             recorded; the test split untouched.
  A0 can start before Stages 2 and 3 finish (no modules registered).
"""

import argparse

from src.common.config import load_config


def run(config: dict) -> None:
    raise NotImplementedError("Stage 4 not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
