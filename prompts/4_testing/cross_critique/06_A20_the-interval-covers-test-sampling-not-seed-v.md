# 4_testing - A20: The interval covers test sampling, not seed variation.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A20 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/stats.py, src/stage5_eval/robust.py, src/stage5_eval/tables.py, src/stage5_eval/criterion.py, docs/crisp_dm/iteration_3/preregistration.md, results/phase2_snapshot/status5.json, results/phase2_snapshot/comparisons.csv, results/phase2_snapshot/iteration_log.json, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/changes.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The interval covers test sampling, not seed variation.

## Response
In `src/stage5_eval/stats.py`, both `paired_bootstrap` and `cluster_bootstrap` compute the 95% confidence interval by resampling evaluation rows/clusters while holding the trained ensemble predictions (`ens[reference]["preds"]` and `ens[candidate]["preds"]`, soft-voted over `seed_set: [0, 1, 2, 3, 4]`) fixed.

### Statistical implication
1. **Conditional on the 5 trained seeds:** The bootstrap CI quantifies uncertainty from sampling the test/holdout images (evaluation-set variance), **not** stochasticity from training runs (weight initialization, batch sampling order, augmentation/synthetic draws across seeds `0..4`).
2. **Risk of over-precision on narrow splits:** Although `src/stage5_eval/stats.py::per_seed_differences` computes paired seed-by-seed differences (`mean`, `std`, `same_sign`) and `src/stage5_eval/tables.py::comparisons_rows` reports `per_seed_mean_std` and `same_sign`, `src/stage5_eval/criterion.py` (`verdict` and `robust_verdict`) only gates on the test-sampling bootstrap CI (`boot["ci"][0] > 0`). If between-seed variance is large relative to test sampling variance, a comparison can show a narrow test-sampling CI that excludes 0 even when individual seeds disagree in sign (`same_sign == False`).

### Recommended handling
1. Keep the pre-registered primary statistic unchanged once a sealed split has been read - per `docs/crisp_dm/iteration_3/preregistration.md`, nothing in the primary rule or CI definition may be altered after a test read.
2. Explicitly disclose that the 95% bootstrap CI captures test-set sampling uncertainty conditional on the trained ensemble, and always report `per_seed_differences` (`mean ± std` and `same_sign` over seeds `0..4`) directly alongside every primary and secondary comparison in `robust_results` / `comparisons.csv` / `status5.json`.
3. If a future iteration wants an interval covering both training-seed and test-sample variation (e.g., a hierarchical or two-stage bootstrap over seeds and clusters), specify it up front in that iteration's pre-registration before any sealed read.

## Validation
- Inspected `src/stage5_eval/stats.py` (`cluster_bootstrap`, `per_seed_differences`), `src/stage5_eval/robust.py` (`per_seed` computation in `analyse`), `src/stage5_eval/tables.py` (`comparisons_rows`), and `docs/crisp_dm/iteration_3/preregistration.md` ("Seed variation is reported next to each interval: per-seed paired differences, their mean and standard deviation, over 5 seeds").
- Inspected `results/phase2_snapshot/status5.json` (`robust.per_seed` and `per_seed`) and `results/phase2_snapshot/comparisons.csv` to verify that per-seed paired differences, `mean`, `std`, and `same_sign` are emitted beside every ensemble CI.

## Our decision
Verdict: **Stands**. State: **Disclosed**. Because the pre-registration forbids modifying the primary statistical test after a sealed read, the team retained the `phash_group` test-sampling CI as the primary interval, explicitly disclosed its scope, continued reporting per-seed paired differences (`mean ± std`, `same_sign`) next to every comparison, and deferred any seed-inclusive interval to a future iteration's pre-registration.

## Measured effect
- In Iteration 3 on perturbed `fresh_holdout_2` (`results/phase2_snapshot/status5.json`): `A2 vs A0` ensemble CI is `[8.89, 9.53]` (half-width `0.32`), while per-seed paired differences across seeds `0..4` are `{0: +11.02, 1: +8.79, 2: +12.17, 3: +11.77, 4: +8.74}` (`mean = +10.50 ± 1.63`, `same_sign = true`), showing seed variation is ~5x wider than test sampling yet positive for every seed.
- Crucially, for secondary `A2 vs A1` on perturbed `fresh_holdout_2`, the ensemble CI is `[2.01, 2.44]` (`+2.22`), while per-seed differences are `{0: -0.67, 1: +4.17, 2: +1.83, 3: +0.02, 4: +1.10}` (`mean = +1.29 ± 1.88`, `same_sign = false`), directly flagging seed-level inconsistency despite the tight test-sampling CI (`iteration_log.json`).
- On the reused test split (`results/phase2_snapshot/comparisons.csv`): `A2 vs A0` ensemble `+0.5` `[-0.2, 1.2]` vs per-seed `1.2 ± 0.3` (`same_sign: yes`); `A2 vs A1` `-0.1` `[-0.7, 0.4]` vs per-seed `-0.0 ± 0.3` (`same_sign: no`). `ShapeSense_Deployed/web/changes.html` records A20 as `Stands` / `Disclosed`.

---

## Upgraded Audit Entry (A20)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)
These entries share a central theme: **the difference between "what the statistic measures" and "what the reader will infer it measures."**

### A20 — Interval covers test sampling, not seed variation

**Expanded statistical reasoning.** The bootstrap holds `ens[ref]["preds"]` and `ens[cand]["preds"]` (soft-votes over seeds 0–4) **fixed** and resamples evaluation rows. So the CI quantifies `Var(test-sampling | trained ensemble)`, *not* `Var(training | data)`. This is a **conditional-vs-unconditional** distinction. The audit's own numbers make the gap vivid:

- `A2 vs A0` (perturbed): ensemble CI `[8.89, 9.53]` half-width `0.32`, but per-seed diffs `{+11.02, +8.79, +12.17, +11.77, +8.74}` → `mean +10.50 ± 1.63`, `same_sign: true`. Seed std (~5×) dwarfs test-sampling half-width — the CI is *massively* over-precise as a statement about "the method," yet the sign is unanimous, so the *decision* is safe.
- `A2 vs A1` (perturbed): ensemble CI `[2.01, 2.44]`, per-seed `{-0.67, +4.17, +1.83, +0.02, +1.10}` → `mean +1.29 ± 1.88`, `same_sign: false`. **The tight CI and the seed disagreement directly conflict** — the tight test-sampling CI would mislead a reader into "A2 > A1 robustly" when seed 0 disagrees.

**Deepened verdict logic.** "Stands / Disclosed" is correct and is the *only* defensible move: the pre-registration forbids changing the primary test after a sealed read, so the team (a) keeps the primary CI, (b) mandates `per_seed_differences` (`mean ± std`, `same_sign`) beside *every* comparison, and (c) defers a seed-inclusive (hierarchical/two-stage) interval to a *future* pre-registration. Point 2 is the load-bearing fix: it converts a potentially misleading statistic into an honestly-scoped one. A reviewer should note the residual risk: a downstream consumer reading only `comparisons.csv`'s `ci` column without `per_seed_*` would still be misled — so the *placement* of `same_sign` adjacent to `ci` is itself a correctness-relevant design choice.

### Cross-Cutting Failure Signature: The Conditional-vs-Unconditional Statistic
CIs conditional on trained seeds, tests unadjusted across classes, and power run on in-sample validation all *look* rigorous and are *systematically over-precise*. The correct mitigation when the primary rule is pre-registered and sealed is **dual reporting** (`strict_pass`, `same_sign`, `drop_ci_lo_adj`, "lower bound") — never silently swapping the rule post-read.

