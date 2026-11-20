# 3_modeling - Full or partial training runs in hyperparameter tuning?

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C12, C26, F22
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [C12](../../3_modeling/claude_opus/23_C12_hyperparameter-tuning.md)

## Prompt 1 (02:41)

> what are theses trials being ran ?

## Response 1

Each trial is one complete training of the shape classifier with a different combination of settings, scored on validation images only. The aim is to find the best settings for each training recipe, before the final training and the one test on sealed data.

| Phase | Trials | What it tries |
|---|---|---|
| Augmentation for Real + augmented (A1) | 24 | Rotation, scale, shear, noise and blur amounts |
| Generator for Real + synthetic (B) | 16 | Synthetic share and shape-drawing ranges |
| Generator for Full mix (A2) | 16 | The same, tuned separately |
| Batch mix for Full mix (A2) | 12 | How many clean and synthetic images go in each batch |
| **Synthetic pretraining (P), running now** | 12 | How long to pretrain on synthetic images, and the generator ranges |
| Learning rate and dropout, all 5 arms | 26 | 6 combinations per arm, minus 4 already done |
| Cross-validation | 75 | Each arm's top 5 settings, tested on 3 data splits at 15 epochs |
| Confirmation | 10 | Each arm's winner on 3 seeds, minus 5 already done |

All but the cross-validation trials train for 60 epochs. At 76 of 191, it's about two-thirds of the way through the pretraining phase.

The winning settings then go into the final training. Choosing them on validation only keeps the sealed test data untouched.

## Prompt 2 (02:42)

> but is this a full training ? or a partial training ?

## Response 2

Most are full trainings. Of the 191:

- **116 are full trainings:** 60 epochs, the same length and model as the final models.
- **75 are partial:** the cross-validation trials run for only 15 epochs, as the pre-registered plan sets out. They compare each arm's top 5 settings quickly across 3 data splits.

Even the full ones aren't the final models, though. Most use a single random seed, because each one is just testing a setting. Once the winners are chosen, Phase 6 retrains each arm from scratch on 5 seeds, plus hold-out runs. Those 40 runs are the models that take the sealed test.

79 of 191 trials are done at 02:42, with 3 finished in the last 5 minutes.

## Prompt 3 (02:42)

> but uusaly in hyper parameter tuninig we dont do full training do we ?

## Response 3

You're right that it's common to avoid full training, especially for large models. Methods like successive halving or early pruning run many settings briefly and only continue the promising ones.

We use full runs here for three reasons:

- **Short runs can pick the wrong winner.** Strong augmentation and synthetic data learn more slowly, so a short run tends to favour weak settings. That bias would land exactly on the comparison this project is about.
- **The learning rate is scheduled across the whole run.** It decays over all 60 epochs, so a shortened run isn't the same training. And arm P spends up to 36 of those epochs on synthetic images only, so 8 or 15 epochs would barely reach its real-image phase.
- **The model is small.** A full trial takes about 3 minutes, so it's affordable.

The plan also uses short runs where they're safest: the 15-epoch cross-validation only compares each arm's top 5 settings, which have already done well in full runs.

The pre-registration fixed this design before any results, and it can only shrink if a job is estimated to take over 24 hours, which this one isn't. For a future iteration, successive halving would be a reasonable thing to pre-register, if you first check that short runs rank settings the same way full ones do.

## Prompt 4 (02:43)

> estimation of completion of the 191 trials ?

## Response 4

**About 2 to 3 hours from now, so around 5 to 6 a.m.**, assuming no more crashes.

| Remaining | Trials | Each | Time |
|---|---|---|---|
| Full trainings (pretraining, learning rate and dropout, confirmation) | 37 | 2 to 3 minutes | 1.25 to 2 hours |
| Cross-validation, 15 epochs | 75 | 30 to 60 seconds, estimated | 40 to 75 minutes |

The cross-validation speed hasn't been measured yet, so that's the least certain part. At 79 of 191, the remaining trials go faster than the count suggests, because most of them are the short ones. After the search come retraining, the sealed evaluation, the report and close-out.

## Prompt 5 (02:44)

> how many of the full trials is done ?

## Response 5

**79 of the 116 full trials are done**, as of 02:42. All 79 finished trials so far are full 60-epoch runs, since the short cross-validation trials come near the end. That leaves 37 full trials and all 75 short ones.

## Prompt 6 (02:45)

> but here you say =[]76 of 191 trials are done at 02:37, with 2 finished in the last 5 minutes.

## Response 6

Both are right, because they're from different times and count different totals:

- **76 at 02:37** was the count of finished trials then. By 02:42 it had reached 79.
- **Out of 191** is every trial in the search, and **out of 116** is only the full 60-epoch ones. All finished trials so far are full ones, so the same 79 counts toward both totals.

So at 02:42 it was 79 of 191 overall, and 79 of the 116 full trials.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Trial counts were checked against the search log. The user caught a mismatch in the reported progress (exchange 6).

## Our decision

We questioned full training in every trial. Opus 5.5 gave reasons to keep full 60-epoch runs. We kept them, and winners are re-scored by grouped CV (C26).

## Measured effect

No direct macro F1 delta. The search's winners fed the iteration 3 result (C38).

---

## Multi-Fidelity Search Architecture & Epoch-Horizon Bias (`C12`, `C26`, `F22`)

### Metadata & Lineage

* **Entries:** `C12` (*Per-arm hyperparameter tuning*), `C26` (*Full 60-epoch search trials paired with 15-epoch grouped CV*), `F22` (*Trial 66 crash recovery*)
* **Date:** `2026-11-10` (02:41–02:45 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)

### Why Multi-Fidelity Truncation (Successive Halving) Was Rejected for Primary Search

While successive halving or early-epoch pruning is standard for large-scale neural architecture search, Iteration 3 intentionally executed **116 full 60-epoch trainings** alongside **75 short 15-epoch grouped CV runs** (`191` unique executions out of `200` nominal specs) for three structural reasons:

1. **Convergence-Rate Confounding Across Data Regimes:** Heavy stochastic augmentations (`A1`, `A2`) and synthetic mixtures (`B`) exhibit slower early-epoch convergence than clean real images (`A0`); truncating trials at 10–15 epochs systematically biases selection toward weak augmentation/synthesis settings.
2. **Cosine Annealing Horizon & Two-Phase Pretraining (`P`):** The cosine LR schedule spans the full 60-epoch trajectory (`2,940` steps), and arm `P` devotes up to **36 epochs** solely to synthetic pretraining before transitioning to real data—making 15-epoch truncation structurally incompatible with `P`'s learning dynamics.
3. **Tractable Unit Compute Cost:** At `2–3 min` per 60-epoch trial on the RTX 3080, full-horizon evaluation remained well within the pre-registered 24-hour ceiling while reserving 15-epoch partial runs strictly for 3-fold `phash_group` cross-validation among each arm's top-5 full-run candidates.

