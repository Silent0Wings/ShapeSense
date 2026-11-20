# 5_direct_llm_prediction - Batch 06 (T101-T120)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T101`–`T120`)
- Peer model response: [06_batch-06.md](../gemini_4_neon/06_batch-06.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_06.png` (`T101`–`T120`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 06
T101,diamond
T102,star
T103,ellipse
T104,diamond
T105,pentagon
T106,triangle
T107,ellipse
T108,triangle
T109,star
T110,circle
T111,ellipse
T112,star
T113,ellipse
T114,hexagon
T115,hexagon
T116,star
T117,hexagon
T118,pentagon
T119,triangle
T120,pentagon
NOTES: T111 is a rounded rectangle (ellipse vs rectangle borderline); T117 is an irregular rounded blob (hexagon vs circle/octagon borderline).
```

### De-anonymized batch scoring (17/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T101` | `kaggle_reevald_diamond_004036` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T102` | `mendeley_elkorchi_star_013389` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T103` | `kaggle_reevald_circle_003718` | `kaggle_reevald` | `circle` | `ellipse` | `circle` | CNN right, LLM miss |
| `T104` | `kaggle_reevald_diamond_004273` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T105` | `mendeley_elkorchi_pentagon_011593` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T106` | `kaggle_reevald_triangle_007521` | `kaggle_reevald` | `triangle` | `triangle` | `triangle` | Both right |
| `T107` | `github_handdrawn_ellipse_000946` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T108` | `mendeley_elkorchi_triangle_014814` | `mendeley_elkorchi` | `triangle` | `triangle` | `triangle` | Both right |
| `T109` | `mendeley_elkorchi_star_013129` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T110` | `kaggle_reevald_circle_003302` | `kaggle_reevald` | `circle` | `circle` | `circle` | Both right |
| `T111` | `github_handdrawn_rectangle_001517` | `github_handdrawn` | `rectangle` | `ellipse` | `rectangle` | CNN right, LLM miss |
| `T112` | `mendeley_elkorchi_star_013905` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T113` | `github_handdrawn_ellipse_000184` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T114` | `mendeley_elkorchi_hexagon_009916` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T115` | `quickdraw_hexagon_016086` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T116` | `quickdraw_star_017560` | `quickdraw` | `star` | `star` | `star` | Both right |
| `T117` | `github_handdrawn_ellipse_000020` | `github_handdrawn` | `ellipse` | `hexagon` | `ellipse` | CNN right, LLM miss |
| `T118` | `mendeley_elkorchi_pentagon_011430` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T119` | `github_handdrawn_triangle_002955` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T120` | `mendeley_elkorchi_pentagon_011546` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T101`–`T120`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 06: `17/20` (`85.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `circle -> ellipse` (1), `rectangle -> ellipse` (1), `ellipse -> hexagon` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 06: `17/20` (`85.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** three different LLM confusions in one batch: circle called ellipse (T103), rectangle called ellipse (T111), ellipse called hexagon (T117). A2_0 is perfect. T117 is an LLM error outside the hexagon/octagon family, and its NOTES listed hexagon, circle and octagon, none of which was the true label.

**Changelog:** [1] three confusion pairs in one batch; [2] T117 is an error outside the hexagon/octagon family; [3] T111 was flagged and T103 was not.

**Open questions:** Is T117's true label (ellipse) a human reading or a source label for a rounded blob? If a source label, the LLM's hexagon call is defensible by geometry, and the benchmark should say which it is. Batch 06's 17/20 is about 1.2 binomial standard deviations below the per-batch mean of 18.5, so it is within noise and not an outlier.
