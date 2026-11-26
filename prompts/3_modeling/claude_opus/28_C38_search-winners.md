# 3_modeling - C38: Search winners
[40_real_iteration-3-search-and-final-retrain.md](40_real_iteration-3-search-and-final-retrain.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C38 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, src/stage4_train/search.py, src/stage4_train/folds.py, tests/stage4/test_search_iter3.py, tests/stage4/test_iteration3.py, docs/crisp_dm/iteration_3/preregistration.md, docs/crisp_dm/iteration_3/search/winners.json, configs/pipeline.yaml, commit e9fd141



## Prompt
The iteration 3 search has finished: 191 trainings plus 9 reused results, and the script wrote `winners.json` under `artifacts/stage4/tuning_iter3/`. `configs/pipeline.yaml` still holds the iteration 2 settings for every arm. How do we freeze the new winners so the final five-seed retrain uses exactly them, and what should we check before anything goes near the sealed holdout?

## Response
Freeze in two places, from one source, and check that they agree.

**1. Commit the search record.** Copy the generated `winners.json` to `docs/crisp_dm/iteration_3/search/winners.json` unchanged. It holds, per arm, the chosen overrides and hparams, the grouped CV scores of the top 5 settings, the three-seed confirmation and the trial counts. That file is the evidence; nobody edits it by hand.

**2. Write the config from it.** For each arm in `configs/pipeline.yaml#arms`, set `hparams` and `overrides` to that arm's winner, and the arm-level shares (`synthetic_fraction`, `pretrain_fraction`) from the same entry. Move the shared budget (60 epochs, no early stopping) into `train`, because the budget rule applies to every arm alike; it should not live in one arm's overrides. Generate these lines from the JSON rather than retyping numbers.

**3. Check before the retrain.**
- Every value in `arms` equals its `winners.json` entry; a small script can compare them key by key.
- The winner of each arm is the best **clean** mean CV macro-F1 among its top 5, as pre-registered, not the best single-seed score. In this file that changes the pick for four arms: only A2's winner is also its top single-seed setting.
- The confirmation used seeds 0, 1 and 2 only, and the final retrain uses 0 to 4 for every arm.
- Perturbed validation is reported for each winner but chose nothing, so the damage in the primary test stays unseen during selection.
- No test or holdout read happened during the search. The CV folds are built from train and validation only, grouped on `phash_group`.

**4. Then retrain and freeze.** Train five seeds per arm plus the hold-out runs from the frozen config, and record the validation scores before any sealed read. If a check fails, fix the config, not the winners.

| Arm | Winner trial | Clean CV macro-F1 | Three-seed validation |
|---|---|---|---|
| A0 | `grid_A0_lr0.003_d0.2` | 93.09 | 94.19 |
| A1 | `augment_t17` | 93.34 | 95.20 |
| B | `synth_t15` | 92.67 | 95.06 |
| A2 | `synth_a2_t03` | 94.01 | 95.80 |
| P | `pretrain_t00` | 92.92 | 95.17 |

## Validation
- `docs/crisp_dm/iteration_3/search/winners.json` holds the table above, `cv_macro_f1_top5` per arm and `trials_per_arm` (A0 6, A1 30, B 22, A2 34, P 18).
- `configs/pipeline.yaml` `arms` matches it (for example B `synthetic_fraction: 0.168`, A2 `synthetic_fraction: 0.12`, P `pretrain_fraction: 0.132`, lr 0.003 and dropout 0.2 for all), with `max_epochs: 60` and `early_stopping_patience: 999` in `train`.
- `tests/stage4/test_search_iter3.py` (`test_cv_covers_every_fold_of_every_setting_at_the_short_budget`) and `tests/stage4/test_iteration3.py` (`test_folds_keep_groups_whole_and_cover_every_image`).

## Our decision
Search winners: iteration 2 settings -> winners of the iteration 3 search, frozen in `configs/pipeline.yaml` and `docs/crisp_dm/iteration_3/search/winners.json`. Chosen on grouped cross-validation over train and validation, confirmed on three seeds.

## Measured effect
Final retraining, validation macro-F1 over five seeds: A0 94.33, A1 95.27, B 95.12, A2 95.82, P 95.22, close to the three-seed confirmation values above (`iteration_log.json`). The sealed primary test later passed: A2 vs A0 +9.20 macro-F1 points on damaged images, CI [8.89, 9.53].

---

## Automated Winner Freezing & Leakage-Free Selection Governance (`C38`)

### Metadata & Lineage

* **Entry ID / Type:** `C38` (`change`, `3_modeling`)
* **Date:** `2026-11-10`
* **Owner / Proposed By:** `40256377` / `opus_medium_5.5` (`proposed`)
* **Primary Artifacts:** `docs/crisp_dm/iteration_3/search/winners.json`, `configs/pipeline.yaml`, `src/stage4_train/folds.py`, `tests/stage4/test_search_iter3.py`, `tests/stage4/test_iteration3.py`, commit `e9fd141`

### Two-Artifact Provenance & Anti-Leakage Verification

To prevent manual transcription errors and selection bias between Iteration 3's 200-trial search and the final 25-run (`5 arms × 5 seeds`) retrain:

1. **Immutable Search Ledger (`docs/crisp_dm/iteration_3/search/winners.json`):** Archived verbatim from `artifacts/stage4/tuning_iter3/winners.json` without manual edits, preserving per-arm trial counts (`A0: 6`, `A1: 30`, `B: 22`, `A2: 34`, `P: 18`), top-5 grouped CV scores, and 3-seed confirmation metrics.
2. **Programmatic Config Synchronization (`configs/pipeline.yaml`):** Populated each arm's `hparams`, `overrides`, and mixture fractions (`B.synthetic_fraction: 0.168`, `A2.synthetic_fraction: 0.12`, `P.pretrain_fraction: 0.132`) directly from `winners.json`, while elevating shared training constants (`max_epochs: 60`, `early_stopping_patience: 999`) to the global `train` block.
3. **Pre-Retrain Audit Invariants:**
   * **Selection Criterion Integrity:** Verified that every arm's winner maximized **clean 3-fold `phash_group`-grouped CV macro-F1** among its top 5 candidates—a rule that altered the selection for **4 of 5 arms** (`A0`, `A1`, `B`, `P`) relative to noisy single-seed `seed=0` scores.
   * **Holdout Blindness:** Confirmed perturbed validation metrics were logged purely for diagnostics (never used for selection) and zero test/holdout reads occurred during CV or confirmation.

### Frozen Iteration 3 Winners & Final 5-Seed Convergence

| Arm | Selected Trial ID | Clean Grouped CV Macro-F1 | 3-Seed Confirmation (`[0,1,2]`) | Final 5-Seed Retrain (`[0..4]`) |
| --- | --- | --- | --- | --- |
| **`A0`** | `grid_A0_lr0.003_d0.2` | `93.09` | `94.19` | `94.33` |
| **`A1`** | `augment_t17` | `93.34` | `95.20` | `95.27` |
| **`B`** | `synth_t15` | `92.67` | `95.06` | `95.12` |
| **`A2`** | `synth_a2_t03` | **`94.01`** | **`95.80`** | **`95.82`** |
| **`P`** | `pretrain_t00` | `92.92` | `95.17` | `95.22` |

