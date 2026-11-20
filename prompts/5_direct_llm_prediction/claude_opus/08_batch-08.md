# 5_direct_llm_prediction - Batch 08 (T141-T160)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T141`–`T160`)
- Peer model response: [08_batch-08.md](../gemini_4_neon/08_batch-08.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_08.png` (`T141`–`T160`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 08
T141,rectangle
T142,ellipse
T143,star
T144,square
T145,octagon
T146,pentagon
T147,diamond
T148,octagon
T149,hexagon
T150,square
T151,octagon
T152,ellipse
T153,diamond
T154,ellipse
T155,octagon
T156,hexagon
T157,square
T158,triangle
T159,rectangle
T160,square
NOTES: T153 (dashed, near-equal axes) is square/diamond borderline; T145 and T155 are thin irregular polygons (octagon vs hexagon), and T142 is circle/ellipse borderline.
```

### De-anonymized batch scoring (19/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T141` | `github_handdrawn_rectangle_001193` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T142` | `kaggle_reevald_circle_003882` | `kaggle_reevald` | `circle` | `ellipse` | `circle` | CNN right, LLM miss |
| `T143` | `mendeley_elkorchi_star_013943` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T144` | `mendeley_elkorchi_square_012833` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T145` | `quickdraw_octagon_016509` | `quickdraw` | `octagon` | `octagon` | `octagon` | Both right |
| `T146` | `mendeley_elkorchi_pentagon_011197` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T147` | `kaggle_reevald_diamond_004664` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T148` | `mendeley_elkorchi_octagon_010096` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T149` | `mendeley_elkorchi_hexagon_009074` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T150` | `kaggle_reevald_square_006682` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T151` | `quickdraw_octagon_016711` | `quickdraw` | `octagon` | `octagon` | `octagon` | Both right |
| `T152` | `github_handdrawn_ellipse_000625` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T153` | `kaggle_reevald_diamond_004220` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T154` | `github_handdrawn_ellipse_000585` | `github_handdrawn` | `ellipse` | `ellipse` | `triangle` | LLM right, CNN miss |
| `T155` | `quickdraw_octagon_016891` | `quickdraw` | `octagon` | `octagon` | `octagon` | Both right |
| `T156` | `mendeley_elkorchi_hexagon_009969` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T157` | `quickdraw_square_017409` | `quickdraw` | `square` | `square` | `square` | Both right |
| `T158` | `mendeley_elkorchi_triangle_014205` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T159` | `github_handdrawn_rectangle_001257` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T160` | `kaggle_reevald_square_006418` | `kaggle_reevald` | `square` | `square` | `square` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T141`–`T160`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 08: `19/20` (`95.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `19/20` (`95.0%`).
- Batch confusion pairs: `circle -> ellipse` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 08: `19/20` (`95.0%`) vs. trained CNN `A2_0` `19/20` (`95.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** the two models miss different tiles. The LLM misses T142 (circle called ellipse), which its NOTES flagged as borderline. A2_0 misses T154 (ellipse called triangle), a pair neither model otherwise confuses, and the NOTES did not flag it. The LLM gets T154 right.

**Changelog:** [1] complementary misses; [2] T142 flagged and wrong; [3] T154 unflagged and LLM-correct.

**Open questions:** T154 and T091 (batch 05) are both github_handdrawn tiles, the only two non-adjacent A2_0 errors in the benchmark. Is A2_0's error rate on github_handdrawn higher than on other sources? That needs a per-source count across all 200 tiles, which this file cannot give.
