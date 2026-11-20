# 4_testing - C41: Iteration 3 report section and dashboard results ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/41_C41_iteration-3-report-section-and-dashboard.md](../gemini_4_neon/41_C41_iteration-3-report-section-and-dashboard.md)
- Date: 2026-11-10
- Worksheet entry: C41 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / 40248536
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `phase2_report.tex`, `src/stage6_report/iteration3.py`, `src/stage6_report/run.py`, `tests/stage6/test_iteration3.py`, `studio/web/js/pages/stage5.js`, `studio/web/js/pages/robustness.js`, `studio/web/js/pages/boot.js`, `docs/crisp_dm/iteration_log.json`, commits `4091dab` and `ec84804`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/robustness.html`, `ShapeSense_Deployed/web/stage6.html`, `ShapeSense_Deployed/web/changes.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** The report stops at Section K (Iteration 2) and the dashboard only shows four arms and validation robustness. How should we structure report Section L and the dashboard updates so they lead with the sealed Iteration 3 verdict, include arm `P`, and draw every number from recorded tables?

## Response ()

> **Opus 5.5:** Mirror the Section K macro pipeline for Section L, put the sealed verdict and summary table right at the top, and update the shared arm list in the dashboard so `P` and the sealed robustness results flow through everywhere:
>
> - **Report generation (`src/stage6_report/iteration3.py`):** Add `collect()` and `write_iteration3()` reading `artifacts/stage5/status.json`, `artifacts/stage4/tuning_iter3/winners.json`, and `docs/crisp_dm/iteration_log.json` to emit `iteration3_facts.tex` (all `\Ithree*` macros, spelling out digits so LaTeX macro names stay valid), `iteration3_log.tex`, `iteration3_failures.tex`, and `iteration3_changes.tex`. Wire `write_iteration3` into `src/stage6_report/run.py` and add `winners` (`tuning_iter3/winners.json`) to `inputs(config)`.
> - **Lead with the result in `phase2_report.tex` Section L:** Place the 5-arm table (`tab:iterthree`), the pre-registered primary verdict (`\IthreePrimary`, `\IthreeDelta`, CI, strict pass, sealed read count), secondary Holm-corrected comparisons, and the clean/earlier-set context first, and put the longer log, failure, and change tables at the end of Section L so readers see the verdict immediately.
> - **Dashboard updates (`stage5.js`, `robustness.js`, `boot.js`):** Add `P` once to `ARM_SERIES` and `studio/settings.py` (`ARMS`), update `stage5.js` to lead with `metrics.robust` on damaged `fresh_holdout_2` while demoting `reused_test` and the first `fresh_holdout` to a secondary context table, and add a toggle on `robustness.js` between `Sealed holdout 2 (the verdict)` and `Validation check, for comparison`.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Put narrative log/failure/change tables before the verdict in Section L | Buries the sealed `+9.20` pass behind pages of tables | Skip |
> | Lead Section L and `stage5.js` with the sealed verdict + artifact-backed macros | Makes the primary result immediately readable with zero hand-typed numbers | **Do this** |
>
> Cover `collect()` with unit tests in `tests/stage6/test_iteration3.py` (testing both populated artifacts and `--` fallbacks when inputs are missing) and confirm `check_report` traceability passes on `phase2_report.tex`.

## Why this reading fits

Commits `4091dab` and `ec84804` implement this exact layout: `src/stage6_report/iteration3.py` generates all Section L macros and tables from recorded JSON artifacts, `ec84804` moves the log/failure/change tables below `robust_comparisons.tex` so Section L leads with the result and removes a duplicate `P` entry from `boot.js`, and `stage5.html` / `robustness.html` in `ShapeSense_Deployed` present the sealed verdict alongside arm `P`.

## Validation

- Added `tests/stage6/test_iteration3.py` (`test_macros_come_from_the_artifacts` and `test_missing_inputs_show_a_dash`), verifying all 57 `MACRO_NAMES` keys populate from `stage5/status.json` and `tuning_iter3/winners.json` and default to `--` when absent.
- Verified `phase2_report.tex` builds and passes `src/stage6_report/traceability.py` (`check_report`), and verified `ShapeSense_Deployed/web/stage5.html`, `robustness.html`, and `stage6.html` in headless Chromium (`build/check.py`).

## Our decision

Added `src/stage6_report/iteration3.py` and `phase2_report.tex` Section L leading with the sealed Iteration 3 verdict, added arm `P` once across `studio/settings.py`, `boot.js`, and `export_arms.py`, and updated `stage5.js` and `robustness.js` to lead with `fresh_holdout_2` sealed robustness results.

## Measured effect

Section L and `stage5.html` / `robustness.html` display all five arms (`A0`, `A1`, `B`, `A2`, `P`) and lead directly with the sealed Iteration 3 primary result: `A2 vs A0` `+9.20` macro-F1 points (`95% CI [8.89, 9.53]`, strict pass `yes`, `4,500` never-read images across `23` damage levels, `92/92` sealed reads), plus secondary Holm-corrected comparisons (`p = 0.004`), clean `fresh_holdout_2` (`+0.64`, `CI [0.19, 1.07]`), and earlier contaminated evaluations (`+0.52` reused test, `+0.54` first fresh holdout), with zero traceability failures.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C41`)

### The verdict-first hierarchy (why order is a correctness property)

A report's first screen determines what a reader believes. If the narrative log precedes the verdict, the reader forms a hypothesis before seeing the pre-registered result — an **anchoring hazard**. Section L therefore orders: (1) 5-arm table, (2) primary pre-registered verdict with CI and sealed-read count, (3) secondary Holm-corrected comparisons, (4) clean/earlier-set context, (5) log/failure/change tables last. The *content* is identical; the *order* is the correctness property.

### The traceability chain

Every `\Ithree*` macro is generated by `iteration3.py:collect()` from recorded JSON (`stage5/status.json`, `tuning_iter3/winners.json`, `iteration_log.json`). The chain is: **artifact $\rightarrow$ macro $\rightarrow$ report**, with `check_report` verifying no macro is hand-typed (the `--` fallback fires if an input is missing). The 57 `MACRO_NAMES` are the complete inventory; `test_macros_come_from_the_artifacts` verifies all 57 populate, and `test_missing_inputs_show_a_dash` verifies the fallback.

### The dashboard parallel

`stage5.js` leads with `metrics.robust` (sealed `fresh_holdout_2`), demoting `reused_test` and the first `fresh_holdout` to context; `robustness.js` toggles `"Sealed holdout 2 (the verdict)"` vs. `"Validation check, for comparison"`. Same hierarchy principle in the UI: **the verdict leads; context follows; contaminated sets are labeled as context.**

