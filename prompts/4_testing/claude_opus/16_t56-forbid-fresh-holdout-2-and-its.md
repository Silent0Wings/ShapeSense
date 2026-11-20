# 4_testing - test(studio): forbid fresh holdout 2 and its Stage 5 folders in the sealed-data sweep
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T56, commit 002ba8c (type: tested)
- Course stage: deployment (not a course stage)
- Worksheet entries: none (no worksheet entry)
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T56), `results/llm_comparison/attribution_worksheet.csv` (no worksheet entry), `results/llm_comparison/opus_task_responses.md` (T56 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T56 - test(studio): forbid fresh holdout 2 and its Stage 5 folders in the sealed-data sweep. Stage: deployment (not a course stage). Type: tested. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

A test that stops the studio from reading the sealed fresh holdout 2 before its time (opus_task_responses.md, T56). Opus proposed it and one team member built it (commit_tasks.csv T56, llm_role: proposed).

## Validation
Cross-checked against commit_tasks.csv row T56 and the T56 section of opus_task_responses.md.

## Our decision
Kept as recorded.

## Measured effect
None recorded. It is a guard, not a result change.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T56`)

### Upgraded reading: a guard as a pre-registration enforcement mechanism

This test **mechanically prevents** the studio from reading `fresh_holdout_2` before its time. The logic chain:
1. A sealed holdout is only sealed if *no code path can read it early*.
2. A policy ("don't read it") is weak; a **test that fails the suite if the sweep touches it** is strong.
3. This is the execution-side complement to C28's single-read-path design: C28 consolidates the read path; T56 forbids the forbidden path.

> **Depth note:** This is the difference between a pre-registration *promise* and a pre-registration *enforced by CI*. The `+9.20` Iteration-3 result is only a clean holdout result because this guard (plus T71) held.

