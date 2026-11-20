## 

# 2_data_preparation/transformation - C03: Rotation range

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: `10_real_augmentation-failure-investigation.md`
- LLM: Claude Opus 5.5, medium effort (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../gemini_4_neon/04_C03_rotation-range.md`
- Date: 2026-11-09
- Entry: C03 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40211352 / 40211352
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c03), `results/llm_comparison/attribution_worksheet.csv` (C03), `docs/crisp_dm/iteration_2/search/phase_ablation.json`, `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c
- **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt

> I want to change the rotation augmentation from ±180° for every class. Full rotation seems to remove the orientation clue that separates square from diamond and rectangle from its rotated forms. How should the config express a tighter limit for some classes, what values should the validation search try, and how do I make sure the cap really reaches the transform?

## Response

Your diagnosis is sound, so this is mostly a question of where the rule lives and how we test it.

### Where the rule should live

I'd put the per-class limit in the taxonomy section of the config, for example `taxonomy.rotate_limit_deg: {square: 10, rectangle: 10, diamond: 10}`, and keep `augment.rotate_deg` as the global range. The reasoning: which classes are orientation-sensitive is a fact about the label set, not about one augmentation run. Every arm that builds the transform then inherits the same rule.

### How the transform uses it

In `build_transform`, map class names to label ids once, and pass the cap for the current label into the per-image augment call. The effective range is `min(global, cap)`. That keeps the hot path cheap and means a missing entry simply means "no cap".

### What to search

Two dimensions, sampled together:

| Knob | Suggested values | Why |
|---|---|---|
| Global range | 0, 5, 10, 15, 20, 30, 45, 90, 180 | Spans "off" to the current setting |
| Cap for the three classes | none, 0, 5, 10, 15, 30 | "None" reproduces the uncapped behaviour as a control |

One cap shared by the three classes is enough at our data size. Separate caps per class triple the space for little expected gain.

### How to check the cap reaches the transform

- A unit test: build the transform with a large global range and a cap of 0 for square, augment one square many times, and assert the output is never rotated beyond what scale and shear alone explain. Do the same for an uncapped class and assert it does rotate.
- A visual check: one real training square through the real transform, with and without the cap, side by side.

### Cautions

- The search must read only train and val. Fix the winner before any test evaluation, or the cap becomes a test-tuned parameter.
- A cap removes a source of label noise but also some variety. Check that square, rectangle and diamond improve on validation and that circle or octagon do not drop.
- If the winning cap equals the global range, the cap did nothing and the simpler config should win.

I'd treat this as a small, reversible change: one config key, a few lines in the transform, and a test.

## Validation

Caught by test (worksheet). The A1 rotation ablation (`phase_ablation.json`, three seeds each) gave validation macro-F1 89.38 at 0°, 93.62 at ±15°, 89.91 at ±45°, 90.58 at ±90° and 90.64 at ±180°. Per-class means ±15° -> ±180°: square 93.9 -> 90.3, rectangle 87.8 -> 82.3, diamond 96.1 -> 86.9.

## Our decision

±180° for every class -> ±20°, capped at ±10° for square, rectangle and diamond, stored as `taxonomy.rotate_limit_deg` in the winner overrides (`winners.json`). The search grid is `ROTATIONS` and `ROTATION_CAPS` in `src/stage4_train/search.py`; the cap is applied in `build_transform` in `src/stage2_augment/transform.py`.

## Measured effect

The A1 winner averaged 94.77 validation macro-F1 over three seeds (`winners.json`). No macro-F1 for this change alone is recorded.

## Deeper detail: why the cap matters

### The cap is class-aware

| Class | Cap | Why |
|---|---|---|
| Most classes | None (global ±20°) | Rotation is label-preserving |
| Square, rectangle, diamond | ±10° | 45° would confuse square with diamond |

- **Why the cap is class-aware:** it protects the three orientation-sensitive classes.
- **Why the global range is ±20°:** it's the best macro F1 (94.77 over three seeds).
- **Why this is a good design:** it's class-aware, not one-size-fits-all.

### The search grid covers both ends

| Knob | Values | Why |
|---|---|---|
| Global range | 0, 5, 10, 15, 20, 30, 45, 90, 180 | Spans "off" to current |
| Cap | none, 0, 5, 10, 15, 30 | "None" is the control |

- **Why the grid covers both ends:** it includes "off" (0°) and the current setting (180°).
- **Why "none" cap is the control:** it reproduces the uncapped behaviour.
- **Why this is a good search design:** it's comprehensive.

### The unit test proves the cap works

- **Cap of 0 for square:** the output is never rotated beyond scale/shear.
- **Uncapped class:** the output does rotate.
- **Why this matters:** it proves the cap actually reaches the transform.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | C03 | The square/diamond distinction is what C03 protects |
| F07 (the finding) | C03 | F07 is the finding; C03 is the fix |
| T35 (transform fix) | C03 | C03 is part of T35's three groups |
| A01 (noise bands) | C03 | The noise bands are the metric for the ablation |

- **Why this matters:** C03 is the fix for F07, building on S07, T35, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The cap is class-aware.** It protects the three orientation-sensitive classes.
- **The search grid covers both ends.** It includes "off" and the current setting.
- **The unit test proves the cap works.** It's a good test.
- **Cross-reference to S07, F07, T35, A01:** C03 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.