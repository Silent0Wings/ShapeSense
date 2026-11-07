"""Stage 6 — report, figures and packaging. Owner: ______

Contract (implementation.md, Stage 6):
  Input:  artifacts/ from all stages; results.json from Stage 5 is the
          only source of numbers for the report
  Output: Phase 2 report figures, updated Figure 2 TikZ, exported
          model (ONNX or TorchScript) with standardize.py bundled
  Done when: report compiles, every number traces to a Stage 5
             artifact, and the exported model loads and predicts on a
             fresh image. Figure work can start day 1; only results
             tables wait on Stage 5.
"""

import argparse

from src.common.config import load_config


def run(config: dict) -> None:
    raise NotImplementedError("Stage 6 not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
