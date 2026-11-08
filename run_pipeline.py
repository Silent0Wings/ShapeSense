"""Root pipeline: guards first, then every stage whose inputs changed.

    python run_pipeline.py                 # every stage whose inputs changed
    python run_pipeline.py --stages 3      # one stage (and its dependencies)
    python run_pipeline.py --check         # guards only: imports + contract tests
    python run_pipeline.py --dashboard     # open the read-only dashboard
    python run_pipeline.py --demo          # draw a shape, press Infer (export/ only)
    python run_pipeline.py --force         # ignore the hash cache, rerun everything

One run_id is minted per invocation and shared by every stage. Each stage
records the hashes of its inputs in artifacts/stageN/status.json; a stage
whose recorded hashes all match (and whose last status is `passed`) is
skipped. A failing guard stops the run before any stage executes; a
failing stage stops the run before later stages.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from src.common import status as st
from src.common.config import REPO_ROOT, load_config, resolve

STAGES = {
    0: "src.stage0_infra.run",
    1: "src.stage1_freeze.run",
    2: "src.stage2_augment.run",
    3: "src.stage3_synth.run",
    4: "src.stage4_train.run",
    5: "src.stage5_eval.run",
    6: "src.stage6_report.run",
}


def stage_number(name: str) -> int:
    return int(name.removeprefix("stage"))


def dependency_closure(requested: list[int], depends: dict[int, list[int]]) -> list[int]:
    """Requested stages plus everything they depend on, in pipeline order."""
    seen: set[int] = set()

    def visit(n: int) -> None:
        if n in seen:
            return
        seen.add(n)
        for d in depends.get(n, []):
            visit(d)

    for n in requested:
        visit(n)
    return sorted(seen)


def _scripts_dir() -> Path:
    return Path(sys.executable).parent


def run_guards(config: dict) -> dict[str, bool]:
    """import-linter + contract tests. Writes artifacts/stage0/guards.json."""
    results = {}
    lint = [sys.executable, "-c",
            "import sys; from importlinter.cli import lint_imports_command as c; "
            "sys.argv=['lint-imports']; c()"]
    results["import_linter"] = subprocess.run(lint, cwd=REPO_ROOT).returncode == 0
    tests = [sys.executable, "-m", "pytest", "tests/contracts", "-q", "-p", "no:cacheprovider"]
    results["contract_tests"] = subprocess.run(tests, cwd=REPO_ROOT).returncode == 0
    out = resolve(config["paths"]["artifacts_dir"]) / "stage0" / "guards.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def run_stages(config: dict, numbers: list[int], *, force: bool,
               load: Callable[[str], object] = importlib.import_module,
               artifacts_dir: Path | None = None,
               log: Callable[[str], None] = print) -> dict[int, str]:
    """Run the given stages in order. Returns {stage: 'passed'|'cached'|...}."""
    artifacts = artifacts_dir or resolve(config["paths"]["artifacts_dir"])
    outcome: dict[int, str] = {}
    for n in numbers:
        mod = load(STAGES[n])
        name = getattr(mod, "STAGE", f"stage{n}")
        inputs = mod.inputs(config)
        if not force and st.is_cached(name, inputs, artifacts_dir=artifacts):
            log(f"--- Stage {n}: cached (inputs unchanged) ---")
            outcome[n] = "cached"
            continue
        log(f"--- Stage {n} ({STAGES[n]}) ---")
        result = st.run_stage(name, lambda: mod.run(config), inputs=inputs,
                              artifacts_dir=artifacts)
        outcome[n] = result["status"]
        log(f"Stage {n}: {result['status']}")
        if result["status"] == "failed":
            log(f"Stage {n} failed; later stages not run.")
            break
    return outcome


def _launch(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=REPO_ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--stages", type=int, nargs="*", choices=list(STAGES), metavar="N")
    parser.add_argument("--check", action="store_true", help="run the guards only")
    parser.add_argument("--dashboard", action="store_true", help="open the dashboard")
    parser.add_argument("--demo", action="store_true", help="open the draw-and-infer demo")
    parser.add_argument("--force", action="store_true", help="ignore the hash cache")
    args = parser.parse_args(argv)

    os.chdir(REPO_ROOT)
    if args.dashboard:
        return _launch([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
    if args.demo:
        return _launch([sys.executable, "-m", "demo.app"])

    os.environ[st.RUN_ID_ENV] = st.new_run_id()
    config = load_config(resolve(args.config))
    print(f"run_id {os.environ[st.RUN_ID_ENV]}")

    guards = run_guards(config)
    print(f"guards: {guards}")
    if not all(guards.values()):
        print("Guard failure: no stage was run.", file=sys.stderr)
        return 1
    if args.check:
        return 0

    depends = {n: [stage_number(d) for d in getattr(importlib.import_module(m), "DEPENDS", [])]
               for n, m in STAGES.items()}
    numbers = dependency_closure(args.stages or list(STAGES), depends)
    outcome = run_stages(config, numbers, force=args.force)
    return 1 if "failed" in outcome.values() else 0


if __name__ == "__main__":
    sys.exit(main())
