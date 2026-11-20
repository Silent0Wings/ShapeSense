# 4_testing - fix(stage5): repair the statistics and checks raised by the outside reviews
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T48, commit 4c7cb90 (type: solved)
- Course stage: 4_testing
- Worksheet entries: C20, C21, C22, C28
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T48), `results/llm_comparison/attribution_worksheet.csv` (C20, C21, C22, C28), `results/llm_comparison/opus_task_responses.md` (T48 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T48 - fix(stage5): repair the statistics and checks raised by the outside reviews. Stage: 4_testing. Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

Opus proposed the statistical fixes, mediated by the team (commit_tasks.csv T48, llm_role: proposed, mediated). C20: near-duplicate images are not independent, so the bootstrap resamples phash clusters (attribution_worksheet.csv C20). C21: a Bonferroni-corrected interval for the per-class harm rule (C21). C22: Holm correction on the bootstrap macro-F1 p-values, with exact McNemar reported (C22). C28: the robustness check moved into Stage 5 so the sealed perturbed sets are read in one place (C28).

## Validation
Cross-checked against commit_tasks.csv row T48 and worksheet entries C20, C21, C22 and C28.

## Our decision
C20, C21, C22 and C28 kept as recorded.

## Measured effect
No numeric change is recorded in these entries.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T48`)

### Upgraded reading: four distinct statistical defects, each with a causal rationale

| ID | Defect | Why it invalidates naive inference | Fix |
|---|---|---|---|
| C20 | Near-duplicate images are not independent | Treating them as i.i.d. understates variance → CIs too narrow → false significance | Bootstrap **resamples phash clusters**, not images |
| C21 | Per-class harm rule needed multiplicity control | Testing many classes inflates false positives | **Bonferroni-corrected** interval |
| C22 | Macro-F1 bootstrap p-values needed multiplicity control | Same inflation across the arm comparisons | **Holm correction**; exact McNemar reported alongside |
| C28 | Robustness check lived outside Stage 5 | Sealed perturbed sets could be read in more than one place → leak risk | Move robustness into Stage 5 so sealed sets are read **in one place** |

### Deeper logic

C20 is the deepest: the *effective sample size* of a dataset with near-duplicates is far below the raw image count. A cluster bootstrap correctly widens the CI to reflect the real number of independent units. This is the difference between "significant because we counted the same drawing five times" and a genuine effect. C21/C22 are family-wise error control across two axes (per-class and per-arm). C28 is a **process isolation** control — sealing is only meaningful if there's exactly one read path.

> **Cross-link:** The Iteration-3 `+9.20` result (`CI [8.89, 9.53]`) is credible *because* these repairs were in place — a narrow CI is only trustworthy if the resampling unit and multiplicity were handled correctly.

