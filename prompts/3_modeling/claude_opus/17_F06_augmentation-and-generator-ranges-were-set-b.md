# 3_modeling - F06: Augmentation and generator ranges were set by hand, and only A1 was tuned. 

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [33_real_iteration-2-plan-tuning-and-a2.md](33_real_iteration-2-plan-tuning-and-a2.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/02_F06_augmentation-and-generator-ranges-were-set-b.md](../gemini_4_neon/02_F06_augmentation-and-generator-ranges-were-set-b.md)
- Date: 2026-11-09
- Worksheet entry: F06 (`failure`, `3_modeling`)
- Owner / Proposed by: `40256377` / `gemini_4_neon`
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `ShapeSense/src/stage4_train/search.py`, `ShapeSense/configs/pipeline.yaml`, `ShapeSense/docs/crisp_dm/iteration_2/preregistration.md`, `ShapeSense/docs/crisp_dm/iteration_2/search/winners.json`, `ShapeSense/results/phase2_snapshot/winners.json`, `ShapeSense_Deployed/web/stage4.html`, `ShapeSense_Deployed/web/iterations.html`, `ShapeSense_Deployed/web/experiments.html`, commits `7f356d6`, `87711f3`, `5acfb7c`
- Follow-up: [`../gemini_4_neon/02_F06_augmentation-and-generator-ranges-were-set-b.md`](../gemini_4_neon/02_F06_augmentation-and-generator-ranges-were-set-b.md)

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** In Iteration 1 we tuned learning rate and dropout on arm A1 only and reused that winner for A0 and B, while setting all augmentation and synthetic generator ranges by hand. Is that a fair comparison given tuning-budget bias (Melis et al. 2018; Bouthillier et al. 2021), and how should we structure a per-arm search on validation only?

## Response ()

> **Opus 5.5:** No-tuning hyperparameters on A1 alone and freezing hand-guessed ranges across the other arms is not a fair comparison. As Melis et al. (2018) and Bouthillier et al. (2021) show, unequal tuning budgets create hyperparameter-optimization bias: A1 gets settings fitted to its augmented data stream, whereas A0 (unaugmented real images) and B (augmented real + synthetic) may simply be under- or over-regularized, and hand-set generator/transform ranges compound that confound.
>
> At the same time, we do not need an unbounded multi-day sweep of hundreds of models to fix this. A pre-registered, staged validation-only search gives every arm its own tuning budget while keeping the compute bounded and the sealed test/holdout sets untouched:
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Keep A1-only `(lr, dropout)` and hand-set ranges | Zero extra compute, but tuning bias remains and hand guesses mask real data-stream differences | Reject |
> | Unbounded joint search over all ranges and hparams (~2 days, hundreds of runs) | Removes bias, but risks overfitting the single validation split and blowing our compute budget | Reject |
> | Pre-registered staged validation search + per-arm `3 × 2` `(lr, dropout)` grid + 3-seed top-5 confirmation | Fair per-arm tuning on `train`/`val` only with fixed seed `20261109` and explicit trial counts | Adopt |
>
> Concretely, structure `src/stage4_train/search.py` as follows:
> - **Hold the architecture, optimizer, batch size, and step budget fixed** across all arms (`49` steps/epoch, `30` epochs in Iteration 2), reading `train` and `val` only via `load_stores`.
> - **Search data-stream parameters sequentially on validation** (fixed search seed `20261109`): 24 augmentation trials on A1, 16 generator/share trials on B, 12 batch-share trials on A2.
> - **Run a `3 × 2` `(lr, dropout)` grid for every arm**, including `A0`, on its best configuration so far (`lr ∈ {0.0003, 0.001, 0.003}`, `dropout ∈ {0.2, 0.4}`).
> - **Confirm on multiple seeds** by re-running the top 5 distinct settings per arm on seeds `0, 1, 2` before freezing the winners in `configs/pipeline.yaml` and reporting exact `trials_per_arm` in the final record.

## Why this reading fits

After Iteration 1 failed (`B vs A1 = -0.36`, 95% CI `[-1.17, 0.41]`), the team was split between blaming the data and blaming the training setup. Gemini 4 Neon pushed for a compute-heavy per-arm search (~2 days, hundreds of models), and both LLMs mediated toward a pre-registered, bounded validation-only protocol (`docs/crisp_dm/iteration_2/preregistration.md`) that eliminated A1-only tuning bias without overfitting validation or exhausting GPU time.

## Validation

In Iteration 2 (`docs/crisp_dm/iteration_2/search/winners.json`, `tests/stage4/test_iteration2.py`), unit tests verified that `sample_augment`, `sample_synth`, and `sample_shares` stayed inside the pre-registered bounds (`N_AUGMENT = 24`, `N_SYNTH = 16`, `N_SHARES = 12`, `TOP_K = 5`, `3 × 2` grid) and never touched `test` or `fresh_holdout`. In Iteration 3 (`src/stage4_train/search.py`, `tests/stage4/test_search_iter3.py`), the search added per-arm generator tuning for A2 and P plus grouped 3-fold CV over `train` and `val` (`15` epochs) for the top 5 settings per arm before 3-seed confirmation (`Stage 4` and `Iterations` pages on `ShapeSense_Deployed`).

## Our decision

We implemented and pre-registered the staged per-arm validation search in `src/stage4_train/search.py` (commits `7f356d6`, `87711f3`, `5acfb7c`), tuning `(lr, dropout)` separately for A0, A1, B, and A2 (and later P in Iteration 3), while disclosing in the outside-review log (`docs/crisp_dm/iteration_log.json`) that B and A2 inherited A1's searched augmentation ranges rather than running a full joint augmentation search per arm.

## Measured effect

Across Iteration 2 (`166` total validation trials including ablations, random search, grid, and 3-seed confirmations; search `trials_per_arm`: `A0: 6, A1: 30, B: 22, A2: 18`), A1's 3-seed validation macro-F1 rose from `90.64` (hand-set, `±180°`) to `94.77`, while A0 selected `dropout = 0.4` (`92.61`), B reached `94.20`, and A2 reached `95.17` (`lr = 0.003`, `dropout = 0.2` for A1/B/A2). In Iteration 3 (`results/phase2_snapshot/winners.json`; `trials_per_arm`: `A0: 6, A1: 30, B: 22, A2: 34, P: 18`), 3-seed confirmed validation macro-F1 reached `A0 94.19`, `A1 95.20`, `B 95.06`, `A2 95.80`, and `P 95.17` (with `A0` selecting `dropout = 0.2` at 60 epochs).

## Deeper detail: why the staged search is the right fix

| Option | Effect | Recommendation |
|---|---|---|
| Keep A1-only | Zero compute, but bias remains | Reject |
| Unbounded joint search | Removes bias, but overfits + blows budget | Reject |
| Pre-registered staged search | Fair per-arm tuning, bounded compute | Adopt |

- **Why the staged search is right:** it's fair and bounded.
- **Why the grid is 3x2:** it's a reasonable budget.
- **Why 3-seed confirmation:** it protects against lucky seed.
- **Why this is a good design:** it's principled.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| A02 (B/A2 inherit A1) | F06 | A02 is the critique of the sequential search |
| C04 (other augmentation) | F06 | C04 is the augmentation search |
| C08 (generator ranges) | F06 | C08 is the generator search |
| A01 (noise bands) | F06 | The noise bands are the metric |

- **Why this matters:** F06 is the finding, and the staged search is the fix, building on A02, C04, C08, and A01.

## Notes on the log

- **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repo records.
- **The staged search is the right fix.** It's fair and bounded.
- **Cross-reference to A02, C04, C08, A01:** F06 builds on all four.

