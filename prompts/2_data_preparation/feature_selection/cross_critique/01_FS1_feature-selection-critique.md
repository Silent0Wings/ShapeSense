# 2_data_preparation/feature_selection - Cross-critique: Input representation and 48 px resolution bottleneck
- LLM: Gemini 4 Neon critiquing Claude Opus 5.5 (and joint verification of F32)
- Category: Two-LLM comparison
- Date: 2026-11-20

Cross-critique of [Claude Opus 5.5](../claude_opus/01_FS1_feature-selection-and-resolution.md) and [Gemini 4 Neon](../gemini_4_neon/01_FS1_feature-selection-and-resolution.md) on the Feature Selection stage ([`inferred_prompts.md`](../inferred_prompts.md) FS1–FS5).

## Prompt

> Another assistant recommended the following for the feature selection step of our pipeline: treat feature selection for a 64x64 grayscale CNN as input representation selection (bounding-box crop with 8% margin, background removal, classical HOG SVM baseline comparison, and an area-resize resolution sweep across 32, 48, and 64 px selected on validation). Check it for errors, risks of data leakage between train and test, and steps that would not help. Say which points you agree with, which you reject, and why.

## Response

### 1. Points of agreement
- **Reframing feature selection as spatial input representation:** For a 4-block CNN (`242,250` parameters), selecting spatial resolution (`32`, `48`, `64 px`) and bounding-box framing (`MARGIN = 0.08`) is the mathematically sound analog of tabular feature selection. Area downsampling to `48×48` acts as a spatial low-pass filter that suppresses source-specific high-frequency stroke noise (F05) while preserving polygon corner geometry.
- **Rejecting Hu moments for the 10-class taxonomy:** Both models rightly flag that Hu moments' full rotation invariance conflicts with the taxonomy definitions (`configs/taxonomy.yaml`), where `square` vs. `diamond` is an orientation boundary protected by the `±10°` rotation cap (F07).
- **Keeping HOG + Linear SVM as an external baseline (`84.3` test F1) rather than fusing with CNN logits:** The `>11`-point gap between HOG + SVM (`84.3`) and the CNN (`95.83`) shows the CNN's learned conv filters already subsume local gradient histograms.

### 2. Leakage and implementation risks checked
- **Validation-only resolution selection (no test leakage):** Selecting `48 px` (`95.90` val F1 vs. `95.85` at `32 px` and `95.80` at `64 px`) across seeds `0..2` before running the 5-seed test evaluation prevents model-selection leakage into the test split.
- **Statistical caveat (validation margin vs. seed noise):** The validation gap between `48 px` (`95.90`) and `64 px` (`95.80`) is `+0.10` points, which is smaller than the seed-to-seed standard deviation (`~0.13–0.31` points). The report must state candidly that while `48 px` won on validation and improved test Macro F1 from `95.83 ± 0.31` to `96.31 ± 0.13` (winning on 4 of 5 seeds), the validation selection margin itself was within seed noise.
- **Float `[0, 1]` vs. `uint8` tensor quantization trap (F32):** Applying a `uint8` image-resize path on GPU tensors already normalized to `[0.0, 1.0]` truncates every non-1.0 pixel to `0`, destroying the image and collapsing test Macro F1 to `25.81`. Keeping area interpolation strictly in float32 `(B, 1, 64, 64) -> (B, 1, 48, 48) -> (B, 1, 64, 64)` avoids the bug and keeps the CNN receptive field unchanged.

## Validation

Checked against `results/improvement_table.csv`, `artifacts/improvement/feature_selection.json`, and `docs/crisp_dm/iteration_log.json` (entry F32).

## Our decision

Agreed on all points: adopt the float32 `48 px` area-resize bottleneck for the Feature Selection step in the course improvement table (`96.31 ± 0.13`, `+7.19` over baseline) and document the validation noise band and F32 fix in `results/README.md` and `docs/course_requirements_answers.md`.

## Measured effect

- Feature selection (`48 px` input): **`96.31 ± 0.13`** test Macro F1 (`+0.48` over 64 px Transformation `95.83 ± 0.31`, and **`+7.19`** over raw Baseline `89.13 ± 0.43`).
