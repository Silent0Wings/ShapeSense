# 5_direct_llm_prediction - Batch 05 (T081-T100)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T081`–`T100`)
- Peer model response: [05_batch-05.md](../claude_opus/05_batch-05.md)

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
T091,diamond
T092,ellipse
T093,rectangle
T094,hexagon
T095,rectangle
T096,diamond
T097,triangle
T098,circle
T099,octagon
T100,circle
NOTES: T083 is slightly wider than tall (borderline circle/ellipse, closer to circle) and T092 is a messy hand-drawn ellipse with a long overshoot loop at top-right.
```

### De-anonymized batch scoring (19/20 correct)

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
| `T091` | `github_handdrawn_rectangle_001081` | `github_handdrawn` | `rectangle` | `diamond` | `diamond` | Both miss |
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
- Blind direct vision accuracy on Batch 05: `19/20` (`95.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `19/20` (`95.0%`).
- Batch confusion pairs: `rectangle -> diamond` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 05: `19/20` (`95.0%`) vs. trained CNN `A2_0` `19/20` (`95.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** Gemini misses T091 (rectangle called diamond), the same miss as A2_0. Opus gets T091 right. The two models' NOTES share no tile in this batch: Gemini flags T083 and T092, both correct, and Opus flags T081 and T091. T091 is an error for Gemini and unflagged, so the flags do not predict it.

**Changelog:** [1] T091 is missed by Gemini and A2_0 and correct for Opus; [2] the NOTES share no tile; [3] the unflagged T091 error shows flags do not predict errors.

**Open questions:** Two models flagging different tiles suggests they read "ambiguous tiles" differently. Is the NOTES instruction read as the model's own uncertainty, or as objective ambiguity?
