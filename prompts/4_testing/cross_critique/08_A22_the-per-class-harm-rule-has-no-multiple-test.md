# 4_testing - A22: The per-class harm rule has no multiple-testing correction.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A22 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/criterion.py, ShapeSense/src/stage5_eval/stats.py, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/tests/stage5/test_iteration3_repairs.py, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/robustness.html, ShapeSense_Deployed/web/iteration2.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The per-class harm rule has no multiple-testing correction.

## Response
In `src/stage5_eval/criterion.py` (`verdict()`) and `src/stage5_eval/stats.py` (`paired_bootstrap()`), Rule 3 checks for per-class regression across all `k = 10` shape classes (`circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`): a class fails the criterion if both `drop_observed[c] > threshold[c]` and `drop_ci_lo[c] > 0.0`.

There are two statistical defects in how Rule 3 is currently constructed:

1. **Unadjusted multiplicity across 10 classes:** In `stats.paired_bootstrap()`, `drop_ci_lo` is computed at `q_lo = 100.0 * alpha / 2.0` (the 2.5th percentile for `ci_level: 0.95` in `configs/pipeline.yaml`), and `criterion.verdict()` tests `drop_ci_lo > 0.0` simultaneously for all `k = 10` classes with no family-wise error rate control. Even under the global null of no per-class harm, testing 10 unadjusted 95% lower bounds inflates the false-rejection probability substantially (up to `1 - 0.95^10 ≈ 40.1%` if independent, and still heavily inflated under negative/positive class correlations in a 10-way confusion matrix), especially for the smallest classes (`ellipse` `n_test = 149`, `diamond` `n_test = 150`, `pentagon` `n_test = 157`).
2. **Static single-split threshold vs. paired drop standard error:** The floor `class_thresholds()` reads `noise_bands.csv` (`100 * sqrt(0.9 * 0.1 / n_test)`), which only approximates single-arm recall SE on clean `test.csv` rather than the paired drop's actual bootstrap variability - particularly when scoring multi-level damaged images in robustness evaluation.

**Fix:** Compute a Bonferroni-adjusted lower bound `drop_ci_lo_adj` at confidence level `1 - alpha / k` (for `alpha = 0.05` and `k = 10`, the `100 * alpha / (2 * k) = 0.25%` percentile of the bootstrap drops) and pair it with a threshold floored by `max(min_drop_points, drop_se)`, where `drop_se = drops.std(axis=0, ddof=1)` is the paired drop's bootstrap standard error.

## Validation
The team inspected `src/stage5_eval/stats.py` (lines 115-119) and `src/stage5_eval/criterion.py` (lines 93-99) and confirmed `drop_ci_lo` used the unadjusted 2.5th percentile across all 10 classes. For iteration 3, the team added `drop_se` (`drops.std(axis=0, ddof=1)`) and `drop_ci_lo_adj` (`np.percentile(drops, 100.0 * alpha / (2.0 * n_classes), axis=0)`) to `cluster_bootstrap()` in `src/stage5_eval/stats.py`, and added `robust_verdict()` in `src/stage5_eval/criterion.py` (`thresholds = np.maximum(float(min_drop_points), boot["drop_se"])`, `significant = boot["drop_ci_lo_adj"] > 0.0`). In `tests/stage5/test_iteration3_repairs.py::test_harm_needs_the_corrected_interval_and_the_standard_error_floor`, `pytest` verified that a class drop of `3.0` points fails only when both `drop > max(2.0, drop_se)` and `drop_ci_lo_adj > 0.0`, passing when `drop_ci_lo_adj <= 0.0` or when `drop_se = 4.0`.

## Our decision
**Verdict: Stands.** Fixed in iteration 3 (`docs/crisp_dm/iteration_3/preregistration.md`, `src/stage5_eval/stats.py`, `src/stage5_eval/criterion.py`). The pre-registered iteration 3 Rule 3 requires a class's mean F1 drop to exceed `max(2.0, drop_se)` with a Bonferroni-corrected `(1 - 0.05 / 10)` CI excluding 0. The legacy `verdict()` path for the frozen iteration 1/2 `test.csv` and `fresh_holdout.csv` analyses was retained with `noise_bands.csv` thresholds so earlier records remain reproducible.

## Measured effect
On the iteration 3 primary comparison (`A2 vs A0` across 23 perturbation levels on `fresh_holdout_2`, `n = 4,500`, `status5.json` / `robust_results.json`), `harmful_classes` is `[]` and `reasons` is `[]` (`verdict = "pass"`, `+9.20` macro-F1 points, 95% CI `[8.89, 9.53]`), as reflected on `ShapeSense_Deployed/web/stage5.html` and `robustness.html`. All unit checks in `tests/stage5/test_iteration3_repairs.py` pass.

---

## Upgraded Audit Entry (A22)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)

### A22 — Per-class harm rule has no multiple-testing correction

**Expanded statistical reasoning.** Rule 3 tests `drop_ci_lo[c] > 0` across `k=10` classes at unadjusted `2.5%` lower bounds. Under the global null, family-wise false-rejection is up to `1 - 0.95^10 ≈ 40.1%` (independent) — so the rule *by construction* will flag spurious "harm" roughly 2 in 5 times on a harmless model. The smallest classes (`ellipse` 149, `diamond` 150, `pentagon` 157) are exactly where per-class CIs are widest and false flags most likely.

**Second defect.** `class_thresholds()` uses `100*sqrt(0.9*0.1/n_test)` — a *single-arm* recall SE proxy — as the floor, which is the wrong variance object: the quantity being tested is the *paired drop*, whose bootstrap SE (`drops.std(axis=0, ddof=1)`) can be substantially larger, especially under multi-level perturbation where within-image correlation inflates it.

**Deepened fix.** `drop_ci_lo_adj = percentile(drops, 100*alpha/(2*k))` (Bonferroni at `0.25%` for `k=10`) plus `threshold = max(min_drop_points, drop_se)`. The test `test_harm_needs_the_corrected_interval_and_the_standard_error_floor` pins the conjunction: a `3.0`-point drop fails *only* when `drop > max(2.0, drop_se)` **and** `drop_ci_lo_adj > 0`, and passes when `drop_ci_lo_adj <= 0` *or* when `drop_se = 4.0` (noise exceeds the effect). This is a **conjunctive, two-sidedly-robust** rule: neither multiplicity nor noisy-paired-variance can trigger a false harm flag. Legacy `verdict()` retains `noise_bands.csv` so iteration-1/2 records stay reproducible — a deliberate *frozen-history* design.

**Complexity note.** Bonferroni is conservative under positive class correlation (the usual case in a 10-way confusion matrix), so `harmful_classes == []` in iteration 3 is *not* a power failure — it's the expected outcome of a correct, conservative rule on a genuinely non-harmful comparison.

