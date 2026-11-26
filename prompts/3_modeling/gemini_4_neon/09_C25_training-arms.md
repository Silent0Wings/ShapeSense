# 3_modeling - C25: Training arms
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C25 (`change`, `3_modeling`)
- Owner / Proposed by: 40297573 + 40211352 / gemini_4_neon + 40297573 + 40211352
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: ShapeSense/configs/pipeline.yaml, ShapeSense/configs/models/P.yaml, ShapeSense/src/stage4_train/train.py, ShapeSense/src/stage4_train/search.py, ShapeSense/src/common/config.py, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/docs/crisp_dm/iteration_3/experiments/scarcity.json, ShapeSense/results/phase2_snapshot/robust_sealed.json, ShapeSense/results/phase2_snapshot/fresh_metrics.csv, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/experiments.html


## Prompt
Would pretraining on synthetic images and then fine-tuning on real images recover the synthetic-to-real gap? Propose it as a new arm P, its schedule, and whether it should be tested or reported descriptively.

## Response
Adding a synthetic-pretraining arm (`P`) directly tests whether separating synthetic exposure from real-image training avoids the synthetic-to-real distribution mixing seen when `B` blends both domains in every batch.

### 1. Config and batch-mix design for `arms.P`
In `configs/pipeline.yaml` (and `src/common/config.py`), define arm `P` with:
- `augment: true`, `synthetic: true`, `synthetic_fraction: 0.0`, and a new `pretrain_fraction` key in `[0.0, 1.0)`.
- During the first `pretrain_epochs = int(pretrain_fraction * max_epochs)` epochs, build batches from a `pretrain_stream` with `synthetic_fraction: 1.0` and `clean_fraction: 0.0` (256 augmented synthetic shapes per batch, zero real images).
- For the remaining `max_epochs - pretrain_epochs` epochs, switch to the main `BatchStream` (`synthetic_fraction: 0.0`, 256 augmented real drawings per batch) while keeping the identical `steps_per_epoch = 49` (`batch_size = 256` on `n_train = 12,405`) so `P` runs the exact same `max_epochs * 49` optimizer steps as `A0`, `A1`, `B`, and `A2`.

### 2. Phase-transition schedule and checkpointing
Because the synthetic-only phase initializes general contour and corner filters in `SmallCNN` (`[32, 64, 128, 128]`), the real-image fine-tuning phase should drop the learning rate by a factor of `0.3` and start a fresh cosine decay (`CosineAnnealingLR` over the remaining fine-tuning steps) when switching to real images, while evaluating validation every epoch under normal `early_stopping_patience` so the best validation checkpoint can be kept at any point. If the synthetic-to-real gap is mostly a feature-initialization mismatch rather than permanent synthetic artifact memorization, `P` should match or surpass `A2` even when 100% of real training images are available.

### 3. Evaluation status: descriptive, outside Holm families
Report `P` **descriptively** against `A0` and `A2` rather than placing it into the pre-registered `evaluation.primary` or Holm-corrected `evaluation.secondary` families. Its optimal `pretrain_fraction` and real-data regime sensitivity are unknown prior to Phase 4, so adding `P` to the confirmatory family would dilute Holm power on the primary `A2 vs A0` robustness hypothesis without pre-specified priors.

## Validation
The team (`40297573`, `40211352`) implemented arm `P` in commit `1f2f15d` (`configs/pipeline.yaml`, `src/common/config.py`, `src/stage4_train/train.py`, `src/stage4_train/search.py`) and caught two flaws in Gemini 4 Neon's schedule and hypothesis during unit testing and validation experiments:
1. **Single continuous schedule & gated checkpointing (`src/stage4_train/train.py`, `tests/stage4/test_iteration3.py`):** Rather than resetting `CosineAnnealingLR` or cutting the LR at the phase switch, `train_one` keeps one continuous `AdamW` (`lr: 0.003`, `weight_decay: 0.0001`) + `CosineAnnealingLR(T_max=max_epochs * steps_per_epoch)` schedule so every arm shares identical optimization dynamics. Crucially, `train.py` adds `if epoch_idx < pretrain_epochs: continue` so synthetic-only epochs can neither trigger `best_score` selection nor count toward `early_stopping_patience` (`test_pretraining_sees_only_synthetic_and_never_picks_a_best_epoch` verifies this).
2. **Scarcity vs. full-data behavior (`docs/crisp_dm/iteration_3/experiments/scarcity.json`):** `P` did **not** beat `A2` with 100% of real data: on clean validation at 100% real data, `P` scored `94.26 ± 0.09` (`75.57 ± 1.94` damaged), matching `B` (`94.20` / `77.07`) and trailing `A2` (`95.17` / `80.29`). `P` only led under scarcity (`10%` real: `92.63` vs `A2` `92.03`, `A0` `81.31`; `25%` real: `93.54` vs `A2` `91.58`, `A0` `83.54`).
3. **Config and LOSO checks (`tests/stage4/test_iteration3.py`, `tests/stage4/test_search_iter3.py`):** Verified `validate_pipeline` rejects `pretrain_fraction >= 1.0`, `sample_pretrain` searches `arms.P.pretrain_fraction` in `[0.1, 0.6]` without touching `synthetic_fraction`, and `LOSO_ARMS` includes `P`.

## Our decision
Adopted arm `P` as a **descriptive** fifth arm in `docs/crisp_dm/iteration_3/preregistration.md`, `configs/pipeline.yaml`, `configs/models/P.yaml`, and the Stage 4 / Experiments pages (`stage4.html`, `experiments.html`). Kept Gemini 4 Neon's `synthetic_fraction: 0.0` fine-tuning split and descriptive reporting rule, but **rejected** the LR reset and synthetic-phase checkpointing in favor of a single continuous cosine schedule and real-phase-only checkpoint selection (`train.py#L467-L468`).

## Measured effect
- **Tuned `P` configuration (`winners.json`, `P.yaml`):** `pretrain_fraction: 0.132` (`7` synthetic-only epochs of `60`, `53` augmented-real epochs, `2,940` total optimizer steps), `lr: 0.003`, `dropout: 0.2`; grouped CV `92.92`, 3-seed validation mean `95.17` (`95.10`, `95.17`, `95.23`); 5-seed final validation mean `95.22`.
- **Sealed `fresh_holdout_2` descriptive results (`robust_sealed.json`, `fresh_metrics.csv`, `metrics.csv`):** `P` ensemble scored `98.0` macro-F1 on clean `fresh_holdout_2` (`A2` `98.3`, `A0` `97.8`), `82.43` mean macro-F1 across the 23 damage levels (`robust_sealed.json`: `A2` `82.84`, `B` `81.42`, `A1` `81.55`, `A0` `72.34`; `iteration_log.json` ensemble damage summary: `P` `84.3` vs `A2` `84.8`, `A0` `75.6`), and `96.2` on the test split soft vote (`95.8 ± 0.1` per-seed mean).

---

## : Gemini 4 Neon Corpus Synthesis (`C25` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C25` (`change`)
* **Logic Depth:** **High** (new arm `P` with two-phase synthetic pretraining + real fine-tuning, interacts with `C26` and `C29`)
* **Risk if Wrong:** **Medium** (descriptive arm kept out of Holm-corrected primary hypothesis families; checkpointing during synthetic epochs would corrupt selection)
* **Adoption Status:** **Adopted with correction** (descriptive `P` and `synthetic_fraction: 0.0` fine-tuning split kept; **rejected** Gemini's LR reset and synthetic-phase checkpointing in favor of one continuous 60-epoch cosine schedule and real-phase-only checkpoint selection).

### 2. Group Synthesis: Search Design and the Budget Gate (`C26` $\rightarrow$ `C12` $\rightarrow$ `C25` $\rightarrow$ `C29`, `C27`)

* **`C25`** is the arm-`P` design: synthetic pretraining then real fine-tuning, `pretrain_fraction` $\in [0.1, 0.6]$, descriptive only (kept out of the Holm families). The team **rejected** Gemini's LR reset and synthetic-phase checkpointing in favor of one continuous cosine schedule and real-phase-only checkpoint selection (`train.py#L467-L468`). Measured: `P` did *not* beat `A2` at 100% real data (`94.26` vs. `95.17` clean in scarcity experiments; `82.43` vs. `82.84` on 23-level damaged `fresh_holdout_2`), but led under extreme data scarcity (`10%` real: `92.63` vs. `92.03`; `25%` real: `93.54` vs. `91.58`).
* **`C26` $\rightarrow$ `C12` $\rightarrow$ `C25` $\rightarrow$ `C29`** forms a unified funnel: grouped 3-fold CV picks the settings (`C26`, changing `P`'s winner off rank-0 to `pretrain_t00` at `pretrain_fraction: 0.132`, 7 epochs of 60), the per-arm grid fixes the hyperparameters (`C12`), `P` is evaluated descriptively (`C25`), and the 60-epoch budget (`C29`) provides the horizon required for two-phase training.

