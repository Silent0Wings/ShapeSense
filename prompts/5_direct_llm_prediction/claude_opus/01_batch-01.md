# 5_direct_llm_prediction - Batch 01 (T001-T020)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T001`–`T020`)
- Peer model response: [01_batch-01.md](../gemini_4_neon/01_batch-01.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_01.png` (`T001`–`T020`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 01
T001,pentagon
T002,circle
T003,star
T004,rectangle
T005,square
T006,octagon
T007,square
T008,star
T009,pentagon
T010,star
T011,rectangle
T012,rectangle
T013,star
T014,octagon
T015,octagon
T016,square
T017,octagon
T018,hexagon
T019,triangle
T020,octagon
NOTES: T006 is a wobbly closed shape (octagon vs circle borderline); T017 is a thin broken outline (octagon vs hexagon); T016 dashed is slightly wide (square vs rectangle).
```

### De-anonymized batch scoring (19/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T001` | `mendeley_elkorchi_pentagon_011543` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T002` | `mendeley_elkorchi_circle_008337` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T003` | `mendeley_elkorchi_star_013967` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T004` | `github_handdrawn_rectangle_001233` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T005` | `mendeley_elkorchi_square_012146` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T006` | `mendeley_elkorchi_octagon_010894` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T007` | `mendeley_elkorchi_square_012483` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T008` | `mendeley_elkorchi_star_013100` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T009` | `mendeley_elkorchi_pentagon_011297` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T010` | `mendeley_elkorchi_star_013568` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T011` | `kaggle_reevald_rectangle_005347` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T012` | `kaggle_reevald_rectangle_005807` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T013` | `mendeley_elkorchi_star_013629` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T014` | `mendeley_elkorchi_octagon_010188` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T015` | `mendeley_elkorchi_octagon_010119` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T016` | `kaggle_reevald_square_006324` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T017` | `quickdraw_hexagon_016024` | `quickdraw` | `hexagon` | `octagon` | `octagon` | Both miss |
| `T018` | `mendeley_elkorchi_hexagon_009106` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T019` | `github_handdrawn_triangle_002543` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T020` | `mendeley_elkorchi_octagon_010154` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T001`–`T020`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 01: `19/20` (`95.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `19/20` (`95.0%`).
- Batch confusion pairs: `hexagon -> octagon` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 01: `19/20` (`95.0%`) vs. trained CNN `A2_0` `19/20` (`95.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** the one miss, T017, is shared. The LLM and A2_0 both predict octagon for a true hexagon, so the difficulty sits in the tile as well as the model.

**Changelog:** [1] T017 is a both-miss; [2] NOTES flags on T006 and T016 were on tiles the LLM got right; [3] raw predictions kept as the record.

**Open questions:** Is the 50-example reference grid the same in all ten batches? If so, the few-shot context is fixed and batch variance comes from the tiles. Does the 200/200 pixel check cover the reference grid, or only the 200 batch tiles?
