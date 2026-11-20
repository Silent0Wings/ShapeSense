# 3_modeling - feat(iteration-3): record the validation experiments under their CRISP-DM steps

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T58, commit 52e79e1 (type: solved)
- Course stage: 3_modeling
- Worksheet entries: F11, C29, F20
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T58), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T58), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F11, C29, F20).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T58 - feat(iteration-3): record the validation experiments under their CRISP-DM steps. Claim: proposed by Opus 5.5, Gemini 4 Neon and two members. Worksheet: F11, C29, F20.

## Response

Repo record (`opus_task_responses.md`, T58), not a saved reply:

> F20: the 108-trial run hung silently for about 2 hours 17 minutes. C29 is the pre-registered rule for raising the training budget to 60 epochs with no early stopping, because each arm gained at least 0.5 validation points (A0 1.99, A1 0.51, A2 0.71). The entry records both the failure and the rule.

## Validation

Cross-read of the three repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F11: Kept the same budget and early stopping for every arm so the comparison stays fair. Not fixed in iteration 2, whose results stay at 30 epochs. Iteration 3 trained every arm for 60 epochs with no early stopping.
- C29: The pre-registered rule: each tested arm gained at least 0.5 validation points (A0 1.99, A1 0.51, A2 0.71).
- F20: Found about 2 hours 17 minutes later, on a status request. Stopped that job and relaunched it with the finished trials reused. Long jobs now run with a stall watcher checked every 5 minutes. Training later stopped using that worker pool.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the rule is pre-registered

| Arm | Gain (validation points) | Threshold |
|---|---|---|
| A0 | 1.99 | >= 0.5 |
| A1 | 0.51 | >= 0.5 |
| A2 | 0.71 | >= 0.5 |

- **Why the rule is pre-registered:** it's decided before the run.
- **Why the threshold is 0.5:** it's the minimum meaningful gain.
- **Why this is a good rule:** it's principled.

### The stall is recorded

| What | Value | Why |
|---|---|---|
| Hung silently | 2h 17m | Real failure |
| Stall watcher | Every 5 min | Fix |
| Worker pool | Stopped using it | Fix |

- **Why the stall matters:** it's a real failure.
- **Why the watcher matters:** it prevents recurrence.
- **Why this is a good fix:** it's robust.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F11 (same budget) | T58 | F11 is the finding, T58 is the record |
| C29 (pre-registered rule) | T58 | C29 is the rule |
| F20 (stall) | T58 | F20 is the failure |

- **Why this matters:** T58 is the record for F11, C29, and F20.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The rule is pre-registered.** It's decided before the run.
- **The stall is recorded.** It's a real failure.
- **Cross-reference to F11, C29, F20:** T58 builds on all three.

