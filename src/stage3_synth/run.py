"""Stage 3 — synthetic generator. Owner: ______

Contract (implementation.md, Stage 3):
  Input:  configs/taxonomy.yaml (classes + ambiguity margins)
  Output: a GeneratorFn factory registered as "synthetic",
          artifacts/stage3/qa/ sample sheet, parameter-range log
  Done when: QA passes, margins enforced and logged, and the generator
             can supply ~30% of a batch on demand. Rendered on the fly,
             never stored. Runs in parallel with Stage 2.
"""

import argparse

from src.common.config import load_config
from src.common.registry import register


def build_generator(config: dict):
    """Return a GeneratorFn (see src/common/interfaces.py)."""
    raise NotImplementedError("Stage 3 not implemented yet")


def run(config: dict) -> None:
    register("synthetic", build_generator)
    raise NotImplementedError("Stage 3 QA not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
