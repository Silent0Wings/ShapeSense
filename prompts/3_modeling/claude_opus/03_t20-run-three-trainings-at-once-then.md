# 3_modeling - chore(config): run three trainings at once on the 8 GB GPU, then two after a VRAM stall

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T20 (commit a77ebe7, "run three trainings at once on the 8 GB GPU") and T21 (commit 45f7fe0, "train two runs at once after a VRAM stall"), type: solved
- Course stage: 3_modeling
- Worksheet entries: F03, C14
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (rows T20, T21), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T20 and T21), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F03, C14).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T20 and T21 - chore(config): run three trainings at once, then two after a VRAM stall. Claim: proposed by Opus 5.5 and the same team member. Worksheet: F03, C14.

## Response

Repo record (`opus_task_responses.md`, T20 and T21), not a saved reply:

> Stage 4 stalled on the 8 GB GPU. T20 tried three parallel runs, and T21 reduced it to two after the stall. C14 pins `train.parallel_runs: 2`. The two commits show the sequence correctly: the first attempt was wrong and was corrected.

## Validation

Cross-read of the repo records above. The two commit diffs themselves were not re-read for this file.

## Our decision

- F03: Limited training to two parallel runs.
- C14: Stage 4 stalled on 8 GB of GPU memory.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why three runs stalled

| Runs | VRAM | Result |
|---|---|---|
| 3 | Over 8 GB | Stall |
| 2 | Fits | Works |

- **Why three stalled:** it exceeded the 8 GB VRAM.
- **Why two works:** it fits.
- **Why this is a good fix:** it's empirical.

### The two commits show the sequence

| Commit | What it did | Why |
|---|---|---|
| a77ebe7 (T20) | Tried three runs | First attempt |
| 45f7fe0 (T21) | Reduced to two | Corrected |

- **Why the sequence matters:** it shows the correction.
- **Why this is a good record:** it's honest.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F03 (limited to two) | T20/T21 | F03 is the finding, T20/T21 is the fix |
| C14 (parallel_runs: 2) | T20/T21 | C14 is the config change |

- **Why this matters:** T20/T21 is the fix for F03, and C14 is the config change.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **Three runs stalled.** Two works.
- **The two commits show the sequence.** First attempt, then correction.
- **Cross-reference to F03, C14:** T20/T21 builds on both.

