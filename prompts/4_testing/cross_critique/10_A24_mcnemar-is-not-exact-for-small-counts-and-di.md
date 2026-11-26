# 4_testing - A24: McNemar is not exact for small counts, and differs from the primary metric.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A24 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/stats.py, ShapeSense/src/stage5_eval/run.py, ShapeSense/src/stage5_eval/robust.py, ShapeSense/results/phase2_snapshot/comparisons.csv, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/tests/stage5/test_iteration3_repairs.py, ShapeSense_Deployed/web/stage5.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: McNemar is not exact for small counts, and differs from the primary metric.

## Response
Examining `src/stage5_eval/stats.py::mcnemar_test()` and `src/stage5_eval/run.py` reveals two issues in how paired significance tests and Holm corrections are computed:

1. **Asymptotic McNemar at small discordant counts:** `mcnemar_test()` previously ran `statsmodels.stats.contingency_tables.mcnemar(..., exact=False, correction=True)` (the continuity-corrected chi-square statistic `(|b - c| - 1)^2 / (b + c)`) for all non-zero `b + c`. When discordant pairs `b + c < 25`, the chi-square normal approximation is unreliable; standard practice is to switch to the exact two-sided binomial test (`exact=True`) whenever `b + c < 25`.
2. **Metric mismatch in the Holm-corrected secondary family:** In `src/stage5_eval/run.py` (following `stages/stage_5.md` R6), `holm()` adjusts the p-values from `mcnemar_test()`, which tests **per-image accuracy** (micro-averaged correctness), whereas every effect size `delta` and `ci` in `comparisons.csv` and the primary hypothesis test **macro-F1**. Because classes are imbalanced (`triangle` `n_test = 572` vs. `ellipse` `149` and `diamond` `150`), accuracy and macro-F1 can diverge in both magnitude and significance.

**Fix:**
- Set `EXACT_BELOW = 25` in `src/stage5_eval/stats.py::mcnemar_test()` so `exact = (b + c < EXACT_BELOW)`.
- Compute two-sided bootstrap p-values directly from the same paired bootstrap macro-F1 distribution used for the CIs (`p_two_sided = min(1.0, 2.0 * (min(sum(deltas <= 0), sum(deltas >= 0)) + 1) / (n_boot + 1))`) and apply `holm()` to those `p_raw` values, retaining McNemar as a descriptive accuracy check only (`p_mcnemar`).

## Validation
The team updated `src/stage5_eval/stats.py` (`EXACT_BELOW = 25` in `mcnemar_test()` and `p_two_sided` in `cluster_bootstrap()`), `src/stage5_eval/run.py` (`secondary[lbl]["p_holm"]` computed from `boot["p_two_sided"]`, while storing `p_mcnemar` separately), and `src/stage5_eval/robust.py` (`_family()`). Verified by `tests/stage5/test_iteration3_repairs.py::test_mcnemar_is_exact_for_few_discordant_pairs` (`10` discordant pairs yielding `2 * 0.5 ** 10`) alongside `tests/stage5/test_stats.py::test_mcnemar_mission_m2` (`b=30, c=50`, chi-square `4.5125`, `p=0.0336`). Note that `tables.py::comparisons_rows()` for the legacy `test` split table still formats `mcnemar["p_value"]` into its `p_raw` column while `status5.json` records both `p_raw` (bootstrap) and `p_mcnemar` explicitly.

## Our decision
**Verdict: Stands.** Fixed in iteration 3 (`src/stage5_eval/stats.py`, `src/stage5_eval/run.py`, `src/stage5_eval/robust.py`, `docs/crisp_dm/iteration_3/preregistration.md`). McNemar now switches to the exact binomial when `b + c < 25` and is purely descriptive; Holm correction in both `run.py` and `robust.py` operates on two-sided bootstrap p-values for macro-F1.

## Measured effect
In iteration 3 on `fresh_holdout_2` across 23 perturbation levels (`status5.json`, `robust_comparisons.csv`), all four secondary comparisons (`A1 vs A0 +6.98`, `B vs A0 +7.52`, `A2 vs A1 +2.22`, `A2 vs B +1.68`) use macro-F1 bootstrap p-values (`p_raw = 0.001`, `p_holm = 0.004`). On clean `fresh_holdout_2`, `A2 vs A0` has bootstrap `p_raw = 0.004` (`p_holm = 0.016`) alongside descriptive `mcnemar_clean` (`b = 40, c = 68, statistic = 6.75, p_value = 0.0094`). On the reused test split (`status5.json`), `A1 vs A0` records `p_raw = 0.116`, `p_mcnemar = 0.194`, and `p_holm = 0.464`.

---

## Upgraded Audit Entry (A24)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)

### A24 — McNemar not exact for small counts; metric mismatch

**Expanded reasoning — two distinct defects.**

1. **Asymptotic-at-small-`b+c`:** continuity-corrected chi-square `(|b-c|-1)^2/(b+c)` is unreliable when `b+c < 25`; the exact two-sided binomial is standard. Fix: `EXACT_BELOW = 25`, `exact = (b+c < EXACT_BELOW)`. Pinned by `test_mcnemar_is_exact_for_few_discordant_pairs` (10 pairs → `2*0.5^10`).
2. **Metric mismatch:** `holm()` corrected McNemar p-values, which test **per-image accuracy** (micro-averaged), while every `delta`/`ci` and the primary test are **macro-F1**. With imbalance (`triangle` 572 vs `ellipse` 149), accuracy and macro-F1 can diverge in both magnitude and significance — so the Holm family was testing a *different hypothesis* than the effect sizes it sat beside. This is a **hypothesis-family/effect-size mismatch**, arguably worse than the exactness issue because it silently changes *what is being claimed*.

**Deepened fix.** `p_two_sided` from the *same* paired bootstrap macro-F1 distribution (`min(1, 2*(min(#<=0,#>=0)+1)/(B+1))`), `holm()` on those, McNemar retained as descriptive `p_mcnemar` only. Iteration-3 numbers make the distinction concrete: `A2 vs A0` clean has bootstrap `p_raw=0.004` (`p_holm=0.016`) beside descriptive `mcnemar_clean` (`b=40, c=68, stat=6.75, p=0.0094`) — the two agree in direction but are now *correctly labeled*. The audit fairly notes a residual: `tables.py::comparisons_rows()` for the *legacy* test-split table still formats `mcnemar["p_value"]` into `p_raw`, a documentation/legacy-rendering inconsistency worth flagging for a future cleanup (it does not affect `status5.json`, which records both explicitly).

