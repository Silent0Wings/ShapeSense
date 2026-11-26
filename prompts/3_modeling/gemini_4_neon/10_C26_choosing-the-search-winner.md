# 3_modeling - C26: Choosing the search winner
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C26 (`change`, `3_modeling`)
- Owner / Proposed by: 40304911 / 40304911
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: ShapeSense/src/stage4_train/folds.py, ShapeSense/src/stage4_train/search.py, ShapeSense/tests/stage4/test_iteration3.py, ShapeSense/tests/stage4/test_search_iter3.py, ShapeSense/results/phase2_snapshot/winners.json, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/experiments.html


## Prompt
One validation split can favour a search setting by chance. How do we re-score the top settings per arm with grouped cross-validation over train and validation, and confirm the winner on several seeds?

## Response
Scoring random-search trials on a single fixed validation split (`n_val = 2,819`) risks selecting hyperparameters or generator ranges that overfit that split's specific near-duplicate clusters. You can eliminate single-split luck without touching `test.csv`, `fresh_holdout.csv`, or `fresh_holdout_2.csv` by adding a two-stage selection funnel inside `src/stage4_train/search.py`.

### 1. Pool train + validation and split with `StratifiedGroupKFold`
Implement `pooled(train, val)` and `grouped_folds(store, n_folds=3, seed=...)` in `src/stage4_train/folds.py`:
- Concatenate `train` (`12,405`) and `val` (`2,819`) into a single `ImageStore` (`15,224` images).
- Use `sklearn.model_selection.StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)` so near-duplicate clusters never straddle train and validation folds. To prevent source-style leakage across folds, group the folds by `source_id` (or `(source_id, phash_group)`).

### 2. Re-score the top 5 settings per arm at the full budget
From each arm's search pool (`augment`, `synth`, `synth_a2 + shares`, `pretrain`, plus `grid`), extract `top_settings(candidates)` (`TOP_K = 5` distinct `(overrides, hparams)` pairs ranked by single-split `val_macro_f1`). Run all `5 * 3 = 15` fold trainings per arm (`seed = 0`) at the full `30`-epoch budget, ranking candidates by mean clean CV macro-F1 (keeping the 23 damage levels unseen during selection).

### 3. Multi-seed confirmation
Take `chosen = top[int(np.argmax(means))]` and run 3-seed confirmation (`SEEDS = (0, 1, 2)`) on the standard `train` / `val` split, reusing any matching finished trial via `execute(..., finished=candidates)` so seed 0 is not retrained needlessly.

## Validation
When `40304911` and the team implemented `folds.py` and `search.py` (commits `1f2f15d` and `686fcc9`), two assumptions in Gemini 4 Neon's proposal were caught and fixed:
1. **Grouping on `source_id` breaks class stratification (`src/stage4_train/folds.py#L4-L6`):** `ellipse` (Hand-Drawn only), `pentagon` (El Korchi only), and `diamond` (single remaining source after excluding Quick, Draw! diamonds) each belong to a single source. Grouping `StratifiedGroupKFold` on `source_id` would drop entire classes from training or validation folds. The team grouped strictly on `phash_group` (`grouped_folds`), leaving cross-source generalization to the dedicated 9-class `loso_handdrawn` runs.
2. **Short CV epoch budget (`src/stage4_train/search.py#L41`, `tests/stage4/test_search_iter3.py`):** Running `5 arms x 5 settings x 3 folds = 75` CV trials at full `60` epochs (once the budget rule adopted `e60_nostop`) would have doubled total search runtime. The team pre-registered `N_FOLDS = 3` at `CV_EPOCHS = 15` (`test_cv_covers_every_fold_of_every_setting_at_the_short_budget`), keeping CV compute bounded while preserving relative ranking.
3. **Unit & end-to-end checks:** `tests/stage4/test_iteration3.py::test_folds_keep_groups_whole_and_cover_every_image` confirmed zero `phash_group` overlap across folds and full coverage of `pooled(train, val)`. `execute()` in `search.py` was verified to reuse matching finished trials (`test_execute_reuses_only_a_trial_with_identical_settings`), saving 9 redundant runs in the 200-spec search (`191` trained).

## Our decision
Adopted the two-stage `top_settings` (`TOP_K = 5`) -> 3-fold grouped CV (`clean` CV macro-F1 only) -> 3-seed confirmation (`SEEDS = (0, 1, 2)`) design in `src/stage4_train/search.py`, **rejecting** `source_id` grouping in favor of `phash_group` (`src/stage4_train/folds.py`) and **reducing** CV length to `CV_EPOCHS = 15` as pre-registered in `docs/crisp_dm/iteration_3/preregistration.md`.

## Measured effect
- **CV re-ranking changed 4 of 5 arm winners (`results/phase2_snapshot/winners.json`):** Among the top 5 single-split settings per arm, grouped 3-fold CV selected a non-rank-0 candidate for `A0` (`93.09` vs `92.82`, `grid_A0_lr0.003_d0.2`), `A1` (`93.34` vs `93.29`, `augment_t17`), `B` (`92.67` vs `92.33`, `synth_t15`), and `P` (`92.92` vs `92.35`, `pretrain_t00`), while confirming rank-0 for `A2` (`94.01`, `synth_a2_t03`).
- **3-seed confirmation means (`winners.json`):** `A0` `94.19` (`94.14, 94.31, 94.11`), `A1` `95.20` (`95.24, 95.28, 95.09`), `B` `95.06` (`95.14, 95.05, 94.98`), `A2` `95.80` (`95.99, 95.79, 95.61`), `P` `95.17` (`95.10, 95.17, 95.23`).
- **Sealed integrity:** Zero sealed test or holdout images were touched (`folds.py` operates strictly on `ImageStore`s from `train` and `val`).

---

## : Gemini 4 Neon Corpus Synthesis (`C26` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C26` (`change`)
* **Logic Depth:** **Very High** (grouped 3-fold CV over pooled `train + val`, re-ranks winners from `C12`/Phase 1 and constrains `F02`)
* **Risk if Wrong:** **High** (CV changed **4 of 5 arm winners**; grouping on `source_id` would have dropped single-source classes like `ellipse`, `pentagon`, `diamond`)
* **Adoption Status:** **Adopted with correction** (`phash_group` grouping instead of `source_id`; `CV_EPOCHS = 15` instead of full 60-epoch budget to bound compute).

### 2. Group Synthesis: Search Design and the Budget Gate (`C26` $\rightarrow$ `C12` $\rightarrow$ `C25` $\rightarrow$ `C29`, `C27`)

* **`C26`** is the most intricate entry in the Gemini 4 Neon corpus. Single-split validation risks selecting settings that overfit one split's near-duplicate clusters (`A11`), so `C26` pools `train + val` (`15,224` images), re-scores the top-5 candidates per arm with 3-fold `StratifiedGroupKFold`, and then confirms the winner on 3 seeds (`0, 1, 2`).
* **Two critical corrections to Gemini's initial proposal:**
  1. **Grouping key (`phash_group` vs. `source_id`):** Because `ellipse`, `pentagon`, and `diamond` (post-`F01`) each reside in only one source (`F02`), grouping CV folds by `source_id` would eliminate entire classes from training/validation folds. Grouping by `phash_group` (`src/stage4_train/folds.py`) prevents near-duplicate leakage across folds while preserving all 10 classes in every fold.
  2. **Bounded CV horizon (`CV_EPOCHS = 15`):** Running 75 CV fold trainings (`5 arms × 5 candidates × 3 folds`) at the full 60-epoch budget (`C29`) would have nearly doubled total search wall time; pre-registering `CV_EPOCHS = 15` evaluated already-vetted top-5 candidates quickly while keeping primary candidate discovery at full 60-epoch fidelity (`39_real`).

