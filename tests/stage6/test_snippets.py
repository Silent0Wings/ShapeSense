"""E35: generated LaTeX snippets for the Phase 2 report (stages/stage_6.md R7;
plan 35). Pure formatting helpers plus the two generated files, with and
without upstream artifacts. Never touches data_set/ or the test split.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common.config import class_names, load_config
from src.stage6_report import snippets as sn

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_fmt_int_thousands():
    assert sn.fmt_int(12761) == "12{,}761"
    assert sn.fmt_int(999) == "999"
    assert sn.fmt_int(1234567) == "1{,}234{,}567"
    assert sn.fmt_int(0) == "0"
    assert sn.fmt_int(None) == sn.MISSING_VALUE


def test_fmt_float_and_auto():
    assert sn.fmt_float(0.5, 3) == "0.500"
    assert sn.fmt_float(2345.67, 1) == "2345.7"
    assert sn.fmt_float(None) == sn.MISSING_VALUE
    assert sn.fmt_float(float("nan")) == sn.MISSING_VALUE
    assert sn.fmt_auto(0.001) == "0.001"
    assert sn.fmt_auto(0.0003) == "0.0003"
    assert sn.fmt_auto(0.2) == "0.2"
    assert sn.fmt_auto(256) == "256"
    assert sn.fmt_auto(1.0) == "1"
    assert sn.fmt_auto(True) == "yes"
    assert sn.fmt_auto(None) == sn.MISSING_VALUE
    assert sn.fmt_pct(0.1234) == "12.3"
    assert sn.fmt_yes_no(False) == "no"
    assert sn.fmt_yes_no(None) == sn.MISSING_VALUE


def test_latex_escape():
    assert sn.latex_escape("A1_0 & 30% #x $y") == r"A1\_0 \& 30\% \#x \$y"
    assert sn.latex_escape("a{b}~c^d") == r"a\{b\}\textasciitilde{}c\textasciicircum{}d"
    assert sn.latex_escape("back\\slash") == r"back\textbackslash{}slash"
    assert sn.latex_escape("plain") == "plain"
    assert sn.latex_escape(None) == sn.MISSING_VALUE


def test_missing_inputs_become_dashes(tmp_path):
    cfg = load_config()
    out = sn.write_snippets(cfg, tmp_path, tmp_path / "export")
    macros = out["macros"]

    for name in ("StepsPerEpoch", "TunedLR", "RealDrawsB", "SynthDrawsB", "ThroughputSynth",
                 "LoaderImagesPerSec", "TestReads", "Verdict", "ShortcutDetected",
                 "SeedDisagreementB", "ExportedRun", "RunId"):
        assert macros[name] == sn.MISSING_VALUE, name
    assert set(out["missing"]) >= {"stage1/status.json", "stage1/source_classifier.json",
                                   "stage3/status.json", "stage3/param_ranges.json",
                                   "stage4/status.json", "stage5/status.json",
                                   "export/model_card.json"}

    # Config-derived plan facts are still filled (single source of truth is the config).
    assert macros["BatchSize"] == sn.fmt_int(cfg["train"]["batch_size"])
    assert macros["SeedsPerArm"] == sn.fmt_int(len(cfg["seed_set"]))
    assert macros["SplitRatios"] == "/".join(
        sn.fmt_int(round(r * 100)) for r in cfg["split"]["ratios"])
    assert macros["NumClasses"] == sn.fmt_int(len(class_names(cfg)))

    facts = out["pipeline_facts"].read_text(encoding="utf-8")
    assert out["pipeline_facts"] == tmp_path / "stage6" / sn.GENERATED_SUBDIR / sn.PIPELINE_FACTS_TEX
    for name in sn.MACRO_NAMES:
        assert f"\\providecommand{{\\{name}}}" in facts, name
    assert "\\providecommand{\\TestReads}{--}" in facts

    # The ranges table still lists every class (all dashes) so the report compiles.
    ranges = out["param_ranges"].read_text(encoding="utf-8")
    for name in class_names(cfg):
        assert name in ranges
    assert "\\begin{tabular}" in ranges and "\\end{tabular}" in ranges


def test_param_ranges_table_has_every_class():
    names = ["circle", "ellipse", "square"]
    ranges = {
        "circle": {"radius_px": [16.0, 28.0]},
        "ellipse": {"axis_ratio": [1.2, 2.5], "radius_px": [16, 28]},
        sn.MARGINS_KEY: {"ellipse_min_axis_ratio": 1.2, "diamond_min_angle_offset_deg": 10},
    }
    tex = sn.param_ranges_table(ranges, names)
    for name in names:
        assert name in tex
    assert "square & -- & -- & --" in tex           # class without ranges still listed
    assert "16.00" in tex and "28.00" in tex and "2.50" in tex
    assert r"axis\_ratio" in tex                     # LaTeX-safe parameter names
    assert r"ellipse\_min\_axis\_ratio" in tex and "1.2" in tex
    assert r"diamond\_min\_angle\_offset\_deg & 10" in tex
    assert tex.count(r"\toprule") == 1 and tex.count(r"\bottomrule") == 1
    assert tex.strip().endswith(r"\end{tabular}")

    empty = sn.param_ranges_table(None, names)
    for name in names:
        assert name in empty
    assert sn.MISSING_VALUE in empty


def test_collect_facts_reads_upstream(tmp_path):
    cfg = load_config()
    art = tmp_path
    (art / "stage1").mkdir()
    (art / "stage4").mkdir()
    (art / "stage5").mkdir()
    (art / "stage1" / "source_classifier.json").write_text(json.dumps(
        {"shortcut_detected": True, "gain_points": 12.34, "pooled_accuracy": 0.9,
         "pooled_majority_rate": 0.5}), encoding="utf-8")
    (art / "stage4" / "status.json").write_text(json.dumps({
        "status": "passed",
        "metrics": {"steps_per_epoch": 57, "hparams": {"lr": 0.001, "dropout": 0.4},
                    "real_draws_per_step": {"A0": 256, "A1": 256, "B": 180},
                    "synthetic_per_step": {"A0": 0, "A1": 0, "B": 76},
                    "loso_required": False, "loso_holdout_source": None,
                    "loader_benchmark": {"images_per_s": 1234.6},
                    "seed_disagreement": {"A0": 0.05, "A1": 0.04, "B": 0.0312}},
    }), encoding="utf-8")
    (art / "stage5" / "status.json").write_text(json.dumps({
        "status": "passed", "run_id": "2026-11-07T10:00:00+01:00/abc123",
        "metrics": {"verdict": "pass"}, "checks": {"test_reads": 11},
    }), encoding="utf-8")
    export = tmp_path / "export"
    export.mkdir()
    (export / "model_card.json").write_text(json.dumps(
        {"run_name": "A1_0", "arm": "A1", "val_macro_f1": 0.91234}), encoding="utf-8")

    macros, missing = sn.collect_facts(cfg, art, export)
    assert macros["StepsPerEpoch"] == "57"
    assert macros["TunedLR"] == "0.001" and macros["TunedDropout"] == "0.4"
    assert macros["RealDrawsB"] == "180" and macros["SynthDrawsB"] == "76"
    assert macros["RealDrawsA"] == "256"
    assert macros["LoaderImagesPerSec"] == "1{,}235"
    assert macros["SeedDisagreementB"] == "3.1"
    assert macros["LosoRequired"] == "no"
    assert macros["ShortcutDetected"] == "yes"
    assert macros["SourceGainPoints"] == "12.3"
    assert macros["SourceClassifierAccPct"] == "90.0"
    assert macros["Verdict"] == "pass"
    assert macros["TestReads"] == "11"
    assert macros["RunId"] == "2026-11-07T10:00:00+01:00/abc123"
    assert macros["ExportedRun"] == r"A1\_0"
    assert macros["ExportedValFone"] == "0.912"
    # Files that were not written are reported, the ones present are not.
    assert "stage3/status.json" in missing and "stage1/status.json" in missing
    assert "stage4/status.json" not in missing and "stage5/status.json" not in missing


def test_report_has_fallback_for_every_macro():
    tex = (REPO_ROOT / "phase2_report.tex").read_text(encoding="utf-8")
    for name in sn.MACRO_NAMES:
        assert f"\\providecommand{{\\{name}}}" in tex, name
    # Sections A to J read frozen iteration 1 copies; Section K reads generated files.
    assert "\\InputIfFileExists{docs/crisp_dm/iteration_1/pipeline_facts.tex}" in tex
    assert "\\InputIfFileExists{docs/crisp_dm/iteration_1/param_ranges.tex}" in tex
    assert "\\InputIfFileExists{artifacts/stage6/generated/iteration2_facts.tex}" in tex
