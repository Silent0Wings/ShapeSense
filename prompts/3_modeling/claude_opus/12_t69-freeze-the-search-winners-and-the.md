# 3_modeling - feat(iteration-3): freeze the search winners and the 60-epoch budget

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T69, commit e9fd141 (type: solved)
- Course stage: 3_modeling
- Worksheet entries: F11, C26, C29, C38, C39
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T69), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T69), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (rows F11, C26, C29, C38, C39).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T69 - feat(iteration-3): freeze the search winners and the 60-epoch budget. Claim: proposed by Opus 5.5 and Gemini 4 Neon, caught by four members. Worksheet: F11, C26, C29, C38, C39.

## Response

Repo record (`opus_task_responses.md`, T69), not a saved reply:

> C26: the top five settings per arm are re-scored by grouped 3-fold CV, because one validation split can favour a setting by chance. C38 freezes the winners in `configs/pipeline.yaml`. F11 is recorded as not fixed in iteration 2 and addressed in iteration 3.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- F11: Kept the same budget and early stopping for every arm so the comparison stays fair. Not fixed in iteration 2, whose results stay at 30 epochs. Iteration 3 trained every arm for 60 epochs with no early stopping.
- C26: One validation split can favour a setting by chance.
- C29: The pre-registered rule: each tested arm gained at least 0.5 validation points (A0 1.99, A1 0.51, A2 0.71).
- C38: Chosen on grouped cross-validation over train and validation, confirmed on three seeds.
- C39: Every optimization that left results unchanged. Two reruns matched the earlier trials on every logged number. Other programs were closed part way through, so the gain is partly from a quieter machine.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why grouped CV matters

| Method | What it does | Why it matters |
|---|---|---|
| Single validation split | Can favour by chance | Biased |
| Grouped 3-fold CV | Re-scores top 5 | Robust |

- **Why grouped CV matters:** it prevents chance favouritism.
- **Why top 5:** it's the candidates worth re-scoring.
- **Why this is a good design:** it's robust.

### The 60-epoch budget is pre-registered

| Arm | Gain (validation points) | Threshold |
|---|---|---|
| A0 | 1.99 | >= 0.5 |
| A1 | 0.51 | >= 0.5 |
| A2 | 0.71 | >= 0.5 |

- **Why the budget is pre-registered:** it's decided before the run.
- **Why the threshold is 0.5:** it's the minimum meaningful gain.
- **Why this is a good rule:** it's principled.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F11 (same budget) | T69 | F11 is the finding, T69 is the fix |
| C26 (grouped CV) | T69 | C26 is the method |
| C29 (pre-registered rule) | T69 | C29 is the rule |
| C38 (freeze winners) | T69 | C38 is the action |
| C39 (measured optimization) | T69 | C39 is the measurement |

- **Why this matters:** T69 is the fix for F11, building on C26, C29, C38, and C39.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **Grouped CV matters.** It prevents chance favouritism.
- **The 60-epoch budget is pre-registered.** It's decided before the run.
- **Cross-reference to F11, C26, C29, C38, C39:** T69 builds on all five.

