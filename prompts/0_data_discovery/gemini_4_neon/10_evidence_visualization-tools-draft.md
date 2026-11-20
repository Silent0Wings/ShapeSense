# 0_data_discovery - Draft toolset for data visualization

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 or earlier
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is the user's own todo entry, verbatim, which was handed to the LLM as the task; the exact chat message was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (the user's todo entry, verbatim)

```text
- [x] [add tools for data visualisation to check the data sets](plan/05_data_visualization_tools.md)
```

_Kept as plain text: the links inside it point to the local plan folder, which is not in the repo. The linked plan is quoted below._

## Response (saved output, verbatim)

### `05_data_visualization_tools.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** SUPERSEDED by 09; Tier 1 implemented in scripts/audit_dataset.py.

# Plan 05: Comprehensive Dataset Visualization & Exploratory Analysis Tools (Section E & Report Figures Enhancement)

## 1. Executive Summary & Purpose
Data visualization is an essential discipline in modern data science engineering. For the **Unified 2D Shape Classifier**, visual inspection tools serve three critical functions:
1. **Pipeline Validation**: Visually verifying that aspect-preserving padding, grayscale conversion, and contrast polarity normalization do not corrupt geometric properties.
2. **Dataset Auditing & Exploratory Data Analysis (EDA)**: Understanding sample distributions, class balances, resolution variations, and foreground-to-background contrast ratios across heterogeneous sources.
3. **Manifold & Domain Gap Analysis**: Projecting high-dimensional shape representations into 2D/3D embeddings (via PCA, t-SNE, and UMAP) to evaluate whether domain gaps (sketches vs. renders vs. synthetic) are bridgeable by the classifier.

---

## 2. Visualization Toolset Architecture

```
+--------------------------------------------------------------------------------------------------+
|                                    DATA VISUALIZATION SUITE                                      |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  [Tool 1: Interactive EDA Dashboard]          [Tool 2: Publication Grid Generator]              |
|  - Framework: Streamlit / Gradio              - Framework: Matplotlib / Seaborn                  |
|  - Interactive source & class filter          - High-res LaTeX figure exports                    |
|  - Dual view: Raw image vs Preprocessed       - $10 \times 10$ shape taxonomy matrix             |
|  - QA Flag Browser (inspect flagged images)   - Class & domain distribution histograms           |
|                                                                                                  |
|  [Tool 3: Statistical Property Profiler]      [Tool 4: Manifold & Embedding Explorer]            |
|  - Resolution / aspect ratio scatter plots    - Methods: PCA, t-SNE, UMAP                        |
|  - Pixel intensity & foreground density plots - Feature extractors: Contour moments & ResNet     |
|  - Outlier detection threshold visualizer     - Domain-overlap clustering plots                  |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. Tool Specifications & Features

### 3.1 Tool 1: Interactive Streamlit Dataset Explorer (`scripts/dashboard.py`)
- **Key Features**:
  - **Filter Sidebar**: Filter by `source_id`, `domain` (render, sketch, synthetic, photo), `class_id`, and `split`.
  - **Side-by-Side Preprocessing Inspection**:
    - Left column: Original raw image with native resolution and channels.
    - Right column: Preprocessed $64 \times 64$ tensor with padding, grayscale conversion, and normalization overlay.
  - **Pixel Intensity Profiler**: Real-time histogram showing pixel intensity distribution $[0.0, 1.0]$.
  - **Quality Audit Gallery**: Quickly browse samples flagged by OCR (text leaks) or Mistral Vision (mislabeling/corruption) for human confirmation.

---

### 3.2 Tool 2: Publication Figure Generator (`scripts/generate_report_figures.py`)
Produces polished, publication-ready vector and raster figures for `phase1_report.tex`:
1. **$10 \times 4$ Domain Comparison Grid**:
   - Rows: 10 target classes (`circle` $\dots$ `diamond`).
   - Columns: Clean render (Kaggle), Sketch (QuickDraw), Procedural synthetic (Pillow), Real scan/photo (Mendeley).
2. **Distribution Plots**:
   - Grouped bar chart comparing image counts per class broken down by domain.
   - Stacked bar chart showing train vs. validation vs. held-out test split allocations.

---

### 3.3 Tool 3: Dimensionality Reduction & Manifold Explorer (`scripts/visualize_embeddings.py`)
- **Objective**: Visualize whether geometric shapes form distinct clusters in feature space regardless of source domain.
- **Workflow**:
  1. Extract feature vectors for a balanced sample of 2,000 images using:
     - Spatial geometric descriptors: Hu Moments + Contour Fourier Descriptors.
     - Deep features: Output of a pre-trained frozen ResNet-18 or DINO backbone.
  2. Compute 2D projections via **UMAP** (Uniform Manifold Approximation and Projection) and **t-SNE**.
  3. Plot scatter plots color-coded by shape class, with marker shapes denoting the domain (circle = render, triangle = sketch, star = synthetic).
- **Insight Provided**: Demonstrates whether the unified dataset creates semantically coherent geometric clusters across diverse visual styles.

---

## 4. Integration into `phase1_report.tex` (Section E Update)

Update Table 3 (Planned tools by role) in `phase1_report.tex` with the visualization and QA tools:

```latex
\begin{table}[H]
\centering
\caption{Planned tools by role across the data lifecycle.}
\label{tab:tools}
\small
\begin{tabularx}{\linewidth}{@{}p{4.5cm} X@{}}
\toprule
Role & Tool \\
\midrule
Synthetic rendering & Pillow, pycairo \\
Sketch rasterization & Custom Python NDJSON parser \\
Data augmentation & Albumentations \\
Deep learning & PyTorch with custom on-demand streaming loader \\
Relational serving & SQLite \\
Quality assurance & Mistral Vision / Pixtral 12B (VLM), Tesseract OCR \\
Data deduplication & imagehash (pHash) \\
Metadata \& schema validation & pandas, pandera \\
Geometric feature extraction & OpenCV (\texttt{findContours}, Hu Moments), Shapely \\
Interactive EDA \& QA inspection & Streamlit, Gradio \\
Report visualization \& figures & Matplotlib, Seaborn \\
Manifold learning \& clustering & scikit-learn (PCA, t-SNE), umap-learn \\
Version control & Git, DVC \\
\bottomrule
\end{tabularx}
\end{table}
```

---

## 5. Action Items & Verification
- [ ] Create `scripts/generate_report_figures.py` to auto-generate sample grids and distribution plots.
- [ ] Implement `scripts/dashboard.py` with Streamlit for interactive local inspection.
- [ ] Add the expanded visualization tool descriptions and updated Table 3 to `phase1_report.tex`.
- [ ] Compile LaTeX report and verify visual presentation.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Opus 5.5's deep research checked each tool against its documentation and weighed setup cost against project scope (plan 09).

## Our decision

Superseded by plan 09. Only Tier 1 (Matplotlib, `scripts/audit_dataset.py`) was built.

## Measured effect

The report figures (class and source chart, before and after grid, fill-to-outline, outliers) come from Tier 1.
