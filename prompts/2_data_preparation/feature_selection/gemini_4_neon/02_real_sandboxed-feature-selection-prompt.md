# 2_data_preparation/feature_selection - Feature selection prompt, sandboxed real run
- LLM: Gemini 4 Neon (`gemini-4-neon-medium`), Antigravity CLI `agy` with `--sandbox --new-project`, started from an empty folder with no repository access
- Category: Two-LLM comparison
- Date: 2026-11-20

A exchange. Gemini saw only the prompt below, with no results, so this answer was given
**before** knowing what the experiment found. [01_FS1_feature-selection-and-resolution.md](01_FS1_feature-selection-and-resolution.md)
[../inferred_prompts.md](../inferred_prompts.md#fs1).

## Prompt

> Answer from your own knowledge only; do not use any tools, web search or files.
> 
> Our input is a 64x64 grayscale image fed to a CNN. What does feature selection mean for this setup, and what would you try (input resolution, cropping to the shape's bounding box, removing background, or hand-made features such as HOG or Hu moments with a classical model)? How do we measure whether it helped?
> 
> Context: a small 4-block CNN classifies 10 shape classes (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond) from images merged from four public sources (sketches, printed and rendered shapes). Images are already cropped to the shape's bounding box with an 8% margin, made black-on-white, and letterboxed to 64x64. Metric: macro F1.

## Response

Unedited. **The reply is truncated**: the CLI's print mode returned only the first 3,129 bytes, and it stops in the
middle of point 4.

### 1. What "feature selection" means for a 64×64 grayscale CNN

In tabular ML, feature selection means choosing a subset of columns. For raw images fed to a CNN, individual pixels are not independent semantic features—the CNN learns edges, corners, and global contours end-to-end.

In this setup, feature selection means **input representation and nuisance-removal engineering**: deciding *what visual signal reaches the network* (resolution, framing, contrast/channels) and *what domain-specific noise is removed* (background texture, stroke-width/fill differences across your four sources), or deciding whether to replace/supplement pixels with explicit geometric descriptors.

---

### 2. What to try (given your current pipeline)

Your current preprocessing—tight bounding-box crop with an 8% margin, black-on-white polarity, and aspect-ratio-preserving letterboxing—already handles the most important geometric invariances (especially preserving aspect ratio so `circle` vs. `ellipse` and `square` vs. `rectangle` stay separable).

Ranked by likely impact for your 10-class, 4-source problem:

1. **Domain & background normalization (highest leverage for 4 mixed sources)**
   - Mixing sketches, printed, and rendered shapes creates **shortcut features** (paper grain, gray background tint, filled interiors vs. thin outlines, compression artifacts).
   - **Try:**
     - Clean background subtraction / contrast normalization (e.g., morphological background removal or percentile clipping) so backgrounds are uniformly white without destroying anti-aliased edges.
     - Comparing **soft grayscale** vs. **adaptive binarization** (Otsu/Sauvola). Binarization removes background noise, though it can erase subtle anti-aliasing that helps distinguish `circle` from `octagon`.
     - **Outline/fill harmonization** (e.g., Canny/Sobel edges, morphological gradient, or distance transform, either alone or stacked as extra input channels alongside grayscale) if some sources are solid filled shapes and others are hand-drawn outlines.

2. **Input resolution (`64×64` vs. `96×96` / `128×128`)**
   - `64×64` is plenty for `triangle`, `square`, `star`, etc., but can blur subtle vertices in **`circle` vs. `octagon` vs. `hexagon`**—especially on noisy sketches.
   - Test `96×96` or `128×128` (and check `48×48` as a lower bound). With a 4-block CNN, check whether the receptive field still covers the whole shape at higher resolution.

3. **Cropping & framing tweaks (minor, mostly sanity checks)**
   - Keep letterboxing (never warp to a square).
   - Verify the 8% margin isn't clipping thick strokes on sketches or creating inconsistent effective margins between thin outlines and thick-bordered shapes.
   - **Avoid orientation-normalizing crops** (like rotating to a minimum-area bounding box): that would collapse `square` and `diamond` into the same class.

4. **Hand-crafted features + classical models (or hybrid fusion)**
   - **HOG + classical model (RBF-SVM, LightGBM/XGBoost, or small MLP):** Strong baseline here because HOG directly encodes edge orientations—very effective for polygon angles and `square` vs. `diamond`.
   - **Explicit contour/geometric features:** Circularity ($4\pi A/P^2$), solidity (area / convex hull area—great for `star`), bounding-box aspect ratio and extent (`circle` vs. `ellipse`, `square` vs. `rectangle`), polygon vertex count (`approxPolyDP`), convexity defects, and Fourier descriptors.
   - **Caveat on Hu moments:** Hu moments are rotation-invariant, so by themselves they **cannot separate `square` from `diamond`** (a 45°-rotated square). Only use them alongside orientation-sensitive features (like HOG or axis-aligned extent).
   - **Caveat on contour extraction:** Hand-drawn sketches with broken strokes or stray marks can break contour-based features; measure how often extraction fails.
   - **Hybrid option:** If classical features excel on specific geometric pairs (e.g., `hexagon` vs. `octagon`) while the CNN is more robust to messy sketches, concatenate normalized geometric features into the CNN's penultimate layer or ensemble the two models.

---

### 3. How to measure whether it helped

1. **Lock a leak-free evaluation protocol**
   - Use a fixed validation split (and untouched test set) **stratified by both class and source**, and grouped by author/page/template if available to prevent near-duplicate leakage.
   - Because you merged four sources, track **both overall macro F1 and per-source macro F1**. If feasible, run a **Leave-One-Source-Out (LOSO)** check: removing background/source artifacts can occasionally *lower* in-distribution F1 (by killing shortcuts) while *improving* generalization to unseen sources.

2. **Run controlled, one-change-at-a-time ablations**
   - Hold the split, augmentations, and training budget constant while changing one input/feature choice at a time.
   - Run **3–5 random seeds** per variant and compare **mean ± std macro F1**.
   - Use a **paired bootstrap** (or McNemar's test on the same validation set) to confirm gains are real rather than seed noise.

3. **Inspect the confusion matrix and per-class F1**
   - Headline macro F1 hides *why* a change worked. Specifically track the hard confusable groups:
     - `circle` ↔ `octagon` ↔ `hexagon` (sensitive to resolution and binarization)
     - `circle` ↔ `ellipse` and `square` ↔ `rectangle` (sensitive to aspect ratio / letterboxing)
     - `square` ↔ `diamond` (sensitive to orientation invariance)
   - Also check **failure modes by source** (e.g., sketches vs. rendered) and weigh any F1 gain against **compute/latency** (e.g., `128×128` is ~4× the FLOPs of `64×64`) and preprocessing failure rates.


## Validation

Compared with the run recorded in [`results/improvement_table.csv`](../../../../results/improvement_table.csv) and FS5:

| Gemini's expectation | What the measurement found |
|---|---|
| Higher resolution (96 or 128 px) may help separate circle, hexagon and octagon; 48 px only as a lower bound | Lower was better: 48 px scored 95.90 on validation against 95.80 at 64 px, and 96.31 on test against 95.83. Higher resolutions were not tested, because the stored images are 64 px |
| Keep letterboxing; never normalize orientation (square and diamond would collapse) | Agrees with the pipeline: letterboxing is kept and orientation is never normalized |
| Domain and background normalization has the highest leverage across the four sources | Agrees: Stage 1 standardization added +5.51 over the raw baseline, the largest single gain |
| HOG with a classical model is a strong baseline | Partly: HOG + linear SVM scored 84.3 on test, against 94.6 for the CNN on the same standardized images |

## Our decision

Kept the resolution search, but in the other direction from Gemini's suggestion. Raising the resolution would mean
re-standardizing every image, while lowering it needs only a resize layer. The measured 48 px gain is small (+0.48),
and its validation margin was within the seed spread.

## Measured effect

Feature selection row: 96.31 ± 0.13 test macro F1, +7.19 over the raw baseline (89.13).
