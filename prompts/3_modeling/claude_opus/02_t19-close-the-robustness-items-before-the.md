# 3_modeling - fix: close the robustness items before the final Stage 4 rerun

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T19, commit e10169d (type: solved)
- Course stage: 3_modeling
- Worksheet entries: N02
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T19), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T19), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (row N02).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T19 - fix: close the robustness items before the final Stage 4 rerun. Claim: proposed by Opus 5.5, caught by Opus 5.5 with a team member. Worksheet: N02.

## Response

Repo record (`opus_task_responses.md`, T19), not a saved reply:

> Fixed the data-store overhead. `ImageStore` now reads its manifest once (e10169d) instead of on every batch. This was a real bottleneck: the GPU sat idle while the SQL catalog was queried.

## Validation

Cross-read of the three repo records above. The commit diff itself was not re-read for this file.

## Our decision

- N02: ImageStore now reads its manifest once (e10169d). Batches are built ahead of the GPU by 7 processes (b3bb15d), and one shared pool with cached validation images followed (534643d). See F21 and C30.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the manifest read was a bottleneck

| Before | After | Why |
|---|---|---|
| Read manifest every batch | Read once | GPU idle |
| GPU idle | GPU busy | Bottleneck removed |

- **Why the manifest read was a bottleneck:** it happened every batch.
- **Why reading once fixes it:** it removes the repeated cost.
- **Why this is a good fix:** it's a real performance improvement.

### The batching is part of the fix

| Commit | What it did | Why |
|---|---|---|
| e10169d | Read manifest once | Removes the bottleneck |
| b3bb15d | 7 processes build batches ahead | Keeps GPU busy |
| 534643d | One shared pool + cached validation | Further optimization |

- **Why batching matters:** it keeps the GPU busy.
- **Why this is a good design:** it's a pipeline.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| N02 (manifest read once) | T19 | N02 is the finding, T19 is the fix |
| F21 (batching) | T19 | F21 is related |
| C30 (shared pool) | T19 | C30 is related |

- **Why this matters:** T19 is the fix for N02, building on F21 and C30.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The manifest read was a bottleneck.** Reading once fixes it.
- **The batching is part of the fix.** It keeps the GPU busy.
- **Cross-reference to N02, F21, C30:** T19 builds on all three.

