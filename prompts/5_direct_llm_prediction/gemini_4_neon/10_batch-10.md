# 5_direct_llm_prediction - Batch 10 (T181-T200)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T181`–`T200`)
- Peer model response: [10_batch-10.md](../claude_opus/10_batch-10.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_10.png` (`T181`–`T200`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 10
T181,ellipse
T182,pentagon
T183,star
T184,square
T185,square
T186,circle
T187,diamond
T188,square
T189,pentagon
T190,hexagon
T191,hexagon
T192,square
T193,hexagon
T194,triangle
T195,diamond
T196,ellipse
T197,star
T198,diamond
T199,ellipse
T200,rectangle
NOTES: T191 is a partial/open thin-line hexagon matching the open hexagon training example, and T188 is a thin-line ~1:1 square with a slightly slanted right edge. T184 uses a thick radial-stroke brush forming an equal-sided square.
```

### De-anonymized batch scoring (20/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T181` | `github_handdrawn_ellipse_000954` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T182` | `mendeley_elkorchi_pentagon_011127` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T183` | `mendeley_elkorchi_star_013068` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T184` | `kaggle_reevald_square_006825` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T185` | `mendeley_elkorchi_square_012961` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T186` | `mendeley_elkorchi_circle_008034` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T187` | `kaggle_reevald_diamond_004478` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T188` | `quickdraw_square_017007` | `quickdraw` | `square` | `square` | `square` | Both right |
| `T189` | `mendeley_elkorchi_pentagon_011032` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T190` | `quickdraw_hexagon_016406` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T191` | `quickdraw_hexagon_016335` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T192` | `kaggle_reevald_square_006979` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T193` | `mendeley_elkorchi_hexagon_009193` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T194` | `mendeley_elkorchi_triangle_014044` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T195` | `kaggle_reevald_diamond_004593` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T196` | `github_handdrawn_ellipse_000597` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T197` | `mendeley_elkorchi_star_013461` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T198` | `kaggle_reevald_diamond_004981` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T199` | `github_handdrawn_ellipse_000800` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T200` | `kaggle_reevald_rectangle_005743` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T181`–`T200`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 10: `20/20` (`100.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: none (20/20 exact match).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 10: `20/20` (`100.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** Gemini's second perfect batch, a control. T191 is a quickdraw hexagon that Gemini gets right with a reference-matching note ("matching the open hexagon training example"). Its description is close to the open-polygon tiles Gemini misses in other batches (T017, T039), so the note does not separate the right answer from the wrong ones.

**Changelog:** [1] control batch; [2] the reference-matching note recurs from batch 03; [3] T191 and T017 share a description and have different outcomes.

### Corrections to the cross-batch analysis

The cross-batch analysis pasted for this folder has counts the batch tables do not support. The figures below come from the 200 rows in the ten Gemini batch tables.

| Measure | Pasted | From the batch tables |
|---|---|---|
| Gemini correct | 188/200 (94.0%) | 188/200 (94.0%) |
| A2_0 correct | 194/200 (97.0%) | 195/200 (97.5%) |
| Gemini perfect batches | 3 | 2 (07, 10) |
| Gemini errors | 12 | 12 |
| Opus errors | 15 | 15 |
| Gemini errors in the two pairs (circle/ellipse plus hexagon/octagon) | 8 | 10 (5 + 5) |
| Opus errors in the two pairs | not stated | 10 (5 + 5) |
| Gemini singleton errors | 4 | 2 (T091, T176) |
| Opus singleton errors | 7 | 5 (T031, T072, T111, T117, T178) |

Gemini's errors in the pairs are T055, T103, T117, T142 and T175 (circle/ellipse), and T017, T039, T063, T069 and T080 (hexagon/octagon). Opus has the same five in each pair except T117 (an ellipse called hexagon) and T162 (an ellipse called circle), so the pair counts are equal.

The gap is in the singletons. Gemini is right where Opus is wrong on five tiles: T031, T072, T111, T162 and T178. Opus is right where Gemini is wrong on two: T091 and T176. The net of three tiles is exactly the 188 vs 185 difference. The pasted account, that the gap is in polygon vertex counting, is wrong: hexagon/octagon errors are equal for the two models.

Claims that do not hold:
- "Opus has a small advantage on github_handdrawn rectangles, Gemini has a one-tile loss there." Opus is right on T091 and also on T176, a quickdraw square, so the advantage is not limited to hand-drawn rectangles.
- "Net advantage of 2 to 1 on batch 04." On batch 04 Gemini is right on T072 and Opus is wrong, but the full benchmark net is the three-tile figure above.
- "Gemini's per-batch range 17 to 20 means it is more stable" is weakly supported. The range is one tile narrower than Opus's, which is not enough on ten batches to call one model more stable.
- "Both VLMs miss two tiles in batch 06." Opus misses three there (T103, T111, T117) and Gemini two (T103, T117).

Source pattern, by count from the batch tables: the circle/ellipse misses on kaggle_reevald (T055, T103, T142, T175) are shared by both VLMs and A2_0 is right on all four.

**Open questions:** Are the quickdraw polygon labels source labels or human readings? Both VLMs miss the open-polygon quickdraw tiles, so label quality decides how much of the hexagon/octagon error is real. Are the NOTES written before or after the label? The benchmark needs that timing to read the NOTES as evidence.
