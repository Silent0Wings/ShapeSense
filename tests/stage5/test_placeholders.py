"""E18: placeholder LaTeX tables (stages/stage_0.md R10)."""

from src.stage5_eval.placeholders import (TABLE_NAMES, is_placeholder,
                                          write_placeholders)


def test_writes_dash_tables_when_missing(tmp_path):
    written = write_placeholders(tmp_path)
    assert {p.stem for p in written} == set(TABLE_NAMES)
    for name in TABLE_NAMES:
        assert is_placeholder(tmp_path / f"{name}.tex")
        assert "--" in (tmp_path / f"{name}.tex").read_text(encoding="utf-8")


def test_never_overwrites_real_table(tmp_path):
    real = tmp_path / "metrics.tex"
    real.write_text("\\begin{tabular}{l}real\\end{tabular}\n", encoding="utf-8")
    write_placeholders(tmp_path)
    assert real.read_text(encoding="utf-8").startswith("\\begin{tabular}")
    assert not is_placeholder(real)
