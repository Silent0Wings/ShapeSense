## 

# 2_data_preparation/transformation - C07: Synthetic stroke width

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Claude Opus 5.5, medium effort (simulated reconstruction)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (Iteration 2; no commit is recorded for this row)
- Entry: C07 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40304911 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv` (C07, F10), `prompts/2_data_preparation/transformation/inferred_prompts.md` (C07), `docs/crisp_dm/iteration_2/investigation/data_analysis.json` (`pixel_stats`), `src/stage3_synth/render.py`, `src/stage3_synth/measure.py`, `configs/pipeline.yaml` (`synth.stroke_px`, `synth.supersample`), `tests/stage3/test_shapes.py`

## Prompt

> Our synthetic generator draws 2-px strokes, but the investigation says real standardized drawings measure about 3.1 px. Before I change `stroke_px`, I want to know two things: what width to set, and how we confirm that the generator output really matches the real images afterwards, not just the config value.

## Response

Set `stroke_px: 3`, and treat the measurement as the part that needs the most care.

### Why 3 px

The real per-class mean stroke in `data_analysis.json` runs from 2.47 px (hexagon) to 3.30 px (diamond), and the synthetic images drawn at 2 px measure 1.81 to 2.00 px. So the rendered stroke already comes out a little under the nominal width, probably because `render_outline` draws at `supersample` resolution, downsamples with a box filter and thresholds at 128, which trims edge pixels. A nominal 3 px should land close to the real mean. Going to 4 px would overshoot hexagon and octagon (2.47 and 2.50 px real).

### How to measure

The width has to be measured on images, with one function applied the same way to real and synthetic sets:

- A simple estimator is ink area divided by outline length, where the length comes from a 1-px skeleton of the ink. It is robust for closed outlines.
- A second option is twice the mean distance-transform value along the skeleton. It is more sensitive to corners.
- Whatever you pick, use the same threshold (`INK_THRESHOLD = 128` in `measure.py`) for both sets.

`src/stage3_synth/measure.py` has `axis_ratio` and `min_interior_angle_deg` but no stroke helper, so this would be a new function.

### What to check after the change

1. Re-run the same per-class table on synthetic images at 3 px and compare per class, not only the overall mean.
2. Add a test in `tests/stage3/` that renders each class and asserts the measured width is within a tolerance of the real reference. Then a later change to `render.py` cannot quietly undo the fix.
3. Look at small stars and diamonds at 3 px. Thicker lines can fill the narrow inner angles.

### Cautions

- Take the real reference from the train split only.
- Thicker strokes also change what Stage 2 sees: the investigation also measured augmented synthetic images (the `synaug` group), so a 3-px line is less likely to break apart after warping.
- Changing the width changes the generator output, so arm B and A2 must be retrained. Old runs are not comparable.

## Validation

- Before and after values are from `results/llm_comparison/attribution_worksheet.csv`: 2 px -> 3 px, against about 3.1 px real.
- Real and synthetic widths at 2 px are from `docs/crisp_dm/iteration_2/investigation/data_analysis.json`.
- Not done: the repo records no stroke measurement of synthetic images at 3 px, and `tests/stage3/test_shapes.py` has no stroke-width test. The measurement method used in the investigation is not documented in that file.

## Our decision

Generator stroke set to 3 px in `configs/pipeline.yaml` (`synth.stroke_px: 3`). The proposed re-measurement and the stroke-width test were not added.

## Measured effect

2 px -> 3 px, against about 3.1 px real. No post-fix stroke measurement and no macro F1 change are recorded.

## Deeper detail: why 3 px is the right choice

### The real mean is about 3.1 px

| Class | Real mean (px) | Synthetic at 2 px (px) | Gap |
|---|---|---|---|
| hexagon | 2.47 | 1.81-2.00 | ~0.5-0.7 |
| diamond | 3.30 | 1.81-2.00 | ~1.3-1.5 |
| most classes | ~3.1 | 1.81-2.00 | ~1.1-1.3 |

- **Why 3 px is the right choice:** it's closest to the real mean (~3.1 px).
- **Why 4 px would overshoot:** hexagon and octagon are 2.47 and 2.50 px real, so 4 px would be too thick.
- **Why this is a good choice:** it balances the per-class spread.

### The measurement needs care

| Method | Pros | Cons |
|---|---|---|
| Ink area / outline length | Robust for closed outlines | Less sensitive to corners |
| 2x mean distance-transform | More sensitive to corners | More complex |

- **Why the measurement needs care:** it's the part that validates the fix.
- **Why the same threshold matters:** it ensures apples-to-apples comparison.
- **Why a new function is needed:** `measure.py` doesn't have a stroke helper.

### The post-change checks are important

1. Re-run the per-class table at 3 px.
2. Add a test that asserts the measured width is within tolerance.
3. Look at small stars and diamonds (thicker lines can fill narrow angles).

- **Why these checks matter:** they validate the fix and prevent regression.
- **Why this is a good design:** it's thorough.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I06 (standardization) | C07 | The standardized 64x64 PNGs are what the stroke width is measured on |
| F10 (the finding) | C07 | F10 is the finding; C07 is the fix |
| T35 (transform fix) | C07 | C07 is part of T35's three groups |
| F09 (broken 1-px strokes) | C07 | Thicker strokes are less fragile under warping |
| A01 (noise bands) | C07 | The noise bands are the metric for the fix |

- **Why this matters:** C07 is the fix for F10, building on I06, T35, F09, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **3 px is the right choice.** It's closest to the real mean.
- **The measurement needs care.** It's the part that validates the fix.
- **The post-change checks are important.** They validate the fix and prevent regression.
- **Cross-reference to I06, F10, T35, F09, A01:** C07 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.