# 5_direct_llm_prediction - Grading Gemini's blind predictions for batch 04
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/04_batch-04.md](../gemini_4_neon/04_batch-04.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon blind predictions for batch 04 (T061 to T080), as Claude Opus 5.5.

The exchange being judged: Gemini classified 20 shuffled 64x64 tiles against a 50-image reference grid and wrote short notes on the ambiguous ones. Batch 04 is Gemini's weakest batch.

## Response

### Grade: B (71 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 21 / 25 | 17 of 20 correct (85%), against 18 of 20 for the trained CNN `A2_0` on the same tiles. All three errors are hexagon and octagon confusions: T063 (octagon called hexagon), T069 and T080 (hexagons called octagon). |
| Read the question correctly | 19 / 20 | It answered in the exact `blind_id,label` format with a short NOTES line, as asked. |
| Fit to this project | 13 / 20 | The prompt told it to count polygon vertices carefully, and its three errors are vertex-count errors on open, thin QuickDraw outlines. |
| Actionable advice | 10 / 20 | The NOTES should flag uncertain tiles. They flagged T063, T069 and T080, but as confident explanations of the wrong answer, so they would not warn a reader. The flags on T073 and T077 were on correct tiles. |
| Accuracy of details | 8 / 15 | The notes describe T069 and T080 as 8-sided and T063 as a 6-sided hexagon. The true labels are the reverse for T063 and T069, and T080 is a hexagon. |

### What it got right
- 17 of 20, and better than Claude Opus 5.5 on this batch, which scored 16 of 20 and also missed T072 (`prompts/5_direct_llm_prediction/claude_opus/04_batch-04.md`).
- Correct on every non-polygon tile and on T072, the pentagon Claude called a hexagon.

### What it got wrong or missed
- Three hexagon and octagon errors, all on QuickDraw tiles. The trained CNN also missed T063 and T069, so those two tiles are hard for both, but the CNN got T080 right.
- Its notes stated vertex counts with confidence and were wrong, which makes them misleading as an uncertainty signal.

### What I would have answered for this project
The same labels where the shapes are clear, and "unsure" notes on the open QuickDraw outlines instead of confident counts. On open strokes the honest note is that the vertex count cannot be read reliably at 64x64. That would not change the score, but it would make the notes a useful warning.

## Validation

- Checked against the batch table in the Gemini file (true labels, Gemini labels and `A2_0` labels for all 20 tiles) and the Claude batch 04 file.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the raw predictions unedited, as recorded. Note in the comparison that hexagon and octagon on open QuickDraw outlines are the hardest tiles for both LLMs.

## Measured effect

None. The batch score stays 17 of 20.
