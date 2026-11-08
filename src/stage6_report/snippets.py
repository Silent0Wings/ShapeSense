"""Generated LaTeX snippets for the Phase 2 report (stages/stage_6.md R5, R7; plan 35).

Writes two files under ``artifacts/stage6/generated/``:

* ``param_ranges.tex`` — a booktabs table of the generator's realized parameter
  ranges per class, read from ``artifacts/stage3/param_ranges.json``, plus the
  ambiguity margins that were in force (R7).
* ``pipeline_facts.tex`` — ``\\providecommand`` macros (``\\StepsPerEpoch``,
  ``\\TestReads``, ``\\Verdict`` ...) read from the status.json / JSON files of
  Stages 1, 3, 4 and 5 and from ``export/model_card.json``.

A missing upstream file never breaks the report: every macro it would have
filled becomes ``--`` and the file is recorded in the returned ``missing``
list. Pure helpers (``fmt_int``, ``fmt_float``, ``fmt_auto``, ``latex_escape``,
``param_ranges_table``, ``pipeline_facts_tex``) take plain values and return
strings; only ``collect_facts`` / ``write_snippets`` touch the file system.
Stage 6 never reads the test split.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from src.common.config import class_names

GENERATED_SUBDIR = "generated"          # under artifacts/stage6/
PARAM_RANGES_TEX = "param_ranges.tex"
PIPELINE_FACTS_TEX = "pipeline_facts.tex"
MISSING_VALUE = "--"                    # printed wherever an upstream value is absent
THOUSANDS_SEPARATOR = "{,}"             # LaTeX thin thousands separator (same as Stage 1)
FLOAT_DECIMALS = 2                      # default decimals for fmt_float
RANGE_DECIMALS = 2                      # decimals for generator parameter bounds
PCT_SCALE = 100.0                       # fraction -> percent
PCT_DECIMALS = 1                        # percent values (seed disagreement)
VAL_F1_DECIMALS = 3                     # val_macro_f1 from model_card.json, printed as recorded
YES = "yes"
NO = "no"

# Upstream artifacts, relative to artifacts_dir (export/model_card.json is relative
# to the export dir). Every one is optional: absent -> "--" and a `missing` entry.
STAGE1_STATUS = Path("stage1") / "status.json"
STAGE1_SOURCE_CLASSIFIER = Path("stage1") / "source_classifier.json"
STAGE3_STATUS = Path("stage3") / "status.json"
STAGE3_PARAM_RANGES = Path("stage3") / "param_ranges.json"
STAGE4_STATUS = Path("stage4") / "status.json"
STAGE4_LOADER_BENCHMARK = Path("stage4") / "loader_benchmark.json"
STAGE4_SEED_DISAGREEMENT = Path("stage4") / "seed_disagreement.json"
STAGE5_STATUS = Path("stage5") / "status.json"
EXPORT_MODEL_CARD = "model_card.json"

MARGINS_KEY = "margins_in_force"        # key Stage 3 adds next to the per-class ranges
ARM_A0, ARM_A1, ARM_B = "A0", "A1", "B"

# Every macro pipeline_facts.tex defines. phase2_report.tex carries a "--"
# \providecommand fallback for each one (tests/stage6/test_snippets.py checks that).
MACRO_NAMES: tuple[str, ...] = (
    # from configs/pipeline.yaml (single source of truth for plan constants)
    "BatchSize", "SeedsPerArm", "SyntheticSharePct", "MaxEpochs", "Patience", "TuningArm",
    "TuningLRs", "TuningDropouts", "Alpha", "NBoot", "MinGainPoints", "MaxClassDropPoints",
    "CILevelPct", "PhashHammingMax", "SplitRatios", "ImageSize", "NumClasses", "NumRuns",
    "PowerLimitPoints", "ShortcutTriggerPoints", "GemstoneFilterSetting",
    # Stage 1
    "ShortcutDetected", "SourceGainPoints", "SourceClassifierAccPct", "SourceMajorityRatePct",
    # Stage 3
    "ThroughputSynth", "ThroughputTarget",
    # Stage 4
    "StepsPerEpoch", "TunedLR", "TunedDropout", "RealDrawsA", "RealDrawsB", "SynthDrawsB",
    "LoaderImagesPerSec", "SeedDisagreementAzero", "SeedDisagreementAone", "SeedDisagreementB",
    "LosoRequired", "LosoHoldoutSource",
    # Stage 5
    "Verdict", "TestReads", "RunId",
    # export bundle
    "ExportedRun", "ExportedArm", "ExportedValFone",
)

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


# --------------------------------------------------------------------------- #
# Pure formatting helpers
# --------------------------------------------------------------------------- #


def latex_escape(text: Any) -> str:
    """Escape the ten LaTeX special characters; ``None`` becomes ``--``."""
    if text is None:
        return MISSING_VALUE
    return "".join(_LATEX_SPECIALS.get(ch, ch) for ch in str(text))


def fmt_int(n: Any) -> str:
    """``12761 -> '12{,}761'``; ``None`` -> ``--``."""
    if n is None:
        return MISSING_VALUE
    return f"{int(n):,}".replace(",", THOUSANDS_SEPARATOR)


def fmt_float(x: Any, decimals: int = FLOAT_DECIMALS) -> str:
    """Fixed decimals; ``None``/NaN -> ``--``."""
    if x is None:
        return MISSING_VALUE
    v = float(x)
    if math.isnan(v):
        return MISSING_VALUE
    return f"{v:.{decimals}f}"


def fmt_auto(x: Any) -> str:
    """Integers with thousands separators, floats in their shortest form (0.001, 0.2)."""
    if x is None:
        return MISSING_VALUE
    if isinstance(x, bool):
        return YES if x else NO
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer() and abs(x) >= 1):
        return fmt_int(x)
    v = float(x)
    if math.isnan(v):
        return MISSING_VALUE
    return f"{v:g}"


def fmt_pct(fraction: Any, decimals: int = PCT_DECIMALS) -> str:
    """Fraction -> percent string; ``None`` -> ``--``."""
    if fraction is None:
        return MISSING_VALUE
    return fmt_float(float(fraction) * PCT_SCALE, decimals)


def fmt_yes_no(flag: Any) -> str:
    if flag is None:
        return MISSING_VALUE
    return YES if bool(flag) else NO


# --------------------------------------------------------------------------- #
# param_ranges.tex
# --------------------------------------------------------------------------- #


def param_ranges_table(ranges: Mapping[str, Any] | None, class_order: Sequence[str]) -> str:
    """Booktabs tabular: one row per (class, parameter) with min/max, then the margins.

    ``ranges`` is the content of ``artifacts/stage3/param_ranges.json``:
    ``{class: {param: [min, max]}, "margins_in_force": {name: value}}``. Every class
    in ``class_order`` gets at least one row (``--`` when the class is absent), so
    the table always lists the whole taxonomy. ``None`` renders an all-dash table.
    """
    ranges = dict(ranges or {})
    margins = ranges.pop(MARGINS_KEY, None) or {}
    lines = [
        "% Generated by Stage 6 (src/stage6_report/snippets.py) from "
        "artifacts/stage3/param_ranges.json. Do not edit.",
        r"\begin{tabular}{@{}llrr@{}}",
        r"\toprule",
        r"Class & Parameter & Min & Max \\",
        r"\midrule",
    ]
    for name in class_order:
        params = ranges.get(name) or {}
        if not params:
            lines.append(f"{latex_escape(name)} & {MISSING_VALUE} & {MISSING_VALUE} & "
                         f"{MISSING_VALUE} \\\\")
            continue
        first = True
        for param in sorted(params):
            bounds = params[param]
            lo, hi = (bounds[0], bounds[1]) if isinstance(bounds, Sequence) and len(bounds) >= 2 \
                else (None, None)
            label = latex_escape(name) if first else ""
            lines.append(f"{label} & {latex_escape(param)} & "
                         f"{fmt_float(lo, RANGE_DECIMALS)} & {fmt_float(hi, RANGE_DECIMALS)} \\\\")
            first = False
    lines.append(r"\midrule")
    if margins:
        first = True
        for key in sorted(margins):
            label = r"\emph{margins in force}" if first else ""
            lines.append(f"{label} & {latex_escape(key)} & {fmt_auto(margins[key])} & \\\\")
            first = False
    else:
        lines.append(f"\\emph{{margins in force}} & {MISSING_VALUE} & {MISSING_VALUE} & \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# pipeline_facts.tex
# --------------------------------------------------------------------------- #


def pipeline_facts_tex(macros: Mapping[str, str]) -> str:
    """``\\providecommand`` lines, one per macro, values already LaTeX-safe."""
    lines = ["% Generated by Stage 6 (src/stage6_report/snippets.py). Do not edit."]
    lines += [f"\\providecommand{{\\{name}}}{{{macros.get(name, MISSING_VALUE)}}}"
              for name in MACRO_NAMES]
    return "\n".join(lines) + "\n"


def _load_json(path: Path, rel_name: str, missing: list[str]) -> dict | None:
    if not path.is_file():
        missing.append(rel_name)
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def _get(d: Mapping | None, *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, Mapping) or k not in cur:
            return None
        cur = cur[k]
    return cur


def config_facts(config: Mapping[str, Any]) -> dict[str, str]:
    """Plan constants from the merged config (never typed into the report)."""
    train = config["train"]
    ev = config["evaluation"]
    crit = config["success_criterion"]
    ratios = config["split"]["ratios"]
    return {
        "BatchSize": fmt_int(train["batch_size"]),
        "SeedsPerArm": fmt_int(len(config["seed_set"])),
        "SyntheticSharePct": fmt_int(round(float(config["synthetic_fraction"]) * PCT_SCALE)),
        "MaxEpochs": fmt_int(train["max_epochs"]),
        "Patience": fmt_int(train["early_stopping_patience"]),
        "TuningArm": latex_escape(train["tuning"]["arm"]),
        "TuningLRs": ", ".join(fmt_auto(v) for v in train["tuning"]["lr"]),
        "TuningDropouts": ", ".join(fmt_auto(v) for v in train["tuning"]["dropout"]),
        "Alpha": fmt_auto(ev["alpha"]),
        "NBoot": fmt_int(ev["n_boot"]),
        "MinGainPoints": fmt_auto(crit["macro_f1_min_gain_points"]),
        "MaxClassDropPoints": fmt_auto(crit["max_class_f1_drop_points"]),
        "CILevelPct": fmt_int(round(float(crit["ci_level"]) * PCT_SCALE)),
        "PhashHammingMax": fmt_int(config["split"]["phash_hamming_max"]),
        "SplitRatios": "/".join(fmt_int(round(float(r) * PCT_SCALE)) for r in ratios),
        "ImageSize": fmt_int(config["image_size"]),
        "NumClasses": fmt_int(len(class_names(config))),
        "NumRuns": fmt_int(len(config["runs"])),
        "PowerLimitPoints": fmt_auto(ev["power_halfwidth_limit_points"]),
        "ShortcutTriggerPoints": fmt_auto(ev["shortcut_trigger_points"]),
        "GemstoneFilterSetting": fmt_yes_no(config["filter_gemstones"]),
    }


def collect_facts(config: Mapping[str, Any], artifacts_dir: str | Path,
                  export_dir: str | Path | None = None) -> tuple[dict[str, str], list[str]]:
    """Read the upstream JSON files and return ``(macros, missing)``.

    Every name in ``MACRO_NAMES`` is present in ``macros``; values whose source
    file is absent are ``--`` and the file's relative name is in ``missing``.
    """
    art = Path(artifacts_dir)
    missing: list[str] = []
    macros: dict[str, str] = {name: MISSING_VALUE for name in MACRO_NAMES}
    macros.update(config_facts(config))

    s1 = _load_json(art / STAGE1_STATUS, STAGE1_STATUS.as_posix(), missing)
    sc = _load_json(art / STAGE1_SOURCE_CLASSIFIER, STAGE1_SOURCE_CLASSIFIER.as_posix(), missing)
    shortcut = _get(sc, "shortcut_detected")
    if shortcut is None:
        shortcut = _get(s1, "metrics", "shortcut_detected")
    macros["ShortcutDetected"] = fmt_yes_no(shortcut)
    macros["SourceGainPoints"] = fmt_float(_get(sc, "gain_points"), PCT_DECIMALS)
    macros["SourceClassifierAccPct"] = fmt_pct(_get(sc, "pooled_accuracy"))
    macros["SourceMajorityRatePct"] = fmt_pct(_get(sc, "pooled_majority_rate"))

    s3 = _load_json(art / STAGE3_STATUS, STAGE3_STATUS.as_posix(), missing)
    thr = _get(s3, "metrics", "throughput_img_s")
    macros["ThroughputSynth"] = fmt_int(round(thr)) if thr is not None else MISSING_VALUE
    tgt = _get(s3, "metrics", "throughput_target_img_s")
    macros["ThroughputTarget"] = fmt_int(round(tgt)) if tgt is not None else MISSING_VALUE

    s4 = _load_json(art / STAGE4_STATUS, STAGE4_STATUS.as_posix(), missing)
    m4 = _get(s4, "metrics") or {}
    macros["StepsPerEpoch"] = fmt_int(m4.get("steps_per_epoch")) \
        if m4.get("steps_per_epoch") is not None else MISSING_VALUE
    macros["TunedLR"] = fmt_auto(_get(m4, "hparams", "lr"))
    macros["TunedDropout"] = fmt_auto(_get(m4, "hparams", "dropout"))
    macros["RealDrawsA"] = fmt_auto(_get(m4, "real_draws_per_step", ARM_A1))
    macros["RealDrawsB"] = fmt_auto(_get(m4, "real_draws_per_step", ARM_B))
    macros["SynthDrawsB"] = fmt_auto(_get(m4, "synthetic_per_step", ARM_B))
    macros["LosoRequired"] = fmt_yes_no(m4.get("loso_required"))
    macros["LosoHoldoutSource"] = latex_escape(m4.get("loso_holdout_source") or MISSING_VALUE)

    bench = _load_json(art / STAGE4_LOADER_BENCHMARK, STAGE4_LOADER_BENCHMARK.as_posix(), missing)
    ips = _get(bench, "images_per_s")
    if ips is None:
        ips = _get(m4, "loader_benchmark", "images_per_s")
    macros["LoaderImagesPerSec"] = (fmt_int(round(ips))
                                   if ips is not None and math.isfinite(float(ips))
                                   else MISSING_VALUE)

    dis = _load_json(art / STAGE4_SEED_DISAGREEMENT, STAGE4_SEED_DISAGREEMENT.as_posix(), missing)
    for arm, macro in ((ARM_A0, "SeedDisagreementAzero"), (ARM_A1, "SeedDisagreementAone"),
                       (ARM_B, "SeedDisagreementB")):
        value = _get(dis, "per_arm", arm, "mean_pairwise_disagreement")
        if value is None:
            value = _get(m4, "seed_disagreement", arm)
        macros[macro] = fmt_pct(value)

    s5 = _load_json(art / STAGE5_STATUS, STAGE5_STATUS.as_posix(), missing)
    macros["Verdict"] = latex_escape(_get(s5, "metrics", "verdict") or MISSING_VALUE)
    reads = _get(s5, "checks", "test_reads")
    macros["TestReads"] = fmt_int(reads) if reads is not None else MISSING_VALUE
    macros["RunId"] = latex_escape(_get(s5, "run_id") or MISSING_VALUE)

    if export_dir is not None:
        card = _load_json(Path(export_dir) / EXPORT_MODEL_CARD,
                          f"export/{EXPORT_MODEL_CARD}", missing)
        macros["ExportedRun"] = latex_escape(_get(card, "run_name") or MISSING_VALUE)
        macros["ExportedArm"] = latex_escape(_get(card, "arm") or MISSING_VALUE)
        macros["ExportedValFone"] = fmt_float(_get(card, "val_macro_f1"), VAL_F1_DECIMALS)
    return macros, missing


def write_snippets(config: Mapping[str, Any], artifacts_dir: str | Path,
                   export_dir: str | Path | None = None) -> dict[str, Any]:
    """Write param_ranges.tex and pipeline_facts.tex under artifacts/stage6/generated/.

    Returns ``{"param_ranges": Path, "pipeline_facts": Path, "macros": dict,
    "missing": [relative names of absent upstream files]}``.
    """
    art = Path(artifacts_dir)
    out_dir = art / "stage6" / GENERATED_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []

    ranges = _load_json(art / STAGE3_PARAM_RANGES, STAGE3_PARAM_RANGES.as_posix(), missing)
    ranges_path = out_dir / PARAM_RANGES_TEX
    ranges_path.write_text(param_ranges_table(ranges, class_names(config)), encoding="utf-8")

    macros, more_missing = collect_facts(config, art, export_dir)
    missing += [m for m in more_missing if m not in missing]
    facts_path = out_dir / PIPELINE_FACTS_TEX
    facts_path.write_text(pipeline_facts_tex(macros), encoding="utf-8")

    return {"param_ranges": ranges_path, "pipeline_facts": facts_path,
            "macros": macros, "missing": missing}
