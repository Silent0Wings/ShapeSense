# 5_direct_llm_prediction - Batch 10 (T181-T200)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T181`–`T200`)
- Peer model response: [10_batch-10.md](../gemini_4_neon/10_batch-10.md)

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
NOTES: T187 is an irregular wobbly quad (diamond vs hexagon), T191 is an open partial polygon (hexagon vs octagon), and T188 is skewed (square vs rectangle).
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

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 10: `20/20` (`100.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** both models are perfect here, the second control. All three NOTES flags, T187, T191 and T188, were on correct tiles, so the flags were false alarms in this batch.

**Changelog:** [1] second both-perfect control; [2] three flagged tiles, all correct.

### Corrections to the cross-batch analysis

The cross-batch synthesis pasted for this folder has counts the ten batch tables do not support. The figures below come from the 200 rows in those tables.

| Measure | Pasted | From the batch tables |
|---|---|---|
| Claude Opus 5.5 correct | 185/200 (92.5%) | 185/200 (92.5%) |
| A2_0 correct | 194/200 (97.0%) | 195/200 (97.5%) |
| A2_0 perfect batches | 5 (01, 03, 07, 09, 10) | 6 (02, 03, 06, 07, 09, 10) |
| Accuracy gap | 4.5 points | 5.0 points |
| LLM errors | 19 | 15 |
| A2_0 errors | 6 | 5 |
| Circle/ellipse LLM errors | 6 | 5 |

LLM errors by true to predicted label: hexagon to octagon 4 (T017, T039, T069, T080); octagon to hexagon 1 (T063); pentagon to hexagon 1 (T072); circle to ellipse 4 (T055, T103, T142, T175); ellipse to circle 1 (T162); rectangle to ellipse 1 (T111); ellipse to hexagon 1 (T117); diamond to square 1 (T178); square to rectangle 1 (T031).

Claims that do not hold:
- "A2_0's errors are 0% adjacent-pair." Three of A2_0's five errors are hexagon/octagon confusions (T017, T063, T069). The other two are T091 (rectangle called diamond) and T154 (ellipse called triangle).
- "Shared errors: 4." The shared errors are three: T017, T063 and T069. For T080, A2_0 is correct.
- "The LLM's errors are 95% adjacent-pair." Of the 15 LLM errors, 12 fall in the four pairs hexagon/octagon, circle/ellipse, square/rectangle and diamond/square. The other three are T072, T111 and T117.
- NOTES: 30 tiles are flagged across the ten batches. 11 of the 15 LLM errors were flagged (73% recall), and 19 of the 30 flags were on tiles the LLM got right (37% precision). The flags catch most errors but are mostly false alarms, so they cannot filter predictions as they stand. They are still not a calibrated confidence score.

Source pattern, by count from the batch tables: quickdraw tiles are 27 of 200 (13.5%) but 6 of the 15 LLM errors and 3 of A2_0's five errors (T017, T063, T069). The two non-adjacent A2_0 errors, T091 and T154, are both github_handdrawn.

**Open questions:** Are the quickdraw polygon labels source labels or human readings? The quickdraw polygons are where both models are weakest, so label quality decides how much of the gap is real. Is A2_0's github_handdrawn error rate higher than on other sources? A per-tile model margin would also show whether batch-level differences come from tile difficulty.
