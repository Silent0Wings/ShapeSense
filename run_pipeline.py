"""Root pipeline: wires the six stages in dependency order.

    python run_pipeline.py                  # run everything implemented so far
    python run_pipeline.py --stages 1 4     # run selected stages

Stages are self-contained under src/stageN_*/ and expose run(config).
Stages 2 and 3 are independent and could run in parallel; they run
sequentially here for simplicity. Unimplemented stages are skipped with
a warning, so the pipeline stays runnable while owners build their
modules.
"""

import argparse
import importlib
import sys

from src.common.config import load_config

STAGES = {
    1: "src.stage1_freeze",
    2: "src.stage2_augment",
    3: "src.stage3_synth",
    4: "src.stage4_train",
    5: "src.stage5_eval",
    6: "src.stage6_report",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--stages", type=int, nargs="*",
                        default=list(STAGES), choices=list(STAGES),
                        metavar="N")
    args = parser.parse_args()

    config = load_config(args.config)
    for n in args.stages:
        name = STAGES[n]
        print(f"--- Stage {n} ({name}) ---")
        run = importlib.import_module(f"{name}.run").run
        try:
            run(config)
        except NotImplementedError as e:
            print(f"skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
