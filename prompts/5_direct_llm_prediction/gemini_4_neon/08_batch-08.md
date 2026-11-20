# 5_direct_llm_prediction - Batch 08 (T141-T160)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T141`–`T160`)
- Peer model response: [08_batch-08.md](../claude_opus/08_batch-08.md)

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
NOTES: T142 is a dashed vertically elongated oval borderline between ellipse and circle; T151 and T155 are messy hand-drawn thin-line octagons, and T157 is a slightly sheared thin-line square.
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

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 08: `19/20` (`95.0%`) vs. trained CNN `A2_0` `19/20` (`95.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** Gemini misses T142 (circle called ellipse), the fourth circle-to-ellipse miss by both VLMs on a kaggle_reevald circle (T055, T103, T142, T175), where A2_0 is right on all four. Here Gemini's NOTES flag T142 as borderline and it is an error, so a flag predicts the error on this tile. Gemini gets T154 right, where A2_0 calls it triangle.

**Changelog:** [1] T142 is the fourth shared kaggle circle miss; [2] a flag on an error; [3] T154 is Gemini-right and A2_0-wrong.

**Open questions:** Is the kaggle_reevald circle convention different from the mendeley_elkorchi circle convention? That is a hypothesis to test with per-source counts, not something this batch establishes. One flag on an error is not a rate.
