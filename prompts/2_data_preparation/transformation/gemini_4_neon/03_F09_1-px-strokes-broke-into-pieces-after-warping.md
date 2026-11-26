## 

# 2_data_preparation/transformation - F09: 1-px strokes broke into pieces after warping



- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: F09 (`failure`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40297573 / gemini_4_neon
- LLM role: proposed
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv` (F09, C06), `results/phase2_snapshot/iteration_log.json` (F09), `prompts/2_data_preparation/transformation/inferred_prompts.md` (F09), `src/stage2_augment/transform.py`, `tests/stage2/test_transform_internals.py`, `tests/stage2/test_outline_survival.py`, `stages/stage_2.md`, commit 87711f3

## Prompt

> Some sources draw with 1-px lines, and after rotation and scaling those outlines come out as dotted fragments. We counted a mean of 17.2 separate pieces per 1-px stroke after warping, where a clean outline should be one piece. Why does the warp break them, how do we keep thin lines connected, and how should we measure a fix?

## Response

**Why it breaks.** `_render` warps a float ink map (ink = 1.0, paper = 0.0) with bilinear interpolation, then cuts at a fixed level of 0.5. A 2-px or 3-px stroke still has pixels near 1.0 after warping, so it survives the cut. A 1-px line rotated by a non-right angle falls between pixel centres: its ink spreads over two neighbours, and each gets a value well below 0.5. The cut then deletes every pixel where the line passes between centres, so the outline becomes a dotted line. In short, the cut after warping is too strict for thin lines.

### Options

| Option | Pros | Cons |
|---|---|---|
| A. Lower the cut when the shape is shrunk (scale the level by the linear shrink) | Small change, keeps thick lines as they are at scale >= 1 | Does not address rotation at scale 1, which is where thin lines break most |
| B. Detect thin strokes and use a separate, lower cut relative to the warped peak | Targets the failing case only | Needs a reliable thin test; too low a level thickens lines |
| C. Dilate thin strokes by 1 px before warping | Simple and robust | Changes the stroke width of those sources, which is itself a style cue |

### Recommendation

Try A first, since it is the smallest change. If the piece count does not drop to about 1, add B: mark an image as thin when no 2x2 block is all ink, and for those images cut at a fraction of the warped maximum, such as 0.2. A relative cut keeps the line joined across the dips between pixels without making it much thicker.

### How to measure

Count connected components of the ink (8-connected) on augmented 1-px references over many seeds and report the mean. The target is 1.0. Also check ink kept against ink in, so a fix cannot "pass" by erasing the line.

### Cautions

- Thin strokes come from some sources more than others, so this is class- and source-dependent harm. Breaking only those sources' outlines teaches the model a source cue.
- Noise must only add ink near the outline, never remove it, or it undoes the fix.
- Measure on training-style references, not on test images.

## Validation

- Pieces per stroke: 17.2 before any fix, 16.3 after the first fix, 1.0 after the final fix (`results/phase2_snapshot/iteration_log.json`, F09).
- The final code in `src/stage2_augment/transform.py` has both the shrink-scaled cut and a thin-line path (`THIN_LINE_LEVEL = 0.2` of the warped peak, thin flag from the 2x2 test). The repo does not say in so many words which of the two was the first fix.
- Tests: `test_thin_outline_survives` (at least half the input ink kept, 100 seeds per class) and `test_one_pixel_sketch_survives_strongest_blur`. No test in `tests/stage2/` counts pieces per stroke. The 17.2, 16.3 and 1.0 counts come from the investigation, and the script that produced them is not identified in the repo.

## Our decision

The first fix barely helped, so a separate thin-line path was added. The worksheet credits the thin-line handling itself (C06) to a team member with no LLM involved, so Gemini's share is the diagnosis and the option list.

## Measured effect

17.2 -> 16.3 pieces after the first fix -> 1.0 piece with the thin-line path. No macro F1 change is recorded.

## Deeper detail: why the cut is too strict

### The cut at 0.5 is too strict for thin lines

| Stroke width | After warping | Cut at 0.5 | Result |
|---|---|---|---|
| 2-3 px | Near 1.0 | Survives | OK |
| 1 px rotated | Well below 0.5 | Deleted | Dotted |

- **Why the cut is too strict:** thin lines fall between pixel centres.
- **Why this matters:** it breaks the outline.
- **Why this is a real problem:** it's a source-dependent harm.

### The three options

| Option | Pros | Cons |
|---|---|---|
| A. Shrink-scaled cut | Small change | Doesn't fix rotation at scale 1 |
| B. Thin-line path | Targets the failing case | Needs a reliable thin test |
| C. Dilate before warping | Simple | Changes stroke width |

- **Why A first:** it's the smallest change.
- **Why B if A fails:** it targets the failing case.
- **Why C is last:** it changes the style cue.

### The measurement is the right one

- **Why connected components:** it directly measures fragmentation.
- **Why 8-connected:** it's the right connectivity for outlines.
- **Why ink kept matters:** it prevents a fix that erases the line.
- **Why training-style references:** it's the right test set.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| C06 (thin-line path) | F09 | C06 is the fix for F09 |
| C07 (stroke width) | F09 | Thicker strokes are less fragile |
| C35 (augmentation speed) | F09 | The thin-line check is related |
| A01 (noise bands) | F09 | The noise bands are the metric for the fix |

- **Why this matters:** F09 is the finding, C06 is the fix, and they build on C07, C35, and A01.

## Notes on the log


- **The cut at 0.5 is too strict for thin lines.** It breaks them.
- **The three options are real.** A, B, C.
- **The measurement is the right one.** Connected components + ink kept.
- **Cross-reference to C06, C07, C35, A01:** F09 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.