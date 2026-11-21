# 2_data_preparation/feature_selection - Grading Gemini's sandboxed feature-selection answer
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/02_real_sandboxed-feature-selection-prompt.md](../gemini_4_neon/02_real_sandboxed-feature-selection-prompt.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon answer to the feature-selection prompt (sandboxed real run), as Claude Opus 5.5.

The exchange being judged: Gemini was asked what feature selection means for a 64x64 grayscale CNN, what to try (resolution, cropping, background removal, HOG or Hu moments) and how to measure it. It was given the pipeline context but no results, and answered before the experiment ran. The reply is real but truncated: the CLI returned only the first 3,129 bytes, and it stops in point 4.

## Response

### Grade: A (88 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 22 / 25 | Feature selection for a CNN means choosing the input representation, not picking columns. That is the right framing, and it matches the project's own answer (FS1 in `../inferred_prompts.md`). |
| Read the question correctly | 19 / 20 | It answered all three parts and used the context given: 10 classes, four sources, the 8% margin crop, letterboxing and macro F1. |
| Fit to this project | 15 / 20 | Its top suggestion, normalizing background and domain across sources, is already done by Stage 1. On resolution it pointed the wrong way: it expected 96 or 128 px to help with circle, hexagon and octagon, but the measured winner was 48 px (95.90 against 95.80 at 64 px on validation, in the file's validation table). It did list 48 px as a lower bound to check. |
| Actionable advice | 18 / 20 | A clear ranked list and a sound measurement plan: one change at a time, 3 to 5 seeds, mean and standard deviation, a paired bootstrap or McNemar test, per-source macro F1 and a leave-one-source-out check. The project does each of these. |
| Accuracy of details | 14 / 15 | The two caveats are exactly right. Hu moments are rotation-invariant, so alone they cannot separate a square from a diamond. Normalizing orientation in the crop would merge those two classes. The note that 128 px costs about 4 times the computation of 64 px is also correct. |

### What it got right
- The framing of feature selection for a CNN.
- The square and diamond caveats on Hu moments and on orientation-normalizing crops. The project protects that pair the same way.
- The warning that contour features break on hand-drawn strokes.
- A measurement protocol that matches the project's: several seeds, paired tests, per-source results and a leave-one-source-out check.

### What it got wrong or missed
- **Direction of the resolution test:** it favoured higher resolution. Lower won, though by less than the seed spread on validation, as the file's decision section notes.
- **What already exists:** background and domain normalization is already Stage 1's job, which added +5.51 over the raw baseline (file's validation table).
- **Truncation:** point 4 is cut off, so any further suggestions are lost. That is a recording limit, not Gemini's error.

### What I would have answered for this project
The same framing and caveats, plus one practical point: the stored images are 64 px, so lower resolutions can be tested with a resize layer at no cost, while higher ones mean re-standardizing every image. I would test 32 and 48 px first, keep 64 px as the reference, and only try higher resolutions if the lower ones lose.

## Validation

- Checked against the Gemini file, including its validation table (48 px at 95.90 on validation and 96.31 on test, standardization +5.51, HOG SVM 84.3 against the CNN's 94.6 on test), and against FS1 in `prompts/2_data_preparation/feature_selection/inferred_prompts.md`.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the reply as the real Gemini record for feature selection. Its measurement protocol and caveats are sound; its resolution expectation was tested and the result went the other way.

## Measured effect

None from this grading. The feature-selection row stays 96.31 test macro F1.
