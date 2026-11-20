# 4_testing - chore(iteration-3): freeze the iteration 2 report inputs and evidence
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T46, commit d12a48e (type: solved)
- Course stage: deployment (not a course stage)
- Worksheet entries: F28
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T46), `results/llm_comparison/attribution_worksheet.csv` (F28), `results/llm_comparison/opus_task_responses.md` (T46 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T46 - chore(iteration-3): freeze the iteration 2 report inputs and evidence. Stage: deployment (not a course stage). Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

F28: report Section K would have shown iteration 3 numbers. The fix makes both report sections read the frozen iteration 2 copies, and the iteration 2 record stays as it was (attribution_worksheet.csv F28). Opus proposed the change (commit_tasks.csv T46).

## Validation
Cross-checked against commit_tasks.csv row T46 and worksheet entry F28.

## Our decision
F28 kept as recorded.

## Measured effect
None recorded.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T46`)

### Upgraded reading: the "living report" hazard

F28: report Section K would have shown *Iteration 3* numbers inside the *Iteration 2* report. This is a **temporal contamination** bug in the reporting layer: the report reads live data instead of a frozen snapshot.
- **Why it matters:** a failure record whose numbers silently drift to a later iteration is *not evidence of what happened in Iteration 2*. It would retrospectively launder a `fail` into whatever the next iteration produced.
- **Fix:** both report sections read the *frozen Iteration 2 copies*; the Iteration 2 record stays as it was.
- **Logic:** freezing is the reporting-layer analogue of the test-split freeze. Same principle, different artifact.

