# 2_data_preparation/feature_selection - FS1–FS5: Input representation, HOG/pixel baselines, framing sensitivity, and 48 px resolution selection
- LLM: Gemini 4 Neon
- Category: Two-LLM comparison / Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- [`inferred_prompts.md`](../inferred_prompts.md) (FS1–FS5), [`PROMPT.md`](../../PROMPT.md), `results/improvement_table.csv`, `results/phase2_snapshot/baselines.json`, `results/phase2_snapshot/exp_preprocess.json`, and `scripts/improvement_table.py` (`fs`). Peer file: [`../claude_opus/01_FS1_feature-selection-and-resolution.md`](../claude_opus/01_FS1_feature-selection-and-resolution.md).

## Prompt

> Our input is a 64x64 grayscale image fed to a CNN. What does feature selection mean for this setup, and what would you try (input resolution, cropping to the shape's bounding box, removing background, or hand-made features such as HOG or Hu moments with a classical model)? How do we measure whether it helped?
>
> Follow-up (FS5): For the final A2 recipe, does a lower input resolution (32 or 48 px) score better than 64 px on validation? Pick one on validation only, then report its test macro F1 against the baseline.

## Response

For an end-to-end convolutional network operating on raster silhouettes, **feature selection** is the choice of **input representation and spatial filtering** before the first learned convolution, rather than dropping tabular columns. Specifically, it decomposes into four testable representations:

1. **Spatial resolution bottlenecks (`32×32`, `48×48`, `64×64`):**
   - High frequency pixel jitter along hand-drawn strokes (`github_handdrawn` at 70×70 upsampled/downsampled, and rasterized `quickdraw` strokes) versus clean anti-aliased synthetic edges (`mendeley_elkorchi`, `kaggle_reevald`) acts as a **source-identifying nuisance feature** (consistent with the 91.7% source classifier in F05).
   - Inserting a deterministic area-interpolation bottleneck (`F.interpolate(..., mode="area")` to `32×32` or `48×48`, then back to `64×64` so the 4-block CNN architecture and receptive field remain identical) acts as a spatial low-pass filter: it discards high-frequency stroke-texture noise while preserving global polygon vertices and aspect ratio.
   - **Caution on implementation:** Area downsampling must be run on float tensors in `[0, 1]` before re-centering/standardization, never via `uint8` GPU round-trip truncation (which floors fractional pixels to zero and collapses thin 1-px strokes).

2. **Bounding-box cropping and margin framing (`MARGIN = 0.08`):**
   - Cropping to the ink bounding box with an 8% margin removes scale and translation variance as nuisance features.
   - Its importance is already measurable via the zero-augmentation reframing probe (`exp_preprocess.json`): altering framing alone drops validation Macro F1 by `-2.8` points on `A0` (`92.6 → 89.8`) and `-1.1` points on `A2` (`95.2 → 94.1`), proving that consistent bounding-box framing is a critical input feature.

3. **Background and polarity removal:**
   - Thresholding and normalizing polarity to single-channel black-on-white silhouettes eliminates RGB background color (`mendeley_elkorchi` random color fills) and alpha channel artifacts (`github_handdrawn` RGBA).

4. **Hand-crafted descriptors (HOG, raw pixels, Hu moments) with classical classifiers:**
   - Classical feature extractors should be evaluated as **reference baselines** (`baselines.py`), not concatenated into the CNN:
     - Raw flattened pixels (`64×64 = 4,096` features) + Logistic Regression (`C = 0.01`): tests linear separability in pixel space.
     - HOG (`8×8` cells, 9 orientations = `1,764` features) + Linear SVM (`C = 1.0`): tests explicit edge-orientation histograms.
     - Hu moments (7 rotation/scale-invariant moments) are unsuitable as a primary representation for our 10-class taxonomy because full rotation and scale invariance collapses the orientation boundary between `square` and `diamond` (F07) and weakens `circle` vs. `ellipse`.

5. **Evaluation protocol:**
   - Sweep candidate resolutions (`32 px`, `48 px`, `64 px`) on **validation Macro F1 only** across multiple seeds (`seeds 0..2`) using the frozen `A2` recipe.
   - Freeze the winning resolution on validation before touching the sealed test set (`2,776` images), then train all 5 seeds (`0..4`) and report `New score − Baseline score` against the raw uncleaned baseline (`89.13 ± 0.43`).

## Validation

Checked against the repository benchmarks and `scripts/improvement_table.py fs`:
- **Classical feature baselines (`results/phase2_snapshot/baselines.json`):**
  - Raw pixels + Logistic Regression: `77.7` val / `77.9` test Macro F1.
  - HOG (1,764 features) + Linear SVM: `82.5` val / `84.3` test Macro F1 (+6.4 test points over raw pixels, but >11 points behind the CNN's learned features).
- **Framing sensitivity (`results/phase2_snapshot/exp_preprocess.json`):** Reframing costs `-2.8` Macro F1 on `A0` and `-1.1` on `A2`, confirming bounding-box crop + fixed margin is an essential spatial feature step.
- **Resolution sweep on validation (`artifacts/improvement/feature_selection.json`, seeds 0–2):**
  - `32 px`: `95.85` validation Macro F1
  - `48 px`: **`95.90`** validation Macro F1 (winner on validation)
  - `64 px`: `95.80` validation Macro F1
- **Bug caught during validation (F32):** An initial GPU `uint8` resize implementation truncated float `[0, 1]` values to zero (`25.81` test F1); fixing the resize to operate in float `[0, 1]` restored proper area filtering.

## Our decision

Selected the **48 px area-downsampled input representation** (chosen on validation at `95.90` Macro F1) for the course improvement table's Feature Selection stage, while keeping the HOG Linear SVM (`84.3` test Macro F1) and raw-pixel Logistic Regression (`77.9` test Macro F1) as classical feature baselines. The deployed browser ONNX models remain the frozen 64 px `A2` checkpoints.

## Measured effect

- **Baseline (raw 64×64, before cleaning/transformation/feature selection):** `89.13 ± 0.43` test Macro F1
- **After Transformation (64 px A2):** `95.83 ± 0.31` test Macro F1 (`+6.70` over baseline)
- **After Feature Selection (48 px A2, 5 seeds):** **`96.31 ± 0.13`** test Macro F1 (**`+7.19`** over raw baseline, `+0.48` over 64 px transformation, higher on 4 of 5 seeds and halving seed standard deviation from `0.31` to `0.13`).
