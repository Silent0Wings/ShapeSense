# 4_testing - A25: The power check is optimistic.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A25 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/power.py, ShapeSense/results/phase2_snapshot/power.json, ShapeSense/results/phase2_snapshot/iter1_status.json, ShapeSense/results/phase2_snapshot/status5.json, ShapeSense_Deployed/web/stage5.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The power check is optimistic.

## Response
In `src/stage5_eval/power.py::power_check()` (invoked by `src/stage5_eval/run.py::power_fn()` before any test read), Stage 5 estimates the expected primary CI half-width on `test.csv` (`n_test = 2,776`) by running `paired_bootstrap()` on the ensembles' **validation** softmax probabilities (`val_probs.npz`, `n_val = 2,819`) and rescaling by `rescale_factor(n_val, n_test) = sqrt(n_val / n_test)` (`≈ 1.008`):

`expected_test_half_width = half_width_val * sqrt(n_val / n_test)`

This estimate is systematically optimistic for three concrete reasons:

1. **In-sample selection optimism on validation (cf. A11):** Validation predictions were used for hyperparameter tuning, search winner selection, and best-epoch checkpointing (`val_macro_f1`). Because both arms fit validation slightly better and make fewer errors there than on unseen data, validation disagreement between ensembles is compressed, shrinking `half_width_val`.
2. **Unclustered bootstrap inside `power_check()`:** Even after `cluster_bootstrap()` was introduced for test/holdout comparisons, `power_check()` calls image-level `paired_bootstrap()` (i.i.d. resampling over `2,819` validation images) rather than resampling `phash_group` clusters. Near-duplicate correlation inflates actual cluster-bootstrap variance relative to i.i.d. image resampling.
3. **Fixed-model variance only:** Rescaling `half_width_val` captures image-sampling noise for fixed trained weights, not seed-to-seed training variance or perturbation-level variance in multi-level evaluations.

Consequently, `expected_test_half_width` should be interpreted strictly as an optimistic lower bound on the test CI half-width, not an exact power guarantee.

## Validation
The team inspected `src/stage5_eval/power.py` and compared `power.json` against realized Stage 5 intervals across iterations. In iteration 1 (`iter1_status.json`), `half_width_val = 0.624` gave `expected_test_half_width = 0.628` while the realized `B vs A1` test CI `[-1.17, 0.41]` had half-width `0.79`. In iteration 3 (`results/phase2_snapshot/power.json` and `status5.json`), `half_width_val = 0.759` gave `expected_test_half_width = 0.765` (with `before_first_test_read = true`, `access_log_reads_at_power_check = 0`), while the realized `reused_test` CI `[-0.24, 1.22]` had half-width `0.73` (`[-0.69, 0.83]`, half-width `0.76` in iteration 2), and the source-clustered sensitivity CI on `robust` (`[3.89, 9.42]`) was substantially wider than the `phash_group` CI (`[8.89, 9.53]`).

## Our decision
**Verdict: Stands - Disclosed.** Kept `power_check()` running on validation before the first test read (`power_check_before_test: true`), and updated documentation/interpretation to treat `expected_test_half_width` (`0.76` points in iteration 3, vs. `limit_points: 1.0`) as a rough lower bound on the interval width rather than a sharp estimate.

## Measured effect
In `results/phase2_snapshot/power.json` (`run_id: 2026-11-10T05:27:17-05:00/933815`), `n_val = 2819`, `n_test = 2776`, `factor = 1.008`, `half_width_val = 0.759`, `expected_test_half_width = 0.765`, `limit_points = 1.0`, `underpowered = false`, `access_log_reads_at_power_check = 0`, disclosed as a lower bound on `ShapeSense_Deployed/web/stage5.html`.

---

## Upgraded Audit Entry (A25)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)

### A25 — Power check is optimistic

**Expanded reasoning.** `expected_test_half_width = half_width_val * sqrt(n_val/n_test)` (`≈1.008`) assumes validation disagreement ≈ test disagreement. Three optimism sources:

1. **Selection optimism (cf. A11):** validation was used for tuning, model selection, and best-epoch checkpointing (`val_macro_f1`); both arms fit val slightly better → compressed disagreement → smaller `half_width_val`.
2. **Unclustered bootstrap:** `power_check()` uses image-level `paired_bootstrap` over 2,819 val images, not `phash_group` clusters → understates variance relative to the (post-A19) test-time cluster bootstrap.
3. **Fixed-model variance only:** rescaling captures image-sampling noise for *fixed* weights, not seed-to-seed or perturbation-level variance.

**Empirical calibration.** Iteration 1: `expected 0.628` vs realized `0.79` (under-estimate). Iteration 3: `expected 0.765` vs realized reused-test `0.73` (slight over), but source-clustered robust CI `[3.89, 9.42]` far wider than `phash_group` `[8.89, 9.53]` — confirming (2)/(3) dominate in correlated regimes. **Verdict "Stands / Disclosed"** is correct: keep `power_check()` *before the first test read* (`access_log_reads_at_power_check == 0`, `before_first_test_read == true`) — preserving its pre-read, non-leaking role — and document `0.76` as a **lower bound** on width (against `limit_points: 1.0`), not a guarantee. The pre-read timing is itself an audit-integrity property: a power check run *after* a test read would be circular.

