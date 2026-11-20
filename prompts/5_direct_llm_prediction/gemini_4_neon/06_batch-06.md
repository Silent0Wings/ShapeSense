# 5_direct_llm_prediction - Batch 06 (T101-T120)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T101`–`T120`)
- Peer model response: [06_batch-06.md](../claude_opus/06_batch-06.md)

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
T111,rectangle
T112,star
T113,ellipse
T114,hexagon
T115,hexagon
T116,star
T117,circle
T118,pentagon
T119,triangle
T120,pentagon
NOTES: T111 has rounded-corner vertical sides (classified as rectangle), T115 is an open-sided hexagon missing its upper-left edge, and T117 is slightly irregular/wide (borderline circle/ellipse).
```

### De-anonymized batch scoring (18/20 correct)

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
| `T111` | `github_handdrawn_rectangle_001517` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T112` | `mendeley_elkorchi_star_013905` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T113` | `github_handdrawn_ellipse_000184` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T114` | `mendeley_elkorchi_hexagon_009916` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T115` | `quickdraw_hexagon_016086` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T116` | `quickdraw_star_017560` | `quickdraw` | `star` | `star` | `star` | Both right |
| `T117` | `github_handdrawn_ellipse_000020` | `github_handdrawn` | `ellipse` | `circle` | `ellipse` | CNN right, LLM miss |
| `T118` | `mendeley_elkorchi_pentagon_011430` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T119` | `github_handdrawn_triangle_002955` | `github_handdrawn` | `triangle` | `triangle` | `triangle` | Both right |
| `T120` | `mendeley_elkorchi_pentagon_011546` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T101`–`T120`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 06: `18/20` (`90.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `circle -> ellipse` (1), `ellipse -> circle` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 06: `18/20` (`90.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** both VLMs miss T103 (circle called ellipse) and T117 (ellipse). The direction differs on T117: Gemini calls it circle and Opus calls it hexagon. Opus also misses T111 (rectangle called ellipse), which Gemini gets right. Opus has three misses here and Gemini two, so this batch is not the one where both models miss two tiles; A2_0 is perfect.

**Changelog:** [1] both VLMs miss T103 and T117; [2] T117 is wrong in different directions for the two models; [3] T111 is Gemini-right and Opus-wrong; [4] the T111 and T115 flags are both correct.

**Open questions:** Is T117's true label (ellipse) a human reading or a source label for a rounded blob? If a source label, neither the circle nor the hexagon call is clearly wrong by geometry, and the benchmark should say which it is.
