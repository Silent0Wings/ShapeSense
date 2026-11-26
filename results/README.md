# Results

Main metric: **macro F1** (10 classes), in points (0 to 100). Every comparison uses the same held-out test split
(2,776 images) unless a row says otherwise.

## 1. Improvement table (run 2026-11-20)

Baseline = the model trained on the collected data before any data preparation: the raw images, only decoded
and resized to 64x64 so they fit one tensor. Each row adds one step to the one above it and retrains. Every model is
the same CNN with the same settings (49 steps x 60 epochs), trained with seeds 0 to 4. Every row is scored on the
same 2,776 test images. Scores are test macro F1, mean ± standard deviation over the 5 seeds.

| Data preparation step | Baseline score | New score | Delta (New - Baseline) |
|---|---|---|---|
| Cleaning | 89.13 ± 0.43 | 89.63 ± 0.74 | +0.50 |
| Transformation | 89.13 ± 0.43 | 95.83 ± 0.31 | +6.70 |
| Feature selection | 89.13 ± 0.43 | 96.31 ± 0.13 | +7.19 |

What each step is (code and details: [`scripts/improvement_table.py`](../scripts/improvement_table.py), numbers:
[`improvement_table.csv`](improvement_table.csv), [`improvement_table.json`](improvement_table.json)):

- **Baseline:** raw images from all four sources: transparency flattened onto white, converted to 8-bit grey, plain
  resize to 64x64. The training set keeps what cleaning removes: the 350 Quick, Draw! "diamonds" in the training
  share, 21 exact duplicates of training images and 1 blank image (12,777 images).
- **Cleaning:** the same raw images, without those 372 items (12,405 images). The gain is within the seed spread, so
  on its own it is not shown to help. Its main purpose was label correctness: the removed "diamonds" were mostly
  not rhombi.
- **Transformation:** Stage 1 standardization (crop to the shape, fixed polarity, letterbox, outline redraw) gives
  94.64 ± 0.18 (+5.51, arm A0). Then class-safe augmentation and synthetic shapes give 95.83 ± 0.31 (+6.70, arm A2,
  the final model).
- **Feature selection:** input resolution for the A2 recipe, chosen on validation only (3 seeds): 32 px 95.85,
  48 px 95.90, 64 px 95.80. 48 px won by less than the seed spread. On test it scored 96.31 ± 0.13 (+0.48 over A2,
  higher on 4 of 5 seeds). The deployed model stays the 64 px A2.

Caveats: this test split had already been read in earlier iterations (F13), so it is weaker evidence than a first
read. The Feature selection row was decided on validation before this test read. The first feature-selection
attempt hit a GPU resize bug (F32) and was rerun.

Colab rerun (2026-11-24, Tesla T4, PyTorch 2.14.1+cu130 from PyPI; printed in
[`jupyter runs clean.pdf`](../jupyter%20runs%20clean.pdf)). Same code, seeds and test split. The numbers above come
from the original machine (RTX 3080 laptop GPU, CUDA 13.0 build), so the T4 scores differ slightly. GPU
convolution kernels are not bit-identical across cards and builds, and five seeds do not average that out. Every
step improves on the baseline in the same order on both machines:

| Data preparation step | Local (RTX 3080) | Colab (T4) | Colab delta vs baseline |
|---|---|---|---|
| Baseline | 89.13 ± 0.43 | 89.26 ± 0.52 | 0.00 |
| Cleaning | 89.63 ± 0.74 | 89.44 ± 0.81 | +0.18 |
| Transformation, standardization (A0) | 94.64 ± 0.18 | 94.43 ± 0.27 | +5.17 |
| Transformation, augmentation + synthetic (A2) | 95.83 ± 0.31 | 95.76 ± 0.19 | +6.50 |
| Feature selection (48 px) | 96.31 ± 0.13 | 96.18 ± 0.11 | +6.92 |

The recorded results, slides and reports quote the local run.

On the 200 images of the direct-LLM benchmark, the baseline model (seed 0) scores 90.6 and the final model (A2, seed 0)
scores 97.5.

## 2. Phase 2 results (from the frozen snapshot)

All files are copied unchanged from the public site snapshot into [`phase2_snapshot/`](phase2_snapshot/).

### Test split (2,776 images), macro F1

| Model | Per-seed mean ± std (5 seeds) | Soft-vote ensemble |
|---|---|---|
| Logistic regression on pixels (classical baseline) | - | 77.9 |
| SVM on HOG features (classical baseline) | - | 84.3 |
| A0: real images only (CNN) | 94.6 ± 0.2 | 95.5 |
| A1: real + augmentation | 95.8 ± 0.1 | 96.2 |
| B: real + synthetic, all augmented | 95.6 ± 0.3 | 95.8 |
| A2: clean real + augmented real + synthetic | 95.8 ± 0.3 | 96.0 |
| P: synthetic pretraining, then real fine-tuning | 95.8 ± 0.1 | 96.2 |

Source: [`phase2_snapshot/metrics.csv`](phase2_snapshot/metrics.csv), [`phase2_snapshot/baselines.json`](phase2_snapshot/baselines.json).

### Fresh holdout, macro F1

| A0 | A1 | B | A2 | P |
|---|---|---|---|---|
| 97.8 | 98.2 | 97.8 | 98.3 | 98.0 |

Source: [`phase2_snapshot/fresh_metrics.csv`](phase2_snapshot/fresh_metrics.csv).

### Pre-registered comparisons

| Comparison | Delta macro F1 | 95% CI |
|---|---|---|
| A2 vs A0 (primary, iteration 2) | +0.5 | [-0.2, 1.2] |
| A1 vs A0 (secondary) | +0.6 | [-0.2, 1.4] |
| A2 vs A0 on damaged images (iteration 3, sealed holdout) | +9.20 | [8.89, 9.53] |

Sources: [`phase2_snapshot/comparisons.csv`](phase2_snapshot/comparisons.csv),
[`phase2_snapshot/robust_sealed.json`](phase2_snapshot/robust_sealed.json).

### Per-class and per-source results

[`per_class.csv`](phase2_snapshot/per_class.csv), [`per_source.csv`](phase2_snapshot/per_source.csv),
[`fresh_per_class.csv`](phase2_snapshot/fresh_per_class.csv), [`split_stats.csv`](phase2_snapshot/split_stats.csv).

## 3. Other results

| Folder | Contents | Status |
|---|---|---|
| [`stage_map.md`](stage_map.md) | Course stages vs. CRISP-DM phases vs. ShapeSense stages, with evidence and key findings per stage | Done |
| [`llm_comparison/`](llm_comparison/) | Gemini's audit of the Claude-built pipeline: 27 claims, team verdicts and actions | Done from the record; Gemini chats still to export |
| [`verification/`](verification/) | How the results were verified, and the dataset-awareness check | Verification done; awareness check still to run |
| [`direct_llm_prediction/`](direct_llm_prediction/) | Each LLM's direct predictions on the test set vs. the trained model | Done (200 test images: CNN `A2_0` 97.50, Claude Opus 5.5 92.55, Gemini 4 Neon 93.97 Macro F1) |
