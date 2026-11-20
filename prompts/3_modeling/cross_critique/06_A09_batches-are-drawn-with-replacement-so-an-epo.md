# 3_modeling - A09: Batches are drawn with replacement, so an epoch does not cover every image.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A09 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/sampling.py, src/stage4_train/train.py, configs/pipeline.yaml, results/phase2_snapshot/split_stats.csv, ShapeSense_Deployed/web/stage4.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Batches are drawn with replacement, so an epoch does not cover every image.

## Response
In `src/stage4_train/sampling.py`, Stage 4 does not iterate over a shuffled permutation of the training set (`n_train = 12,405`). Instead, `BatchStream.epoch` generates `steps = 49` independent batches (`configs/pipeline.yaml#train.steps_per_epoch: 49`, computed by `required_steps_per_epoch` as `ceil(12405 / 256)`), and each step calls `raw_batch` with an isolated `step_rng(seed, epoch, step)`:

- `_labels_for_batch` allocates class-balanced labels (`256 / 10 ≈ 25.6` per class for `A0`/`A1`; fewer real labels for `B` and `A2`).
- `sample_real_indices` (lines 116-136) samples uniformly **with replacement** within each class (`pool[rng.integers(0, pool.size, size=pos.size)]`).

Because each step draws independently with replacement - and draws equal counts per class regardless of class size (`pentagon` has `680` training images while `triangle` has `2,351`) - an "epoch" of 49 steps (`12,544` total draws in `A0`/`A1`, `9,065` real draws in Iteration 2 `B`) neither guarantees coverage of all `12,405` training images nor visits every image once before moving to the next epoch. On average, in any single epoch of `A0`, a substantial fraction of images in the largest classes are skipped while images in smaller classes are seen multiple times.

This is consistent with Decision 11 (class-balanced batches) and Decision 13 (fixed step budget per arm), so it is not a bug in the sampling code, but calling the 49-step block an "epoch" can mislead readers who assume full-dataset traversal per epoch. It should be explicitly disclosed in the Stage 4 specification and report.

## Validation
The team verified `sample_real_indices`, `BatchStream`, and `required_steps_per_epoch` in `src/stage4_train/sampling.py` and `src/stage4_train/train.py`, along with `configs/pipeline.yaml`:
- Confirmed `n_train = 12,405` (`split_stats.csv`), `batch_size = 256`, and `steps_per_epoch = ceil(12405 / 256) = 49`.
- Confirmed that class-balanced sampling with replacement is required so that every arm (`A0`, `A1`, `B`, `A2`, `P`) executes the exact same 49 optimizer steps per epoch (`1,470` steps over 30 epochs in Iteration 2; `2,940` steps over 60 epochs in Iteration 3) without running out of minority-class samples (`pentagon: 680`, `diamond: 700`, `ellipse: 701`) mid-epoch or introducing epoch-boundary imbalance.

## Our decision
- **Team verdict: `Stands` (`Disclosed`).** Gemini 4 Neon's observation is exact. No code change was needed because fixed 49-step epochs with class-balanced, with-replacement sampling are intentional under Decisions 11 and 13; the team disclosed the exact definition ("an epoch is a fixed 49 steps, by design") in `gemini_audit.md` and the Stage 4 documentation.

## Measured effect
- **Sampling budget invariant:** Every main run executes exactly `49` steps per epoch (`batch_size = 256`, `12,544` total samples/epoch) across `12,405` stored training images (`n_train`), verified by `checks.same_steps_every_run: true` in `docs/crisp_dm/iteration_2/data/stage4_status.json` and `results/phase2_snapshot/status4.json`.

---

## With-Replacement Stratified Batch Sampling vs. Epoch Coverage Semantics (`A09`)

### Claim Metadata

* **Entry ID:** `A09` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `winning-decision (70% tier)`
* **Grounding Artifacts:** `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, `configs/pipeline.yaml`, `results/phase2_snapshot/split_stats.csv`, `results/phase2_snapshot/status4.json`

### Mechanistic & Statistical Analysis

Stage 4 does not iterate over a shuffled without-replacement permutation of the $N = 12,405$ training images. Instead, `BatchStream.epoch` generates $S = 49$ independent mini-batches (`required_steps_per_epoch = ceil(12405 / 256)`), where each step calls `sample_real_indices` using `step_rng(seed, epoch, step)` to sample uniformly **with replacement** within each class (`pool[rng.integers(0, pool.size, size=pos.size)]`).

Because the training set is imbalanced across the 10 shape classes (ranging from $N_{\text{pentagon}} = 680$ to $N_{\text{triangle}} = 2,351$) while every batch allocates $\approx 25.6$ draws per class (`A0`/`A1`), class-wise sampling frequencies per 49-step epoch differ substantially:

* **Expected draws per class per epoch (`A0`/`A1`):** $M_c = 12,544 / 10 = 1,254.4$ draws.
* **Expected fraction of unique images visited in a single epoch:** $1 - (1 - 1/N_c)^{M_c} \approx 1 - e^{-M_c / N_c}$:
  * **Pentagon ($N_c = 680$):** $\approx 84.2\%$ unique coverage per epoch (mean $1.84$ visits/image).
  * **Triangle ($N_c = 2,351$):** $\approx 41.4\%$ unique coverage per epoch (mean $0.53$ visits/image; $\approx 58.6\%$ skipped in any single epoch).

### Resolution

* **Verdict:** **Stands** (`Disclosed`).
* **Action:** No code modification. Class-balanced with-replacement sampling is an intentional invariant required by Decisions 11 and 13 so that minority classes ($N_c \ge 680$) never deplete mid-epoch and every arm executes an identical $49$ gradient steps per epoch ($1,470$ steps in Iter 2; $2,940$ steps in Iter 3). Updated documentation to define an "epoch" explicitly as a fixed 49-step sampling block rather than a full dataset pass.

