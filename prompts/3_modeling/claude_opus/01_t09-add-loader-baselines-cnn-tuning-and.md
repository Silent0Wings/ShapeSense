# 3_modeling - feat(stage4): add loader, baselines, CNN, tuning and seeded sweep

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T09, commit 62c5fe8 (type: solved)
- Course stage: 3_modeling
- Worksheet entries: F17, C09, D03
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T09), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T09), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F17, C09, D03).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T09 - feat(stage4): add loader, baselines, CNN, tuning and seeded sweep. Claim: proposed by Opus 5.5, caught by Gemini 4 Neon. Worksheet: F17, C09, D03.

## Response

Repo record (`opus_task_responses.md`, T09), not a saved reply:

> Opus proposed the CNN design critique. The first network had three blocks and a 22-px receptive field, too small to see a whole shape (F17). Change C09 moved to four blocks, 46 px. This is a fair attribution of a real design fix.

## Validation

Cross-read of the three repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F17: Moved to four convolution blocks.
- C09: The network could not see a whole shape.
- D03: Final network (src/stage4_train/model.py): 4 blocks of Conv 3x3 -> BatchNorm -> ReLU -> MaxPool 2, channels 32/64/128/128, then global average pooling, Dropout and one Linear layer (242,250 parameters). The depth change from 3 to 4 blocks (22-px to 46-px receptive field on 64-px images) is F17/C09.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the receptive field matters

| Blocks | Receptive field | Can see whole shape? |
|---|---|---|
| 3 | 22 px | No |
| 4 | 46 px | Yes |

- **Why the receptive field matters:** it determines what the network can see.
- **Why 22 px is too small:** it can't see a whole 64-px shape.
- **Why 46 px is enough:** it can.
- **Why this is a good fix:** it's a real design improvement.

### The network design

| Layer | What it does | Why |
|---|---|---|
| 4 blocks Conv 3x3 -> BN -> ReLU -> MaxPool 2 | Feature extraction | Standard |
| Channels 32/64/128/128 | Increasing capacity | Standard |
| Global average pooling | Reduces to a vector | Standard |
| Dropout | Regularization | Standard |
| One Linear layer | Classification | Standard |
| 242,250 parameters | Model size | Reasonable |

- **Why this design:** it's standard and effective.
- **Why this is a good design:** it's well-known.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F17 (receptive field too small) | T09 | F17 is the finding, T09 is the fix |
| C09 (four blocks) | T09 | C09 is the change |
| D03 (final network) | T09 | D03 is the result |

- **Why this matters:** T09 is the fix for F17, C09 is the change, D03 is the result.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The receptive field matters.** 22 px is too small.
- **The network design is standard.** It's effective.
- **Cross-reference to F17, C09, D03:** T09 builds on all three.

