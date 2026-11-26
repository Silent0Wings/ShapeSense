## 

# 2_data_preparation/transformation - F10: Synthetic strokes were thinner than real ones



- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (Iteration 2; no commit is recorded for this row)
- Entry: F10 (`failure`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40211352 + 40253714 / opus_medium_5.5 + 40211352 + 40253714
- LLM role: proposed
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv` (F10), `results/phase2_snapshot/iteration_log.json` (F10), `prompts/2_data_preparation/transformation/inferred_prompts.md` (F10), `docs/crisp_dm/iteration_2/investigation/data_analysis.json` (`pixel_stats`), `src/stage3_synth/render.py`, `configs/pipeline.yaml` (`synth.stroke_px`), `stages/stage_3.md`

## Prompt

> In the iteration 2 investigation we measured stroke width per class for real, augmented and synthetic images. The generator draws with `stroke_px: 2`, because the Stage 3 brief asks for a "~2-px black outline". The synthetic outlines look noticeably thinner than the real ones on the contact sheets. Is this a real gap, and if so what width should the generator use?

## Response

Yes, it is a real gap, and it is consistent across classes, which is what makes it worth fixing.

### What the numbers say

In `data_analysis.json` the real per-class mean stroke runs from 2.47 px (hexagon) to 3.30 px (diamond), with most classes near 3.1 px. Synthetic images drawn at 2 px measure 1.81 to 2.00 px. So the generator is not just slightly off: every class is thinner than its real counterpart, and the "~2-px" in the brief does not match the standardized data the model is actually trained and tested on. The brief was written before Stage 1 standardization was measured.

### Why it matters

Stroke width is a cheap shortcut. If synthetic images are always thinner, a model can learn "thin outline = synthetic-style image" instead of the shape. In arm B that cue is harmless only if real test images share it, and they do not. Thin synthetic strokes are also more fragile under Stage 2 warping.

### Options

| Option | Pros | Cons |
|---|---|---|
| A. Fixed 3 px | One-line config change, closest integer to the real mean | Ignores per-class spread (hexagon and octagon are near 2.5 px) |
| B. Sample width per image, e.g. 2 to 4 px | Covers the real spread | A new range to search; more risk of a thick outline closing up small shapes |
| C. Match per class | Closest fit | Hard-codes a data quirk per class; overfits the current sources |

### Recommendation

A, 3 px. It closes most of the gap with no new search dimension. Keep `render_outline` as it is: it already takes `stroke_px` in output pixels and draws at `supersample` resolution before downsampling, so 3 px is honoured.

### Cautions

- Measure stroke width on synthetic images again after the change, with the same measurement used for the real images. Otherwise "3 px" is a setting, not a verified match.
- Check the smallest shapes at 3 px for the star and diamond, where a thicker line can merge the inner corners.
- Update the Stage 3 brief so it no longer asks for 2 px.
- Use train images only for the reference width. Do not tune this on test.

## Validation

- Real and synthetic widths are from `docs/crisp_dm/iteration_2/investigation/data_analysis.json`: real per-class means 2.47 to 3.30 px, synthetic at 2 px 1.81 to 2.00 px.
- The repo records no stroke measurement of synthetic images after the change, and no test in `tests/stage3/` checks stroke width. The Opus caution to re-measure is not shown as done.
- `stages/stage_3.md` now opens with "The synthetic stroke is 3 px, against about 3.1 px in real images", though its R2 still says "~2-px".

## Our decision

The team took option A: `synth.stroke_px: 3` in `configs/pipeline.yaml`, commented "real standardized outlines measure about 3.1 px (iteration 2)". Same change as C07.

## Measured effect

2 px -> 3 px, against about 3.1 px real (`results/phase2_snapshot/iteration_log.json`, F10). No post-fix stroke measurement and no macro F1 change are recorded.

## Deeper detail: why the gap matters

### The stroke width gap is consistent across classes

| Class | Real mean (px) | Synthetic at 2 px (px) | Gap |
|---|---|---|---|
| hexagon | 2.47 | 1.81-2.00 | ~0.5-0.7 |
| diamond | 3.30 | 1.81-2.00 | ~1.3-1.5 |
| most classes | ~3.1 | 1.81-2.00 | ~1.1-1.3 |

- **Why the gap matters:** it's consistent across classes, which means it's a systematic issue, not noise.
- **Why "every class is thinner" matters:** it's not just one class; it's all of them.
- **Why the brief was written before standardization:** the "~2-px" was a guess, not a measurement.

### Stroke width is a shortcut

- **Why it's a shortcut:** if synthetic images are always thinner, a model can learn "thin outline = synthetic-style image" instead of the shape.
- **Why this matters for arm B:** the cue is harmless only if real test images share it, and they do not.
- **Why thin strokes are fragile:** they're more likely to break under warping (per F09).

### The three options

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Fixed 3 px | Simple, closest to real mean | Ignores per-class spread | **Adopted** |
| B. Sample 2-4 px | Covers the spread | New search dimension, risk of closing small shapes | Rejected |
| C. Match per class | Closest fit | Overfits the current sources | Rejected |

- **Why A is best:** it's simple and closes most of the gap.
- **Why B is rejected:** it adds a search dimension and risks closing small shapes.
- **Why C is rejected:** it overfits the current sources.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I06 (standardization) | F10 | The standardized 64x64 PNGs are what the stroke width is measured on |
| T35 (transform fix) | F10 | F10 is part of T35's three groups |
| F09 (broken 1-px strokes) | F10 | Thin strokes are more fragile under warping |
| C07 (stroke_px 3) | F10 | C07 is the fix for F10 |
| A01 (noise bands) | F10 | The noise bands are the metric for the fix |

- **Why this matters:** F10 is the finding that synthetic strokes are thinner, and C07 is the fix.

## Notes on the log


- **The gap is consistent across classes.** It's a systematic issue.
- **Stroke width is a shortcut.** Thin synthetic strokes are a cue.
- **Option A (3 px) is the right fix.** Simple and closes most of the gap.
- **Cross-reference to I06, T35, F09, C07, A01:** F10 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.