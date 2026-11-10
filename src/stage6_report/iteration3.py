"""Generated LaTeX for the report's CRISP-DM iteration 3 part (Section L).

Writes under ``artifacts/stage6/generated/``:
  ``iteration3_facts.tex``     macros from Stage 5, the search and the config;
  ``iteration3_log.tex``       the findings per CRISP-DM step, from the iteration log;
  ``iteration3_failures.tex``  the failures of this iteration and how each was handled;
  ``iteration3_changes.tex``   every change and audit point, under its CRISP-DM step.
Every number in that part of the report comes from these files.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.common.config import REPO_ROOT
from src.stage6_report.iteration2 import MISSING, change_tables, failure_tables, log_table
from src.stage6_report.snippets import latex_escape

ARM_MACROS = (("A0", "Azero"), ("A1", "Aone"), ("B", "B"), ("A2", "Atwo"), ("P", "P"))
COMPARISON_MACROS = (("A1 vs A0", "AoneAzero"), ("B vs A0", "BAzero"), ("A2 vs A1", "AtwoAone"), ("A2 vs B", "AtwoB"))
CLEAN_PRIMARY = "A2 vs A0"
ITERATION_TAG = "Iteration 3"
MACRO_NAMES = (
    "IthreePrimary", "IthreeDelta", "IthreeCILo", "IthreeCIHi", "IthreeVerdict", "IthreeStrict",
    "IthreeSourceCILo", "IthreeSourceCIHi", "IthreeN", "IthreeLevels", "IthreeReads", "IthreeReadsExpected",
    "IthreeCleanDelta", "IthreeCleanCILo", "IthreeCleanCIHi",
    "IthreeTestDelta", "IthreeTestCILo", "IthreeTestCIHi", "IthreeTestVerdict",
    "IthreeFreshDelta", "IthreeFreshCILo", "IthreeFreshCIHi", "IthreeFreshVerdict",
    *(f"IthreeSec{m}Delta" for _, m in COMPARISON_MACROS), *(f"IthreeSec{m}P" for _, m in COMPARISON_MACROS),
    *(f"IthreeDamaged{m}" for _, m in ARM_MACROS), *(f"IthreeClean{m}" for _, m in ARM_MACROS),
    *(f"IthreeVal{m}" for _, m in ARM_MACROS), *(f"IthreeTrials{m}" for _, m in ARM_MACROS),
    *(f"IthreeLoso{m}" for _, m in ARM_MACROS),
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _num(value: Any, digits: int = 2) -> str:
    return MISSING if value is None else f"{float(value):.{digits}f}"


def _bounds(block: Mapping | None) -> list:
    return list((block or {}).get("ci") or [None, None])


def _yes_no(value: Any) -> str:
    return MISSING if value is None else ("yes" if value else "no")


def collect(artifacts_dir: Path) -> dict[str, str]:
    """Every macro of the iteration 3 part, MISSING when an input is absent."""
    art = Path(artifacts_dir)
    status = _load(art / "stage5" / "status.json")
    metrics = status.get("metrics", {})
    robust = metrics.get("robust") or {}
    winners = _load(art / "stage4" / "tuning_iter3" / "winners.json")
    checks = status.get("checks", {})
    ci, source = _bounds(robust), robust.get("ci_clustered_by_source") or [None, None]
    clean, test, fresh = (robust.get("clean") or {}).get(CLEAN_PRIMARY), metrics.get("reused_test"), metrics.get("fresh_holdout")
    macros = {
        "IthreePrimary": latex_escape(robust.get("label") or MISSING),
        "IthreeDelta": _num(robust.get("delta")), "IthreeCILo": _num(ci[0]), "IthreeCIHi": _num(ci[1]),
        "IthreeVerdict": latex_escape(robust.get("verdict") or MISSING),
        "IthreeStrict": _yes_no(robust.get("strict_pass")),
        "IthreeSourceCILo": _num(source[0]), "IthreeSourceCIHi": _num(source[1]),
        "IthreeN": f"{robust['n']:,}" if "n" in robust else MISSING,
        "IthreeLevels": str(len(robust["levels"])) if "levels" in robust else MISSING,
        "IthreeReads": str(checks.get("test_reads", MISSING)), "IthreeReadsExpected": str(checks.get("test_reads_expected", MISSING)),
    }
    for prefix, block, verdict in (("Clean", clean, False), ("Test", test, True), ("Fresh", fresh, True)):
        lo, hi = _bounds(block)
        macros[f"Ithree{prefix}Delta"] = _num((block or {}).get("delta"))
        macros[f"Ithree{prefix}CILo"], macros[f"Ithree{prefix}CIHi"] = _num(lo), _num(hi)
        if verdict:
            macros[f"Ithree{prefix}Verdict"] = latex_escape((block or {}).get("verdict") or MISSING)
    for label, name in COMPARISON_MACROS:
        row = (robust.get("secondary") or {}).get(label) or {}
        macros[f"IthreeSec{name}Delta"], macros[f"IthreeSec{name}P"] = _num(row.get("delta")), _num(row.get("p_holm"), 3)
    loso: dict[str, list[float]] = {}
    for row in metrics.get("loso") or []:
        loso.setdefault(row["arm"], []).append(float(row["accuracy"]))
    for arm, name in ARM_MACROS:
        ensemble = (robust.get("ensembles") or {}).get(arm) or {}
        macros[f"IthreeDamaged{name}"] = _num(ensemble.get("perturbed_macro_f1"), 1)
        macros[f"IthreeClean{name}"] = _num(ensemble.get("clean_macro_f1"), 1)
        macros[f"IthreeVal{name}"] = _num((winners.get("winners", {}).get(arm) or {}).get("mean_val_macro_f1"), 1)
        trials = winners.get("trials_per_arm", {}).get(arm)
        macros[f"IthreeTrials{name}"] = MISSING if trials is None else str(trials)
        macros[f"IthreeLoso{name}"] = _num(sum(loso[arm]) / len(loso[arm]) * 100, 1) if arm in loso else MISSING
    return macros


def write_iteration3(artifacts_dir: str | Path, repo_root: Path = REPO_ROOT) -> list[Path]:
    """Write the generated files of Section L; returns their paths."""
    out = Path(artifacts_dir) / "stage6" / "generated"
    out.mkdir(parents=True, exist_ok=True)
    macros = collect(Path(artifacts_dir))
    files = {
        "iteration3_facts.tex": "% Generated by Stage 6 (src/stage6_report/iteration3.py). Do not edit.\n" + "".join(
            f"\\providecommand{{\\{name}}}{{{macros[name]}}}\n" for name in MACRO_NAMES),
        "iteration3_log.tex": log_table(repo_root, iteration=3),
        "iteration3_failures.tex": failure_tables(repo_root, iteration=ITERATION_TAG),
        "iteration3_changes.tex": change_tables(repo_root),
    }
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return [out / name for name in files]
