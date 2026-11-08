"""E35: number-traceability check for the Phase 2 report (stages/stage_6.md
Mission M1, Done-when 2; plan 35).

The five Mission M1 sentences drive the tests: sentence 3 ("about 2 points")
and sentence 5 (the Phase 1 split counts) must be flagged; sentences 1 and 4
(\\input) must pass. Placeholder tables and bibliography scope are covered too.
"""

from __future__ import annotations

from pathlib import Path

from src.stage6_report import traceability as tr

REPO_ROOT = Path(__file__).resolve().parents[2]

# Mission M1 sentences (stages/stage_6.md).
S1 = r"Model B reached a macro-F1 of \input{artifacts/stage5/tables/b_macro_f1.tex}."
S3 = "Model B improved macro-F1 by about 2 points."
S4 = r"The gemstone filter removed \input{artifacts/stage1/gemstones.tex} drawings."
S5 = "The split holds 12,761 train, 2,890 validation and 2,849 test images."


def _doc(body: str) -> str:
    return "\\documentclass{article}\n\\begin{document}\n" + body + "\n\\end{document}\n"


def _kinds(findings: list[dict]) -> list[str]:
    return [f["kind"] for f in findings]


def test_flags_hand_typed_number():
    findings = tr.scan(_doc(S3))
    assert _kinds(findings) == [tr.KIND_HAND_TYPED]
    assert findings[0]["token"] == "2"
    assert findings[0]["line"] == 3

    # A precise result number is flagged even without a hedge word.
    plain = tr.scan(_doc("Model B reached a macro-F1 of 91.2 points on the test split."))
    assert _kinds(plain) == [tr.KIND_HAND_TYPED]
    assert plain[0]["token"] == "91.2"

    # Mission M1 sentence 2: copied generator bounds are hand-typed too.
    copied = tr.scan(_doc("Synthetic ellipses use axis ratios between 1.2 and 2.0."))
    assert sorted(f["token"] for f in copied) == ["1.2", "2.0"]


def test_flags_phase1_counts():
    findings = tr.scan(_doc(S5))
    phase1 = [f for f in findings if f["kind"] == tr.KIND_PHASE1]
    assert {f["token"] for f in phase1} == {"12,761", "2,890", "2,849"}
    assert all(f["line"] == 3 for f in phase1)

    # "Anywhere": the preamble and the LaTeX thousands spelling count as well.
    preamble = tr.scan("\\providecommand{\\N}{12{,}761}\n\\begin{document}\n\\end{document}\n")
    assert _kinds(preamble) == [tr.KIND_PHASE1]
    assert preamble[0]["token"] == "12,761"
    assert tr.is_phase1_count("2849")


def test_input_lines_ok():
    assert tr.scan(_doc(S1)) == []
    assert tr.scan(_doc(S4)) == []
    guarded = r"\InputIfFileExists{artifacts/stage5/tables/metrics.tex}{}{--}"
    assert tr.scan(_doc(guarded)) == []


def test_allowed_constants_ok():
    body = (
        "The data is split 70/15/15 by pHash group. Images are $64{\\times}64$ pixels "
        "(64×64 in the figures) over 10 classes; $\\alpha = 0.05$; the locked criterion "
        "is a 1-point gain of at least 1 point. Arms A0, A1 and B use 3 seeds and a "
        "batch size of 256 images."
    )
    assert tr.scan(_doc(body)) == []


def test_allowed_contexts_ok():
    body = "\n".join([
        r"\includegraphics[width=0.6\linewidth]{figures/errors_2.png}",
        r"\IfFileExists{artifacts/stage5/figures/confusion_A0.png}{x}{y}",
        r"\begin{minipage}[c]{0.32\linewidth}\end{minipage}",
        r"\label{tab:3}\ref{tab:3}\cite[slides 4--5]{lecdp}\cite[slide 20]{lecfd}",
        r"Decision 13 and Stage 5 (R19, E35, md5, 2D shapes) \\[4pt] text width=4.7cm",
        r"\node[box] at (6.5,5) {Model A1}; CC BY 4.0 and CC0.",
    ])
    assert tr.scan(_doc(body)) == []


def test_equals_sign_does_not_hide_result():
    """An "=" in prose is not a TikZ option: the number after it is a result."""
    findings = tr.scan(_doc("Ensemble macro-F1 = 91.2 points, CI = [0.6, 3.0]."))
    tokens = {f["token"] for f in findings}
    assert "91.2" in tokens, findings
    assert {"0.6", "3.0"} <= tokens, findings
    assert set(_kinds(findings)) == {tr.KIND_HAND_TYPED}
    # key=value inside an option list and the plan alpha stay allowed.
    assert tr.scan(_doc(r"\node[opacity=0.37, text width=4.7cm] at (0,0) {x};")) == []
    assert tr.scan(_doc(r"\draw[arr, line width=0.8pt] (a) -- (b);")) == []
    assert tr.scan(_doc(r"\tikzset{box/.style={fill=gray!37, scale=0.93}}")) == []
    assert tr.scan(_doc(r"We use $\alpha = 0.05$ throughout.")) == []


def test_bibliography_out_of_scope():
    bib = "\n".join([
        r"\begin{thebibliography}{9}",
        r"\bibitem{zauner} C. Zauner. Thesis, 2010. arXiv:2108.02497. DOI 10.17632/x.1",
        r"\end{thebibliography}",
    ])
    assert tr.scan(_doc(bib)) == []
    # The same year in the body is a bare number and gets flagged.
    assert _kinds(tr.scan(_doc("Published in 2010."))) == [tr.KIND_HAND_TYPED]
    # Phase 1 counts are flagged even inside the bibliography ("anywhere").
    assert _kinds(tr.scan(_doc(bib.replace("2010", "12,761")))) == [tr.KIND_PHASE1]


def test_flags_placeholder_tables(tmp_path):
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "metrics.tex").write_text(tr.PLACEHOLDER_MARK + "\n--\n", encoding="utf-8")
    (tables / "real.tex").write_text("\\begin{tabular}{l}x\\end{tabular}\n", encoding="utf-8")
    tex = tmp_path / "report.tex"
    tex.write_text(_doc("\\InputIfFileExists{tables/metrics.tex}{}{--}\n"
                        "\\input{tables/real.tex}\n\\input{tables/absent.tex}"),
                   encoding="utf-8")

    result = tr.check_report(tex, tmp_path)
    assert result["ok"] is False
    assert result["placeholders"] == ["tables/metrics.tex"]
    assert result["missing_inputs"] == ["tables/absent.tex"]
    assert tr.KIND_PLACEHOLDER in _kinds(result["findings"])
    assert tr.KIND_MISSING in _kinds(result["findings"])

    # Once Stage 5 overwrote the placeholder, only the missing input remains and ok holds.
    (tables / "metrics.tex").write_text("\\begin{tabular}{l}real\\end{tabular}\n",
                                        encoding="utf-8")
    again = tr.check_report(tex, tmp_path)
    assert again["ok"] is True
    assert again["placeholders"] == []
    assert again["n_failing"] == 0


def test_placeholder_mark_matches_stage5_text():
    # Stages may not import each other, so the mark is re-declared; it must stay
    # byte-identical to src/stage5_eval/placeholders.py (checked textually).
    src = (REPO_ROOT / "src" / "stage5_eval" / "placeholders.py").read_text(encoding="utf-8")
    assert f'PLACEHOLDER_MARK = "{tr.PLACEHOLDER_MARK}"' in src


def test_artifacts_dir_override_resolves_inputs(tmp_path):
    art = tmp_path / "art"
    (art / "stage5" / "tables").mkdir(parents=True)
    (art / "stage5" / "tables" / "metrics.tex").write_text(tr.PLACEHOLDER_MARK + "\n--\n",
                                                           encoding="utf-8")
    tex = tmp_path / "report.tex"
    tex.write_text(_doc(r"\input{artifacts/stage5/tables/metrics}"), encoding="utf-8")
    result = tr.check_report(tex, art)
    assert result["placeholders"] == ["artifacts/stage5/tables/metrics"]
    assert result["ok"] is False


def test_phase2_report_has_no_hand_typed_numbers():
    text = (REPO_ROOT / "phase2_report.tex").read_text(encoding="utf-8")
    findings = tr.scan(text)
    assert findings == [], findings
