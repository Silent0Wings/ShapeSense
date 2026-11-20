# 4_testing - Live prediction: predict on demand, with a drawing toolbar above the canvas

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-17
- Task: T90, commit deployed: 24f7170 (type: built)
- Course stage: deployment (not a course stage) (filed here: deployment and support work goes under 4_testing)
- Worksheet entries: none
- Source: **, not a live chat.** Split from [opus_task_responses.md](../../../results/llm_comparison/opus_task_responses.md). The response is written from the commit and worksheet records.

## Prompt

> Here is a task from our commit log that credits you. Task: T90 - Live prediction: predict on demand, with a drawing toolbar above the canvas. Claim: all members with Opus 5.5 and Gemini 4 Neon. Using only the recorded evidence, say what you proposed or did, why, and what it changed.

## Response

Adds on-demand prediction in the browser, which relies on the ONNX export in D02. Interface plus inference, no new model.

## Validation

Checked against commit deployed: 24f7170 and the linked worksheet entries in [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv).

## Our decision

Kept as committed. No worksheet entry is linked to this task.

## Measured effect

No separate measurement recorded for this task.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`T90`)

### Upgraded reading

On-demand in-browser prediction, relying on the D02 ONNX export. **Interface plus inference, no new model** — so no accuracy claim is possible or made. Correctly scoped.

