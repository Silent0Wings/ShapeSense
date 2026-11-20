# 3_modeling - feat(studio): make the dashboard easier to explore and read

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T78, commit ff7ddbf (type: solved)
- Course stage: deployment (not a course stage) / 3_modeling
- Worksheet entries: C43, C44, C45, C46, C47, C48, C49, C50, C51, F11
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T78), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T78), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F11, C43 to C51).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T78 - feat(studio): make the dashboard easier to explore and read. Claim: proposed by Opus 5.5 and Gemini 4 Neon, reviewed by the whole team. Worksheet: F11, C43 to C51.

## Response

Repo record (`opus_task_responses.md`, T78), not a saved reply:

> Many small readability fixes. C43: the main finding now shows every model, not only Full mix vs Real. C44: a slider walks iterations 1 to 3. C45: close dots spread into lanes instead of a log scale, which would distort distances. C51: the browser now receives update notices so stale pages are not shown.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- C43: A reader could not see how the other models compared. Synthetic pretraining has no line because it was descriptive and no interval was calculated.
- C44: The wheel hid how the project moved from one question to the next.
- C45: A log scale would stretch only one end of the axis and distort distances, while lanes keep the axis honest.
- C46: It shows how the images respond to the settings.
- C47: Rows were hard to follow across the chart, and labels and values gave no feedback on hover.
- C48: A reader could not see that the models share one network and differ in their training images.
- C49: It shows at a glance which models agree and what the vote chose.
- C50: It shows where failures clustered and how the project moved between steps.
- C51: An update to the CRISP-DM wheel did not appear until the cached page was replaced.
- F11: Kept the same budget and early stopping for every arm so the comparison stays fair. Not fixed in iteration 2, whose results stay at 30 epochs. Iteration 3 trained every arm for 60 epochs with no early stopping.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the readability fixes matter

| Fix | What it does | Why |
|---|---|---|
| C43: every model | Shows all models | Complete |
| C44: slider walks iterations | Shows progression | Clear |
| C45: lanes not log scale | Honest distances | Accurate |
| C51: update notices | No stale pages | Fresh |

- **Why the fixes matter:** they make the dashboard readable.
- **Why this is a good design:** it's user-centered.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| C43-C51 (readability) | T78 | They're the findings, T78 is the fix |
| F11 (same budget) | T78 | F11 is related |

- **Why this matters:** T78 is the fix for C43-C51, building on F11.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The readability fixes matter.** They make the dashboard readable.
- **Cross-reference to C43-C51, F11:** T78 builds on all.

