"""Stage 1 — data freeze and splits. Owner: ______

Contract (implementation.md, Stage 1):
  Input:  data_set/unified/catalog.sqlite, scripts/
  Output: configs/splits/{train,val,test}.txt, filtered catalog,
          artifacts/stage1/split_stats.json, source-classifier result
  Done when: leakage assertions pass (no image_id in two splits, no
             pHash group spanning splits), counts reconcile with report
             Table 2, catalog hash + seed recorded in build_log.txt.
  The test split is locked here; only Stage 5 may read it.
"""

import argparse

from src.common.config import load_config


def run(config: dict) -> None:
    raise NotImplementedError("Stage 1 not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
