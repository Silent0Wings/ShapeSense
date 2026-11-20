# 5_direct_llm_prediction - Batch 09 (T161-T180)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T161`–`T180`)
- Peer model response: [09_batch-09.md](../claude_opus/09_batch-09.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_09.png` (`T161`–`T180`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 09
T161,hexagon
T162,ellipse
T163,triangle
T164,pentagon
T165,triangle
T166,star
T167,rectangle
T168,diamond
T169,square
T170,circle
T171,ellipse
T172,triangle
T173,triangle
T174,triangle
T175,ellipse
T176,rectangle
T177,star
T178,diamond
T179,diamond
T180,pentagon
NOTES: T173 is a flat right-triangle wedge with a slightly blunted right tip, and T176 is a slightly wide thin-line rectangle (~1.3:1 aspect ratio) that is mildly borderline with square. T162 is moderately elongated (~1.25:1) and classified as ellipse rather than circle.
```

### De-anonymized batch scoring (18/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T161` | `mendeley_elkorchi_hexagon_009417` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T162` | `github_handdrawn_ellipse_000979` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T163` | `quickdraw_triangle_018387` | `quickdraw` | `triangle` | `triangle` | `triangle` | Both right |
| `T164` | `mendeley_elkorchi_pentagon_011717` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T165` | `kaggle_reevald_triangle_007588` | `kaggle_reevald` | `triangle` | `triangle` | `triangle` | Both right |
| `T166` | `mendeley_elkorchi_star_013086` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T167` | `github_handdrawn_rectangle_001820` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T168` | `kaggle_reevald_diamond_004413` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T169` | `kaggle_reevald_square_006992` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T170` | `mendeley_elkorchi_circle_008671` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T171` | `github_handdrawn_ellipse_000853` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T172` | `quickdraw_triangle_018152` | `quickdraw` | `triangle` | `triangle` | `triangle` | Both right |
| `T173` | `github_handdrawn_triangle_002409` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T174` | `github_handdrawn_triangle_002710` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T175` | `kaggle_reevald_circle_003963` | `kaggle_reevald` | `circle` | `ellipse` | `circle` | CNN right, LLM miss |
| `T176` | `quickdraw_square_017022` | `quickdraw` | `square` | `rectangle` | `square` | CNN right, LLM miss |
| `T177` | `mendeley_elkorchi_star_013308` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T178` | `kaggle_reevald_diamond_004285` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T179` | `kaggle_reevald_diamond_004568` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T180` | `mendeley_elkorchi_pentagon_011337` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T161`–`T180`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 09: `18/20` (`90.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `circle -> ellipse` (1), `square -> rectangle` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 09: `18/20` (`90.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** Gemini misses T175 (circle called ellipse, shared with Opus) and T176 (square called rectangle). Opus gets T176 right. Gemini is correct on T162 and T178, which Opus misses. Gemini's NOTES give a 1.3:1 aspect ratio for T176, a threshold the prompt does not define for the square/rectangle boundary.

**Changelog:** [1] T176 is Gemini's only square/rectangle error and is Opus-right; [2] T162 and T178 are Gemini-right and Opus-wrong; [3] the 1.3:1 threshold is self-stated, not checked against the examples.

**Open questions:** Do the reference examples imply a square/rectangle aspect-ratio threshold? If the five squares are near 1:1 and the five rectangles near 2:1, the boundary is about 1.5:1, and 1.3:1 would be a misapplication.
