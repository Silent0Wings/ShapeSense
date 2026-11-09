"""CSV + LaTeX table writers for Stage 5 (stages/stage_5.md Deliverables,
Should 1-2; plan 30 step 3).

Pure: every function takes numbers already computed by the orchestrator
and returns ``(columns, rows)`` of **pre-formatted strings**, so the CSV
and the LaTeX file are rendered from the same cells and can never drift
apart. ``write_table`` writes both files, overwriting the Stage 0
placeholders under ``artifacts/stage5/tables/``.

Units: F1 in points (1 decimal), accuracy in percent (1 decimal),
p-values with 3 decimals.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

POINTS_DECIMALS = 1  # F1 points
PCT_DECIMALS = 1  # accuracy percent
P_DECIMALS = 3  # p-values
FACTOR_DECIMALS = 3  # sqrt(n_val / n_test)
PCT_SCALE = 100.0  # fraction -> percent
GAP_CLOSE_FRACTION = 0.80  # A1 closes >= this share of the A0 -> B gap => "generator adds little"
ASTERISK = "*"  # marks single-source classes when a shortcut was detected
PLUS_MINUS = "±"
LOSO_LABEL = "unseen-source generalization"  # R10 wording for LOSO rows
SAME_SOURCE_LABEL = "same-source generalization"  # the primary comparison

_LATEX_SPECIALS = {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#"}


def latex_escape(text: str) -> str:
    """Escape ``_ % & #`` for LaTeX; ``±`` stays as is (report uses UTF-8)."""
    out = []
    for ch in str(text):
        out.append(_LATEX_SPECIALS.get(ch, ch))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Number formatting (one place, so CSV and TeX agree)
# --------------------------------------------------------------------------- #


def fmt(x: float | None, decimals: int) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{float(x):.{decimals}f}"


def fmt_points(x: float | None) -> str:
    return fmt(x, POINTS_DECIMALS)


def fmt_pct(fraction: float | None) -> str:
    return "--" if fraction is None else fmt(float(fraction) * PCT_SCALE, PCT_DECIMALS)


def fmt_p(p: float | None) -> str:
    return fmt(p, P_DECIMALS)


def fmt_ci(ci: Sequence[float]) -> str:
    return f"[{fmt_points(ci[0])}, {fmt_points(ci[1])}]"


def fmt_mean_std(mean: float, std: float, decimals: int = POINTS_DECIMALS) -> str:
    return f"{fmt(mean, decimals)} {PLUS_MINUS} {fmt(std, decimals)}"


def fmt_signed(x: float) -> str:
    return f"{float(x):+.{POINTS_DECIMALS}f}"


# --------------------------------------------------------------------------- #
# Writers
# --------------------------------------------------------------------------- #


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[Sequence[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(columns))
        for row in rows:
            w.writerow(list(row))
    return path


def latex_tabular(columns: Sequence[str], rows: Sequence[Sequence[str]],
                  align: str | None = None) -> str:
    """A booktabs tabular; first column left-aligned, the rest right-aligned."""
    if align is None:
        align = "l" + "r" * (len(columns) - 1)
    lines = [f"\\begin{{tabular}}{{{align}}}", "\\toprule",
             " & ".join(latex_escape(c) for c in columns) + r" \\", "\\midrule"]
    for row in rows:
        lines.append(" & ".join(latex_escape(c) for c in row) + r" \\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def write_table(tables_dir: str | Path, name: str, columns: Sequence[str],
                rows: Sequence[Sequence[str]], align: str | None = None) -> tuple[Path, Path]:
    """Write ``<name>.csv`` and ``<name>.tex`` from the same string cells."""
    d = Path(tables_dir)
    d.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv(d / f"{name}.csv", columns, rows)
    tex_path = d / f"{name}.tex"
    tex_path.write_text(latex_tabular(columns, rows, align), encoding="utf-8")
    return csv_path, tex_path


def write_paragraph(tables_dir: str | Path, name: str, paragraph: str,
                    kv_rows: Sequence[Sequence[str]]) -> tuple[Path, Path]:
    """A LaTeX paragraph (``<name>.tex``) plus its key/value CSV twin."""
    d = Path(tables_dir)
    d.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv(d / f"{name}.csv", ("key", "value"), kv_rows)
    tex_path = d / f"{name}.tex"
    tex_path.write_text(latex_escape(paragraph) + "\n", encoding="utf-8")
    return csv_path, tex_path


# --------------------------------------------------------------------------- #
# Table builders (columns, rows of strings)
# --------------------------------------------------------------------------- #

METRICS_COLUMNS = ("model", "arm", "kind", "accuracy_pct", "macro_f1_points")


def metrics_rows(
    seed_models: Sequence[Mapping],
    arm_summaries: Sequence[Mapping],
    ensembles: Sequence[Mapping],
    baselines: Sequence[Mapping],
    ablations: Sequence[Mapping] = (),
) -> tuple[tuple[str, ...], list[list[str]]]:
    """Metrics table.

    ``seed_models``: {name, arm, accuracy (fraction), macro_f1 (points)}.
    ``arm_summaries``: {arm, acc_mean, acc_std (fractions), f1_mean, f1_std}.
    ``ensembles``: {arm, accuracy, macro_f1}. ``baselines``: {name, accuracy, macro_f1}.
    """
    rows: list[list[str]] = []
    for m in seed_models:
        rows.append([str(m["name"]), str(m["arm"]), "seed model",
                     fmt_pct(m["accuracy"]), fmt_points(m["macro_f1"])])
    for s in arm_summaries:
        rows.append([f"{s['arm']} per-seed mean {PLUS_MINUS} std", str(s["arm"]), "seed summary",
                     fmt_mean_std(s["acc_mean"] * PCT_SCALE, s["acc_std"] * PCT_SCALE, PCT_DECIMALS),
                     fmt_mean_std(s["f1_mean"], s["f1_std"])])
    for e in ensembles:
        rows.append([f"{e['arm']} ensemble (soft vote)", str(e["arm"]), "ensemble",
                     fmt_pct(e["accuracy"]), fmt_points(e["macro_f1"])])
    for b in baselines:
        rows.append([str(b["name"]), "--", "baseline", fmt_pct(b["accuracy"]),
                     fmt_points(b["macro_f1"])])
    for a in ablations:
        rows.append([str(a["name"]), str(a["arm"]), "ablation", fmt_pct(a["accuracy"]),
                     fmt_points(a["macro_f1"])])
    return METRICS_COLUMNS, rows


DROP_COLUMN = "drop_candidate_minus_reference"
PER_CLASS_COLUMNS = ("class", "n_test", "f1_A0", "f1_A1", "f1_B", DROP_COLUMN,
                     "drop_ci_lo", "threshold", "flag")


def per_class_rows(
    class_names: Sequence[str],
    n_test: Sequence[int],
    f1_by_arm: Mapping[str, np.ndarray],
    drop_observed: np.ndarray,
    drop_ci_lo: np.ndarray,
    thresholds: np.ndarray,
    harmful_classes: Sequence[int],
    reported_drops: Sequence[int],
    shortcut_detected: bool,
    single_source_classes: Sequence[str] = (),
    arm_order: Sequence[str] = ("A0", "A1", "B"),
) -> tuple[tuple[str, ...], list[list[str]]]:
    """Per-class ensemble F1 with the B − A1 drop, its threshold and a flag.

    ``drop_observed`` is F1(A1) − F1(B) in points (a positive value is a
    drop); the table column shows the signed B − A1 change. Classes in
    ``single_source_classes`` get an asterisk when ``shortcut_detected``
    (Should 1).
    """
    harmful = set(int(c) for c in harmful_classes)
    reported = set(int(c) for c in reported_drops)
    single = set(single_source_classes)
    columns = ("class", "n_test") + tuple(f"f1_{a}" for a in arm_order) + (
        DROP_COLUMN, "drop_ci_lo", "threshold", "flag")
    rows: list[list[str]] = []
    for c, name in enumerate(class_names):
        label = str(name)
        if shortcut_detected and name in single:
            label += ASTERISK
        flag = "harmful" if c in harmful else ("reported" if c in reported else "")
        row = [label, str(int(n_test[c]))]
        row += [fmt_points(float(f1_by_arm[a][c])) if a in f1_by_arm else "--" for a in arm_order]
        row += [fmt_signed(-float(drop_observed[c])), fmt_points(float(drop_ci_lo[c])),
                fmt_points(float(thresholds[c])), flag]
        rows.append(row)
    return columns, rows


COMPARISON_COLUMNS = ("comparison", "role", "delta_macro_f1_points", "ci", "mcnemar_b",
                      "mcnemar_c", "p_raw", "p_holm", "per_seed_mean_std", "same_sign")


def comparisons_rows(
    primary: Mapping,
    secondary: Mapping[str, Mapping],
    per_seed: Mapping[str, Mapping],
) -> tuple[tuple[str, ...], list[list[str]]]:
    """Primary, secondary (Holm) and per-seed robustness rows kept separate.

    ``primary``: {label, boot: {delta, ci}, mcnemar: {b, c, p_value}}.
    ``secondary``: label -> {boot, mcnemar, p_holm}.
    ``per_seed``: label -> per_seed_differences() output.
    """
    rows: list[list[str]] = []

    def _row(label: str, role: str, comp: Mapping, p_holm: float | None) -> list[str]:
        ps = per_seed.get(label)
        return [label, role, fmt_signed(comp["boot"]["delta"]), fmt_ci(comp["boot"]["ci"]),
                str(int(comp["mcnemar"]["b"])), str(int(comp["mcnemar"]["c"])),
                fmt_p(comp["mcnemar"]["p_value"]), fmt_p(p_holm) if p_holm is not None else "--",
                fmt_mean_std(ps["mean"], ps["std"]) if ps else "--",
                ("yes" if ps["same_sign"] else "no") if ps else "--"]

    rows.append(_row(str(primary["label"]), "primary", primary, None))
    for label, comp in secondary.items():
        rows.append(_row(str(label), "secondary (Holm)", comp, comp.get("p_holm")))
    return COMPARISON_COLUMNS, rows


PER_SOURCE_COLUMNS = ("group", "kind", "arm", "n", "accuracy_pct", "note")


def per_source_rows(
    per_source: Mapping[str, Mapping[str, float]],
    per_domain: Mapping[str, Mapping[str, float]],
    source_counts: Mapping[str, int],
    domain_counts: Mapping[str, int],
    loso: Sequence[Mapping] | None = None,
) -> tuple[tuple[str, ...], list[list[str]]]:
    """Ensemble accuracy per source and per domain; LOSO rows labelled R10.

    ``per_source`` / ``per_domain``: arm -> group -> accuracy fraction.
    ``loso``: [{name, arm, source, n, accuracy}] evaluated on the held-out
    source only.
    """
    rows: list[list[str]] = []
    for arm in per_source:
        for src in sorted(per_source[arm]):
            rows.append([src, "source", arm, str(int(source_counts.get(src, 0))),
                         fmt_pct(per_source[arm][src]), ""])
    for arm in per_domain:
        for dom in sorted(per_domain[arm]):
            rows.append([dom, "domain", arm, str(int(domain_counts.get(dom, 0))),
                         fmt_pct(per_domain[arm][dom]), ""])
    for rec in loso or ():
        rows.append([str(rec["source"]), "held-out source", str(rec["arm"]), str(int(rec["n"])),
                     fmt_pct(rec["accuracy"]), f"{LOSO_LABEL} ({rec['name']})"])
    return PER_SOURCE_COLUMNS, rows


POWER_COLUMNS = ("quantity", "value")


def power_rows(power: Mapping) -> tuple[tuple[str, ...], list[list[str]]]:
    rows = [
        ["n_val", str(int(power["n_val"]))],
        ["n_test", str(int(power["n_test"]))],
        ["rescale factor sqrt(n_val / n_test)", fmt(power["factor"], FACTOR_DECIMALS)],
        ["validation CI half-width (points)", fmt_points(power["half_width_val"])],
        ["expected test CI half-width (points)", fmt_points(power["expected_test_half_width"])],
        ["limit (points)", fmt_points(power["limit_points"])],
        ["underpowered", "yes" if power["underpowered"] else "no"],
    ]
    return POWER_COLUMNS, rows


def power_sentence(power: Mapping) -> str:
    exp = fmt_points(power["expected_test_half_width"])
    lim = fmt_points(power["limit_points"])
    if power["underpowered"]:
        return (f"Power check (run before any test prediction): the expected half-width of the "
                f"primary CI is {exp} points, above the {lim}-point limit, so the test set has "
                f"limited power to resolve a {lim}-point gain; the criterion is unchanged.")
    return (f"Power check (run before any test prediction): the expected half-width of the "
            f"primary CI is {exp} points, within the {lim}-point limit.")


def gap_closure(f1_a0: float, f1_a1: float, f1_b: float) -> float | None:
    """Share of the A0 -> B macro-F1 gap that A1 alone closes; None if B <= A0."""
    gap = f1_b - f1_a0
    if gap <= 0:
        return None
    return (f1_a1 - f1_a0) / gap


def verdict_paragraph(
    verdict: Mapping,
    class_names: Sequence[str],
    power: Mapping,
    min_gain_points: float,
    ci_level: float,
    gap_closed: float | None,
    shortcut_detected: bool,
    primary_label: str = "B vs A1",
) -> str:
    """One LaTeX paragraph stating the verdict, the numbers and the reasons."""
    ci_pct = int(round(ci_level * PCT_SCALE))
    parts = [
        f"Primary comparison ({primary_label} soft-vote ensembles, {SAME_SOURCE_LABEL} on the locked "
        f"test split): macro-F1 change {fmt_signed(verdict['delta'])} points, {ci_pct}% paired "
        f"bootstrap CI {fmt_ci(verdict['ci'])}. Verdict: {str(verdict['verdict']).upper()} "
        f"against the locked criterion (gain of at least {fmt_points(min_gain_points)} points, "
        f"CI excluding 0, no harmful class drop)."
    ]
    if verdict["reasons"]:
        parts.append("Reasons: " + "; ".join(str(r) for r in verdict["reasons"]) + ".")
    if verdict["harmful_classes"]:
        names = ", ".join(class_names[int(c)] for c in verdict["harmful_classes"])
        parts.append(f"Harmful class drops: {names}.")
    if verdict.get("reported_drops"):
        names = ", ".join(class_names[int(c)] for c in verdict["reported_drops"])
        parts.append(f"Reported (non-failing) drops: {names}.")
    parts.append(power_sentence(power))
    if gap_closed is not None and gap_closed >= GAP_CLOSE_FRACTION:
        parts.append(
            f"Secondary finding: A1 closes {fmt_pct(gap_closed)}% of the A0 to B macro-F1 gap, "
            "so augmentation alone closes most of the gap, so the generator adds little.")
    elif gap_closed is not None:
        parts.append(f"Secondary finding: A1 closes {fmt_pct(gap_closed)}% of the A0 to B "
                     "macro-F1 gap.")
    if shortcut_detected:
        parts.append("Stage 1 detected a source shortcut; single-source classes are starred and "
                     "the per-source table is mandatory.")
    return " ".join(parts)


def verdict_kv_rows(verdict: Mapping, power: Mapping, gap_closed: float | None) -> list[list[str]]:
    return [
        ["verdict", str(verdict["verdict"])],
        ["delta_macro_f1_points", fmt_signed(verdict["delta"])],
        ["ci_lo", fmt_points(verdict["ci"][0])],
        ["ci_hi", fmt_points(verdict["ci"][1])],
        ["reasons", "; ".join(str(r) for r in verdict["reasons"])],
        ["harmful_classes", ";".join(str(c) for c in verdict["harmful_classes"])],
        ["expected_test_half_width", fmt_points(power["expected_test_half_width"])],
        ["underpowered", "yes" if power["underpowered"] else "no"],
        ["gap_closed_fraction", "--" if gap_closed is None else fmt(gap_closed, P_DECIMALS)],
    ]


TEST_READS_COLUMNS = ("run_id", "test_reads", "expected", "ok")


def test_reads_rows(run_id: str, count: int, expected: int) -> tuple[tuple[str, ...], list[list[str]]]:
    return TEST_READS_COLUMNS, [[str(run_id), str(int(count)), str(int(expected)),
                                "yes" if int(count) == int(expected) else "no"]]
