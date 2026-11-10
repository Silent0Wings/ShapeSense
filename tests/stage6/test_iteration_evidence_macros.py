"""Macro names from the iteration 1 evidence stay valid LaTeX and never collide."""

import re

from src.stage6_report.iteration_evidence import macro_key


def test_existing_names_keep_their_macros():
    assert macro_key("A0_0") == "IterOneAZeroSeedZero"
    assert macro_key("A1_2") == "IterOneAOneSeedTwo"
    assert macro_key("B_1") == "IterOneBSeedOne"


def test_digits_never_appear_in_a_macro_name():
    for name in ("A2_0", "A2_loso_hd_3", "P_4"):
        assert re.fullmatch(r"[A-Za-z]+", macro_key(name)), name


def test_a_held_out_run_does_not_collide_with_a_main_run():
    assert macro_key("A0_loso_0") != macro_key("A0_0")
