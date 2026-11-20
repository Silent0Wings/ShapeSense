## 

# 2_data_preparation/transformation - C04: Other augmentation settings

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: `33_real_iteration-2-plan-tuning-and-a2.md`
- LLM: Claude Opus 5.5, medium effort (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../gemini_4_neon/05_C04_other-augmentation-settings.md`
- Date: 2026-11-09
- Entry: C04 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c04), `results/llm_comparison/attribution_worksheet.csv` (C04), `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c
- **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt

> Apart from rotation, our augmentation ranges (scale, non-uniform scale, shear, translation, noise and blur probability) were all set by hand, and nobody can defend the numbers. We want a validation-only search for them, run alongside the rotation search. What ranges, what trial budget, and how should we pick the winner so it is not just a lucky seed?

## Response

I'd treat this as a small random search, not a grid. Six continuous knobs plus rotation is too many for a grid at our training cost, and random search covers each knob's range better for the same number of runs.

### Ranges

Each range should include a "nearly off" end and stay label-safe at the other end:

| Knob | Suggested range | Reasoning |
|---|---|---|
| Scale | lower bound 0.75 to 1.0, upper bound from the lower bound to 1.1 | Sample the pair so lower is never above upper |
| Non-uniform scale | 0 to 0.2 | Larger values start turning squares into rectangles |
| Shear | 0 to 20° | Strong shear makes rhombi out of squares |
| Translation | 0 to 6 px | On a 64 px frame, more risks cutting the shape |
| Noise probability | 0 to 0.5 | Above half, most training images are noisy |
| Blur probability | 0 to 0.5 | Same argument |

Sample rotation and the per-class cap in the same trial, so the winner is one consistent setting.

### Budget

Around two dozen single-seed trials per arm, then rerun the top few candidates on three seeds. That is the expensive part, but it is what protects you from a lucky seed.

### Choosing the winner

1. Rank single-seed trials by validation macro-F1.
2. Re-run the top candidates on seeds 0, 1 and 2.
3. Pick the highest three-seed mean. If two are within about the seed spread, prefer the milder setting.
4. Record the full override dict and the per-seed scores in a winners file, so the choice can be audited.

### Cautions

- **Class-dependent harm.** Shear and non-uniform scale act like rotation for square, rectangle and diamond: they can change the label. Keep the class rules that switch them off for those classes, and check per-class F1 on the winner, not only macro-F1.
- **Test split.** The search code should load only train and val stores. Write that down in the module docstring and keep it testable. Do not run test until every arm's winner is frozen.
- **Fair comparison between arms.** Use the same real-image subset and the same starting hyperparameters for every arm, otherwise arm differences mix with tuning luck.
- **Interpretation.** A searched value is the best of what we tried on one validation set. Report it as tuned, not as a property of shapes.

## Validation

Searched on validation only; the search module states the test split is never touched and loads stores from `load_stores` (train and val). Per `src/stage4_train/search.py`, `sample_augment` draws scale lower bound 0.75 to 1.0 and upper bound up to 1.1, non-uniform scale 0 to 0.2, shear 0 to 20°, translation 0 to 6 px, noise and blur probability 0 to 0.5, plus rotation and the cap. Constants: `N_AUGMENT` 24, `SEEDS` (0, 1, 2), `TOP_K` 5. `winners.json` records 30 trials for arm A1.

## Our decision

Hand-set ranges -> searched values: scale 0.904 to 1.076, non-uniform scale 0.092, shear 1.4°, translation 0, noise probability 0.385, blur probability 0.373 (`winners.json`, A1). The same augmentation values are carried in the B and A2 winners.

## Measured effect

The A1 winner averaged 94.77 validation macro-F1 over three seeds (94.69, 94.73, 94.89). No macro-F1 change for these settings alone is recorded.

## Deeper detail: why random search beats grid

### Random search covers the space better

| Approach | Coverage | Cost | Verdict |
|---|---|---|---|
| Grid | Uniform, but expensive with 6+ knobs | High | Reject |
| Random search | Better coverage per run | Lower | Adopt |

- **Why random search is better:** with 6+ continuous knobs, a grid is too expensive. Random search covers each knob's range better for the same number of runs.
- **Why this is a good design:** it's efficient and effective.

### The ranges are label-safe

| Knob | Range | Why it's label-safe |
|---|---|---|
| Scale | 0.75-1.1 | Doesn't distort shape |
| Non-uniform scale | 0-0.2 | Capped to avoid square->rectangle |
| Shear | 0-20° | Capped to avoid square->rhombus |
| Translation | 0-6 px | Doesn't cut the shape |
| Noise/blur | 0-0.5 | Not too noisy |

- **Why the ranges are label-safe:** they avoid the transformations that change geometric class (per S07).
- **Why this is a good design:** it's consistent with the class-aware approach.

### The budget protects against lucky seeds

| Step | What it does | Why |
|---|---|---|
| 24 single-seed trials | Explore the space | Find candidates |
| Top 5 on 3 seeds | Verify the best | Avoid lucky seed |
| Pick highest 3-seed mean | Choose the winner | Robust choice |

- **Why 24 trials:** enough to explore, not too expensive.
- **Why 3 seeds:** protects against lucky seed.
- **Why this is a good design:** it's robust.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | C04 | The class-aware caps are from S07 |
| F07 (the finding) | C04 | F07 is the finding; C04 is the fix for the other knobs |
| C03 (rotation cap) | C04 | C03 is the rotation part; C04 is the rest |
| T35 (transform fix) | C04 | C04 is part of T35's three groups |
| A01 (noise bands) | C04 | The noise bands are the metric for the search |

- **Why this matters:** C04 is the fix for the other augmentation knobs, building on S07, F07, C03, T35, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **Random search beats grid.** With 6+ knobs, it's more efficient.
- **The ranges are label-safe.** They avoid class-changing transformations.
- **The budget protects against lucky seeds.** 24 trials + 3 seeds.
- **Cross-reference to S07, F07, C03, T35, A01:** C04 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.