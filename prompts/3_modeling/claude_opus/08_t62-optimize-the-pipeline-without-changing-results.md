# 3_modeling - perf: optimize the pipeline without changing results

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T62, commit 534643d (type: solved)
- Course stage: 3_modeling / 1_data_integration / 2_data_preparation/transformation / 4_testing
- Worksheet entries: C34, C35, C36, F23, F24, C31, N02
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T62), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T62), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows C31, C34, C35, C36, F23, F24, N02).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T62 - perf: optimize the pipeline without changing results. Claim: proposed by Opus 5.5 and Gemini 4 Neon, built by team members. Worksheet: F23, F24, C31, C34 to C36, N02.

## Response

Repo record (`opus_task_responses.md`, T62), not a saved reply:

> Opus proposed the speedups. F24 is the key check: converting pixels on the GPU would have changed every result, so the team measured it and used a CPU lookup table. F23: the first shared worker pool had five bugs, all found by audit before they did harm. Two reruns matched the earlier trials on every logged number.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- C34: Every run pays for hashing. These do not change any result.
- C35: The same stored images are augmented many times. Tests and reruns confirm identical output.
- C36: Removes repeated work without changing any number.
- F23: A code audit found and fixed all five before they caused harm. Tests passed and reruns matched exactly.
- F24: Measured it before using it, and used a lookup table of the exact CPU values instead.
- C31: A named stage inside Modeling. Optimizations are registered once measured. Both reruns matched the earlier trials on every logged number.
- N02: ImageStore now reads its manifest once (e10169d). Batches are built ahead of the GPU by 7 processes (b3bb15d), and one shared pool with cached validation images followed (534643d). See F21 and C30.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why "without changing results" is the bar

| Optimization | What it does | Why it doesn't change results |
|---|---|---|
| C34 | Every run pays for hashing | No result change |
| C35 | Same images augmented many times | Identical output |
| C36 | Removes repeated work | No number change |
| F24 | GPU conversion would change results | CPU lookup table instead |

- **Why "without changing results" is the bar:** it's the requirement.
- **Why F24 is the key check:** it's the one that could change results.
- **Why this is a good design:** it's safe.

### The five bugs were found by audit

| Bug | What it was | Fix |
|---|---|---|
| F23 | Five bugs in shared pool | All fixed by audit |

- **Why audit matters:** it catches bugs before harm.
- **Why reruns matter:** they confirm identical output.
- **Why this is a good practice:** it's rigorous.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| C31 (named stage) | T62 | C31 is the step |
| C34-C36 (optimizations) | T62 | They're the optimizations |
| F23 (five bugs) | T62 | F23 is the audit |
| F24 (GPU conversion) | T62 | F24 is the key check |
| N02 (manifest once) | T62 | N02 is related |

- **Why this matters:** T62 is the optimization task, building on C31, C34-C36, F23, F24, and N02.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **"Without changing results" is the bar.** It's the requirement.
- **The five bugs were found by audit.** Before harm.
- **Cross-reference to C31, C34-C36, F23, F24, N02:** T62 builds on all.

