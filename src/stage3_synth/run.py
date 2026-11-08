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
import json
import time

import numpy as np

from src.common.config import class_names, load_config, resolve
from src.common.hashing import config_subtree_hash, sha256_obj, sha256_path
from src.common.registry import register

from .generate import build_generator, build_generator_with_log
from .qa import qa_sheet
from .shapes import STAR_INNER_RATIO_CEILING

STAGE = "stage3"
DEPENDS = ["stage0"]
SAMPLES_PER_CLASS = 2000  # images per class rendered for the parameter log
THROUGHPUT_CALLS = 5000  # generate() calls timed, single-threaded, labels cycled
# Images per second, single-threaded. Source: stages/stage_3.md R8 (absolute
# target so Stage 4's batch of ~77 synthetic images fits in one CPU step).
THROUGHPUT_TARGET_IMG_S = 2000
QA_PER_CLASS = 10  # samples per class on the QA sheet
PARAM_RANGES_FILE = "param_ranges.json"


def inputs(config: dict) -> dict:
    """Hashes of everything that determines this stage's outputs (status.json inputs)."""
    return {
        "code": sha256_path(resolve("src/stage3_synth")),
        "common": sha256_path(resolve("src/common")),
        "config.synth": config_subtree_hash(config, "synth"),
        "taxonomy": sha256_obj(config["taxonomy"]),
        "image_size": sha256_obj(config["image_size"]),
    }


def run(config: dict) -> dict:
    """Render QA sheet, log parameter ranges and measure throughput.

    Writes artifacts/stage3/qa/qa_sheet.png and artifacts/stage3/param_ranges.json.
    Does not write status.json; the runner does that through common.status.
    """
    register("synthetic", build_generator)
    names = class_names(config)
    n_classes = len(names)
    stage_dir = resolve(config["paths"]["artifacts_dir"]) / STAGE
    qa_path = stage_dir / "qa" / "qa_sheet.png"
    ranges_path = stage_dir / PARAM_RANGES_FILE
    rng = np.random.default_rng(int(config["seed_set"][0]))

    plain = build_generator(config)
    qa_sheet(plain, names, rng, qa_path, per_class=QA_PER_CLASS)

    logged, param_log = build_generator_with_log(config)
    for label in range(n_classes):
        for _ in range(SAMPLES_PER_CLASS):
            logged(label, rng)
    margins = config["taxonomy"]["ambiguity_margins"]
    margins_in_force = {k: float(v) for k, v in margins.items()}
    margins_in_force["star_inner_ratio_max"] = STAR_INNER_RATIO_CEILING
    margins_from_config = all(
        margins_in_force[k] == float(margins[k]) for k in margins)
    ranges = param_log.to_dict()
    ranges["margins_in_force"] = margins_in_force
    ranges_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ranges_path, "w", encoding="utf-8") as f:
        json.dump(ranges, f, indent=2)
        f.write("\n")

    start = time.perf_counter()
    for i in range(THROUGHPUT_CALLS):
        plain(i % n_classes, rng)
    elapsed = time.perf_counter() - start
    throughput = THROUGHPUT_CALLS / elapsed
    throughput_ok = throughput >= THROUGHPUT_TARGET_IMG_S

    result = {
        "status": "passed" if throughput_ok else "failed",
        "outputs": [str(qa_path), str(ranges_path)],
        "metrics": {
            "throughput_img_s": round(throughput, 1),
            "throughput_target_img_s": THROUGHPUT_TARGET_IMG_S,
            "margins_in_force": margins_in_force,
            "qa": "pending_review",
        },
        "checks": {
            "throughput_ok": throughput_ok,
            "margins_from_config": margins_from_config,
        },
    }
    if not throughput_ok:
        result["error"] = (f"throughput {throughput:.0f} img/s is below the "
                           f"{THROUGHPUT_TARGET_IMG_S} img/s target")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
