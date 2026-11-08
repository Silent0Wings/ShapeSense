"""E20/E34: LaTeX count macros for the report's Split paragraph."""

from src.stage1_freeze.report_snippets import FILTER_PENDING, latex_int, write_report_counts


def test_macros_written_with_thousands_separator(tmp_path):
    p = write_report_counts(tmp_path / "report_counts.tex",
                            {"train": 12761, "val": 2890, "test": 2849},
                            gemstones_removed=0, filter_state=FILTER_PENDING,
                            n_groups=15321, largest_group=175)
    text = p.read_text(encoding="utf-8")
    assert r"\providecommand{\SplitTrain}{12{,}761}" in text
    assert r"\providecommand{\SplitVal}{2{,}890}" in text
    assert r"\providecommand{\SplitTest}{2{,}849}" in text
    assert r"\providecommand{\SplitTotal}{18{,}500}" in text
    assert r"\providecommand{\GemstonesRemoved}{0}" in text
    assert r"\providecommand{\GemstoneFilterState}{not yet applied (review pending)}" in text
    assert r"\providecommand{\NearDupGroups}{15{,}321}" in text
    assert r"\providecommand{\LargestNearDupGroup}{175}" in text
    assert latex_int(1234567) == "1{,}234{,}567"
