# Shape grid 3 - opus 5.5 labels checked against the row names of grid 4 (not a course LLM)
- LLM: opus 5.5 (claude-opus-5-5). Not Claude Opus 5.5 or Gemini 4 Neon, so this does not count toward the two-LLM comparison or the direct prediction run.
- Date: 2026-11-19
- opus labels: read from images\3.png (5 rows x 6 columns, 30 images), by row.
- Reference: row names in images\4.png. The user described these as CNN predictions. The strip itself does not mark them as predictions, so they are recorded as "row names", not verified CNN output.

## Comparison
| Row | opus label (grid 3) | Row name (grid 4) | Matches |
|---|---|---|---|
| 1 | circle | circle | 6 of 6 |
| 2 | ellipse | ellipse | 6 of 6 |
| 3 | square | square | 6 of 6 |
| 4 | rectangle | rectangle | 6 of 6 |
| 5 | diamond | diamond | 6 of 6 |

Agreement: 30 of 30 (100%) on the rows that could be matched.

## Notes
- The row-to-image match assumes that grid 4 uses the same images in the same row order as grid 3. This was judged by eye, not by pixel comparison.
- Least certain in grid 3: row 1 (circle vs. ellipse, since some are slightly oval), and row 4, columns 5 and 6 (rectangle vs. parallelogram).
- This is a single grid of 30 images, not a test set. It is not a macro F1 score.
- The comparison that counts for the course is the CNN against the same 200 test images (see prompts/5_direct_llm_prediction/PROMPT.md).
