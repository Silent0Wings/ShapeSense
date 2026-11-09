"""E30: CSV + LaTeX table writers (stage_5.md Deliverables, Should 1-2)."""

import csv

import numpy as np

from src.stage5_eval import tables

NAMES = ["circle", "ellipse", "pentagon", "square"]
K = len(NAMES)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def _power(underpowered=False):
    return {"n_val": 3000, "n_test": 2900, "factor": 1.017, "half_width_val": 0.9,
            "expected_test_half_width": 1.2 if underpowered else 0.9, "limit_points": 1.0,
            "underpowered": underpowered}


def _verdict(verdict="pass", reasons=()):
    return {"verdict": verdict, "delta": 1.8, "ci": [0.6, 3.0], "reasons": list(reasons),
            "harmful_classes": [], "reported_drops": []}


def test_latex_escapes_underscores(tmp_path):
    assert tables.latex_escape("svm_hog 95% a&b #1") == r"svm\_hog 95\% a\&b \#1"
    cols, rows = tables.metrics_rows(
        [{"name": "A1_0", "arm": "A1", "accuracy": 0.912, "macro_f1": 90.25}], [], [],
        [{"name": "baseline_svm_hog", "accuracy": 0.8, "macro_f1": 79.0}])
    _, tex = tables.write_table(tmp_path, "metrics", cols, rows)
    text = tex.read_text(encoding="utf-8")
    assert r"A1\_0" in text and r"baseline\_svm\_hog" in text
    assert r"macro\_f1\_points" in text
    assert "\\toprule" in text and "\\bottomrule" in text
    # No unescaped underscore survives in the LaTeX file.
    assert "_" not in text.replace("\\_", "")


def test_csv_and_tex_match(tmp_path):
    primary = {"label": "B vs A1", "boot": {"delta": 1.8, "ci": [0.6, 3.0]},
               "mcnemar": {"b": 30, "c": 50, "p_value": 0.0336}}
    secondary = {"A1 vs A0": {"boot": {"delta": 2.5, "ci": [1.0, 4.0]},
                              "mcnemar": {"b": 20, "c": 60, "p_value": 0.0001}, "p_holm": 0.0002},
                 "B vs A0": {"boot": {"delta": 4.3, "ci": [2.6, 6.0]},
                             "mcnemar": {"b": 10, "c": 70, "p_value": 0.00005}, "p_holm": 0.0001}}
    per_seed = {"B vs A1": {"mean": 1.7, "std": 0.4, "same_sign": True}}
    cols, rows = tables.comparisons_rows(primary, secondary, per_seed)
    csv_path, tex_path = tables.write_table(tmp_path, "comparisons", cols, rows)
    csv_rows = _read_csv(csv_path)
    assert csv_rows[0] == list(cols)
    assert len(csv_rows) == 1 + 3
    assert csv_rows[1][0] == "B vs A1" and csv_rows[1][1] == "primary"
    assert csv_rows[1][2] == "+1.8" and csv_rows[1][3] == "[0.6, 3.0]"
    assert csv_rows[1][6] == "0.034" and csv_rows[1][7] == "--"
    assert csv_rows[2][7] == "0.000" and csv_rows[3][1] == "secondary (Holm)"
    assert csv_rows[1][8] == "1.7 ± 0.4" and csv_rows[1][9] == "yes"
    # Every CSV cell appears verbatim (after escaping) in the LaTeX body.
    tex = tex_path.read_text(encoding="utf-8")
    for row in csv_rows[1:]:
        for cell in row:
            assert tables.latex_escape(cell) in tex
    body = [ln for ln in tex.splitlines() if ln.endswith(r"\\")]
    assert len(body) == len(csv_rows)  # header + 3 data rows


def test_asterisk_on_single_source_classes_when_shortcut():
    f1 = {"A0": np.array([90.0, 80.0, 85.0, 88.0]), "A1": np.array([91.0, 82.0, 86.0, 89.0]),
          "B": np.array([92.0, 79.0, 87.0, 90.0])}
    drop = f1["A1"] - f1["B"]
    drop_lo = np.array([-1.0, 0.5, -1.0, -1.0])
    thresholds = np.array([2.0, 2.4, 2.0, 2.0])
    args = (NAMES, [500, 150, 300, 400], f1, drop, drop_lo, thresholds, [], [1])
    cols, rows_flagged = tables.per_class_rows(*args, True, ["pentagon", "ellipse"])
    cols2, rows_plain = tables.per_class_rows(*args, False, ["pentagon", "ellipse"])
    by_name = {r[0]: r for r in rows_flagged}
    assert "ellipse*" in by_name and "pentagon*" in by_name
    assert "circle" in by_name and "square" in by_name
    assert {r[0] for r in rows_plain} == set(NAMES)
    assert by_name["ellipse*"][-1] == "reported"
    assert by_name["ellipse*"][cols.index(tables.DROP_COLUMN)] == "-3.0"
    assert by_name["ellipse*"][cols.index("threshold")] == "2.4"
    assert cols == cols2


def test_verdict_sentence_mentions_same_source(tmp_path):
    text = tables.verdict_paragraph(_verdict(), NAMES, _power(), 1.0, 0.95, gap_closed=0.5,
                                    shortcut_detected=False)
    assert "same-source generalization" in text
    assert "PASS" in text and "+1.8" in text and "[0.6, 3.0]" in text
    assert "generator adds little" not in text
    # Should 2: A1 closing >= 80% of the A0 -> B gap triggers the sentence.
    text2 = tables.verdict_paragraph(_verdict(), NAMES, _power(True), 1.0, 0.95, gap_closed=0.85,
                                     shortcut_detected=False)
    assert "augmentation alone closes most of the gap, so the generator adds little" in text2
    assert "limited power" in text2
    # Fail verdicts carry their reasons.
    text3 = tables.verdict_paragraph(_verdict("fail", ["gain 0.60 < 1.00 points"]), NAMES,
                                     _power(), 1.0, 0.95, gap_closed=None, shortcut_detected=True)
    assert "FAIL" in text3 and "gain 0.60 < 1.00 points" in text3 and "shortcut" in text3
    # The written .tex escapes the percent sign and the CSV twin exists.
    csv_path, tex_path = tables.write_paragraph(
        tmp_path, "verdict", text, tables.verdict_kv_rows(_verdict(), _power(), 0.5))
    tex = tex_path.read_text(encoding="utf-8")
    assert "95\\%" in tex and "%" not in tex.replace("\\%", "")
    assert dict(_read_csv(csv_path)[1:])["verdict"] == "pass"


def test_gap_closure():
    assert tables.gap_closure(80.0, 84.0, 85.0) == 0.8
    assert tables.gap_closure(80.0, 84.0, 80.0) is None
    assert tables.gap_closure(80.0, 84.0, 79.0) is None


def test_test_reads_and_power_rows(tmp_path):
    cols, rows = tables.test_reads_rows("2026-11-10T09:00:00-05:00/3f9a1c", 11, 11)
    assert rows == [["2026-11-10T09:00:00-05:00/3f9a1c", "11", "11", "yes"]]
    cols_p, rows_p = tables.power_rows(_power(True))
    assert ["underpowered", "yes"] in rows_p
    assert ["expected test CI half-width (points)", "1.2"] in rows_p
    csv_path, tex_path = tables.write_table(tmp_path, "test_reads", cols, rows)
    assert _read_csv(csv_path)[1] == rows[0]
    assert "11 & 11 & yes" in tex_path.read_text(encoding="utf-8")


def test_ablation_rows_rendered():
    ablation = {"name": "B_equalreal_0", "arm": "B", "accuracy": 0.9, "macro_f1": 88.5}
    cols, rows = tables.metrics_rows([], [], [], [], [ablation])
    assert rows == [["B_equalreal_0", "B", "ablation", "90.0", "88.5"]]
