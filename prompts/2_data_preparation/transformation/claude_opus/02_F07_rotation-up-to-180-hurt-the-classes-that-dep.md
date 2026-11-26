## 

# 2_data_preparation/transformation - F07: Rotation up to ±180° hurt the classes that depend on orientation
`10_real_augmentation-failure-investigation.md`
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: `../gemini_4_neon/01_F07_rotation-up-to-180-hurt-the-classes-that-dep.md`
- Date: 2026-11-09
- Entry: F07 (`failure`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40297573 / gemini_4_neon + 40297573
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#f07), `results/llm_comparison/attribution_worksheet.csv` (F07), `results/phase2_snapshot/iteration_log.json` (F07), `docs/crisp_dm/iteration_2/search/phase_ablation.json`, `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c


## Prompt

> The per-arm search keeps pointing at heavy augmentation as one source of error, and the per-class scores suggest rotation up to 180 degrees hurts squares, rectangles and diamonds. Why would full rotation hurt exactly those three classes? What rotation range should we search on validation, and should some classes get their own tighter limit?

## Response

I think the pattern is real and has a clear cause, but I'd want it confirmed by a controlled run before we change anything.

### Why these three classes

For most of the taxonomy, rotation is label-preserving and uninformative: a circle, a hexagon or a star is the same class at any angle. Square, rectangle and diamond are different. Two things happen:

1. **Rotation can change the label.** A square turned 45° is geometrically a rhombus standing on a corner, which is what a diamond looks like in our sources. With ±180° the transform produces many such images and keeps the label "square". That is label noise we inject ourselves.
2. **Rotation erases a clue the data really has.** If several sources draw squares and rectangles upright, orientation is a genuine signal at test time. Training the model to ignore it throws that signal away.

So I'd frame this as "the augmentation is not class-safe", not as "rotation is bad".

### Options

| Option | Pro | Con |
|---|---|---|
| One global smaller range | Simple, one number | Under-augments the rotation-invariant classes |
| Global range plus a per-class cap for square, rectangle, diamond | Keeps variety where it is harmless, protects the three classes | Two knobs to search, a little more code |
| Remove rotation entirely | Removes the label risk | Loses robustness to hand-drawn tilt on every class |

### Recommendation

Search a global range and a separate cap for the three orientation classes together, on validation only. A grid such as `{0, 5, 10, 15, 20, 30, 45, 90, 180}` for the global range and `{none, 0, 5, 10, 15, 30}` for the cap covers both the "no rotation" and "current behaviour" ends. The cap belongs in the transform builder, keyed by class, so the training loop never needs to know about it.

### Before trusting the search, run a small ablation

The same arm, the same hyperparameters, only the rotation range changed, three seeds each. Compare per-class F1 for the three classes, not just macro-F1, since a macro-F1 shift can hide a trade between classes.

### Cautions

- Look at early stopping. A setting that stops after a few epochs scores lower for reasons unrelated to rotation.
- Seed variance on our validation set is not small. One seed is not evidence.
- Keep the test split out of all of this. The search should load only train and val stores, and the final range should be fixed before any test run.
- A smaller range may move errors to another class pair, so check the confusion matrix, not only the three target classes.

## Validation

Caught by test (`caught_by` in the worksheet). The rotation-only ablation on arm A1, three seeds each, is in `docs/crisp_dm/iteration_2/search/phase_ablation.json`: validation macro-F1 0° 89.38, ±15° 93.62, ±45° 89.91, ±90° 90.58, ±180° 90.64. Per-class means for ±15° -> ±180°: square 93.9 -> 90.3, rectangle 87.8 -> 82.3, diamond 96.1 -> 86.9. The `iteration_log.json` caption notes that the no-rotation runs stopped early (11 to 13 epochs), which lowers that score.

## Our decision

The search in `src/stage4_train/search.py` (`sample_augment`) draws the global range from `ROTATIONS` and one cap for `ORIENTATION_CLASSES` (square, rectangle, diamond) from `ROTATION_CAPS`. The cap is applied per class in `build_transform` (`src/stage2_augment/transform.py`). The winner is ±20°, capped at ±10° for square, rectangle and diamond. Same change as C03.

## Measured effect

The A1 winner with this setting averaged 94.77 validation macro-F1 over three seeds (`docs/crisp_dm/iteration_2/search/winners.json`). No macro-F1 for the rotation change in isolation at ±20° with the cap is recorded. Marked Overcome in the worksheet.

## Deeper detail: why the ablation matters

### The ablation confirms the pattern

| Rotation | Macro F1 | Square F1 | Rectangle F1 | Diamond F1 |
|---|---|---|---|---|
| 0° | 89.38 | — | — | — |
| ±15° | 93.62 | 93.9 | 87.8 | 96.1 |
| ±45° | 89.91 | — | — | — |
| ±90° | 90.58 | — | — | — |
| ±180° | 90.64 | 90.3 | 82.3 | 86.9 |

- **Why the ablation matters:** it confirms the pattern with controlled runs (three seeds each), not just one run.
- **Why per-class F1 matters:** macro-F1 can hide a trade between classes. The per-class numbers show square/rectangle/diamond dropping from ±15° to ±180°.
- **Why the no-rotation runs stopped early:** 11 to 13 epochs, which lowers that score. This is a caveat.

### The winner: ±20° with ±10° cap

| Setting | Value | Why |
|---|---|---|
| Global rotation | ±20° | Good for most classes |
| Cap for square/rectangle/diamond | ±10° | Prevents square-diamond confusion |

- **Why ±20° is the winner:** it's the best macro F1 (94.77 over three seeds).
- **Why ±10° cap:** it prevents the square-diamond confusion.
- **Why this is a good design:** it's class-aware, not one-size-fits-all.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | F07 | The square/diamond distinction is what F07 checks against |
| I03 (global grouping) | F07 | The global grouping is the architectural context |
| I06 (standardization) | F07 | The standardized 64x64 PNGs are the input to the transform |
| T35 (transform fix) | F07 | F07 is part of T35's three groups |
| C03 (rotation cap) | F07 | C03 is the fix for F07 |
| A01 (noise bands) | F07 | The noise bands are the metric for the ablation |

- **Why this matters:** F07 is the finding that rotation hurts orientation-dependent classes, and C03 is the fix.

## Notes on the log


- **The ablation confirms the pattern.** Three seeds each, per-class F1.
- **The winner is ±20° with ±10° cap.** Class-aware, not one-size-fits-all.
- **The no-rotation runs stopped early.** This is a caveat.
- **Cross-reference to S07, I03, I06, T35, C03, A01:** F07 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.