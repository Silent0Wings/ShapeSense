## Expanded entry

# 2_data_preparation/transformation - C05: Shape framing after augmentation



- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C05 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40304911 / 40304911
- LLM role: assisted
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv` (C05, F08), `prompts/2_data_preparation/transformation/inferred_prompts.md` (C05), `docs/crisp_dm/iteration_2/investigation/data_analysis.json` (`pixel_stats`), `src/stage2_augment/transform.py`, `configs/pipeline.yaml` (`augment`), `tests/stage2/test_outline_survival.py`, commit 87711f3

## Prompt

> I have traced the small augmented shapes (about 51 px against 57 px real in a 64-px frame) to the re-framing step in `_augment`, and I want to replace the hard-coded margin with a config setting. Can you help me write the re-framing so it matches Stage 1, name the setting, and write a test that would have caught the bug?

## Response

Your diagnosis fits the numbers: the per-class long side is 50.75 to 51.16 px augmented against 56.42 to 57.81 px real, the same gap for every class. Here is how I would structure the change.

### Re-framing, step by step

1. Take the ink positions and their centroid.
2. Apply the linear part (rotation, shear, per-axis stretch) to the centred points and take the bounding box of the result.
3. Scale so the longest side of that box equals `target = size / (1 + 2 * frame_margin)`, then multiply by the sampled scale jitter.
4. Shift so the box is centred in the frame, plus the sampled translation.
5. Only then run the fit-to-frame loop, as a safety net for blur and interpolation that still reach the outer ring.

The order matters: the fit loop can shrink a shape but never grow it, so if it does the framing, rotated shapes end up small.

### The setting

Put it in `configs/pipeline.yaml` as `augment.frame_margin`, defined as a share of the bounding-box side, the same convention Stage 1 uses. Read it in `build_transform` into the ranges dataclass, so nothing in `_augment` is a literal. A value of 0.06 gives 64 / 1.12, about 57.1 px.

### The test

```python
target = size / (1 + 2 * aug["frame_margin"])
expected = target * float(np.mean(aug["scale"]))
assert abs(np.mean(sides) - expected) <= 3.0
```

Run it on a thin circle and a square outline over many seeds, and also assert the shape never touches the frame edge (`max(sides) <= size - 2`).

### Cautions

- Use one margin for all classes. A per-class margin would make size a class cue.
- Retune the scale jitter after this change. The current range was chosen with the bug in place.
- This changes every augmented image, so all arms that use augmentation must be retrained.

## Validation

- `src/stage2_augment/transform.py` follows these steps: `target = r.size / (1.0 + 2.0 * r.frame_margin)`, re-centring, then the fit loop.
- `configs/pipeline.yaml` sets `frame_margin: 0.06`, commented "re-frames to about 57 px, the size Stage 1 really produces".
- `test_augmented_shapes_keep_standardized_size` in `tests/stage2/test_outline_survival.py` uses this check over 100 seeds on a thin circle and a square.
- No per-class size table is recorded after the fix.

## Our decision

The team member wrote and kept the change, with Gemini assisting. In the same commit the scale range was searched on validation (C04: 0.904 to 1.076).

## Measured effect

About 51 px against 57 px real -> framing set by `augment.frame_margin` (about 57 px target). No post-fix size table and no macro F1 value are recorded.

## Deeper detail: why the order matters

### The order is: scale, then fit loop

| Step | What it does | Why the order matters |
|---|---|---|
| 1-2. Linear transform | Rotate/shear/stretch | Gets the transformed box |
| 3. Scale to target | Sets the size | This is the framing |
| 4. Centre + translate | Positions it | Completes the framing |
| 5. Fit loop | Safety net | Only shrinks, never grows |

- **Why the order matters:** the fit loop only shrinks, so it must come last.
- **Why this is a good design:** it's correct.

### The setting is a config value, not a literal

- **Why `augment.frame_margin`:** it's a setting, not a literal.
- **Why 0.06:** it gives ~57.1 px, matching real.
- **Why the same convention as Stage 1:** it ensures consistency.

### The test would have caught the bug

```python
target = size / (1 + 2 * aug["frame_margin"])
expected = target * float(np.mean(aug["scale"]))
assert abs(np.mean(sides) - expected) <= 3.0
```

- **Why this test matters:** it directly checks the framing.
- **Why thin circle + square:** they're the extremes.
- **Why 100 seeds:** it's robust.
- **Why the edge check matters:** it prevents overflow.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F08 (shapes too small) | C05 | F08 is the finding, C05 is the fix |
| I06 (standardization) | C05 | The 64x64 resize is what the margin is relative to |
| C04 (other augmentation) | C05 | The scale jitter should be retuned after the fix |
| A01 (noise bands) | C05 | The noise bands are the metric for the fix |

- **Why this matters:** C05 is the fix for F08, building on I06, C04, and A01.

## Notes on the log


- **The order matters.** Scale, then fit loop.
- **The setting is a config value, not a literal.** It's `augment.frame_margin`.
- **The test would have caught the bug.** It directly checks the framing.
- **Cross-reference to F08, I06, C04, A01:** C05 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.
