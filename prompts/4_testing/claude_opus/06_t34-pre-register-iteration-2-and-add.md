# 4_testing - docs(crisp-dm): pre-register iteration 2 and add a fresh holdout
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T34, commit 7f356d6 (type: solved)
- Course stage: 4_testing / 3_modeling / 1_data_integration
- Worksheet entries: F06, F13, C02, C15, C16
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T34), `results/llm_comparison/attribution_worksheet.csv` (F06, F13, C02, C15, C16), `results/llm_comparison/opus_task_responses.md` (T34 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T34 - docs(crisp-dm): pre-register iteration 2 and add a fresh holdout. Stage: 4_testing / 3_modeling / 1_data_integration. Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

Opus proposed the pre-registration and the fresh holdout, mediated by the team (commit_tasks.csv T34, llm_role: proposed, mediated). F13: the test split had already been read in iteration 1. C02: a 4,500-image fresh holdout that informed no choice, sealed like the test split. C15: A2 vs A0 became the primary comparison, fixed before tuning. C16: the evaluation data became the reused test split plus the fresh holdout (attribution_worksheet.csv F13, C02, C15, C16). F06 records the hand-set augmentation ranges that were searched in iteration 2.

## Validation
Cross-checked against commit_tasks.csv row T34 and worksheet entries F06, F13, C02, C15 and C16.

## Our decision
C02, C15 and C16 kept as recorded. The test split was reused alongside the fresh holdout, not replaced (C16). Pre-registration was recorded before tuning (C15).

## Measured effect
No macro F1 change is recorded in this entry. The outcome of the pre-registered comparison is in F14 (A2 vs A0, +0.06 on test, +0.08 on the fresh holdout).
