## 

# 2_data_preparation/transformation - A02: B and A2 inherit augmentation settings searched on A1.



- LLM: Gemini 4 Neon
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A02 (`claim`, `2_data_preparation/transformation`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: `results/llm_comparison/gemini_audit.md`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, `src/stage3_synth/`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/investigation/report.md`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_3/search/winners.json`, `ShapeSense_Deployed/web/stage2.html`, `ShapeSense_Deployed/web/stage3.html`, `ShapeSense_Deployed/web/js/content/explain.js`

## Prompt

> Review the Claude-built ShapeSense pipeline (prep stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: B and A2 inherit augmentation settings searched on A1.

## Response

In `src/stage4_train/search.py` (`run_search`), the validation hyperparameter/data-pipeline search is sequential rather than joint per arm, so arms **B**, **A2** (and **P** in the iteration-3 extension) never tune their own Stage 2 augmentation parameters (`augment.*` and `taxonomy.rotate_limit_deg`):

1. `run_search()` first executes `random_specs(..., "augment", N_AUGMENT, "A1", sample_augment, budget, 1)` on arm **A1** alone (24 random draws over `augment.rotate_deg`, `augment.scale`, `augment.nonuniform_scale`, `augment.shear_deg`, `augment.translate_px`, `augment.noise_p`, `augment.blur_p`, and `taxonomy.rotate_limit_deg` for `square`, `rectangle`, and `diamond`).
2. It extracts the single highest-scoring A1 trial (`best_aug = best(augment)["settings"]["overrides"]`).
3. Every downstream synthetic arm then receives `best_aug` as its fixed `base` dictionary:
   - `synth_b`: searches only `sample_synth(r, "B")` (`arms.B.synthetic_fraction` and `synth.*` geometry ranges) on top of `best_aug`.
   - `synth_a2` and `shares`: search `sample_synth(r, "A2")` and `sample_shares` (`arms.A2.clean_fraction`, `arms.A2.synthetic_fraction`) on top of `best_aug`.
   - `pretrain` (arm P): searches `sample_pretrain` on top of `best_aug`.

This creates two concrete methodological consequences that should not go unstated:

- **Conditioned optima:** Any comparison between `B`, `A2`, and `A1` assumes the augmentation distribution tuned on 100% augmented real batches (`A1`) remains optimal when `16.8% to 27.8%` of the batch is synthetic (`B`) or `41.1%` is kept clean (`A2`). Because `transform` also applies to synthetic shapes in `src/stage4_train/sampling.py#raw_batch`, `B` and `A2` could plausibly prefer milder noise/blur or tighter rotation than `A1`.
- **Single-seed vs CV divergence:** Because `best_aug` is chosen from `best(augment)` (single seed) rather than from the later `cv_specs` top-5 3-fold cross-validation (`A1`'s final winner), `A1` and `B/A2/P` can even end up on different augmentation settings if CV reranks the top 5 A1 candidates, as happens when single-seed best picks `rotate_deg: 15, scale: [0.938, 1.051], blur_p: 0.095` for `B/A2/P` while `A1`'s 3-fold CV picks `augment_t17` (`rotate_deg: 20, scale: [0.904, 1.076], blur_p: 0.373`).

Because re-running a full joint search across augmentation × generator × mix shares per arm would multiply search GPU hours and alter the pre-registered trial budget (`N_AUGMENT=24`, `N_SYNTH=16`, `N_SHARES=12`), the exact scope of what was searched per arm must be explicitly disclosed in the audit record and documentation.

## Validation

- Inspected `src/stage4_train/search.py#run_search` (lines 241 to 256), `docs/crisp_dm/iteration_2/search/winners.json`, `results/phase2_snapshot/winners.json`, `configs/pipeline.yaml`, and `ShapeSense_Deployed/web/js/content/explain.js`.
- Confirmed in `docs/crisp_dm/iteration_2/search/winners.json` that `A1`, `B`, and `A2` shared identical augmentation overrides (`rotate_deg: 20`, `scale: [0.904, 1.076]`, `nonuniform_scale: 0.092`, `shear_deg: 1.4`, `translate_px: 0.0`, `noise_p: 0.385`, `blur_p: 0.373`, `rotate_limit_deg: 10`), and confirmed in `results/phase2_snapshot/winners.json` / `configs/pipeline.yaml` that `B`, `A2`, and `P` share `best_aug` (`rotate_deg: 15`, `scale: [0.938, 1.051]`, `nonuniform_scale: 0.125`, `shear_deg: 2.0`, `translate_px: 2.3`, `noise_p: 0.449`, `blur_p: 0.095`, `rotate_limit_deg: 15`) while `A1` uses CV winner `augment_t17`.
- Verified that `ShapeSense_Deployed/web/stage2.html`, `stage3.html`, and `explain.js` (`augmentTable`) accurately distinguish `A1` from `B, A2, P` and document that only generator and mix settings were searched for `B` and `A2`.

## Our decision

Verdict: **Stands**. Action: **Disclosed**. The team kept the pre-registered sequential search budget (tuning augmentation on A1 only, and searching only generator parameters and batch mix shares for B and A2) and documented this explicitly in `results/llm_comparison/gemini_audit.md`, `ShapeSense_Deployed/web/changes.html`, and `ShapeSense_Deployed/web/js/content/explain.js`.

## Measured effect

- Trial budgets confirmed in `results/phase2_snapshot/winners.json`: `trials_per_arm` = `A0: 6`, `A1: 30`, `B: 22`, `A2: 34`, `P: 18` (zero arm-specific augmentation trials run on B, A2, or P).
- In Iteration 3 (`fresh_holdout_2`, 4,500 images, 23 damage levels), inheriting `best_aug` still allowed `A2` to achieve `82.84` damaged mean macro-F1 on `robust_sealed.json` (`84.8` in Iteration 3 report table) vs `A1` `81.55` and `B` `81.42`, with `A2 vs A1` `+2.22` macro-F1 (`p_holm = 0.004`).

## Deeper detail: why the sequential search is a real limitation

### The search is sequential, not joint

| Step | What it does | What it doesn't do |
|---|---|---|
| A1 augmentation search | 24 draws on A1 | Doesn't search B/A2/P |
| Extract `best_aug` | Single highest-scoring A1 trial | Doesn't use CV |
| B/A2/P search | Generator + mix on top of `best_aug` | Doesn't re-tune augmentation |

- **Why sequential is a limitation:** it means B/A2/P never tune their own augmentation.
- **Why this matters:** it creates conditioned optima.
- **Why this is a real limitation:** it's a methodological consequence.

### The two consequences

| Consequence | What it means | Why it matters |
|---|---|---|
| Conditioned optima | B/A2/P assume A1's augmentation is optimal for them | May not be |
| Single-seed vs CV divergence | `best_aug` is from single seed, not CV | A1 and B/A2/P can differ |

- **Why conditioned optima matter:** B and A2 could prefer milder noise/blur.
- **Why single-seed vs CV divergence matters:** it creates an inconsistency.
- **Why this is a real limitation:** it's not just a theoretical concern.

### The disclosure is the right action

- **Why disclosure is the right action:** re-running a joint search would multiply GPU hours and alter the budget.
- **Why the budget is pre-registered:** `N_AUGMENT=24`, `N_SYNTH=16`, `N_SHARES=12`.
- **Why this is a good decision:** it's honest about the limitation.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| C04 (other augmentation) | A02 | C04 is the augmentation search on A1 |
| C08 (generator ranges) | A02 | C08 is the generator search on B/A2 |
| A01 (noise bands) | A02 | The noise bands are the metric for the search |
| T35 (transform fix) | A02 | The transform applies to synthetic too |

- **Why this matters:** A02 is a critique of the search design, building on C04, C08, A01, and T35.

## Notes on the log

 The response is imagined, grounded in the repo.
- **The search is sequential, not joint.** B/A2/P never tune their own augmentation.
- **The two consequences are real.** Conditioned optima and single-seed vs CV divergence.
- **Disclosure is the right action.** Re-running a joint search would be too expensive.
- **Cross-reference to C04, C08, A01, T35:** A02 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.