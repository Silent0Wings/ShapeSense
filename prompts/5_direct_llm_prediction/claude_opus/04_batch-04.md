# 5_direct_llm_prediction - Batch 04 (T061-T080)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T061`–`T080`)
- Peer model response: [04_batch-04.md](../gemini_4_neon/04_batch-04.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_04.png` (`T061`–`T080`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 04
T061,pentagon
T062,ellipse
T063,hexagon
T064,triangle
T065,rectangle
T066,triangle
T067,star
T068,hexagon
T069,octagon
T070,triangle
T071,pentagon
T072,hexagon
T073,rectangle
T074,star
T075,hexagon
T076,ellipse
T077,rectangle
T078,circle
T079,pentagon
T080,octagon
NOTES: T069 and T063 are thin open outlines (octagon vs hexagon uncertain); T072 is borderline hexagon vs pentagon.
```

### De-anonymized batch scoring (16/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T061` | `mendeley_elkorchi_pentagon_011953` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T062` | `github_handdrawn_ellipse_000847` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T063` | `quickdraw_octagon_016715` | `quickdraw` | `octagon` | `hexagon` | `hexagon` | Both miss |
| `T064` | `github_handdrawn_triangle_002007` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T065` | `github_handdrawn_rectangle_001464` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T066` | `quickdraw_triangle_018066` | `quickdraw` | `triangle` | `triangle` | `triangle` | Both right |
| `T067` | `mendeley_elkorchi_star_013740` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T068` | `mendeley_elkorchi_hexagon_009138` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T069` | `quickdraw_hexagon_016174` | `quickdraw` | `hexagon` | `octagon` | `octagon` | Both miss |
| `T070` | `github_handdrawn_triangle_002614` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T071` | `mendeley_elkorchi_pentagon_011777` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T072` | `mendeley_elkorchi_pentagon_011682` | `mendeley_elkorchi` | `pentagon` | `hexagon` | `pentagon` | CNN right, LLM miss |
| `T073` | `kaggle_reevald_rectangle_005420` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T074` | `mendeley_elkorchi_star_013509` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T075` | `mendeley_elkorchi_hexagon_009286` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T076` | `github_handdrawn_ellipse_000792` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T077` | `kaggle_reevald_rectangle_005745` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T078` | `mendeley_elkorchi_circle_008798` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T079` | `mendeley_elkorchi_pentagon_011981` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T080` | `quickdraw_hexagon_016151` | `quickdraw` | `hexagon` | `octagon` | `hexagon` | CNN right, LLM miss |

## Validation

- Parsed `20/20` unique blind IDs (`T061`–`T080`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 04: `16/20` (`80.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `18/20` (`90.0%`).
- Batch confusion pairs: `hexagon -> octagon` (2), `octagon -> hexagon` (1), `pentagon -> hexagon` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 04: `16/20` (`80.0%`) vs. trained CNN `A2_0` `18/20` (`90.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** this is the worst batch for both models (LLM 16/20, A2_0 18/20). Three of the LLM's four errors, T063, T069 and T072, were flagged in NOTES. The fourth, T080 (hexagon called octagon), was not flagged, and A2_0 gets it right.

**Changelog:** [1] worst batch for both models; [2] three of four LLM errors flagged; [3] T072 (pentagon called hexagon) is an LLM error A2_0 avoids.

**Open questions:** Are the quickdraw polygon labels (T063, T069) source labels or human readings? If source labels, both models' misses on these tiles may be label disagreement rather than model error.
