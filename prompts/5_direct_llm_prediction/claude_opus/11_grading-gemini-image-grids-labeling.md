# 5_direct_llm_prediction - Grading Gemini's labels for the five shape grids
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/01_image-grids-labeling.md](../gemini_4_neon/01_image-grids-labeling.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon answer that labelled the five Studio shape grids, as Claude Opus 5.5.

The exchange being judged: the user attached five grid images (`3.png`, `1.png`, `5.png`, `7.png`, `9.png`, 180 tiles in all), asked Gemini to label them and store the labels, and said the CNN scored 100% on them. Gemini labelled every tile by row or column, flagged a few borderline tiles, and scored 180 of 180 against the paired reference images.

## Response

### Grade: B (82 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 23 / 25 | Every label matches the reference images (180 of 180, as recorded in the file's validation). The borderline notes are honest, for example the `1.png` column 4 tile that is about 1.25 to 1 and could read as a rectangle. |
| Read the question correctly | 16 / 20 | It labelled all five grids in the order given. It labelled by row or column rather than tile by tile, which is efficient but means the grouping did part of the work. |
| Fit to this project | 15 / 20 | The grids are grouped by class, so the layout gives the label away. The record rightly keeps this out of the 200-image benchmark. The user's message also included the CNN's 100% score, which the project's own protocol says must not be shown to the LLM before it answers. |
| Actionable advice | 15 / 20 | The output is a usable label list, but it adds little beyond confirming the reference strips. It cannot measure anything the blind benchmark does not already measure. |
| Accuracy of details | 13 / 15 | Shape descriptions (rotated squares at about 45 degrees with right angles, concave-sided triangles, notched rectangles) are careful and specific. The CNN score is correctly recorded as user-reported and unverified. |

### What it got right
- All 180 labels match the references.
- It flagged its least certain tile instead of hiding it.
- It treated the CNN's 100% as a claim it could not check from the images.

### What it got wrong or missed
- **Weak test design, not Gemini's fault:** grouped grids leak the answer. A row of six identical circles needs one decision, not six.
- **Protocol:** the prompt carried the CNN's score. Gemini did not use it, but the record should not count as a clean direct-prediction run.
- **Storage:** the prompt asked for the labels to be stored in a file. The response lists them; whether a file was written is not shown in this record.

### What I would have answered for this project
Label the tiles, then say plainly that grouped grids cannot measure direct prediction, because the layout gives the label away. Point to the blind, shuffled 200-tile benchmark in `results/direct_llm_prediction/` as the real comparison. That benchmark scored Gemini 93.97 macro F1 against 97.50 for the CNN (`prompts/5_direct_llm_prediction/gemini_4_neon/01_batch-01.md`, Measured effect).

## Validation

- Checked against the Gemini file (180 of 180 against the paired references, CNN score recorded as unverified) and the benchmark figures in `01_batch-01.md`.
- I did not open the grid images or `results/image_labels/`, so the per-tile labels were not re-checked by me.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the record as exploratory only, as it already says. It does not count toward the direct-prediction requirement.

## Measured effect

None. No change was made.
