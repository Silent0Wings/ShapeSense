# 4_testing - A19: The bootstrap treats images as independent.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A19 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/stats.py, src/stage5_eval/evaluate.py, src/stage5_eval/run.py, src/stage5_eval/fresh.py, src/stage5_eval/robust.py, tests/stage5/test_iteration3_repairs.py, docs/crisp_dm/iteration_3/preregistration.md, results/phase2_snapshot/status5.json, results/phase2_snapshot/iteration_log.json, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/changes.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The bootstrap treats images as independent.

## Response
In `src/stage5_eval/stats.py`, `paired_bootstrap(y, pred_a, pred_b, ...)` draws resamples uniformly over individual images:

```python
idx = rng.integers(0, n, size=(stop - start, n))
```

This assumes every image in the evaluation split is statistically independent, which is violated in two ways in ShapeSense:
1. **Near-duplicate `phash_group` clusters:** In `configs/pipeline.yaml` (`split.group_by: phash`, `phash_hamming_max: 2`), Stage 1 grouped near-duplicate drawings across all sources into `phash_group` clusters so near-duplicates would never straddle `train`/`val`/`test`. That guarantees near-duplicate shapes sit *together inside* the same split. Resampling individual images splits near-duplicates across bootstrap draws, artificially inflating the effective sample size and narrowing the confidence interval.
2. **Repeated images across perturbation levels (Iteration 3):** Evaluating the same 4,500 images of `fresh_holdout_2` across 23 perturbation levels (`rot15` through `occlude24`) introduces strong within-image and within-`phash_group` correlation across levels; resampling levels or images independently would severely understate variance.
3. **Source-level correlation:** The splits draw from three distinct sources (`github_handdrawn`, `kaggle_reevald`, `mendeley_elkorchi`), creating potential intra-source correlation, though a bootstrap clustered on only 3 sources is very coarse.

### Recommended fix
1. Propagate `group_ids` (`r.get("phash_group", r["image_id"])`) from manifest rows through `evaluate._rows_arrays`, `save_predictions`, `load_predictions`, and `ensemble` in `src/stage5_eval/evaluate.py`.
2. Implement `cluster_bootstrap(y, preds_a, preds_b, groups, n_classes, n_boot, rng, ci_level)` in `src/stage5_eval/stats.py` that aggregates per-cluster confusion counts (`_cluster_counts`) and draws multinomial weights `rng.multinomial(m, 1/m)` over the $m$ `phash_group` clusters, so all near-duplicates in a group enter or leave each resample together. When `preds_a`/`preds_b` has shape `(levels, n)`, score all perturbation levels on the **same** cluster resample and average their per-class F1 scores.
3. Use `cluster_bootstrap` for primary and secondary comparisons in `run.py`, `fresh.py`, and `robust.py`, and report a source-clustered `cluster_bootstrap` (`sources` as `groups`) alongside the primary interval as a sensitivity check.

## Validation
- Inspected `src/stage5_eval/stats.py` (`cluster_bootstrap`, `_cluster_counts`), `src/stage5_eval/evaluate.py` (`_rows_arrays`, `group_ids`), and `src/stage5_eval/robust.py` (`analyse`).
- Verified the two unit tests in `tests/stage5/test_iteration3_repairs.py`:
  - `test_clusters_widen_the_interval_when_images_are_near_duplicates`: tiles 300 images 8 times (`n = 2,400`, `n_clusters = 300`) and asserts `as_groups["half_width"] > 1.8 * as_single["half_width"]`.
  - `test_levels_are_averaged_and_scored_on_the_same_resample`: confirms stacked levels yield the exact same `delta` and `ci` as single-level scoring on the same resample.
- Executed in Iteration 3 (`results/phase2_snapshot/status5.json` and `docs/crisp_dm/iteration_3/preregistration.md`).

## Our decision
Verdict: **Stands**. Fixed in iteration 3 (commit `4c7cb90`) and codified in `docs/crisp_dm/iteration_3/preregistration.md`. All Stage 5 comparisons in `run.py`, `fresh.py`, and `robust.py` now use `cluster_bootstrap` over `phash_group` clusters (`2,000` resamples), with a source-clustered `cluster_bootstrap` sensitivity interval (`ci_clustered_by_source`) reported beside the primary comparison.

## Measured effect
- On Iteration 3's pre-registered primary test (`fresh_holdout_2`, 4,500 images, `n_clusters: 4500`, 23 damage levels; `results/phase2_snapshot/status5.json`): `A2 vs A0` `delta = +9.20` macro-F1 points, `phash_group`-clustered 95% CI `[8.89, 9.53]` (`[8.889, 9.527]`, PASS, also clearing the strict `ci_lo >= 1.0` reading).
- The source-clustered sensitivity check (`ci_clustered_by_source`) spans `[3.89, 9.42]` (`[3.888, 9.425]`), remaining well above `0` and `1.0`.
- Clean `fresh_holdout_2`: `A2 vs A0` `+0.64`, CI `[0.19, 1.07]`; reused `test` split: `+0.52`, CI `[-0.24, 1.22]`; first `fresh_holdout`: `+0.54`, CI `[0.10, 0.99]`. `ShapeSense_Deployed/web/changes.html` records A19 as `Stands` / `Fixed in iteration 3`.

---

## Upgraded Audit Entry (A19)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)
These entries share a central theme: **the difference between "what the statistic measures" and "what the reader will infer it measures."**

### A19 — Bootstrap treats images as independent

**Expanded statistical reasoning.** `paired_bootstrap` draws `idx = rng.integers(0, n, size=(B, n))` — i.i.d. over *images*. Three independence violations compound:

1. **`phash_group` near-duplicates:** Stage 1 deliberately clusters near-duplicates (`phash_hamming_max: 2`) so they never straddle splits. But *within* a split, resampling images splits a group across draws, treating 8 near-identical drawings as 8 independent observations. Effective `n` is inflated by the cluster-size factor; CI half-width shrinks by roughly `1/sqrt(cluster_size)`.
2. **Perturbation levels:** Iteration 3 evaluates the *same* 4,500 images across 23 levels (`rot15`…`occlude24`). Treating levels as exchangeable observations double-counts each image 23×; variance is severely understated.
3. **Source correlation:** three sources create intra-source correlation; a 3-cluster bootstrap is too coarse to use as primary but is a valid sensitivity check.

**Deepened fix rationale.** `cluster_bootstrap` aggregates per-cluster confusion counts (`_cluster_counts`) and draws **multinomial weights over `m` clusters** — so all near-duplicates enter/leave together. For multi-level `(levels, n)` predictions, it scores all levels on the *same* cluster resample and averages per-class F1, which is essential: resampling levels independently would reintroduce the correlation the fix is meant to remove. The `test_clusters_widen_the_interval_when_images_are_near_duplicates` test (300 clusters tiled 8× → half-width `> 1.8×`) is a *directional* correctness proof, not just a smoke test. Reporting `ci_clustered_by_source` beside the primary is the right sensitivity posture: primary stays pre-registered, source-clustered shows robustness to the coarsest correlation structure.

**Subtlety.** When `n_clusters == n` (no near-duplicates in a split, as in clean `fresh_holdout_2` with 4,500 clusters over 4,500 images), `cluster_bootstrap` reduces to `paired_bootstrap` — the fix is a strict generalization, not a replacement, which is why all prior results remain comparable.

