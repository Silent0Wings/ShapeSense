# 1_data_integration - Draft of integration cases and edge cases

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 or earlier
- Worksheet entries: I01
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is the user's own todo entry, verbatim, which was handed to the LLM as the task; the exact chat message was not saved. The Response quotes the LLM's saved output files verbatim.
- Reconstructions of the same entries: [I01](../claude_opus/04_I01_schema-harmonization-and-label-mapping.md), [I01](03_I01_source-capping-and-label-harmonization.md)

## Prompt (the user's todo entry, verbatim)

```text
- [x] [need more cases and example covered for how we we do data integration  .for handling the edge cases normalisation , dimension difference , gray scale vs color ranges , prefered diagram examples , and how the syntethic data plug into this , and how augementation plug in into this cas  in section C .](plan/02_data_integration_cases.md)
```

_Kept as plain text: the links inside it point to the local plan folder, which is not in the repo. The linked plan is quoted below._

## Response (saved output, verbatim)

### `02_data_integration_cases.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE (implemented, not just planned): scripts/standardize.py + scripts/build_unified_dataset.py. Differences from this draft: grayscale BT.601 replaced by an RGB-distance shape mask (handles random backgrounds and equal-grey colours), plus a fill-to-outline redraw; see Section C.

# Plan 02: Data Integration Pipeline, Edge Cases & Architecture (Section C Enhancement)

## 1. Overview & Objective
This plan establishes a rigorous, comprehensive data integration architecture for the **Unified 2D Shape Classifier**. It addresses all edge cases and integration scenarios required for **Section C (Data Integration)** of `phase1_report.tex`:
- Dimension differences & aspect-ratio preservation
- Grayscale vs. multi-channel color representations
- Contrast polarity and normalization schemes
- Preferred architectural diagrams for data flow
- Seamless integration of procedurally generated synthetic data
- Dynamic, on-the-fly augmentation injection

---

## 2. End-to-End Integration Architecture

The integration pipeline transforms heterogeneous, multi-domain raw inputs into a unified, high-performance training stream.

```
+---------------------------------------------------------------------------------------------------+
|                                      RAW SOURCE INGESTION                                         |
|  [Quick, Draw!] (NDJSON strokes)  |  [Kaggle reevald] (RGB JPG)  |  [Kaggle dinesh] (Grayscale PNG)|
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                   STAGE 1: TAXONOMIC HARMONIZATION                                 |
|  - Map synonyms: 'rhombus' -> 'diamond'                                                           |
|  - Drop non-taxonomy shapes: 'kite', 'trapezoid', 'parallelogram'                                  |
|  - Semantic filtering: drop gem-cut QuickDraw jewelry drawings                                    |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                              STAGE 2: GEOMETRIC & SPATIAL STANDARDIZATION                         |
|  - Vector Stroke Rasterization: QuickDraw stroke vectors -> $64 \times 64$ anti-aliased bitmap    |
|  - Dimension Standardization: Aspect-preserving resize with symmetric reflection/constant pad     |
|  - Target resolution: Standardized to $64 \times 64$ (or $128 \times 128$)                        |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                           STAGE 3: PHOTOMETRIC & NORMALIZATION HARMONIZATION                      |
|  - Channel unification: Convert RGBA/RGB -> 1-channel Grayscale: $Y = 0.299R + 0.587G + 0.114B$   |
|  - Polarity alignment: Enforce dark shape on light background (or bright on dark) across sources   |
|  - Value scaling: Map integer $[0, 255]$ to floating-point $[0.0, 1.0]$                            |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             STAGE 4: METADATA & REPOSITORY SERVING                                |
|  - SQLite Catalog: `Source`, `Label`, `LabelMapping`, `Image` metadata tables                     |
|  - Deduplication: Perceptual hashing (pHash) with Hamming distance threshold $\tau \le 4$         |
|  - Split partition: Strict separation into train, validation, and real-only held-out test split   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                        STAGE 5: ON-THE-FLY SERVING & AUGMENTATION PIPELINE                        |
|  +-------------------------------------+      +------------------------------------------------+  |
|  |     Procedural Synthetic Engine     |      |       Albumentations Augmentation Engine       |  |
|  | - pycairo / Pillow generation       | ---> | - Random affine (rotation, scale, shear)       |  |
|  | - Injected dynamically (30-50%)    |      | - Noise injection (Gaussian, salt-and-pepper)  |  |
|  | - Tagged as `domain='synthetic'`   |      | - Blur (Gaussian, median)                      |  |
|  +-------------------------------------+      +------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|                                    PyTorch Batch Tensor Streaming                                 |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Concrete Edge Cases & Engineering Solutions

### Case 1: Dimension Differences & Aspect Ratio Distortion
- **The Problem**: 
  - QuickDraw drawings are rasterized from $256 \times 256$ vector coordinate space to $28 \times 28$.
  - Kaggle reevald images are $224 \times 224$.
  - Kaggle dinesh images are $200 \times 200$.
  - Naive isotropic stretching (e.g. `cv2.resize(img, (64, 64))`) distorts aspect ratio: a rectangle can deform into a square, or an ellipse into a circle, fundamentally corrupting ground-truth geometry!
- **The Solution**: 
  - **Aspect-Preserving Resize with Letterbox Padding**:
    1. Compute scaling factor $s = \min(64 / W_{\text{orig}}, 64 / H_{\text{orig}})$.
    2. Resize to $(W_{\text{new}}, H_{\text{new}}) = (s \cdot W_{\text{orig}}, s \cdot H_{\text{orig}})$.
    3. Center image and pad the remaining borders symmetrically with background color (reflection or white/black constant) to produce an exact $64 \times 64$ tensor.

### Case 2: Grayscale vs. Multi-Channel Color Ranges
- **The Problem**:
  - Kaggle reevald contains 3-channel RGB renders with arbitrary colorful backgrounds and shaded gradients.
  - Some sources contain 4-channel RGBA with transparent alpha channels.
  - QuickDraw and Dinesh datasets are single-channel grayscale or binary masks.
  - Feeding mismatched channels causes dimension errors in CNN convolutional kernels.
- **The Solution**:
  - **Alpha Channel Flattening**: Composite RGBA onto a solid white/black background using alpha blending:
    $$I_{\text{composite}} = I_{\text{RGB}} \cdot \alpha + I_{\text{bg}} \cdot (1 - \alpha)$$
  - **Luminance Conversion**: Apply ITU-R BT.601 standard conversion to RGB:
    $$Y = 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$$
  - Single-channel tensors ensure the model learns geometric invariants (angles, edges, vertices) rather than spurious color shortcuts.

### Case 3: Contrast Polarity Inversion (Background vs. Foreground)
- **The Problem**:
  - QuickDraw raw stroke renderings are black strokes on white background (strokes = 0, background = 255).
  - Synthetic mask datasets often represent foreground shapes as white on black background (shape = 255, background = 0).
  - Unaligned polarity forces the network to spend capacity learning dual-contrast filters.
- **The Solution**:
  - **Automatic Polarity Detection & Inversion**:
    1. Sample the four corner pixels $(0,0), (0,H-1), (W-1,0), (W-1,H-1)$.
    2. If mean corner intensity $< 128$, image is dark-background; if $> 128$, image is light-background.
    3. Invert if necessary to enforce universal convention: **White background ($1.0$), Dark shape outline/fill ($0.0$)** (or vice versa).

### Case 4: Pixel Value Scaling & Normalization
- **The Problem**:
  - Raw images are 8-bit unsigned integers $[0, 255]$.
  - Training directly on $[0, 255]$ causes gradient explosion or numerical instability.
- **The Solution**:
  - Cast to `torch.float32` and scale linearly to $[0.0, 1.0]$.
  - Apply standard channel normalization with dataset mean $\mu$ and standard deviation $\sigma$:
    $$x_{\text{norm}} = \frac{x - \mu}{\sigma}$$

### Case 5: Taxonomic Ambiguities & Semantic Mappings
- **The Problem**:
  - Kaggle dataset includes `rhombus`, which is geometrically a `diamond`.
  - Kaggle includes `trapezoid`, `kite`, `parallelogram` which fall outside the 10-class taxonomy.
  - QuickDraw `diamond` category includes user sketches of faceted gemstone engagement rings rather than geometric rhombi.
- **The Solution**:
  - Synonym merge: `rhombus` $\to$ `diamond`.
  - Dropped classes: Out-of-taxonomy folders are filtered during catalog ingestion.
  - Heuristic filtering + VLM check: Filter QuickDraw diamond drawings with interior facets/bands.

---

## 4. Plugging Synthetic Data into the Pipeline

Synthetic data is a first-class citizen in the integration schema:
1. **Procedural Vector Engine**: A Python module using `cairo` or `Pillow.ImageDraw` creates parameterized geometric primitives ($n$-gons, stars, ellipses, rounded rectangles).
2. **Schema Alignment**:
   - Synthetic images are assigned a deterministic ID: `synth_<class>_<seed>`.
   - In the SQLite `Image` table:
     - `source_id = 'procedural_synthetic'`
     - `domain = 'synthetic'`
     - `split = 'train'` (Strict constraint: synthetic data is **never** added to the test split).
3. **Dynamic On-The-Fly Generation**:
   - Instead of saving millions of synthetic files to disk, the PyTorch `Dataset` generates synthetic samples on-demand when `domain == 'synthetic'`, ensuring infinite variation in rotation, stroke thickness, and scale.

---

## 5. Plugging Data Augmentation into the Pipeline

Augmentation expands training diversity while preserving geometric semantics:
1. **Albumentations Pipeline**:
   ```python
   import albumentations as A
   from albumentations.pytorch import ToTensorV2

   train_transform = A.Compose([
       A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=45, p=0.7),
       A.Affine(shear=(-15, 15), p=0.5),
       A.GaussianBlur(blur_limit=(3, 5), p=0.3),
       A.GaussNoise(var_limit=(10.0, 50.0), p=0.4),
       A.Normalize(mean=[0.5], std=[0.5]),
       ToTensorV2(),
   ])
   ```
2. **Integration Guarantee**:
   - Augmentation is applied inside `__getitem__` during training only.
   - For offline generated augmentations, entries are logged in `AugmentationRecord` with `parent_id` and exact parameter dictionaries for 100% reproducibility.

---

## 6. Preferred TikZ Diagram Code for Section C (LaTeX)

The following TikZ code should be added to `phase1_report.tex` to visually convey this integration process:

```latex
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=0.8cm and 1.2cm,
  box/.style={draw, thick, rounded corners=2pt, fill=gray!8, font=\footnotesize, align=center, inner sep=5pt},
  flow/.style={-Latex, thick},
]
\node[box] (raw) {Raw Multi-Source Data\\(Sketches, Renders, Masks)};
\node[box, right=of raw] (geo) {Geometric Standardization\\(Aspect-Preserving Resize, Pad to $64\times64$)};
\node[box, right=of geo] (photo) {Photometric Normalization\\(Grayscale BT.601, Polarity Align, $[0,1]$)};
\node[box, below=1.2cm of photo] (sql) {Unified SQLite Catalog\\(Metadata, Deduplication, Train/Val/Test Split)};
\node[box, left=of sql] (synth) {Procedural Synthetic Generator\\(Pillow/Cairo On-The-Fly)};
\node[box, left=of synth] (loader) {Streaming Data Loader\\+ Albumentations Augmentation};

\draw[flow] (raw) -- (geo);
\draw[flow] (geo) -- (photo);
\draw[flow] (photo) -- (sql);
\draw[flow] (sql) -- (synth);
\draw[flow] (synth) -- (loader);
\end{tikzpicture}
\caption{Comprehensive Data Integration & Preprocessing Pipeline.}
\label{fig:integration_pipeline}
\end{figure}
```

---

## 7. Action Items & Verification
- [ ] Implement aspect-preserving letterbox padding function in `scripts/preprocess.py`.
- [ ] Add polarity detection and grayscale conversion routines.
- [ ] Insert the expanded Section C text and TikZ diagram into `phase1_report.tex`.
- [ ] Re-run `scripts/check_fds.py` to confirm that schema constraints hold across all integrated rows.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Opus 5.5's deep research looked for citable sources for each technique (plan 08). The implementation was checked by looking at the output images.

## Our decision

We implemented it with changes. BT.601 grayscale was replaced by an RGB-distance shape mask, which handles random background colours (plan 02 status). Synthetic and augmented images plug in after the split, on the train side only.

## Measured effect

12,490 of 18,500 images (67.5%) were redrawn as outlines. No model at this stage.
