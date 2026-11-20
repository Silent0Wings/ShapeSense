# 5_direct_llm_prediction - Batch 03 (T041-T060)

- LLM: Claude Opus 5.5, medium effort (`claude-opus-5-5-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T041`–`T060`)
- Peer model response: [03_batch-03.md](../gemini_4_neon/03_batch-03.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_03.png` (`T041`–`T060`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 03
T041,pentagon
T042,rectangle
T043,circle
T044,star
T045,circle
T046,ellipse
T047,rectangle
T048,star
T049,octagon
T050,rectangle
T051,ellipse
T052,octagon
T053,pentagon
T054,star
T055,ellipse
T056,square
T057,diamond
T058,octagon
T059,square
T060,diamond
NOTES: T049 (wobbly round, octagon vs circle) and T052 (thin irregular outline, octagon vs hexagon) are borderline; T042 is a very thin rectangle.
```

### De-anonymized batch scoring (19/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T041` | `mendeley_elkorchi_pentagon_011615` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T042` | `github_handdrawn_rectangle_001093` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T043` | `mendeley_elkorchi_circle_008998` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T044` | `mendeley_elkorchi_star_013240` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T045` | `kaggle_reevald_circle_003433` | `kaggle_reevald` | `circle` | `circle` | `circle` | Both right |
| `T046` | `github_handdrawn_ellipse_000512` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T047` | `github_handdrawn_rectangle_001888` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T048` | `mendeley_elkorchi_star_013599` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T049` | `mendeley_elkorchi_octagon_010337` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T050` | `kaggle_reevald_rectangle_005608` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T051` | `github_handdrawn_ellipse_000131` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T052` | `quickdraw_octagon_016937` | `quickdraw` | `octagon` | `octagon` | `octagon` | Both right |
| `T053` | `mendeley_elkorchi_pentagon_011382` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T054` | `mendeley_elkorchi_star_013103` | `mendeley_elkorchi` | `star` | `star` | `star` | Both right |
| `T055` | `kaggle_reevald_circle_003863` | `kaggle_reevald` | `circle` | `ellipse` | `circle` | CNN right, LLM miss |
| `T056` | `mendeley_elkorchi_square_012092` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T057` | `kaggle_reevald_diamond_004091` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T058` | `mendeley_elkorchi_octagon_010305` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T059` | `kaggle_reevald_square_006973` | `kaggle_reevald` | `square` | `square` | `square` | Both right |
| `T060` | `kaggle_reevald_diamond_004407` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T041`–`T060`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 03: `19/20` (`95.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `circle -> ellipse` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/claude_opus_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 03: `19/20` (`95.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **92.55 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Gemini 4 Neon in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** the one LLM miss, T055 (circle called ellipse), is a tile A2_0 gets right, and it was not flagged in NOTES. The two flagged tiles, T049 and T052, were both correct, so the flags did not predict the error.

**Changelog:** [1] the LLM's error was unflagged; [2] two flagged tiles were correct; [3] flags on this batch do not predict errors.

**Open questions:** Is there a numeric confidence per prediction? Prose NOTES cannot be scored across batches; a numeric field would let flags be checked against errors over all ten batches.
