## 

# 2_data_preparation/transformation - F07: Rotation up to ±180° hurt the classes that depend on orientation



- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: `../claude_opus/02_F07_rotation-up-to-180-hurt-the-classes-that-dep.md`
- Date: 2026-11-09
- Entry: F07 (`failure`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40297573 / gemini_4_neon + 40297573
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#f07), `results/llm_comparison/attribution_worksheet.csv` (F07), `results/phase2_snapshot/iteration_log.json` (F07), `docs/crisp_dm/iteration_2/search/phase_ablation.json`, `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c

## Prompt

> The per-arm search keeps pointing at heavy augmentation as one source of error, and the per-class scores suggest rotation up to 180 degrees hurts squares, rectangles and diamonds. Why would full rotation hurt exactly those three classes? What rotation range should we search on validation, and should some classes get their own tighter limit?

## Response

Short answer: those three classes are the only ones in your taxonomy where angle is part of the definition, and your sources are not angle-balanced.

### Step 1: check the data before the model

Open a contact sheet of training squares and rectangles, one row per source. My expectation is that some sources draw them almost always upright and others at any angle. If that holds, orientation is a real feature for part of the data, and ±180° removes it. It is also a source-style signal, so keep that in mind when you read the results.

### Step 2: name the two failure modes

- Square at 45° looks like a diamond. Diamond at 45° looks like a square. Full rotation makes these pairs overlap in training while the labels stay fixed.
- Rectangle has no such twin in the taxonomy, but a rotated rectangle loses the upright cue that some sources provide.

### Step 3: design the search

I'd make it two-dimensional:

1. A global range for all classes, from small to the current value, for example 0, 5, 10, 15, 20, 30, 45, 90, 180 degrees.
2. A per-class cap for square, rectangle and diamond only, including "no cap" and "zero rotation", for example none, 0, 5, 10, 15, 30.

Effective rotation for a capped class is the smaller of the two. Implement it inside the transform so every arm that uses the transform gets the same rule.

### Step 4: add a one-factor ablation

Fix the arm and hyperparameters, vary only the global range (0, 15, 45, 90, 180), three seeds each. This tells you whether the effect is rotation or something the random search happened to change at the same time.

### Step 5: decide on per-class F1

Use macro-F1 to rank, but a winner should not lower square, rectangle or diamond against the uncapped setting.

### Risks

- Do not tune on the test split, and do not peek at test per-class numbers to choose the cap. Validation only.
- The cap only fixes rotation. Shear and non-uniform scale can also turn a square into a rhombus or a rectangle into a square. Check whether those need class rules too.
- Watch for runs that stop very early; their scores are not comparable.

## Validation

Caught by test (worksheet). In `docs/crisp_dm/iteration_2/search/phase_ablation.json` (arm A1, three seeds each), validation macro-F1 was 0° 89.38, ±15° 93.62, ±45° 89.91, ±90° 90.58, ±180° 90.64. Per-class means ±15° -> ±180°: square 93.9 -> 90.3, rectangle 87.8 -> 82.3, diamond 96.1 -> 86.9. The no-rotation runs stopped after 11 to 13 epochs (`iteration_log.json` caption).

## Our decision

Searched the range on validation with `sample_augment` in `src/stage4_train/search.py` (global `ROTATIONS` plus one cap from `ROTATION_CAPS` for square, rectangle and diamond); the cap is applied in `build_transform`. Winner: ±20°, capped at ±10° for the three classes. Same change as C03.

## Measured effect

A1 winner: 94.77 mean validation macro-F1 over three seeds (`winners.json`). No isolated macro-F1 effect of the cap is recorded. State: Overcome.

## Deeper detail: why rotation hurts these classes

### The three classes depend on angle

| Class | Why angle matters | What full rotation does |
|---|---|---|
| Square | 45° looks like diamond | Overlaps with diamond |
| Rectangle | Upright cue lost | Loses the cue |
| Diamond | 45° looks like square | Overlaps with square |

- **Why angle matters for these three:** they're the only classes where angle is part of the definition.
- **Why full rotation hurts:** it removes the orientation cue.
- **Why this is a real failure:** it's a class-definition issue.

### The two failure modes

| Failure mode | What it does | Which classes |
|---|---|---|
| Square/diamond overlap | 45° makes them look alike | Square, diamond |
| Rectangle loses upright cue | Rotated rectangle loses the cue | Rectangle |

- **Why these two modes matter:** they explain the per-class drops.
- **Why the ablation is needed:** it isolates rotation from other changes.
- **Why this is a good design:** it's causal.

### The search is two-dimensional

| Dimension | What it searches | Why |
|---|---|---|
| Global range | 0 to 180° | Finds the best overall |
| Per-class cap | none to 30° for 3 classes | Protects the angle-dependent classes |

- **Why two dimensions:** the global range and the per-class cap are separate.
- **Why the cap is per-class:** only the 3 angle-dependent classes need it.
- **Why this is a good design:** it's targeted.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | F07 | The class definitions are why angle matters |
| C03 (rotation cap) | F07 | C03 is the fix for F07 |
| C04 (other augmentation) | F07 | Shear and non-uniform scale are related |
| A01 (noise bands) | F07 | The noise bands are the metric for the fix |

- **Why this matters:** F07 is the finding, C03 is the fix, and they build on S07, C04, and A01.

## Notes on the log


- **The three classes depend on angle.** That's why full rotation hurts them.
- **The two failure modes are real.** Square/diamond overlap and rectangle losing the cue.
- **The search is two-dimensional.** Global range + per-class cap.
- **Cross-reference to S07, C03, C04, A01:** F07 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.