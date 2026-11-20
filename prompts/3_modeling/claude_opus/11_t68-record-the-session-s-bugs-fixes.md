# 3_modeling - docs(iteration-3): record the session's bugs, fixes and improvements by CRISP-DM step

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T68, commit 6b310f8 (type: solved)
- Course stage: 3_modeling
- Worksheet entries: F23, F19, F20, F25, C37
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T68), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T68), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F23, F19, F20, F25, C37).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T68 - docs(iteration-3): record the session's bugs, fixes and improvements by CRISP-DM step. Claim: proposed by Opus 5.5 and Gemini 4 Neon, caught by four members. Worksheet: F23, F19, F20, F25, C37.

## Response

Repo record (`opus_task_responses.md`, T68), not a saved reply:

> Records the session's failures by step. F25 is a useful correction: the GPU looked idle in Task Manager, but `nvidia-smi` and run records show training on the RTX 3080, with use swinging between 0% and 96% as it waits for batches.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F23: A code audit found and fixed all five before they caused harm. Tests passed and reruns matched exactly.
- F19: Relaunched at first. Training later replaced that pool with one that starts every worker at once and turns a stalled batch into an error.
- F20: Found about 2 hours 17 minutes later, on a status request. Stopped that job and relaunched it with the finished trials reused. Long jobs now run with a stall watcher checked every 5 minutes. Training later stopped using that worker pool.
- F25: Confirmed with nvidia-smi and the run records that training was on the RTX 3080. Its use swings between 0% and 96% as it waits for the next batch.
- C37: A crash at 66 of 191 trials showed the gap.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the GPU looked idle

| Tool | What it showed | Why it misled |
|---|---|---|
| Task Manager | GPU idle | Wrong metric |
| `nvidia-smi` | Training on RTX 3080 | Correct |
| Run records | Use swings 0-96% | Correct |

- **Why the GPU looked idle:** Task Manager showed the wrong metric.
- **Why `nvidia-smi` is correct:** it shows the real GPU use.
- **Why this is a good correction:** it's empirical.

### The five bugs were found and fixed

| Bug | What it was | Fix |
|---|---|---|
| F23 | Five bugs in the shared pool | All fixed by audit |
| F19 | Relaunched at first | Later replaced the pool |
| F20 | Hung silently 2h17m | Stall watcher every 5 min |
| F25 | GPU looked idle | Confirmed with nvidia-smi |
| C37 | Crash at 66/191 | Rule for next crash |

- **Why these matter:** they're real bugs with real fixes.
- **Why this is a good record:** it's thorough.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F23 (five bugs) | T68 | F23 is the finding, T68 is the record |
| F19 (relaunched) | T68 | F19 is related |
| F20 (stall watcher) | T68 | F20 is related |
| F25 (GPU idle) | T68 | F25 is the correction |
| C37 (crash rule) | T68 | C37 is the rule |

- **Why this matters:** T68 is the record for all five, building on F23, F19, F20, F25, and C37.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The GPU looked idle but wasn't.** Task Manager misled.
- **The five bugs were found and fixed.** All by audit.
- **Cross-reference to F23, F19, F20, F25, C37:** T68 builds on all five.

