# 3_modeling - C27: Training options
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C27 (`change`, `3_modeling`)
- Owner / Proposed by: 40248536 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/src/stage4_train/experiments.py, ShapeSense/src/stage4_train/data.py, ShapeSense/src/stage4_train/sampling.py, ShapeSense/src/common/config.py, ShapeSense/tests/stage4/test_experiments.py, ShapeSense/tests/stage4/test_iteration3.py, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense_Deployed/web/experiments.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
We want to measure scarcity, equal real images and training length in validation experiments. What training options should we add (equal-real, real-fraction, training length), and under what pre-registered rule would a longer budget be adopted?

## Response
To run the iteration 3 validation experiments cleanly through the same `BatchStream`, `ImageStore`, and `train_one` code paths - without breaking Decision 13 step-budget parity or duplicating training loops - add three config-driven options validated by `src/common/config.py` and orchestrated by `src/stage4_train/experiments.py`.

### 1. `equal_real` (per-arm batch composition toggle)
- Add `arms.<arm>.equal_real: bool` (default `false`), validated in `_check_arm_extras`.
- In `src/stage4_train/sampling.py#batch_composition`, when `arm_cfg.get("equal_real")` is `True`, return `(batch_size, n_syn)` instead of `(batch_size - n_syn, n_syn)`. That keeps a full `256` real draws per step across `A0`, `A1`, `B`, and `A2`, appending `n_syn` synthetic images on top (`experiments.equal_real_specs` tests `B` and `A2` across 3 seeds = 6 runs), directly answering the outside review point on unequal real images per step.

### 2. `real_fraction` (group-safe data scarcity)
- Add `train.real_fraction: float` in `(0, 1]` (default `1.0`), validated in `validate_pipeline`.
- Add `ImageStore.real_subset(fraction, seed)` in `src/stage4_train/data.py` to sample `ceil(fraction * class_count)` images per class **by whole `phash_group`s** using a fixed `SUBSET_SEED` (`20261109` in `search.py`) so every arm sees the exact same subset at `FRACTIONS = (0.1, 0.25, 0.5, 1.0)` (`5 arms x 4 fractions x 3 seeds = 60` runs in `scarcity_specs`), while keeping `steps_per_epoch = 49` frozen.

### 3. Training-length options & pre-registered adoption rule
- Define three alternatives in `BUDGETS` against the iteration 2 baseline (`e30`: `max_epochs=30` with early stopping):
  - `e60`: `{"train.max_epochs": 60}`
  - `e30_nostop`: `{"train.early_stopping_patience": 999}`
  - `e60_nostop`: `{"train.max_epochs": 60, "train.early_stopping_patience": 999}`
- Test these across `BUDGET_ARMS = ("A0", "A1", "A2")` on 3 seeds (`27` runs in `budget_specs`).
- **Pre-registered adoption rule (`ADOPT_GAIN = 0.5`):** Switch every arm to an alternative budget **only if every tested arm (`A0`, `A1`, `A2`) gains at least `0.5` clean validation macro-F1 points** on its 3-seed mean over `e30`. If multiple options qualify, pick the one with the highest mean gain across tested arms (`max(adopted, key=lambda name: np.mean(list(gains[name].values())))`); otherwise keep `e30`. `search.py#adopted_budget()` must enforce this gate by reading `budget.json` and refusing to start the search if it is missing.

## Validation
Implemented in commit `1f2f15d` and verified by `40248536` across unit tests and the 108-trial validation experiment suite (`experiments.py` + `search.py`):
- `tests/stage4/test_experiments.py` verified exact run counts (`60` scarcity, `6` equal-real, `27` budget, `15` one-transform-on = `108` runs), unique `run_name`s, and isolated overrides.
- `tests/stage4/test_iteration3.py` confirmed:
  - `test_equal_real_keeps_a_full_real_batch_and_adds_synthetic` (`(256, 64)` vs `(192, 64)` at `25%` synthetic, `batch_size=256`) and `test_equal_real_batch_has_every_image`.
  - `test_real_subset_is_repeatable_group_safe_and_per_class` (no split `phash_group`s, identical subsets across calls, `fraction=1.0` returns `self`).
  - `test_config_rejects_a_bad_data_fraction` (`real_fraction=0.0` raises `ConfigError`).
- `tests/stage4/test_search_iter3.py::test_search_refuses_to_start_before_the_budget_rule_has_run` confirmed `adopted_budget()` raises `FileNotFoundError` until `budget.json` exists.

## Our decision
Adopted all three training options (`equal_real`, `train.real_fraction` with group-safe `ImageStore.real_subset`, and the `e60` / `e30_nostop` / `e60_nostop` budget sweep) and locked the `ADOPT_GAIN = 0.5` unanimous per-arm rule verbatim in `docs/crisp_dm/iteration_3/preregistration.md`, `src/stage4_train/experiments.py`, and `src/stage4_train/search.py`.

## Measured effect
- **Equal-real experiment (`equal_real.json`):** Keeping `256` real draws per step lowered clean validation macro-F1 on both tested arms (`B`: `94.20 -> 92.18`, `-2.03` pts; `A2`: `95.17 -> 94.66`, `-0.51` pts), closing the outside-review point empirically without altering the main batch mix.
- **Scarcity experiment (`scarcity.json`):** Measured all 5 arms across `10%`, `25%`, `50%`, `100%` real data (`60` runs); revealed `P` leads at `10%` (`92.63`) and `25%` (`93.54`), while `B` does not beat `A1` beyond augmentation at `10%` (`91.58` vs `91.56`).
- **Budget gate:** Enabled the programmatic, pre-registered transition to `e60_nostop` (`budget.json`) before the 191-trial search ran.

---

## Upgraded & Expanded: Gemini 4 Neon Corpus Synthesis (`C27` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C27` (`change`)
* **Logic Depth:** **High** (three validation experiment families + pre-registered `ADOPT_GAIN = 0.5` unanimous rule; feeds `C29` and `C26`)
* **Risk if Wrong:** **High** (`ADOPT_GAIN = 0.5` unanimous rule governs the global 30 $\rightarrow$ 60 epoch transition; `adopted_budget()` refuses to start the search without `budget.json`)
* **Adoption Status:** **Adopted verbatim** (`equal_real`, `real_fraction` with group-safe `ImageStore.real_subset`, and `e60` / `e30_nostop` / `e60_nostop` budget sweep locked in `preregistration.md`, `experiments.py`, and `search.py`).

### 2. Group Synthesis: Search Design and the Budget Gate (`C26` $\rightarrow$ `C12` $\rightarrow$ `C25` $\rightarrow$ `C29`, `C27`)

* **`C27`** adds the three experiment families (`equal_real`, `real_fraction` with group-safe `real_subset`, and the budget sweep) under one pre-registered rule: adopt a longer budget only if **every tested arm gains $\ge 0.5$** (`ADOPT_GAIN = 0.5` across `BUDGET_ARMS = (A0, A1, A2)`).
* **`C29`** applies `C27`'s rule: `e60_nostop` gains `A0 +1.99`, `A1 +0.51`, `A2 +0.71`, so $\min = 0.506 \ge 0.5 \rightarrow$ adopt. Even though `A1`'s margin (`+0.006`) is smaller than its 3-seed SD, the team enforced the pre-registered rule strictly and **rejected** Gemini's suggestion to run an extra `B`/`P` check or lower patience to `20` as post-hoc.
* **`C26`** then bounds the resulting 60-epoch search cost by running 3-fold `phash_group` CV at `CV_EPOCHS = 15` over each arm's top-5 full-run candidates.

