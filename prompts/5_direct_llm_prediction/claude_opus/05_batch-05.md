# 5_direct_llm_prediction - Batch 05 (T081-T100)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T081`–`T100`)
- Peer model response: [05_batch-05.md](../gemini_4_neon/05_batch-05.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_05.png` (`T081`–`T100`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 05
T081,octagon
T082,diamond
T083,circle
T084,triangle
T085,triangle
T086,diamond
T087,circle
T088,octagon
T089,square
T090,diamond
T091,rectangle
T092,ellipse
T093,rectangle
T094,hexagon
T095,rectangle
T096,diamond
T097,triangle
T098,circle
T099,octagon
T100,circle
NOTES: T081 has roughly 7-8 vertices (octagon vs hexagon borderline); T091 is a skewed parallelogram (rectangle vs diamond borderline).
```

### De-anonymized batch scoring (20/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T081` | `mendeley_elkorchi_octagon_010661` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T082` | `kaggle_reevald_diamond_004351` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T083` | `quickdraw_circle_015139` | `quickdraw` | `circle` | `circle` | `circle` | Both right |
| `T084` | `kaggle_reevald_triangle_007303` | `kaggle_reevald` | `triangle` | `triangle` | `triangle` | Both right |
| `T085` | `mendeley_elkorchi_triangle_014248` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T086` | `kaggle_reevald_diamond_004282` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T087` | `mendeley_elkorchi_circle_008556` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T088` | `mendeley_elkorchi_octagon_010184` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T089` | `mendeley_elkorchi_square_012865` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T090` | `kaggle_reevald_diamond_004766` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T091` | `github_handdrawn_rectangle_001081` | `github_handdrawn` | `rectangle` | `rectangle` | `diamond` | LLM right, CNN miss |
| `T092` | `github_handdrawn_ellipse_000426` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T093` | `github_handdrawn_rectangle_001956` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T094` | `mendeley_elkorchi_hexagon_009263` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T095` | `github_handdrawn_rectangle_001780` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T096` | `kaggle_reevald_diamond_004290` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T097` | `kaggle_reevald_triangle_007635` | `kaggle_reevald` | `triangle` | `triangle` | `triangle` | Both right |
| `T098` | `mendeley_elkorchi_circle_008379` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T099` | `mendeley_elkorchi_octagon_010312` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T100` | `kaggle_reevald_circle_003139` | `kaggle_reevald` | `circle` | `circle` | `circle` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T081`–`T100`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 05: `20/20` (`100.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `19/20` (`95.0%`).
- Batch confusion pairs: none (20/20 exact match).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 05: `20/20` (`100.0%`) vs. trained CNN `A2_0` `19/20` (`95.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** the LLM scores 20/20 and A2_0 scores 19/20. A2_0's single miss, T091 (rectangle called diamond), is not a pair the LLM confuses. The LLM's NOTES flagged T091 as borderline and it still got the tile right.

**Changelog:** [1] the only batch where the LLM beats A2_0; [2] A2_0's miss is a github_handdrawn rectangle; [3] the NOTES flag on T091 was on a tile the LLM got right.

**Open questions:** Is A2_0's T091 error a source-level weakness on github_handdrawn rectangles or a one-off? A per-source error table would answer this; the batch file cannot. See batch 08 for the second github_handdrawn error.
