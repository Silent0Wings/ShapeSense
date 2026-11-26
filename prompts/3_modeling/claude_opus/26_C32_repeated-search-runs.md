# 3_modeling - C32: Repeated search runs 
[14_real_opus-sub-agents-check-gemini-speed-report.md](../cross_critique/14_real_opus-sub-agents-check-gemini-speed-report.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C32 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, src/stage4_train/search.py, src/stage4_train/train.py, tests/stage4/test_search_iter3.py, docs/crisp_dm/iteration_3/preregistration.md, docs/crisp_dm/iteration_3/search/winners.json, commit 69dcb02



## Prompt
Before we launch the iteration 3 search I counted the planned trainings in `src/stage4_train/search.py`: 200 runs. Some of them look like the same trial twice, for example the grid cell at lr 0.003 and dropout 0.2 on top of a setting that was already trained with exactly those values. Is it safe to reuse the finished result instead of training it again, and how do we detect "identical" reliably? We do not want to change any trial limit in the pre-registration.

## Response
Yes, if "identical" is defined strictly and the training is deterministic. Both hold here.

**Where the 200 come from.** Augment 24 + B generator 16 + A2 generator 16 + A2 shares 12 + P pretraining 12 = 80 phase trials; a 3 x 2 grid for five arms = 30; grouped CV on each arm's top 5 settings over 3 folds = 75; confirmation on seeds 0, 1 and 2 for five arms = 15. Total 200.

**Where the repeats are.** Two places, by construction:
- **Grid.** Every phase trial uses the starting hparams, lr 0.003 and dropout 0.2, on seed 0. The grid for A1, B, A2 and P starts from that arm's best phase setting, so its lr 0.003, dropout 0.2 cell is that same trial. A0 has no phase trials, so it has no repeat. That is 4.
- **Confirmation.** The seed 0 confirmation run of each arm's chosen setting is the trial it was chosen from. That is 5.

4 + 5 = 9, so 191 runs actually train.

**Why reuse is safe.** Each step draws from its own generator derived from the run seed, the epoch and the step (`sampling.step_rng`), so the same settings give the same batches, the same model and the same scores. Retraining would reproduce the number, not add evidence. Reuse also does not change any limit: the 9 still count as trials of their phase, and the reported trials per arm stay as pre-registered.

**How to detect identical settings.**
1. Build the key from everything that defines a trial: arm, seed, overrides, hparams and fold. Serialise with `json.dumps(..., sort_keys=True)` so dict order cannot create false misses.
2. In `execute`, drop any pending spec whose key matches a finished result, and return the finished result under the new run name.
3. In `run_trial`, also check the `settings` saved in `result.json` before reusing it, so a stale folder with other settings is retrained, not reused.
4. Keep the recipe fingerprint check on top: a run recorded under another recipe is never reused, so a code or budget change forces a retrain.

**What must not be merged.** A CV fold run is never the same trial as a full-data run, even with equal hparams, because `fold` is in the key. Likewise seeds 1 and 2 are never reused from seed 0.

## Validation
- `src/stage4_train/search.py`: `_settings` takes arm, seed, overrides, hparams and fold; `execute` reuses "any finished trial with exactly the same settings"; the grid and confirmation phases pass the earlier results as `finished`.
- `tests/stage4/test_search_iter3.py` has `test_execute_reuses_only_a_trial_with_identical_settings`.
- `docs/crisp_dm/iteration_3/preregistration.md` keeps the iteration 2 search spaces and trial limits.

## Our decision
Repeated search runs: 9 of the 200 search runs repeated a finished trial with identical settings -> those 9 reuse the finished result, so 191 runs train. Identical settings give the same result, so training them again adds nothing. No trial limit changes.

## Measured effect
191 trainings instead of 200, with 9 results reused (`iteration_log.json`). The winners and trials per arm (A0 6, A1 30, B 22, A2 34, P 18) are in `docs/crisp_dm/iteration_3/search/winners.json`. No separate time saving was recorded.

---

## Deterministic Trial Deduplication & Content-Addressable Caching (`C32`)

### Metadata & Lineage

* **Entry ID / Type:** `C32` (`change`, `3_modeling`)
* **Date:** `2026-11-09`
* **Owner / Proposed By:** `40256377` / `opus_medium_5.5` (`proposed`)
* **Primary Artifacts:** `src/stage4_train/search.py`, `src/stage4_train/train.py`, `tests/stage4/test_search_iter3.py`, `docs/crisp_dm/iteration_3/search/winners.json`, commit `69dcb02`

### Combinatorial Search Decomposition (200 Planned vs. 191 Executed)

Iteration 3's pre-registered search space comprised **200 nominal trial specifications** across four sequential phases:

1. **Phase 1 — Data-Stream & Generator Search (`80` trials):** `24` augmentation trials + `16` `B`-generator trials + `16` `A2`-generator trials + `12` `A2` batch-share trials + `12` `P` pretraining trials (`lr=0.003`, `dropout=0.2`, `seed=0`).
2. **Phase 2 — Per-Arm Hparam Grid (`30` trials):** `3 (lr) × 2 (dropout) × 5 arms (A0, A1, B, A2, P)` anchored on each arm's Phase 1 winner (`seed=0`).
3. **Phase 3 — Grouped Cross-Validation (`75` trials):** Top `5` candidate configurations per arm $\times$ `3` `phash_group` folds $\times$ `5` arms.
4. **Phase 4 — Multi-Seed Confirmation (`15` trials):** Winning configuration per arm $\times$ `3` seeds (`[0, 1, 2]`) $\times$ `5` arms.

#### Exact Algebraic Origin of the 9 Duplicates

* **4 Grid Collisions:** For arms `A1`, `B`, `A2`, and `P`, the `(lr=0.003, dropout=0.2)` grid cell atop the Phase 1 winner reproduces the exact Phase 1 winning trial (`A0` has no Phase 1 trials $\rightarrow$ `0` collisions).
* **5 Confirmation Collisions:** For all five arms (`A0`, `A1`, `B`, `A2`, `P`), the `seed=0` confirmation trial duplicates the exact trial from which that arm's winner was selected.

### Canonical Equivalence Key & Cache Safety Invariants

Because `sampling.step_rng(seed, epoch, step)` guarantees bit-exact trajectory determinism for identical specifications, `src/stage4_train/search.py` implements two-tier deduplication without altering pre-registered phase trial budgets:

1. **In-Memory Spec Canonicalization (`_settings`):** Constructs a tuple of `(arm, seed, overrides, hparams, fold)` serialized via `json.dumps(..., sort_keys=True)` to eliminate dictionary key-ordering drift. `execute()` filters pending specs against completed trials and aliases the cached result under the new trial identifier.
2. **On-Disk Artifact Verification (`run_trial`):** Validates both the embedded `settings` object inside `result.json` and the global **recipe fingerprint** before reusing any disk artifact, preventing stale directory collisions or cross-recipe contamination.
3. **Isolation Boundaries:** Explicitly includes `fold` (`None` vs. `0/1/2`) and `seed` in the canonical key so full-dataset runs and CV fold runs never alias.

