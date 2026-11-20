# 5_direct_llm_prediction - Batch 09 (T161-T180)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T161`–`T180`)
- Peer model response: [09_batch-09.md](../gemini_4_neon/09_batch-09.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_09.png` (`T161`–`T180`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 09
T161,hexagon
T162,circle
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
T176,square
T177,star
T178,square
T179,diamond
T180,pentagon
NOTES: T173 is a tapered wedge (triangle vs rectangle), T176 could be rectangle, and T178 is a dashed rounded quadrilateral (square vs diamond); T162 is slightly wide (circle vs ellipse).
```

### De-anonymized batch scoring (17/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T161` | `mendeley_elkorchi_hexagon_009417` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T162` | `github_handdrawn_ellipse_000979` | `github_handdrawn` | `ellipse` | `circle` | `ellipse` | CNN right, LLM miss |
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
| `T176` | `quickdraw_square_017022` | `quickdraw` | `square` | `square` | `square` | Both right |
| `T177` | `mendeley_elkorchi_star_013308` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T178` | `kaggle_reevald_diamond_004285` | `kaggle_reevald` | `diamond` | `square` | `diamond` | CNN right, LLM miss |
| `T179` | `kaggle_reevald_diamond_004568` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T180` | `mendeley_elkorchi_pentagon_011337` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T161`–`T180`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 09: `17/20` (`85.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `ellipse -> circle` (1), `circle -> ellipse` (1), `diamond -> square` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 09: `17/20` (`85.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** three LLM misses: T162 (ellipse called circle), T175 (circle called ellipse), T178 (diamond called square). A2_0 is perfect. T178 is the only diamond-to-square error in the benchmark. The prompt states the convention that a 45-degree square counts as a square and a diamond needs non-90-degree corners, so T178 is a convention error, not a geometry error. The NOTES flagged T162 and T178, both errors, and T173 and T176, both correct.

**Changelog:** [1] T178 is a convention error given the prompt's own rule; [2] T162 and T175 show circle/ellipse errors in both directions; [3] two of four flags were errors and two were correct.

**Open questions:** Does the few-shot reference show the square/diamond convention as clearly as the prompt states it? If not, T178 points to a prompt-design issue rather than a model failure.
