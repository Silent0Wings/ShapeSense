# 4_testing - test(stage5): expect hold-out runs for all five arms
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T71, commit a5d57b3 (type: tested)
- Course stage: 4_testing
- Worksheet entries: none (no worksheet entry)
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T71), `results/llm_comparison/attribution_worksheet.csv` (no worksheet entry), `results/llm_comparison/opus_task_responses.md` (T71 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T71 - test(stage5): expect hold-out runs for all five arms. Stage: 4_testing. Type: tested. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

A test that expects hold-out runs for all five arms, which keeps the test suite in line with the arm list (opus_task_responses.md, T71; commit_tasks.csv T71, llm_role: proposed).

## Validation
Cross-checked against commit_tasks.csv row T71 and the T71 section of opus_task_responses.md.

## Our decision
Kept as recorded.

## Measured effect
None recorded.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T71`)

### Upgraded reading

Keeps the test suite in line with the arm list (A0, A1, B, A2, P). The subtle point: if the suite silently stopped requiring a hold-out run for one arm, that arm's absence would look like a pass. **A test that expects all five arms is a completeness guard** — it prevents "missing data" from masquerading as "no difference."

