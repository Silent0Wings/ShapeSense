# 4_testing - feat(studio): add the equal-weight All models vote
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Task: T75, commit 916e7df (type: solved)
- Course stage: deployment (not a course stage)
- Worksheet entries: F30, C40, D01
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T75), `results/llm_comparison/attribution_worksheet.csv` (F30, C40, D01), `results/llm_comparison/opus_task_responses.md` (T75 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T75 - feat(studio): add the equal-weight All models vote. Stage: deployment (not a course stage). Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

D01: the team added model voting. On the test split, soft-vote ensembles of the five seeds beat the per-seed mean for every arm: A0 94.6 to 95.5, A1 95.8 to 96.2, B 95.6 to 95.8, A2 95.8 to 96.0, P 95.8 to 96.2 macro F1 (attribution_worksheet.csv D01, citing results/phase2_snapshot/metrics.csv). C40: equal weights scored 95.59 against 94.80 for per-class weights on held-apart validation. That validation was reused, so the figures are optimistic (C40). F30: the first vote comparison scored an empty class as zero. The fix balances the halves by class and leaves absent classes out (F30). Opus proposed the vote (commit_tasks.csv T75, llm_role: proposed).

## Validation
Cross-checked against commit_tasks.csv row T75 and worksheet entries D01, C40 and F30. The D01 numbers are as recorded in the worksheet and were not re-run here.

## Our decision
Equal weights kept (C40). The team disagreed over weighted and per-class options (C40 notes).

## Measured effect
Macro F1 soft-vote deltas on test (D01): A0 +0.9, A1 +0.4, B +0.2, A2 +0.2, P +0.4. C40: 95.59 vs 94.80 on reused validation.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T75`)

### Upgraded reading: ensembling as variance reduction, with an honest caveat

D01: soft-vote ensembles of five seeds beat the per-seed mean for **every** arm:
- A0 `94.6 → 95.5`, A1 `95.8 → 96.2`, B `95.6 → 95.8`, A2 `95.8 → 96.0`, P `95.8 → 96.2` macro-F1.

**Mechanism:** averaging decorrelated errors across seeds reduces variance without adding bias — a near-free gain. **Design choice:** C40 — equal weights `95.59` vs per-class weights `94.80` on held-apart validation; the team chose equal weights and *noted disagreement* over weighted/per-class options. **Honest caveat:** that validation was *reused*, so the figures are optimistic. **Bug history:** F30 — the first vote comparison scored an empty class as zero; fixed by balancing halves by class and excluding absent classes.

> **Depth note:** The empty-class bug is instructive: a vote that imputes zero for an absent class *systematically penalizes* arms that legitimately don't predict that class. The fix is not cosmetic — it changes which arm wins.

