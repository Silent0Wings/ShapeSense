# 3_modeling - docs(iteration-3): record the GPU error during the search

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T67, commit b81b67f (type: faced (recorded))
- Course stage: 3_modeling
- Worksheet entries: F22, C37
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T67), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T67), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F22, C37).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T67 - docs(iteration-3): record the GPU error during the search. Claim: proposed by Opus 5.5 and Gemini 4 Neon, caught by two members. Worksheet: F22, C37.

## Response

Repo record (`opus_task_responses.md`, T67), not a saved reply:

> F22: the search stopped at 66 of 191 trials with a GPU error. The response was to confirm the GPU worked, stop the leftover process, relaunch, and carry over the 66 finished trials. C37 writes that as a rule for the next crash.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F22: Confirmed the GPU still worked, stopped the leftover process and relaunched. The 66 finished trials carried over.
- C37: A crash at 66 of 191 trials showed the gap.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the response is the right one

| Step | What it does | Why |
|---|---|---|
| Confirm GPU works | Rules out hardware | Correct diagnosis |
| Stop leftover process | Frees the GPU | Correct action |
| Relaunch | Resumes | Correct action |
| Carry over 66 trials | Saves compute | Efficient |

- **Why the response is right:** it's a correct diagnosis + correct action + efficiency.
- **Why this is a good practice:** it's systematic.

### The rule for the next crash

| Rule | What it means | Why |
|---|---|---|
| C37 | Written rule for next crash | Prevents repeat |

- **Why the rule matters:** it prevents repeat.
- **Why this is a good practice:** it's proactive.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F22 (GPU error) | T67 | F22 is the finding, T67 is the record |
| C37 (crash rule) | T67 | C37 is the rule |

- **Why this matters:** T67 is the record for F22 and the rule for C37.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The response is the right one.** Correct diagnosis + action + efficiency.
- **The rule for the next crash.** It prevents repeat.
- **Cross-reference to F22, C37:** T67 builds on both.

