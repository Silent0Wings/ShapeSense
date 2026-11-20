# 4_testing - T39: feat(report): keep iteration 1 frozen and add a generated iteration 2 part
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T39 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40253714 / gemini_4_neon + 40253714
- Calibration: `close-to-reality`
- Grounding sources: ShapeSense/src/stage6_report/iteration2.py, ShapeSense/src/stage6_report/run.py, ShapeSense/phase2_report.tex, ShapeSense/tests/stage6/test_iteration2.py, ShapeSense/tests/stage6/test_snippets.py, git commit a474930, ShapeSense_Deployed/web/stage6.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T39 (built, stage `deployment (not a course stage)`): feat(report): keep iteration 1 frozen and add a generated iteration 2 part. Propose or assist with the exact implementation, checks, and configuration needed for commit `a474930`.

## Response
To keep Sections A to J of `phase2_report.tex` immutable when Stage 5 and Stage 6 re-run for Iteration 2, isolate the Iteration 1 report inputs into a frozen snapshot directory and generate Iteration 2 macros and tables separately:

1. **Freeze Iteration 1 report assets under `docs/crisp_dm/iteration_1/`:**
   - Copy the 8 PNG figures (`confusion_A0.png`, `confusion_A1.png`, `confusion_B.png`, `errors_circle_ellipse.png`, `errors_square_diamond.png`, `errors_square_rectangle.png`, `qa_stage2.png`, `qa_stage3.png`) into `docs/crisp_dm/iteration_1/figures/`.
   - Copy `pipeline_facts.tex`, `param_ranges.tex`, and the 7 LaTeX tables (`comparisons.tex`, `metrics.tex`, `per_class.tex`, `per_source.tex`, `power.tex`, `test_reads.tex`, `verdict.tex`) into `docs/crisp_dm/iteration_1/` and `docs/crisp_dm/iteration_1/tables/`.
   - Update `phase2_report.tex` so Sections A-J `\InputIfFileExists` and `\GuardedGraphic` calls point to `docs/crisp_dm/iteration_1/...` rather than `artifacts/stage5/` or `artifacts/stage6/generated/`.

2. **Add `src/stage6_report/iteration2.py` and wire `src/stage6_report/run.py`:**
   - Implement `collect(config, artifacts_dir)` reading `artifacts/stage5/status.json`, `artifacts/stage4/tuning_iter2/winners.json`, and `configs/pipeline.yaml`, returning `--` (`MISSING`) whenever an input is absent.
   - Implement `log_table(repo_root, iteration=2)` to render the CRISP-DM findings per step (`business`, `data`, `prep`, `model`, `eval`, `deploy`) from `docs/crisp_dm/iteration_log.json`, and `write_iteration2(config, artifacts_dir, repo_root)` to emit `artifacts/stage6/generated/iteration2_facts.tex` and `artifacts/stage6/generated/iteration_log.tex`.
   - For the per-arm macros, emit `\ItwoEnsA0`, `\ItwoEnsA1`, `\ItwoEnsB`, `\ItwoEnsA2` (and similarly `\ItwoFresh*`, `\ItwoVal*`, `\ItwoTrials*`, `\ItwoLoso*`) matching the arm keys `A0`, `A1`, `B`, `A2`.
   - In `src/stage6_report/run.py`, register `"iteration_log"` and `"iteration2_winners"` in `inputs(config)` via `sha256_path`, call `write_iteration2(config, art)` in `run(config)`, and append its returned paths to `outputs`.

3. **Update `phase2_report.tex` for Section K and tests:**
   - Add `\providecommand` fallbacks for all Iteration 2 macros, input `artifacts/stage6/generated/iteration2_facts.tex`, add a dashed TikZ arrow (`\draw[arr, dashed] (ev.north) to[bend left=18] node[font=\scriptsize, above]{iteration 2} (dp.south west);`), and include `artifacts/stage6/generated/iteration_log.tex` inside Section K.
   - Add `tests/stage6/test_iteration2.py` covering `collect()` with mock artifacts, missing-input fallback to `--`, and `log_table()` step coverage.

## Validation
- **Macro naming failure caught during LaTeX check:** TeX control sequence names cannot contain digits, so the proposed `\ItwoEnsA0`, `\ItwoEnsA1`, `\ItwoEnsA2`, `\ItwoValA0`, etc. failed to parse in `phase2_report.tex`.
- **Snippet test path mismatch caught by pytest:** `tests/stage6/test_snippets.py` still asserted `\InputIfFileExists{artifacts/stage6/generated/pipeline_facts.tex}` and `param_ranges.tex`, failing after Sections A-J were repointed to `docs/crisp_dm/iteration_1/`.
- After fixing both, `40253714` verified `tests/stage6/test_iteration2.py` (`test_macros_come_from_the_artifacts`, `test_missing_inputs_show_a_dash`, `test_findings_table_lists_every_step_of_the_iteration`) and `tests/stage6/test_snippets.py` (`test_report_has_fallback_for_every_macro`) pass against `phase2_report.tex`.

## Our decision
- **Kept:** Freezing Iteration 1 figures, tables, and macros under `docs/crisp_dm/iteration_1/`, adding `src/stage6_report/iteration2.py` (`collect`, `log_table`, `write_iteration2`), wiring `inputs()` and `run()` in `src/stage6_report/run.py`, and adding Section K + the dashed Iteration 2 TikZ arrow in `phase2_report.tex`.
- **Refined from Gemini 4 Neon's response:** Replaced numeric arm suffixes in macro names with spelled-out words via `ARM_MACROS = (("A0", "Azero"), ("A1", "Aone"), ("B", "B"), ("A2", "Atwo"))` (producing `\ItwoEnsAzero`, `\ItwoEnsAone`, `\ItwoEnsB`, `\ItwoEnsAtwo`, `\ItwoTrialsAzero`, etc.) and updated `tests/stage6/test_snippets.py` to assert `docs/crisp_dm/iteration_1/pipeline_facts.tex`, `docs/crisp_dm/iteration_1/param_ranges.tex`, and `artifacts/stage6/generated/iteration2_facts.tex`.

## Measured effect
- Commit `a474930` touched 22 files (`517 insertions(+), 21 deletions(-)`), freezing 17 Iteration 1 artifacts (8 PNG figures, 7 `.tex` tables, `pipeline_facts.tex`, `param_ranges.tex`) under `docs/crisp_dm/iteration_1/`.
- `src/stage6_report/iteration2.py` generates 36 `\Itwo*` macros (`MACRO_NAMES`) plus `iteration_log.tex` for Section K, isolating Iteration 1 (A0 `93.88`, A1 `90.86`, B `90.50`, verdict `B vs A1 -0.36`, CI `[-1.17, 0.41]`) from subsequent Stage 5/6 re-runs.
- Stage 6 snippet and Iteration 2 unit suites pass (`tests/stage6/test_iteration2.py`, `tests/stage6/test_snippets.py`).

---

## Upgraded & Expanded Technical Analysis (`T39`)

### 1. Snapshot Path Decoupling & LaTeX Control-Word Lexical Compliance
- **Eliminating Live-Artifact Aliasing in Sections A–J:** Prior to commit `a474930`, Sections A–J of `phase2_report.tex` included figures and tables directly from `artifacts/stage5/` and `artifacts/stage6/generated/`. Re-running Stage 5 and Stage 6 for Iteration 2 overwrote those paths in place, silently mutating Iteration 1's historical tables and confusion matrices. Copying all 17 Iteration 1 assets into `docs/crisp_dm/iteration_1/` and repointing `\InputIfFileExists` and `\GuardedGraphic` makes Sections A–J invariant under future pipeline runs.
- **Why `\ItwoEnsA0` Failed LaTeX Tokenization (Catcode 11 vs. 12):** In TeX, multi-letter control sequences allow only characters with category code 11 (`A–Z`, `a–z`). Digits `0–9` have category code 12, so `\ItwoEnsA0` is scanned as the undefined macro `\ItwoEnsA` followed by the digit `0`. Introducing `ARM_MACROS = (("A0", "Azero"), ("A1", "Aone"), ("B", "B"), ("A2", "Atwo"))` in `src/stage6_report/iteration2.py` maps all 36 `\Itwo*` macros to pure alphabetic control words (`\ItwoEnsAzero`, `\ItwoEnsAtwo`, etc.).
- **Beneficial Test Failure (`test_snippets.py`):** When Sections A–J were repointed from `artifacts/stage6/generated/pipeline_facts.tex` to `docs/crisp_dm/iteration_1/pipeline_facts.tex`, `test_snippets.py` immediately flagged the path change — proving the snippet test actively guards the exact include paths compiled by `phase2_report.tex`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** this entry hit the same digit-in-macro bug as F27, independently. The name with a digit fails because digits are not valid in TeX control-sequence names.

**Correction to the batch synthesis:** the current repo has no `macro_key()` or `DIGIT_WORDS`. The spelled-out names are defined as `ARM_MACROS` twice: `src/stage6_report/iteration2.py:22` (four arms) and `src/stage6_report/iteration3.py:22` (five arms, adding `P`). That is a live instance of the "second copy drifts" failure mode, and the iteration 3 copy is the one that would diverge.

**Changelog:** [1] digit bug recurs; [2] duplicated `ARM_MACROS` identified in the code; [3] freeze by location (`docs/crisp_dm/iteration_1/`) is stronger than freeze by comment; [4] `MISSING` (`--`) is the report-honest default.

**Open questions:** Should both iteration modules import one `ARM_MACROS`? Are the TikZ node names `ev` and `dp` stable if Section K changes?
