# 5_direct_llm_prediction - Batch 07 (T121-T140)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T121`–`T140`)
- Peer model response: [07_batch-07.md](../gemini_4_neon/07_batch-07.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_07.png` (`T121`–`T140`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 07
T121,triangle
T122,ellipse
T123,circle
T124,ellipse
T125,square
T126,ellipse
T127,pentagon
T128,hexagon
T129,triangle
T130,triangle
T131,octagon
T132,star
T133,ellipse
T134,circle
T135,pentagon
T136,octagon
T137,circle
T138,diamond
T139,rectangle
T140,square
NOTES: T124 (mildly tall oval) is circle/ellipse borderline; T136 could be read as a heptagon/hexagon but was labeled octagon.
```

### De-anonymized batch scoring (20/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T121` | `mendeley_elkorchi_triangle_014167` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T122` | `github_handdrawn_ellipse_000304` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T123` | `mendeley_elkorchi_circle_008191` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T124` | `github_handdrawn_ellipse_000904` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T125` | `mendeley_elkorchi_square_012310` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T126` | `github_handdrawn_ellipse_000660` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T127` | `mendeley_elkorchi_pentagon_011426` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T128` | `quickdraw_hexagon_016034` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T129` | `quickdraw_triangle_018045` | `quickdraw` | `triangle` | `triangle` | `triangle` | Both right |
| `T130` | `mendeley_elkorchi_triangle_014543` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T131` | `mendeley_elkorchi_octagon_010059` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T132` | `mendeley_elkorchi_star_013682` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T133` | `github_handdrawn_ellipse_000218` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T134` | `quickdraw_circle_015369` | `quickdraw` | `circle` | `circle` | `circle` | Both right |
| `T135` | `mendeley_elkorchi_pentagon_011761` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T136` | `mendeley_elkorchi_octagon_010608` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T137` | `mendeley_elkorchi_circle_008692` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T138` | `kaggle_reevald_diamond_004708` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T139` | `github_handdrawn_rectangle_001639` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T140` | `kaggle_reevald_square_006621` | `kaggle_reevald` | `square` | `square` | `square` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T121`–`T140`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 07: `20/20` (`100.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: none (20/20 exact match).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 07: `20/20` (`100.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** both models are perfect, so this batch is a control. The two flagged tiles, T124 and T136, were both correct, so here the NOTES over-flagged.

**Changelog:** [1] both-perfect control; [2] NOTES flags on two correct tiles.

**Open questions:** A per-tile model margin would show whether this batch's tiles are easier than the others. The batch file has no such measure.
