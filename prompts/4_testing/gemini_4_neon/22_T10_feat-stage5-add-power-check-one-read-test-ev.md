# 4_testing - T10: feat(stage5): add power check, one-read test evaluation and verdict
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T10 (`task`, `4_testing`)
- Owner / Proposed by: 40248536 / gemini_4_neon + 40248536
- Calibration: `winning-decision (70% tier)`
- Grounding sources: src/stage5_eval/criterion.py, src/stage5_eval/evaluate.py, src/stage5_eval/figures.py, src/stage5_eval/metrics.py, src/stage5_eval/placeholders.py, src/stage5_eval/power.py, src/stage5_eval/run.py, src/stage5_eval/stats.py, src/stage5_eval/tables.py, tests/stage5/test_criterion.py, tests/stage5/test_evaluate.py, tests/stage5/test_metrics.py, tests/stage5/test_placeholders.py, tests/stage5/test_power.py, tests/stage5/test_run.py, tests/stage5/test_stats.py, tests/stage5/test_tables.py, results/phase2_snapshot/comparisons.csv, results/phase2_snapshot/robust_sealed.json, docs/crisp_dm/iteration_3/preregistration.md, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/robustness.html, ShapeSense_Deployed/web/iteration2.html, git commit 8f16f26

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T10 (built, stage `4_testing`): feat(stage5): add power check, one-read test evaluation and verdict. Propose or assist with the exact implementation, checks, and configuration needed for commit `8f16f26`.

## Response
Structure `src/stage5_eval/` around pure, RNG-injected statistical modules and a strict single-read test orchestrator so sealed splits are read at most once per model, never tuned on, and never cross-imported from Stage 4:

1. **Pre-test power check (`src/stage5_eval/power.py`)**
   - Execute **before** any test-split read. Stack per-seed `val_probs.npz` files via `align_validation_probs()` and enforce row-for-row `image_id` and `label` equality across arms via `check_arm_alignment()`.
   - Run `paired_bootstrap()` on validation soft-vote predictions (`A1` vs `B`, or configured reference/candidate) and rescale the validation CI half-width by `rescale_factor(n_val, n_test) = sqrt(n_val / n_test)` to write `artifacts/stage5/power_check.json`. Disclose limited power if the projected half-width exceeds the configured limit without changing the criterion.

2. **One-read sealed evaluation and caching (`src/stage5_eval/evaluate.py`)**
   - Load models purely by file (`torch.jit.load` on `model.pt` with `PREDICT_BATCH = 1024`, or `joblib` for baselines) with zero Stage 4 imports.
   - Key cached predictions (`artifacts/stage5/predictions/<name>.npz`) by both `model_fingerprint(path)` (`sha256_path(model) + "+" + sha256_path("src/common/features.py")`) and `test_manifest_hash(config)` (hashing `configs/splits/test.csv` directly without calling `load_split`).
   - Call the injected `test_reader()` at most once per uncached model (appending one line to `artifacts/test_access.log`), and compute ensembles strictly via `soft_vote()` from cached per-seed probabilities so ensembles trigger zero additional reads.

3. **Paired statistics and locked criterion (`stats.py`, `metrics.py`, `criterion.py`)**
   - Express all F1 values in **points** (`0-100`, `F1_POINTS_SCALE = 100.0`).
   - In `stats.py`, implement vectorized `paired_bootstrap()` (`BOOT_CHUNK = 256`, resampling identical indices across both arms to avoid unpaired-CI inflation), `mcnemar_test()` (`EXACT_BELOW = 25` switching to exact binomial when discordant pairs `< 25`), `holm()` step-down correction over secondary comparisons, and `per_seed_differences()`.
   - In `criterion.py`, compute `noise_band_points(n, accuracy=0.9) = 100 * sqrt(accuracy * (1 - accuracy) / n)` (`n = 150 -> 2.45` points), `class_thresholds(bands, min_drop_points) = np.maximum(min_drop_points, bands)`, and `verdict()` passing iff:
     1. `delta >= min_gain_points` (`1.0`),
     2. `ci[0] > 0.0` (strict exclusion of `0`), and
     3. no class satisfies both `drop_observed > threshold_c` and `drop_ci_lo > 0.0`.

4. **Single-source tables, figures, placeholders, and orchestrator (`tables.py`, `figures.py`, `placeholders.py`, `run.py`)**
   - Format `(columns, rows)` strings once in `tables.py` and emit both CSV and booktabs LaTeX from the exact same formatted cells so tables never drift.
   - Render row-normalized `Blues` confusion matrices (`confusion_figure()`) and `true→pred` error galleries (`error_gallery()`, `MAX_PER_DIRECTION = 16`, `GALLERY_COLS = 8`) in `figures.py` because Stage 6 cannot read test images.
   - In `run.py`, enforce the order: power check -> one-read evaluation -> primary + Holm secondary comparisons -> criterion verdict -> tables/figures/galleries -> LOSO check on `github_handdrawn` when triggered. Ensure `status.json` records `status = "passed"` even when `metrics.verdict == "fail"`.

## Validation
- Ran the full 8-module Stage 5 unit and integration suite (`python -m pytest tests/stage5 -q`):
  - `test_criterion.py`: verified Decision 10 noise-band numbers (`150 -> 2.4495`, `572 -> 1.254`, `375 -> 1.549`), strict `ci[0] == 0.0` failure, and class-noise-band protection vs flat `2.0`-point drops.
  - `test_evaluate.py`: verified 1-read-per-model enforcement, cache hits on matching `model_fingerprint` + `test_manifest_hash`, cache invalidation on preprocessing or manifest change, and 0 reads for ensembles.
  - `test_power.py`, `test_stats.py`, `test_metrics.py`, `test_tables.py`, `test_placeholders.py`, and `test_run.py`: verified `sqrt(n_val / n_test)` scaling, `image_id` alignment guards, exact McNemar switching under 25 pairs, Holm correction, CSV/LaTeX cell identity, and `"passed"` stage status on `"fail"` verdicts.
- Ran `lint-imports` via `run_pipeline.py --check` to confirm zero imports from `src.stage4_train`.

## Our decision
The team adopted Gemini 4 Neon's entire 9-module `src/stage5_eval/` package and 8-module test suite verbatim in commit `8f16f26`. In Iteration 3, the team built cleanly on top of this design by adding `cluster_bootstrap`, `robust_verdict`, and the `fresh` / `robust` evaluation modules into Stage 5 without breaking the core one-read and pure-stat contracts.

## Measured effect
- **Commit `8f16f26`:** 18 files changed (`3,138 insertions(+), 13 deletions(-)`), establishing the complete statistical evaluation, artifact generation, and sealed-read auditing layer.
- **Project-wide sealed-read & verdict impact:** Enforced `92 of 92` expected sealed reads with zero unaccounted reads across the final audit (`docs/crisp_dm/iteration_log.json`), cleanly rejected Iteration 1 (`B vs A1 = -0.36`, CI `[-1.17, 0.41]`) and Iteration 2 (`A2 vs A0 = +0.06` / `+0.08`), and verified the pre-registered Iteration 3 pass (`A2 vs A0 = +9.20` macro-F1 points across 23 damage levels on `fresh_holdout_2`, 95% CI `[8.89, 9.53]`).

---

## Upgraded & Expanded Technical Analysis (`T10`)

### 1. Paired Resampling Variance Reduction & Pre-Test Power Scaling
- **Why Identical Resample Indices Across Arms Are Mandatory:** For two model ensembles $A$ and $B$ evaluated on the same test split, the variance of their paired macro-F1 difference is:
  $$\text{Var}(\hat{F}_1(B) - \hat{F}_1(A)) = \text{Var}(\hat{F}_1(B)) + \text{Var}(\hat{F}_1(A)) - 2\,\text{Cov}(\hat{F}_1(B), \hat{F}_1(A))$$
  Because both ensembles face the same easy and hard drawings, $\text{Cov}(\hat{F}_1(B), \hat{F}_1(A)) > 0$ is large. Drawing **identical bootstrap indices** (`BOOT_CHUNK = 256`) for both arms preserves this covariance term; independent resampling would drop $-2\,\text{Cov}$, artificially inflating the CI width by $2\text{--}3\times$.
- **Validation-to-Test Power Rescaling (`power.py`):** Before any test read (`access_log_reads_at_power_check == 0`), `align_validation_probs()` verifies exact row-for-row `(image_id, label)` alignment across all seeds and arms, computes the validation paired bootstrap half-width $h_{\text{val}}$, and projects $h_{\text{test}} = h_{\text{val}} \sqrt{n_{\text{val}} / n_{\text{test}}}$.

### 2. Zero-Read Ensemble Soft-Voting & Stage-Status vs. Hypothesis-Verdict Decoupling
- **One Read Per Uncached Seed Model, Zero Reads Per Ensemble:** `evaluate_models()` keys each seed prediction cache by `(model_fingerprint, test_manifest_hash)` where `test_manifest_hash` hashes the raw bytes of `test.csv` without invoking `load_split("test")`. Soft-vote ensembles (`soft_vote()`) average the cached `(N, 10)` probability arrays in memory, triggering **zero** additional sealed reads (`92 of 92` expected reads across all iterations, `extra_reads == 0`).
- **Execution Status (`"passed"`) vs. Scientific Verdict (`"fail"` / `"pass"`):** In `src/stage5_eval/run.py`, `status.json` records `status = "passed"` whenever the statistical pipeline executes cleanly and satisfies all audit invariants (`test_reads_ok`, `power_check_before_test`), even when `metrics.verdict == "fail"` (as in Iterations 1 and 2). Separating *pipeline execution health* from *scientific hypothesis acceptance* ensures `run_pipeline.py` can proceed to Stage 6 to compile the report documenting a negative finding without treating a refuted hypothesis as a software crash.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** `status = "passed"` on `verdict = "fail"` is correct. The stage evaluated successfully; the experiment failed. Marking the stage failed would stop the report stage and conflate the two.

**Changelog:** [1] the passed/fail distinction; [2] `test_manifest_hash` must not call `load_split`, because that would itself be a read; [3] `model_fingerprint` includes `features.py`, so feature changes invalidate the cache; [4] F1 in points avoids unit-conversion bugs against the 1.0-point threshold.

**Open questions:** Is `EXACT_BELOW = 25` a convention or a calibrated decision? Is the `sqrt(n_val / n_test)` rescaling assumption (similar distributions) stated in the preregistration?
