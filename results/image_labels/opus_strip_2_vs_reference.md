# Shape strip 2 - opus 5.5 labels checked against the reference strip (not a course LLM)
- LLM: opus 5.5 (claude-opus-5-5). Not Claude Opus 5.5 or Gemini 4 Neon, so this does not count toward the two-LLM comparison or the direct prediction run.
- Date: 2026-11-19
- Reference: names printed under each shape in images\2.png (original 2072x260). These are the true labels, not CNN predictions.
- CNN predictions for these 10 images: not available. The strip does not show them.

## Comparison
| # | opus label (from strip 1) | Reference label | Match |
|---|---|---|---|
| 1 | circle | circle | yes |
| 2 | ellipse | ellipse | yes |
| 3 | triangle | triangle | yes |
| 4 | rectangle | square | no |
| 5 | rectangle | rectangle | yes |
| 6 | pentagon | pentagon | yes |
| 7 | hexagon | hexagon | yes |
| 8 | octagon | octagon | yes |
| 9 | star | star | yes |
| 10 | diamond | diamond | yes |

Agreement: 9 of 10 (90%).

## Notes
- Shape 4 is the miss. opus read it as a rectangle (about 1.4 times wider than tall). The reference calls it a square. This was the shape flagged as least certain in the original reply.
- This is a single strip of 10 images, not a test set. It is not a macro F1 score.
- The comparison that counts for the course is the CNN against the same 200 test images (see prompts/5_direct_llm_prediction/PROMPT.md).
