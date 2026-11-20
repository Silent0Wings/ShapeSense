# Direct LLM Prediction Results (Stage 5)

Blind head-to-head comparison between the final frozen pipeline CNN (`A2_0` exported ONNX) and direct visual classification by **Claude Opus 5.5** (`claude-opus-5-5-medium`) and **Gemini 4 Neon** (`gemini-4-neon-medium`) on the exact same **200** held-out test images ([sample_ids.csv](sample_ids.csv), 20 per class, drawn with seed 0 from `configs/splits/test.csv`).

## Summary scores

| Model | Images | Macro F1 (points) | Accuracy (%) | Correct / 200 | Top confusion | Predictions CSV |
|---|---:|---:|---:|---:|---|---|
| **Trained CNN (`A2_0`, final model)** | 200 | **97.50** | **97.50%** | **195/200** | `hexagon -> octagon` (2) | [trained_cnn_predictions.csv](trained_cnn_predictions.csv) |
| Claude Opus 5.5 (`claude-opus-5-5-medium`) | 200 | **92.55** | **92.50%** | **185/200** | `circle -> ellipse (4)` | [claude_opus_predictions.csv](claude_opus_predictions.csv) |
| Gemini 4 Neon (`gemini-4-neon-medium`) | 200 | **93.97** | **94.00%** | **188/200** | `circle -> ellipse (4)` | [gemini_4_neon_predictions.csv](gemini_4_neon_predictions.csv) |

## Per-class F1 & Per-source accuracy

| Class | n | CNN `A2_0` F1 | Opus 5.5 F1 | Gemini 4 Neon F1 |
|---|---:|---:|---:|---:|
| `circle` | 20 | 100.00 | 86.49 | 86.49 |
| `ellipse` | 20 | 97.44 | 83.72 | 88.37 |
| `triangle` | 20 | 97.56 | 100.00 | 100.00 |
| `square` | 20 | 100.00 | 95.00 | 97.44 |
| `rectangle` | 20 | 97.44 | 95.00 | 95.00 |
| `pentagon` | 20 | 100.00 | 97.44 | 100.00 |
| `hexagon` | 20 | 92.31 | 82.05 | 86.49 |
| `octagon` | 20 | 92.68 | 88.37 | 88.37 |
| `star` | 20 | 100.00 | 100.00 | 100.00 |
| `diamond` | 20 | 97.56 | 97.44 | 97.56 |

| Source | n | CNN `A2_0` | Opus 5.5 | Gemini 4 Neon |
|---|---:|---:|---:|---:|
| `mendeley_elkorchi` | 88 | 100.00% (88/88) | 98.86% (87/88) | 100.00% (88/88) |
| `kaggle_reevald` | 46 | 100.00% (46/46) | 89.13% (41/46) | 91.30% (42/46) |
| `github_handdrawn` | 39 | 94.87% (37/39) | 92.31% (36/39) | 94.87% (37/39) |
| `quickdraw` | 27 | 88.89% (24/27) | 77.78% (21/27) | 77.78% (21/27) |

## Provenance & Artifacts

- **Test sample:** [sample_ids.csv](sample_ids.csv) (200 test IDs verified 200/200 by pixel MD5 against `configs/splits/test.csv`).
- **Few-shot reference images:** [fewshot_example_ids.csv](fewshot_example_ids.csv) (50 training images, 5 per class, seed 0, verified 50/50 by pixel MD5 against `configs/splits/train.csv`).
- **Blind shuffle mapping:** [blind_id_map.csv](blind_id_map.csv) (`T001`–`T200` across batches 01–10; filenames withheld from both LLMs during classification).
- **Full metrics JSON:** [summary.json](summary.json).
- **Batch logs & error analysis:** [PROMPT.md](../../prompts/5_direct_llm_prediction/PROMPT.md), [claude_opus/](../../prompts/5_direct_llm_prediction/claude_opus/), [gemini_4_neon/](../../prompts/5_direct_llm_prediction/gemini_4_neon/), and [01_direct-prediction-error-comparison.md](../../prompts/5_direct_llm_prediction/cross_critique/01_direct-prediction-error-comparison.md).
