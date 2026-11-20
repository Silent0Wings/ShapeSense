# 4_testing - fix(studio): correct old failure charts and make results easier to read
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T82, commit 9d24f95 (type: solved)
- Course stage: deployment (not a course stage)
- Worksheet entries: F31, C54
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T82), `results/llm_comparison/attribution_worksheet.csv` (F31, C54), `results/llm_comparison/opus_task_responses.md` (T82 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T82 - fix(studio): correct old failure charts and make results easier to read. Stage: deployment (not a course stage). Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

F31: the page for failure F14 showed iteration 3 numbers. Earlier failures now read the frozen record of their own iteration, so F14 shows +0.06 and +0.08. F11 shows a note, because no per-epoch log was kept for that run (attribution_worksheet.csv F31). C54: the screen review fixes, including headline wording, contrast, folding of findings and phone touch targets (attribution_worksheet.csv C54). Opus assisted (commit_tasks.csv T82, llm_role: assisted).

## Validation
Cross-checked against commit_tasks.csv row T82 and worksheet entries F31 and C54.

## Our decision
F31 and C54 kept as recorded.

## Measured effect
F14 now shows +0.06 and +0.08 from its own frozen record (F31).

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T82`)

### Upgraded reading: two fixes with different logics

- **F31 (temporal correctness):** the F14 page was showing *Iteration 3* numbers; now earlier failures read their *own* frozen iteration, so F14 correctly shows `+0.06` and `+0.08`. F11 shows a note because no per-epoch log was kept — i.e., **absence of evidence is labeled as such**, not silently filled.
- **C54 (accessibility/legibility):** headline wording, contrast, folding of findings, phone touch targets — makes the verdict readable to a real audience.

> **Depth note:** This is the same contamination family as T46 and T73. Three separate fixes (T46, T73, T82) all defend the principle *"a record must show its own iteration's numbers."* That repetition is itself evidence the team treated temporal integrity as a first-class requirement.

