# 3_modeling - docs(report): correct the Phase 2 report and add the LOSO and GPU statements

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T24, commit 8984a50 (type: solved)
- Course stage: 3_modeling
- Worksheet entries: F02, F17, C09, D03, D04
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T24), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T24), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F02, F17, C09, D03, D04).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T24 - docs(report): correct the Phase 2 report and add the LOSO and GPU statements. Claim: proposed by Opus 5.5 and Gemini 4 Neon. Worksheet: F02, F17, C09, D03, D04.

## Response

Repo record (`opus_task_responses.md`, T24), not a saved reply:

> Corrected the report so it says leave-one-source-out runs use nine classes and are scored on Hand-Drawn triangles and rectangles only (F02). It also records the GPU move (D04). The correction matters because the earlier text overstated coverage.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F02: Runs use nine classes and are scored on Hand-Drawn triangles and rectangles only.
- F17: Moved to four convolution blocks.
- C09: The network could not see a whole shape.
- D03: Final network (src/stage4_train/model.py): 4 blocks of Conv 3x3 -> BatchNorm -> ReLU -> MaxPool 2, channels 32/64/128/128, then global average pooling, Dropout and one Linear layer (242,250 parameters). The depth change from 3 to 4 blocks (22-px to 46-px receptive field on 64-px images) is F17/C09.
- D04: Added GPU support with a CUDA build of PyTorch and pinned train.device: cuda so a run cannot fall back to the CPU. Rule kept: every arm of one experiment trains on the same hardware, because GPU and CPU runs are not numerically identical. Estimated 1 to 2 h instead of 12+ h for the 17-run budget (estimate, 2026-11-08); measured later: 175 trainings in about 3 h 50 min in the iteration 3 search (C39).

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the correction matters

| Before | After | Why |
|---|---|---|
| Overstated coverage | Correct: 9 classes, 2 scored | Accurate |
| No GPU statement | GPU move recorded | Complete |

- **Why the correction matters:** the earlier text overstated coverage.
- **Why the GPU statement matters:** it completes the record.
- **Why this is a good fix:** it's accurate.

### The LOSO scope is now correct

| Scope | What it means | Why |
|---|---|---|
| 9 classes | One left out | Correct |
| 2 scored | Hand-Drawn triangles + rectangles | Correct |

- **Why the scope matters:** it's the actual coverage.
- **Why this is a good fix:** it's accurate.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F02 (LOSO scope) | T24 | F02 is the finding, T24 is the fix |
| F17 (receptive field) | T24 | F17 is related |
| C09 (four blocks) | T24 | C09 is related |
| D03 (final network) | T24 | D03 is related |
| D04 (GPU support) | T24 | D04 is related |

- **Why this matters:** T24 is the fix for F02, building on F17, C09, D03, and D04.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The correction matters.** The earlier text overstated coverage.
- **The LOSO scope is now correct.** 9 classes, 2 scored.
- **Cross-reference to F02, F17, C09, D03, D04:** T24 builds on all five.

