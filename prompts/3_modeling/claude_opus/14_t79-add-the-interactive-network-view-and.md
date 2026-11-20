# 3_modeling - feat(studio): add the interactive network view and explain the models

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T79, commit b39a942 (type: solved)
- Course stage: 3_modeling / deployment (not a course stage)
- Worksheet entries: C48, C52
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T79), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T79), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows C48, C52).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T79 - feat(studio): add the interactive network view and explain the models. Claim: proposed by Opus 5.5 and two members, assisted. Worksheet: C48, C52.

## Response

Repo record (`opus_task_responses.md`, T79), not a saved reply:

> C48: an interactive diagram showing that the models share one network and differ only in their training images. C52: the home page now defines the five models and their training-image kinds in one place.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- C48: A reader could not see that the models share one network and differ in their training images.
- C52: A new reader could not tell what the models were or what their training data meant.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the interactive view matters

| Element | What it shows | Why |
|---|---|---|
| Interactive diagram | Models share one network | Clarifies |
| Differ only in training images | The real difference | Clarifies |
| Home page defines 5 models | One place | Clarifies |

- **Why the interactive view matters:** it clarifies the model structure.
- **Why this is a good design:** it's educational.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| C48 (interactive diagram) | T79 | C48 is the finding, T79 is the fix |
| C52 (home page) | T79 | C52 is the finding, T79 is the fix |

- **Why this matters:** T79 is the fix for C48 and C52.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The interactive view matters.** It clarifies the model structure.
- **Cross-reference to C48, C52:** T79 builds on both.

