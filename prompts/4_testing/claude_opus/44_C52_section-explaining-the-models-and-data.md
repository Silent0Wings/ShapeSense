# 4_testing - C52: Section explaining the models and data
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C52 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40256377 / 40256377
- LLM role: assisted
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c52, studio/web/js/widgets/models-explainer.js, studio/web/js/pages/home.js, configs/models/A2.yaml, configs/models/B.yaml, configs/models/P.yaml, ShapeSense_Deployed/web/index.html, commit b39a942

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
When we showed the dashboard to someone outside the team, they could not tell what A0, A1, B, A2 and P are, or what "augmented" and "synthetic" mean, because we never define them in one place. I want a home page section with a real, an augmented and a computer-generated example of the same shape, and one card per model saying what it tests and what its batches contain. Can you help me build it from the data we already serve?

## Response
Good plan. The section should teach two words before any chart uses them: the three kinds of training image, then the five models as mixes of those three. Build it from data the home page already receives, so it cannot disagree with the config.

**Part 1: three kinds of image.** One row of three tiles for the same class:
- *Real*: a standardized drawing from the training pool.
- *Real, augmented*: that same drawing after the Stage 2 augmentation, using the default augmentation settings.
- *Computer-generated*: a shape from the Stage 3 generator with its default ranges.

Give each kind a fixed colour from the series palette and reuse it everywhere below. Add two buttons, one for the next class and one for another example, so the reader sees it is not one cherry-picked image. Keep each caption to one sentence.

**Part 2: one card per model.** Open with the sentence that matters most: all five models share one network and differ only in what they trained on. Then each card has a colour swatch, a plain name with the code in brackets, one line on what the model tests, and a stacked bar of its batch make-up in the three image colours. Read the counts from the recipes the server already computes. For example, with a batch size of 256 the recipes work out to (the same counts are now recorded in `configs/models/`):

| Model | Real unchanged | Real augmented | Synthetic |
|---|---|---|---|
| B | 0 | 213 | 43 |
| A2 | 105 | 120 | 31 |
| P (after pretraining) | 0 | 256 | 0 |

P needs two bars, because it trains on 256 synthetic images per batch for its first 7 epochs before switching. Label them by epoch range from the data (`Epochs 1 to N`, then `Epochs N+1 to max`) rather than typing the numbers into the page.

Cautions:
- Do not hard-code percentages or epoch counts in the widget; pass `recipes` and `max_epochs` in.
- Keep the section below the headline result, so the home page still opens on the finding.
- Check that bar labels stay readable on the bright series colours.

## Validation
`studio/web/js/widgets/models-explainer.js` defines `KINDS` (the three image kinds), `ABOUT` (one line per model), `batchBar`, and `modelCard`, which splits P into `Epochs 1 to ${r.pretrain_epochs}` and `Epochs ${r.pretrain_epochs + 1} to ${maxEpochs}`. `studio/web/js/pages/home.js` mounts it in the card "What the models are and what they trained on", passing `recipes`, `max_epochs`, the classes and the augmentation and generator defaults. The section is published on `ShapeSense_Deployed/web/index.html`.

## Our decision
Built by 40256377 as proposed, with Opus helping on the layout and wiring: the home page shows a real, an augmented and a computer-generated example of a shape, and a card per model with what it tests and the make-up of its batches. Reason recorded: a new reader could not tell what the models were or what their training data meant.

## Measured effect
No separate measurement recorded.

---

## Expanded & Upgraded: Visual-Honesty Cluster Synthesis (`C52`)

### Vocabulary Before Taxonomy & Data-Derived Recipes

`models-explainer.js` enforces two structural principles from the `C45`–`C55` visual-honesty cluster:
1. **Vocabulary precedes taxonomy:** the widget teaches the three training-image kinds (*Real unchanged*, *Real augmented*, *Computer-generated*) with live interactive examples *before* defining the five models (`A0`, `A1`, `B`, `A2`, `P`) as mixtures of those three kinds.
2. **Data-derived taxonomy:** batch counts (`B`: `0 / 213 / 43`, `A2`: `105 / 120 / 31`, `P`: `7` pretraining epochs of `256` synthetic followed by `53` epochs of `256` augmented real) are computed dynamically from `recipes` and `max_epochs`, never hard-coded in prose or JavaScript.

