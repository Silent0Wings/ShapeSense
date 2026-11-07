"""Stage 5 — evaluation and statistics. Owner: ______

Contract (implementation.md, Stage 5):
  Input:  artifacts/stage4/models/ (Stage 4),
          configs/splits/test.txt — the ONLY stage that reads the
          locked test split, once per trained model
  Output: artifacts/stage5/results.json, confusion matrices,
          statistical tests, pass/fail verdict
  Done when: verdict delivered against the locked criterion (B beats A1
             if macro-F1 improves >= 1 point with bootstrap CI
             excluding 0 and no class drops > 2 points), with McNemar
             tests and CIs for A0-A1, A1-B and A0-B.
"""

import argparse

from src.common.config import load_config


def run(config: dict) -> None:
    raise NotImplementedError("Stage 5 not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
