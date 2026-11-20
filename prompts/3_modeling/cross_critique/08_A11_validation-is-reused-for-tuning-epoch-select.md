# 3_modeling - A11: Validation is reused for tuning, epoch selection and the power check.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A11 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/train.py, src/stage4_train/tuning.py, src/stage4_train/search.py, results/phase2_snapshot/power.json, docs/crisp_dm/iteration_3/preregistration.md, ShapeSense_Deployed/web/stage4.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Validation is reused for tuning, epoch selection and the power check.

## Response
The single validation split (`configs/splits/val.csv`, `n_val = 2,819`) is reused at three sequential decision points without nested splitting:

1. **Hyperparameter and augmentation/generator search (`tuning.py`, `search.py`):** Trials across `lr`, `dropout`, `augment.*`, `synth.*`, and batch mix fractions are scored and ranked by `val_macro_f1` on `val_store`.
2. **Per-run checkpoint selection (`train.py` lines 450-475):** During final training of every `(arm, seed)` run, `train_one` evaluates `val_images` after every epoch and retains `best_state` and `best_probs` (`val_probs.npz`) solely by maximizing `val_macro_f1` on that same `val_store`.
3. **Pre-test power check (`results/phase2_snapshot/power.json`):** Stage 5's power gate reads those saved `val_probs.npz` files (`n_val = 2,819`) to estimate `delta_val`, `half_width_val`, and `expected_test_half_width` before reading the sealed test split.

Because both model configurations and epoch checkpoints are selected by maximizing over `val_macro_f1` on the same `2,819` images, the resulting `val_macro_f1` scores and `delta_val` exhibit selection optimism (winner's curse), and `val_probs.npz` understates uncertainty for the power check. Formal statistical claims must therefore rely exclusively on the untouched test split and fresh holdout splits, never on validation scores, and validation optimism should be explicitly disclosed.

## Validation
The team audited `src/stage4_train/train.py`, `src/stage4_train/tuning.py`, `src/stage4_train/search.py`, and `results/phase2_snapshot/power.json`:
- Confirmed `val_store` (`n_val = 2,819`) serves all three roles in Iteration 2: search (`trials_per_arm`: `A0=6`, `A1=30`, `B=22`, `A2=18`), epoch checkpointing (`val_probs.npz`), and the pre-test power check (`power.json`: `delta_val = 1.139`, `ci_val = [0.385, 1.903]`, `half_width_val = 0.759`, `expected_test_half_width = 0.765` at `n_test = 2,776`, `access_log_reads_at_power_check = 0`).
- Compared validation optimism against held-out evaluations: in Iteration 2, validation `A2` (`95.17`) led `A0` (`92.61`) by `+2.56` points across 3 seeds, whereas on the unseen `fresh_holdout` (`4,500` images) `A2 vs A0` was `+0.08` points (95% CI `[-0.41, 0.57]`).
- In Iteration 3 (`docs/crisp_dm/iteration_3/preregistration.md`, `src/stage4_train/search.py`), the team partially mitigated search overfitting by re-scoring each arm's top-5 trials via 3-fold grouped CV (`phash_group`) over pooled train+val (`folds.py`) before selecting the winner, while keeping the final verdict strictly on `fresh_holdout_2`.

## Our decision
- **Team verdict: `Stands` (`Disclosed`).** The team agreed that validation scores (`val_macro_f1` and `delta_val`) are optimistic due to reuse across search, checkpoint selection, and power estimation, and explicitly disclosed this limitation. All formal hypothesis verdicts use only the test split (Iteration 1) and the fresh holdouts (`fresh_holdout` in Iteration 2; `fresh_holdout_2` in Iteration 3), never validation.

## Measured effect
- **Validation vs. sealed holdout divergence:** Iteration 2 `A2 vs A0` appeared as `+2.56` points on reused validation (`95.17` vs `92.61`), but measured `+0.06` (`[-0.69, 0.83]`) on reused test and `+0.08` (`[-0.41, 0.57]`) on `fresh_holdout`.
- **Stage 5 power check (`power.json`):** `half_width_val = 0.759` -> `expected_test_half_width = 0.765` (`< 1.0` limit) computed with `0` test reads prior to unsealing, treated strictly as a pre-test gate alongside A25 disclosure.

---

## Multi-Stage Validation Reuse and Selection Optimism (Winner's Curse) (`A11`)

### Claim Metadata

* **Entry ID:** `A11` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `winning-decision (70% tier)`
* **Grounding Artifacts:** `src/stage4_train/train.py`, `src/stage4_train/tuning.py`, `src/stage4_train/search.py`, `results/phase2_snapshot/power.json`, `docs/crisp_dm/iteration_3/preregistration.md`

### Mechanistic & Statistical Analysis

The validation split (`configs/splits/val.csv`, $n_{\text{val}} = 2,819$) is queried across three nested selection stages without sample splitting:

1. **Hyperparameter & Generator Search:** Ranking candidate trials (`A0=6`, `A1=30`, `B=22`, `A2=18` in Iter 2) by `val_macro_f1`.
2. **Epoch Checkpoint Selection:** Selecting `best_state` and exporting `val_probs.npz` across $E_{\max}$ epochs per run by maximizing `val_macro_f1`.
3. **Pre-Test Statistical Power Gate:** Estimating $\Delta_{\text{val}}$, confidence interval half-width (`half_width_val = 0.759`), and projected test precision (`expected_test_half_width = 0.765` at $n_{\text{test}} = 2,776$) from `val_probs.npz` prior to unsealing the test set (`access_log_reads_at_power_check = 0`).

Because selection operators $\max_{\theta \in \Theta} \widehat{\text{F1}}_{\text{val}}(\theta)$ and $\max_{e \in [1..E]} \widehat{\text{F1}}_{\text{val}}(\theta^*, e)$ positively bias empirical validation estimates proportional to search cardinality $|\Theta|$, $\Delta_{\text{val}}$ exhibits upward selection optimism and understates out-of-sample variance.

### Empirical Divergence Measurement

Comparing reused validation against strictly held-out evaluation splits quantified this optimism gap directly:

* **Iteration 2 Reused Validation (`val.csv`, 3 seeds):** `A2` ($95.17$) outperformed `A0` ($92.61$) by **$+2.56$ macro-F1 points**.
* **Iteration 2 Reused Test (`test.csv`):** `A2 vs. A0` measured **$+0.06$ points** ($95\%$ CI $[-0.69, 0.83]$).
* **Iteration 2 Unseen Fresh Holdout (`fresh_holdout`, $4,500$ images):** `A2 vs. A0` measured **$+0.08$ points** ($95\%$ CI $[-0.41, 0.57]$).

To curb search-level overfitting in Iteration 3 (`docs/crisp_dm/iteration_3/preregistration.md`), the team re-ranked each arm's top-5 candidates using 3-fold perceptual-hash grouped cross-validation (`phash_group` in `folds.py`) across pooled `train + val` before locking final configurations, while restricting all formal hypothesis verdicts exclusively to `fresh_holdout_2`.

### Resolution

* **Verdict:** **Stands** (`Disclosed`).
* **Action:** Disclosed validation optimism; treated `power.json` strictly as a pre-unsealing gate and grounded all formal statistical conclusions exclusively in sealed holdout splits (`fresh_holdout` and `fresh_holdout_2`).

