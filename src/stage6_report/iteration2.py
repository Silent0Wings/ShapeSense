"""Generated LaTeX for the report's CRISP-DM iteration 2 part.

Writes under ``artifacts/stage6/generated/``:
  ``iteration2_facts.tex``  macros from Stage 5, the search and the config;
  ``iteration_log.tex``     the findings per CRISP-DM step, from the iteration log;
  ``failures.tex``          every recorded failure and how it was handled;
  ``changes.tex``           every change and audit point, under its CRISP-DM step.
Every number in that part of the report comes from these two files.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.common.config import REPO_ROOT
from src.stage6_report.snippets import latex_escape

MISSING = "--"
ARM_MACROS = (("A0", "Azero"), ("A1", "Aone"), ("B", "B"), ("A2", "Atwo"))
STEP_NAMES = (("business", "Business Understanding"), ("data", "Data Understanding"), ("prep", "Data Preparation"),
              ("model", "Modeling"), ("eval", "Evaluation"), ("deploy", "Deployment"))
MACRO_NAMES = (
    "ItwoPrimary", "ItwoDelta", "ItwoCILo", "ItwoCIHi", "ItwoVerdict", "ItwoReads",
    "ItwoFreshN", "ItwoFreshDelta", "ItwoFreshCILo", "ItwoFreshCIHi", "ItwoFreshVerdict",
    "ItwoRotate", "ItwoRotateCap", "ItwoAtwoClean", "ItwoAtwoSynth", "ItwoBSynth",
    *(f"ItwoEns{m}" for _, m in ARM_MACROS), *(f"ItwoFresh{m}" for _, m in ARM_MACROS),
    *(f"ItwoVal{m}" for _, m in ARM_MACROS), *(f"ItwoTrials{m}" for _, m in ARM_MACROS),
    *(f"ItwoLoso{m}" for _, m in ARM_MACROS),
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _num(value: Any, digits: int = 2) -> str:
    return MISSING if value is None else f"{float(value):.{digits}f}"


def _pct(value: Any) -> str:
    return MISSING if value is None else f"{float(value) * 100:.0f}"


def _rotation(config: Mapping) -> tuple[str, str]:
    arm = config["arms"]["A1"]
    over = arm.get("overrides", {})
    caps = sorted(set(over.get("taxonomy.rotate_limit_deg", {}).values()))
    return (_num(over.get("augment.rotate_deg"), 0), _num(caps[0], 0) if caps else MISSING)


def collect(config: Mapping, artifacts_dir: Path) -> dict[str, str]:
    """Every macro of the iteration 2 part, MISSING when an input is absent."""
    art = Path(artifacts_dir)
    status = _load(art / "stage5" / "status.json")
    metrics = status.get("metrics", {})
    fresh = metrics.get("fresh_holdout") or {}
    winners = _load(art / "stage4" / "tuning_iter2" / "winners.json")
    ci = metrics.get("ci") or [None, None]
    fresh_ci = fresh.get("ci") or [None, None]
    rotate, cap = _rotation(config)
    macros = {
        "ItwoPrimary": latex_escape((metrics.get("primary") or {}).get("label") or MISSING),
        "ItwoDelta": _num(metrics.get("delta")), "ItwoCILo": _num(ci[0]), "ItwoCIHi": _num(ci[1]),
        "ItwoVerdict": latex_escape(metrics.get("verdict") or MISSING),
        "ItwoReads": str(status.get("checks", {}).get("test_reads", MISSING)),
        "ItwoFreshN": f"{fresh['n']:,}" if "n" in fresh else MISSING,
        "ItwoFreshDelta": _num(fresh.get("delta")), "ItwoFreshCILo": _num(fresh_ci[0]),
        "ItwoFreshCIHi": _num(fresh_ci[1]), "ItwoFreshVerdict": latex_escape(fresh.get("verdict") or MISSING),
        "ItwoRotate": rotate, "ItwoRotateCap": cap,
        "ItwoAtwoClean": _pct(config["arms"]["A2"].get("clean_fraction")),
        "ItwoAtwoSynth": _pct(config["arms"]["A2"].get("synthetic_fraction")),
        "ItwoBSynth": _pct(config["arms"]["B"].get("synthetic_fraction")),
    }
    loso: dict[str, list[float]] = {}
    for row in metrics.get("loso") or []:
        loso.setdefault(row["arm"], []).append(float(row["accuracy"]))
    for arm, name in ARM_MACROS:
        macros[f"ItwoEns{name}"] = _num((metrics.get("ensembles", {}).get(arm) or {}).get("macro_f1"), 1)
        macros[f"ItwoFresh{name}"] = _num((fresh.get("arms", {}).get(arm) or {}).get("macro_f1"), 1)
        macros[f"ItwoVal{name}"] = _num((winners.get("winners", {}).get(arm) or {}).get("mean_val_macro_f1"), 1)
        trials = winners.get("trials_per_arm", {}).get(arm)
        macros[f"ItwoTrials{name}"] = MISSING if trials is None else str(trials)
        macros[f"ItwoLoso{name}"] = _num(sum(loso[arm]) / len(loso[arm]) * 100, 1) if arm in loso else MISSING
    return macros


def log_table(repo_root: Path = REPO_ROOT, iteration: int = 2) -> str:
    """A two-column table of one iteration's findings per step."""
    log = _load(repo_root / "docs" / "crisp_dm" / "iteration_log.json")
    entry = next((i for i in log.get("iterations", []) if i["id"] == iteration), None)
    if entry is None:
        return ""
    rows = [f"{name} & {latex_escape(entry['findings'][key])} \\\\"
            for key, name in STEP_NAMES if key in entry["findings"]]
    return "\\begin{tabular}{p{0.18\\linewidth}p{0.74\\linewidth}}\n\\toprule\nStep & Finding \\\\\n\\midrule\n" \
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"


def failure_tables(repo_root: Path = REPO_ROOT, iteration: str | None = None) -> str:
    """One table per failure group, so that each fits on a page; ``iteration`` keeps only that one."""
    log = _load(repo_root / "docs" / "crisp_dm" / "iteration_log.json")
    groups: dict[str, list[str]] = {}
    for f in log.get("failures", []):
        if iteration is not None and f["iteration"] != iteration:
            continue
        groups.setdefault(f["group"], []).append(
            f"\\textbf{{{latex_escape(f['failure'])}}} {latex_escape(f['cause'])} & "
            f"{latex_escape(f['handled'])} & {latex_escape(f['state'])} \\\\")
    head = "\\begin{tabular}{p{0.34\\linewidth}p{0.46\\linewidth}p{0.11\\linewidth}}\n\\toprule\n"
    return "\n\\medskip\n\n".join(
        f"\\textit{{{latex_escape(name)}}}\n\n{head}What failed, and why & How it was handled & State \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n" for name, rows in groups.items())


def _table(columns: str, head: str, rows: list[str]) -> str:
    return f"\\begin{{tabular}}{{{columns}}}\n\\toprule\n{head} \\\\\n\\midrule\n" \
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"


def change_tables(repo_root: Path = REPO_ROOT) -> str:
    """Per CRISP-DM step: what changed, then what the outside reviews found."""
    log = _load(repo_root / "docs" / "crisp_dm" / "iteration_log.json")
    wide = "p{0.20\\linewidth}p{0.30\\linewidth}p{0.41\\linewidth}"
    review = "p{0.38\\linewidth}p{0.11\\linewidth}p{0.42\\linewidth}"
    parts = []
    for key, name in STEP_NAMES:
        changes = [f"{latex_escape(c['what'])} & {latex_escape(c['before'])} & {latex_escape(c['after'])} \\\\"
                   for c in log.get("changes", []) if c["step"] == key]
        audit = [f"{latex_escape(a['claim'])} & {latex_escape(a['verdict'])} & {latex_escape(a['action'])} \\\\"
                 for a in log.get("audit", []) if a["step"] == key]
        if changes:
            parts.append(f"\\textit{{{name}: changes}}\n\n" + _table(wide, "What changed & Before & After", changes))
        if audit:
            parts.append(f"\\textit{{{name}: outside review}}\n\n" + _table(review, "Point raised & Verdict & What was done", audit))
    return "\n\\medskip\n\n".join(parts)


def write_iteration2(config: Mapping, artifacts_dir: str | Path, repo_root: Path = REPO_ROOT) -> list[Path]:
    """Write both generated files; returns their paths."""
    out = Path(artifacts_dir) / "stage6" / "generated"
    out.mkdir(parents=True, exist_ok=True)
    macros = collect(config, Path(artifacts_dir))
    facts = "% Generated by Stage 6 (src/stage6_report/iteration2.py). Do not edit.\n" + "".join(
        f"\\providecommand{{\\{name}}}{{{macros[name]}}}\n" for name in MACRO_NAMES)
    (out / "iteration2_facts.tex").write_text(facts, encoding="utf-8")
    (out / "iteration_log.tex").write_text(log_table(repo_root), encoding="utf-8")
    (out / "failures.tex").write_text(failure_tables(repo_root), encoding="utf-8")
    (out / "changes.tex").write_text(change_tables(repo_root), encoding="utf-8")
    return [out / "iteration2_facts.tex", out / "iteration_log.tex", out / "failures.tex", out / "changes.tex"]
