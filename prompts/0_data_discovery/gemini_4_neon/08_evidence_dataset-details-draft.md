# 0_data_discovery - First draft of the dataset inventory

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 or earlier
- Worksheet entries: S01
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is the user's own todo entry, verbatim, which was handed to the LLM as the task; the exact chat message was not saved. The Response quotes the LLM's saved output files verbatim.
- Reconstructions of the same entries: [S01](../claude_opus/01_four-public-sources.md), [S01](01_four-public-sources.md)

## Prompt (the user's todo entry, verbatim)

```text
- [x] [more details about data set used  .](plan/01_dataset_details.md)
```

_Kept as plain text: the links inside it point to the local plan folder, which is not in the repo. The linked plan is quoted below._

## Response (saved output, verbatim)

### `01_dataset_details.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE in Section B with measured numbers. Note: several figures in this draft were wrong (see 06); the report uses data_set/unified/summary.json instead.

# Plan 01: Detailed Dataset Breakdown & Documentation (Section B Enhancement)

## 1. Overview & Objectives
The goal of this plan is to establish an exhaustive, well-structured inventory of all datasets collected and utilized for the **Unified 2D Shape Classifier** project. This documentation directly addresses the requirements of **Section B (Summary of Collected Datasets)** in `phase1_report.tex`, ensuring full transparency regarding data provenance, licenses, dimensional characteristics, table schemas, and class distributions.

---

## 2. Inventory of Current Datasets

### 2.1 Quick, Draw! Subset (Google Creative Lab)
- **Domain**: Hand-drawn sketches.
- **Source URL**: `https://github.com/googlecreativelab/quickdraw-dataset`
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Installed Location**: `data_set/quickdraw/subset/`
- **File Format**: NDJSON (Newline Delimited JSON) containing vector drawing stroke sequences `[[x], [y], [t]]`.
- **Installed Subset Statistics**:
  - 7 categories matching target taxonomy: `circle`, `diamond`, `hexagon`, `octagon`, `square`, `star`, `triangle`.
  - Exactly 500 drawings sampled per category ($7 \times 500 = 3,500$ drawings).
  - Total on-disk footprint: ~1.0 MB.
- **Attributes per Record**:
  - `key_id`: 64-bit unique drawing ID.
  - `word`: Label name.
  - `recognized`: Boolean indicating whether QuickDraw's AI engine recognized the sketch.
  - `timestamp`: UTC drawing timestamp.
  - `countrycode`: ISO 2-letter country code of user.
  - `drawing`: List of stroke coordinate arrays.
- **Preprocessing Transformation**:
  - Rasterization of vector stroke paths onto a $28 \times 28$ bitmap (standard QuickDraw grid), then standardized into $64 \times 64$ anti-aliased single-channel images.

---

### 2.2 Geometric Shapes Mathematics (reevald / Kaggle)
- **Domain**: Clean digital renders.
- **Source URL**: `https://www.kaggle.com/datasets/reevald/geometric-shapes-mathematics`
- **License**: CC0 Public Domain.
- **Installed Location**: `data_set/test/`
- **File Format & Dimensions**: JPEG images, native resolution $224 \times 224 \times 3$ (RGB).
- **Class Breakdown & Ingestion Actions**:
  - Total: 4,000 files across 8 class folders (500 images per class):
    1. `circle` (500) $\to$ mapped to `circle`.
    2. `square` (500) $\to$ mapped to `square`.
    3. `triangle` (500) $\to$ mapped to `triangle`.
    4. `rectangle` (500) $\to$ mapped to `rectangle`.
    5. `rhombus` (500) $\to$ mapped as synonym to `diamond`.
    6. `trapezoid` (500) $\to$ dropped (outside target taxonomy).
    7. `kite` (500) $\to$ dropped (outside target taxonomy).
    8. `parallelogram` (500) $\to$ dropped (outside target taxonomy).
  - Usable images for target taxonomy: 2,500 images.
  - Total on-disk size: 25.1 MB.

---

### 2.3 Geometric Shapes Dataset (dineshpiyasamara / Kaggle)
- **Domain**: Synthetic black-and-white 2D geometric masks/renders.
- **Source URL**: `https://www.kaggle.com/datasets/dineshpiyasamara/geometric-shapes-dataset`
- **License**: CC0 Public Domain.
- **Installed Location**: `data_set/geometric shapes dataset/`
- **File Format & Dimensions**: PNG images, native resolution $200 \times 200 \times 1$ (Grayscale).
- **Class Breakdown**:
  - `Circle`: 10,000 images.
  - `Square`: 10,000 images.
  - `Triangle`: 10,000 images.
  - Total: 30,000 images (~28 MB uncompressed).
- **Role in Project**:
  - High-volume benchmark source for basic shapes, providing strong baseline statistical power.

---

### 2.4 Procedural Synthetic Generation
- **Domain**: Procedural vector rendering (pycairo / Pillow).
- **Target Size**: ~2,250 – 5,000 images across all 10 target classes.
- **Parameters Generated**:
  - Scale ($r \in [10, 28]$ px), rotation ($\theta \in [0, 360^\circ]$), stroke thickness ($w \in [1, 4]$ px), stroke color, fill/no-fill, center jitter ($\Delta x, \Delta y \in [-4, 4]$).
  - Target 10 classes: `circle`, `ellipse`, `triangle`, `square`, `rectangle`, `pentagon`, `hexagon`, `octagon`, `star`, `diamond`.
- **Purpose**: Balance under-represented classes (especially `ellipse`, `pentagon`, `hexagon`, `octagon`) and systematically evaluate synthetic-to-real transfer.

---

## 3. SQLite Relational Schema & Attribute Dictionary

To ensure functional dependencies and structured queries, metadata is managed in a normalized SQLite database.

```sql
CREATE TABLE Source (
    source_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    license VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL -- 'sketch', 'render', 'photo', 'synthetic'
);

CREATE TABLE Label (
    label_id VARCHAR(50) PRIMARY KEY,
    label_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE LabelMapping (
    source_id VARCHAR(50) NOT NULL,
    original_label VARCHAR(100) NOT NULL,
    label_id VARCHAR(50),
    PRIMARY KEY (source_id, original_label),
    FOREIGN KEY (source_id) REFERENCES Source(source_id),
    FOREIGN KEY (label_id) REFERENCES Label(label_id)
);

CREATE TABLE Image (
    image_id VARCHAR(100) PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL,
    label_id VARCHAR(50) NOT NULL,
    file_path TEXT NOT NULL,
    native_width INT NOT NULL,
    native_height INT NOT NULL,
    channels INT NOT NULL,
    split VARCHAR(10) NOT NULL, -- 'train', 'val', 'test'
    FOREIGN KEY (source_id) REFERENCES Source(source_id),
    FOREIGN KEY (label_id) REFERENCES Label(label_id)
);

CREATE TABLE AugmentationRecord (
    aug_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id VARCHAR(100) NOT NULL,
    parent_id VARCHAR(100) NOT NULL,
    transform_type VARCHAR(50) NOT NULL,
    parameters_json TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES Image(image_id)
);
```

---

## 4. Updates Required in `phase1_report.tex` (Section B)

1. **Table 1 (`tab:stats`) Expansion**:
   - Explicitly list each distinct source: Quick, Draw!, Kaggle (reevald), Kaggle (dineshpiyasamara), and Synthetic generator.
   - Include columns: Source Name, Domain, Raw Files, Usable Taxonomy Files, Native Dimensions, Channels, Size (MB), License.
2. **Text Narrative**:
   - Detail the sampling strategy from QuickDraw (why 500 samples per class were drawn from the 100k+ pool).
   - Document the drop rate of Kaggle reevald (1,500 dropped out of 4,000 due to non-taxonomy shapes: trapezoid, kite, parallelogram).
   - Document the inclusion of Dinesh Piyasamara's 30k shape dataset to support high-confidence training on fundamental polygons.

---

## 5. Action Items & Verification Checklist
- [ ] Verify MD5 hashes and file integrity across all installed datasets.
- [ ] Run `scripts/check_fds.py` with the updated rows to ensure all 6 functional dependencies continue to hold with 100% adherence.
- [ ] Update Table 1 and Section B in `phase1_report.tex` with the verified numbers.
- [ ] Recompile PDF using `pdflatex phase1_report.tex` to confirm formatting integrity.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Plan 06 fact-checked this draft against each dataset's source page. Several figures were wrong.

## Our decision

We did not use the draft's numbers. Section B of the Phase 1 report uses the measured numbers in `data_set/unified/summary.json` instead (status line of plan 01).

## Measured effect

No model at this stage. The report's dataset statistics were replaced with measured ones.
