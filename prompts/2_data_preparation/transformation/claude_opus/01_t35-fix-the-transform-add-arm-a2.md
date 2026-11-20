## 

# 2_data_preparation/transformation - T35: Fix the transform, add arm A2, tuning and the fresh holdout

- LLM: Claude Opus 5.5, medium effort (simulated reconstruction)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T35 (`solved`, `2_data_preparation/transformation / 3_modeling / 4_testing`)
- Owner / Proposed by: 40256377 + 40297573 + 40304911 + 40211352 + 40248536 + 40253714 / gemini_4_neon + opus_medium_5.5 + 40297573 + 40211352 + 40304911 + 40248536 + 40256377 + 40253714
- LLM role: proposed, mediated, assisted (both LLMs)
- Grounding sources: `results/llm_comparison/commit_tasks.csv` (T35), `results/llm_comparison/attribution_worksheet.csv` (F06 to F09, C03 to C06, C08, C10 to C12, C16), `results/phase2_snapshot/iteration_log.json`, `docs/crisp_dm/iteration_2/investigation/data_analysis.json`, `src/stage2_augment/transform.py`, `configs/pipeline.yaml`, commit 87711f3
- **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt

> The iteration 2 investigation is in. Augmented shapes come out at about 51 px against about 57 px for real images, 1-px strokes break into pieces after warping, and rotation up to ±180° seems to hurt square, rectangle and diamond. Gemini suggested searching the augmentation and generator ranges on validation instead of setting them by hand, and only A1 was ever tuned. We want to fix the transform and retrain in one commit. What should go in, and is there a training arm we are missing?

## Response

There are three groups of problems here, and I'd keep them separate in the commit message even if they land together.

### 1. Transform bugs (fix first, no search needed)

- The 51 px against 57 px gap and the broken 1-px strokes are defects, not settings to tune.
- **Why the 51 vs 57 px gap matters:** an augmented training shape is about 6 px smaller than a validation or test image, so a model trained on them sees a size shift that never appears at evaluation. This is a train/test mismatch.
- **Why broken 1-px strokes matter:** warping breaks 1-px strokes into pieces, which corrupts the shape.
- **Fix:** re-frame the transformed bounding box the way Stage 1 standardizes images (`frame_margin: 0.06`), and give 1-px strokes their own handling after warping.
- **Why measurement, not macro F1:** these are defects, not settings. They should be checked by measurement (shape size, pieces per stroke), not by macro F1.

### 2. Settings that were guesses

- I agree with Gemini that rotation, scale, shear, translation, noise and blur ranges, and the generator ranges, should be searched.
- **Two cautions:**
  - Search on validation only. The test split must not choose any setting.
  - Rotation is class-dependent. A square turned 45° looks like a diamond, so a single global range can help most classes and hurt three. Search a global range plus a tighter cap for square, rectangle and diamond.
- **Why tuning only A1 is a problem:** sharing A1's learning rate and dropout with every arm favours A1. Tune each arm on its own.

### 3. A missing arm

- Right now B mixes clean and synthetic images, and A1 mixes clean and augmented ones. Nothing tests clean + augmented + synthetic together.
- **Why A2 is needed:** you can't tell whether the two help each other or overlap without testing all three together.
- **Fix:** add an arm A2 with all three in each batch, with its generator ranges searched separately from B's.

### On the test split

- After several rounds of decisions, the test split has been seen many times. A fresh holdout that played no part in any choice gives you one number you can defend.

### Order of work

- Fix the transform, rerun the measurements, then search, then train. If the search runs on the buggy transform, its winners are tuned to the bug.

## Validation

- Commit 87711f3 solves F06 to F09, C03 to C06, C08, C10 to C12 and C16 (`results/llm_comparison/commit_tasks.csv`).
- Opus's recorded share: proposed C10 (arm A2); mediated F06, F07, C03, C04, C08, C11 and C12 together with Gemini. F08, F09, C05 and C16 are credited to Gemini, and C06 to a team member with no LLM (`results/llm_comparison/attribution_worksheet.csv`).
- The framing fix is visible in `src/stage2_augment/transform.py` (`frame_margin`) and `configs/pipeline.yaml` (`frame_margin: 0.06`, commented "re-frames to about 57 px").

## Our decision

All three groups went into one commit. The team kept the order transform fix -> search -> training. A2 was added as proposed.

## Measured effect

- Rotation: ±180° -> ±20°, capped at ±10° for square, rectangle and diamond (C03).
- Searched settings: scale 0.904 to 1.076, shear 1.4°, translation 0, noise probability 0.385, blur probability 0.373 (C04).
- A2 batches hold 105 clean, 100 augmented and 51 synthetic images (C10).
- Tuned per arm: learning rate 0.003 for all, dropout 0.2, except A0 at 0.4 (C12).
- Pieces per 1-px stroke: 17.2 -> 16.3 -> 1.0 (F09). No macro F1 change is recorded for this commit as a whole.

## Deeper detail: why each fix matters

### The 51 vs 57 px gap is a train/test mismatch

| Aspect | Augmented (train) | Real (val/test) | Gap |
|---|---|---|---|
| Shape size | ~51 px | ~57 px | ~6 px |

- **Why this is a problem:** the model trains on 51 px shapes but evaluates on 57 px shapes, which is a size mismatch.
- **Why this hurts:** the model learns "51 px is normal", then sees 57 px at evaluation and gets confused.
- **Why `frame_margin: 0.06` fixes it:** it re-frames the transformed bounding box to about 57 px, matching the real images.

### Broken 1-px strokes are a defect

| Metric | Before | After fix |
|---|---|---|
| Pieces per 1-px stroke | 17.2 | 1.0 |

- **Why this is a problem:** warping breaks 1-px strokes into 17.2 pieces, which corrupts the shape.
- **Why the fix works:** giving 1-px strokes their own handling after warping reduces pieces to 1.0 (no breaking).
- **Why this is a defect, not a setting:** it's a bug, not a tunable parameter.

### Rotation is class-dependent

| Class | Safe rotation | Why |
|---|---|---|
| Most classes | ±20° | General augmentation |
| Square, rectangle, diamond | ±10° | 45° would confuse square with diamond |

- **Why rotation is class-dependent:** a square turned 45° looks like a diamond, so a single global range can help most classes and hurt three.
- **Why the tighter cap for square/rectangle/diamond:** it prevents the confusion.
- **Why this is a good design:** it's class-aware, not one-size-fits-all.

### Arm A2 is the missing combination

| Arm | Clean | Augmented | Synthetic | Why |
|---|---|---|---|---|
| A0 | Yes | No | No | Baseline |
| A1 | Yes | Yes | No | Clean + augmented |
| B | Yes | No | Yes | Clean + synthetic |
| A2 | Yes | Yes | Yes | All three |

- **Why A2 is needed:** without it, you can't tell whether augmented and synthetic help each other or overlap.
- **Why 105/100/51:** the batch composition for A2 (105 clean, 100 augmented, 51 synthetic).
- **Why this is a good design:** it tests the full combination.

### The fresh holdout is the unbiased check

- **Why a fresh holdout:** after several rounds of decisions, the test split has been seen many times. A fresh holdout that played no part in any choice gives you one number you can defend.
- **Why this matters:** it's the same pattern as C02/C24 (fresh holdouts for unbiased evaluation).

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | T35 | The 18,000 active rows are the input to the transform |
| I02 (identity) | T35 | The `md5`/`phash` come from the transform |
| I03 (global grouping) | T35 | The `phash_group` comes from the transform |
| I04 (fail-closed freeze) | T35 | The fresh holdout is part of the sealed splits |
| I05 (FD checks) | T35 | The 6 FDs validate the schema the transform preserves |
| I06 (standardization) | T35 | The 64x64 standardized PNGs are the input to the transform |
| F05 (source attribution) | T35 | The shortcut is mitigated by the transform |
| C02 (fresh holdout) | T35 | The first fresh holdout is part of the sealed splits |
| C24 (second fresh holdout) | T35 | The second fresh holdout is part of the sealed splits |
| A01 (noise bands) | T35 | The noise bands are the metric for the transform |

- **Why this matters:** T35 is the task that fixes the transform, adds arm A2, tunes the settings, and adds the fresh holdout, building on much of the rest of the pipeline.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The three groups (transform bugs, settings, missing arm) are well-scoped.** Each is addressed clearly.
- **The 51 vs 57 px gap is a train/test mismatch.** It's a real problem.
- **The broken 1-px strokes are a defect.** They're fixed by measurement, not macro F1.
- **Rotation is class-dependent.** The tighter cap for square/rectangle/diamond is a good design.
- **Arm A2 is the missing combination.** It tests all three (clean + augmented + synthetic).
- **The fresh holdout is the unbiased check.** It's the same pattern as C02/C24.
- **Cross-reference to I01-I06, F05, C02, C24, A01:** T35 builds on much of the rest of the pipeline.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.