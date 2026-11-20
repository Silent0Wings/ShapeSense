# 5_direct_llm_prediction - Batch 02 (T021-T040)

- LLM: Gemini 4 Neon, medium effort (`gemini-4-neon-medium`)
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19
- Protocol: Blind vision evaluation (seed-0 50-example reference grid + shuffled 20-tile batch contact sheet; original filenames hidden behind `T021`–`T040`)
- Peer model response: [02_batch-02.md](../claude_opus/02_batch-02.md)

## Prompt

> Classify every 64x64 grayscale 2D shape tile in `batch_02.png` (`T021`–`T040`) against the 50 labeled training examples (5 per class across all 10 classes in `fewshot_examples.png`). Notice the geometric conventions in the labeled examples: `square` includes rotated right-angle squares (~45°), while `diamond` requires non-90° acute/obtuse rhombus corners; `circle` vs `ellipse` depends on aspect ratio; count polygon vertices carefully for `pentagon`, `hexagon`, and `octagon`. Images are randomly shuffled and stripped of filenames.
> 
> Answer ONLY with lines in the form `blind_id,label`, using one of: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`, followed by a concise `NOTES:` observation on ambiguous tiles.

## Response

```text
### BATCH 02
T021,hexagon
T022,octagon
T023,diamond
T024,circle
T025,pentagon
T026,ellipse
T027,diamond
T028,hexagon
T029,octagon
T030,pentagon
T031,square
T032,rectangle
T033,diamond
T034,hexagon
T035,star
T036,square
T037,octagon
T038,circle
T039,octagon
T040,rectangle
NOTES: T031 is a hand-drawn thin-line quadrilateral with near-1:1 aspect ratio and ~90-degree corners (square), and T039 is an open/partial polygon with horizontal, vertical, and 45-degree corner segments consistent with an octagon.
```

### De-anonymized batch scoring (19/20 correct)

| Blind ID | `image_id` | Source | True label | This LLM | Trained CNN (`A2_0`) | Result |
|---|---|---|---|---|---|---|
| `T021` | `mendeley_elkorchi_hexagon_009974` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T022` | `quickdraw_octagon_016633` | `quickdraw` | `octagon` | `octagon` | `octagon` | Both right |
| `T023` | `kaggle_reevald_diamond_004340` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T024` | `mendeley_elkorchi_circle_008288` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T025` | `mendeley_elkorchi_pentagon_011267` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T026` | `github_handdrawn_ellipse_000213` | `github_handdrawn` | `ellipse` | `ellipse` | `ellipse` | Both right |
| `T027` | `kaggle_reevald_diamond_004898` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T028` | `quickdraw_hexagon_016434` | `quickdraw` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T029` | `mendeley_elkorchi_octagon_010783` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T030` | `mendeley_elkorchi_pentagon_011112` | `mendeley_elkorchi` | `pentagon` | `pentagon` | `pentagon` | Both right |
| `T031` | `quickdraw_square_017034` | `quickdraw` | `square` | `square` | `square` | Both right |
| `T032` | `kaggle_reevald_rectangle_005977` | `kaggle_reevald` | `rectangle` | `rectangle` | `rectangle` | Both right |
| `T033` | `kaggle_reevald_diamond_004845` | `kaggle_reevald` | `diamond` | `diamond` | `diamond` | Both right |
| `T034` | `mendeley_elkorchi_hexagon_009378` | `mendeley_elkorchi` | `hexagon` | `hexagon` | `hexagon` | Both right |
| `T035` | `quickdraw_star_017803` | `quickdraw` | `star` | `star` | `star` | Both right |
| `T036` | `mendeley_elkorchi_square_012869` | `mendeley_elkorchi` | `square` | `square` | `square` | Both right |
| `T037` | `mendeley_elkorchi_octagon_010173` | `mendeley_elkorchi` | `octagon` | `octagon` | `octagon` | Both right |
| `T038` | `mendeley_elkorchi_circle_008601` | `mendeley_elkorchi` | `circle` | `circle` | `circle` | Both right |
| `T039` | `quickdraw_hexagon_016467` | `quickdraw` | `hexagon` | `octagon` | `hexagon` | CNN right, LLM miss |
| `T040` | `github_handdrawn_rectangle_001656` | `github_handdrawn` | `rectangle` | `rectangle` | `rectangle` | Both right |

## Validation

- Parsed `20/20` unique blind IDs (`T021`–`T040`) matching `results/direct_llm_prediction/blind_id_map.csv` (`results/direct_llm_prediction/sample_ids.csv` frozen test subset, pixel MD5s verified `200/200`).
- Blind direct vision accuracy on Batch 02: `19/20` (`95.0%`), compared against frozen exported CNN `A2_0` on the same 20 images: `20/20` (`100.0%`).
- Batch confusion pairs: `hexagon -> octagon` (1).

## Our decision

Kept the raw unedited blind predictions in `results/direct_llm_prediction/gemini_4_neon_predictions.csv` under frozen Stage 5 protocol (`configs/splits/test.csv` never used for tuning).

## Measured effect

- Batch 02: `19/20` (`95.0%`) vs. trained CNN `A2_0` `20/20` (`100.0%`).
- Full 200-image benchmark cumulative score: **93.97 Macro F1** vs. `97.50` Macro F1 for `A2_0` (peer comparison with Claude Opus 5.5 in [01_direct-prediction-error-comparison.md](../cross_critique/01_direct-prediction-error-comparison.md)).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** Gemini misses T039 (hexagon called octagon), the same tile Opus misses; A2_0 is right. On T031 (square) Gemini is right and Opus calls it rectangle, so the two models differ on one tile and agree on the other error.

**Changelog:** [1] T039 is a shared miss; [2] T031 is Gemini-right and Opus-wrong; [3] NOTES flag T039 (an error) and T031 (correct).

**Open questions:** The quickdraw source has misses by both VLMs on T017, T039, T063, T069 and T080, all open-polygon tiles. Is the ground truth a source label or a human reading? If a source label, some of these misses may be label disagreement rather than model error.
