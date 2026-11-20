# 3_modeling - docs(readme): say the committed config needs a CUDA GPU

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T25, commit ed7f55a (type: documented)
- Course stage: 3_modeling
- Worksheet entries: D04
- Source: ** from repo, not a saved chat.** Cited repo files: [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) (row T25), [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md) (section T25), [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (row D04).

## Prompt

No prompt was saved for this task. The task statement below is the repo record, not a message that was sent to the model:

> Task: T25 - docs(readme): say the committed config needs a CUDA GPU. Claim: proposed and caught by Opus 5.5. Worksheet: D04.

## Response

Repo record (`opus_task_responses.md`, T25), not a saved reply:

> The README now says the committed config needs a CUDA GPU, which matches `train.device: cuda`. A run fails rather than falling back to the CPU, so the README should say so.

## Validation

Cross-read of the repo records above. The commit diff itself was not re-read for this file.

## Our decision

- D04: Added GPU support with a CUDA build of PyTorch and pinned train.device: cuda so a run cannot fall back to the CPU. Rule kept: every arm of one experiment trains on the same hardware, because GPU and CPU runs are not numerically identical. Estimated 1 to 2 h instead of 12+ h for the 17-run budget (estimate, 2026-11-08); measured later: 175 trainings in about 3 h 50 min in the iteration 3 search (C39).

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why the README needs to say this

| Config | What it does | Why the README matters |
|---|---|---|
| `train.device: cuda` | Requires CUDA | Must be documented |
| Fails rather than falls back | No CPU fallback | Must be documented |

- **Why the README matters:** it documents the requirement.
- **Why no fallback matters:** it's a hard requirement.
- **Why this is a good doc:** it's accurate.

### The GPU rule is consistent

| Rule | What it means | Why |
|---|---|---|
| Same hardware for all arms | GPU and CPU not numerically identical | Fair comparison |
| 1-2 h vs 12+ h | GPU is much faster | Justified |

- **Why the rule matters:** it ensures fairness.
- **Why the speed matters:** it justifies the GPU.
- **Why this is a good rule:** it's principled.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| D04 (GPU support) | T25 | D04 is the finding, T25 is the doc |
| C39 (175 trainings in 3h50m) | T25 | C39 is the measurement |

- **Why this matters:** T25 is the doc for D04, and C39 is the measurement.

## Notes on the log

- **This is a repo record, not a saved chat.** The prompt and response are from the repo.
- **The README needs to say this.** It documents the requirement.
- **The GPU rule is consistent.** Same hardware for all arms.
- **Cross-reference to D04, C39:** T25 builds on both.

