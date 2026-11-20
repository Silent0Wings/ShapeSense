# 4_testing - Deploy the public site: ONNX models with in-browser inference, Vercel hosting, interactive presentation
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-11
- Task: T86, commit ShapeSense_Deployed (separate repository) (type: built)
- Course stage: deployment (not a course stage)
- Worksheet entries: D02
- Source: ** from repo, not a saved chat.** Cited: `results/llm_comparison/commit_tasks.csv` (row T86), `results/llm_comparison/attribution_worksheet.csv` (D02), `results/llm_comparison/opus_task_responses.md` (T86 section).

## Prompt
>  prompt (no saved chat exists for this task; wording written for this file from the repo record).
> Task: T86 - Deploy the public site: ONNX models with in-browser inference, Vercel hosting, interactive presentation. Stage: deployment (not a course stage). Type: built. Say what Opus proposed or did, why, and what it changed, using only the recorded evidence.

## Response
 from the repo records above, not a saved reply:

D02: deploy the project online by exporting the five models to ONNX and running them in the visitor's browser through ONNX Runtime Web, with no server. Browser output was checked against Python (logits within 1e-4). The site is public at https://shapesense-ten.vercel.app since 2026-11-11, the presentation went live 2026-11-16 and the Predict button on 2026-11-17 (attribution_worksheet.csv D02). Credited to all members with Opus 5.5 and Gemini 4 Neon (commit_tasks.csv T86).

## Validation
Cross-checked against commit_tasks.csv row T86 and worksheet entry D02. The site was not re-audited for this file.

## Our decision
D02 kept as recorded.

## Measured effect
Logit agreement within 1e-4 between browser and Python (D02). No accuracy change is recorded.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T86`)

### Upgraded reading: deployment fidelity as a measurable claim

D02: five models exported to **ONNX**, run in the visitor's browser via **ONNX Runtime Web**, **no server**. Browser output checked against Python: **logits within 1e-4**. Public at `https://shapesense-ten.vercel.app` since 2026-11-11; presentation live 2026-11-16; Predict button 2026-11-17.
- **Logic:** the 1e-4 logit agreement is the *only* thing that licenses "the deployed model is the evaluated model." Without it, deployment is an unverified reimplementation. No accuracy change is recorded — correctly, because deployment doesn't change the model.

