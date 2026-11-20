# 4_testing - chore(iteration-2): close the iteration and restore frozen winners in a clean clone
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Task: T43, commit 3a5a3b3 (type: solved)
- Course stage: deployment (not a course stage)
- Worksheet entries: F16
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T43), `results/llm_comparison/attribution_worksheet.csv` (F16), `results/llm_comparison/opus_task_responses.md` (T43 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T43 - chore(iteration-2): close the iteration and restore frozen winners in a clean clone. Stage: deployment (not a course stage). Type: solved. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

F16: a clean clone could not find the tuning result. run_pipeline.py now restores the committed copy when it is absent, and the rehearsal reproduced every result (attribution_worksheet.csv F16). Opus proposed the change (commit_tasks.csv T43, llm_role: proposed).

## Validation
Cross-checked against commit_tasks.csv row T43 and worksheet entry F16.

## Our decision
F16 kept as recorded: the committed copy is restored when absent.

## Measured effect
The rehearsal reproduced every result (F16). No numeric change is recorded.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T43`)

### What the record says (and nothing more)

F16: a clean clone could not find the tuning result. `run_pipeline.py` now restores the committed copy when absent; the rehearsal reproduced every result. Opus *proposed* the change (`commit_tasks.csv` T43, `llm_role: proposed`).

### Upgraded reading: the reproducibility logic

A "clean clone cannot find the tuning result" is a **deterministic-reproducibility defect**, not a cosmetic bug. The chain:
1. A frozen winner is an *evidence artifact* — the only defensible basis for a verdict.
2. If a fresh clone can't reconstruct it, the verdict is **not independently reproducible**, which is a validity threat to every downstream claim.
3. Fix: treat the committed copy as the *source of truth* and restore it when absent — i.e., make the pipeline **idempotent and self-healing** rather than dependent on local state.
4. Validation: the rehearsal reproduced *every* result → the restore path is verified, not assumed.

> **Depth note:** This is the kind of fix that is invisible in accuracy numbers but load-bearing for trust. It belongs in the record precisely because "it worked on my machine" is the failure it prevents.

