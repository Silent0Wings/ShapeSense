# 2_data_preparation/feature_selection - FS1–FS5: Input representation, HOG/pixel baselines, framing sensitivity, and 48 px resolution selection
- LLM: Claude Opus 5.5
- Category: Two-LLM comparison / Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Reconstructed / grounded from: [`inferred_prompts.md`](../inferred_prompts.md) (FS1–FS5), [`PROMPT.md`](../../PROMPT.md), `results/improvement_table.csv`, `results/phase2_snapshot/baselines.json`, `results/phase2_snapshot/exp_preprocess.json`, and `scripts/improvement_table.py` (`fs`). Peer file: [`../gemini_4_neon/01_FS1_feature-selection-and-resolution.md`](../gemini_4_neon/01_FS1_feature-selection-and-resolution.md).

## Prompt

> Our input is a 64x64 grayscale image fed to a CNN. What does feature selection mean for this setup, and what would you try (input resolution, cropping to the shape's bounding box, removing background, or hand-made features such as HOG or Hu moments with a classical model)? How do we measure whether it helped?
>
> Follow-up (FS5): For the final A2 recipe, does a lower input resolution (32 or 48 px) score better than 64 px on validation? Pick one on validation only, then report its test macro F1 against the baseline.

## Response

A CNN learns its own filters from pixels, so feature selection here means choosing the **input representation**, not picking columns from a table. Five concrete choices apply to this pipeline:

1. **Cropping to the shape's bounding box (`MARGIN = 0.08`):** `src/stage1_freeze/standardize.py` crops every image to the ink bounding box, adds an 8% margin, pads to a square, and resizes to 64×64. That strips position and scale differences across the four sources. The zero-randomness reframing check (`exp_preprocess.json`) confirms the models rely on this framing: re-framing alone drops validation macro F1 by `-2.8` points on `A0` (`92.6 → 89.8`) and `-1.1` on `A2` (`95.2 → 94.1`).
2. **Removing background and colour:** Standardization outputs single-channel black ink on white background, removing El Korchi's random background/foreground colours and hand-drawn RGBA transparency.
3. **Hand-made features (HOG vs. raw pixels):** Stage 4 trains two classical models (`src/common/features.py`, `src/stage4_train/baselines.py`) on 6,000 balanced real images:
   - Raw pixels + logistic regression (`C = 0.01`): `77.7` validation / `77.9` test macro F1.
   - HOG (9 orientations, 8 px cells, 1,764 values) + linear SVM (`C = 1.0`): `82.5` validation / `84.3` test macro F1.
   HOG adds `+6.4` test points over raw pixels for a linear classifier, showing edge-orientation histograms are informative, but the CNN (`95.8 ± 0.3` on `A2`) still leads by more than 11 points. Hu moments are rotation-invariant and would blur `square` vs. `diamond`, where orientation is class-defining (F07).
4. **Input resolution (`32 px`, `48 px`, `64 px`):** Putting a fixed area-resize bottleneck (`32×32` or `48×48`) in front of the CNN tests whether smoothing fine stroke-width and pixel-jitter differences across sources improves generalization while keeping the 4-block architecture fixed.
5. **How to measure:** Compare mean validation macro F1 across seeds `0..2` on the same `A2` training recipe before reading test. Once the best resolution is chosen on validation, train all 5 seeds (`0..4`) and score once on the 2,776-image test split against the raw baseline (`89.13 ± 0.43`).

### Resolution run results (FS5)

Validation macro F1 (mean of seeds 0 to 2, `artifacts/improvement/feature_selection.json`):
- `32 px`: `95.85`
- `48 px`: **`95.90`** (chosen on validation)
- `64 px`: `95.80`

Retrained across all 5 seeds (`0..4`), the `48 px` input scored **`96.31 ± 0.13`** on the sealed test split against `95.83 ± 0.31` at `64 px` (`+0.48` test points, higher on 4 of 5 seeds, and `+7.19` over the raw baseline `89.13 ± 0.43`). Note: the first run failed at chance (`25.81` test F1, logged as failure **F32**) because a GPU `uint8` cast truncated float `[0, 1]` tensors to zero; fixing the resize to keep float `[0, 1]` resolved it.

## Validation

- Verified against `results/improvement_table.csv`, `artifacts/improvement/feature_selection.json`, `results/phase2_snapshot/baselines.json`, `results/phase2_snapshot/exp_preprocess.json`, and `docs/crisp_dm/iteration_log.json` (F32, C56, C57).

## Our decision

Keep bounding-box crop (`MARGIN = 0.08`) and background removal in Stage 1, keep HOG + SVM as the classical feature reference, and adopt the `48 px` validation winner as the Feature Selection row in `results/improvement_table.csv`.

## Measured effect

- **Raw baseline → Cleaning → Transformation → Feature selection (48 px):** `89.13 ± 0.43 → 89.63 ± 0.74 (+0.50) → 95.83 ± 0.31 (+6.70) → 96.31 ± 0.13 (+7.19)`.
