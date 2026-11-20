# 2_data_preparation/cleaning - Draft: QA sanity check with Mistral Vision and OCR

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19 or earlier
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is the user's own todo entry, verbatim, which was handed to the LLM as the task; the exact chat message was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (the user's todo entry, verbatim)

```text
- [x] ~~[add todo that we are using mistral vision + ocr as data sanity check .](plan/04_mistral_vision_ocr_sanity_check.md)~~
```

_Kept as plain text: the links inside it point to the local plan folder, which is not in the repo. The linked plan is quoted below._

## Response (saved output, verbatim)

### `04_mistral_vision_ocr_sanity_check.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** SKIPPED by decision: no OCR or AI-based checks in this project.

# Plan 04: Automated Data Sanity & Quality Assurance Pipeline via Mistral Vision & OCR (Section D & E Enhancement)

## 1. Executive Summary & Problem Formulation
In real-world computer vision datasets—especially multi-source and crowd-sourced collections like Quick, Draw!—data quality issues are pervasive:
1. **Shortcut Learning (Clever Hans effect)**: Images from online repositories often contain watermark text, class labels, or page numbers burned directly into the pixel grid (e.g., a diagram labeled "Figure 1: Equilateral Triangle"). Neural networks tend to exploit these text features instead of learning geometric invariants.
2. **Crowd-sourced Semantic Noise**: In Quick, Draw!, players frequently drew non-geometric items under the `diamond` prompt (e.g., faceted jewelry rings, baseball diamonds) or drew faces inside circles.
3. **Corrupted or Incomplete Renderings**: Blank canvases, open contours, or truncated file bytes.

To address these without requiring infeasible manual inspection of 40,000+ images, we design an automated **Dual-Engine QA Sanity Check Pipeline** combining **Optical Character Recognition (OCR)** and **Mistral Vision (VLM)**.

---

## 2. Dual-Engine Architecture

```
                  +---------------------------------------+
                  |         Raw Candidate Image           |
                  +---------------------------------------+
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
        +--------------------------+     +--------------------------+
        |     ENGINE 1: OCR        |     |  ENGINE 2: MISTRAL VLM   |
        |  (Tesseract / EasyOCR)   |     |  (Pixtral / Mistral API) |
        +--------------------------+     +--------------------------+
                     |                                 |
        Text string detected?            Zero-shot geometric prompt
        - Check for class label leak     - Output: JSON {pred, conf,
        - Check for watermarks             is_valid, reason}
                     |                                 |
                     +----------------+----------------+
                                      |
                                      v
                  +---------------------------------------+
                  |          ARBITRATION & QA LOG         |
                  |  - If text detected: FLAG_LEAK        |
                  |  - If VLM conf > 0.85 & mismatch:     |
                  |    FLAG_MISLABEL                      |
                  |  - If is_valid == False: FLAG_CORRUPT |
                  +---------------------------------------+
                                      |
                                      v
                  +---------------------------------------+
                  |         SQLite QualityAudit           |
                  |   Store audit status in database      |
                  +---------------------------------------+
```

---

## 3. Engine Specifications & Implementation

### 3.1 Engine 1: OCR Text & Watermark Detection
- **Tools**: `pytesseract` / `easyocr`.
- **Target**: Scan image tensors for text characters, numerical labels, or watermark glyphs.
- **Rules**:
  1. If any detected token matches any shape label name (e.g. `"circle"`, `"triangle"`, `"square"`), flag immediately with `FLAG_LABEL_LEAK`.
  2. If general alphanumeric text is detected with confidence $> 0.6$, flag with `FLAG_WATERMARK` for background inpainting or exclusion.

```python
import pytesseract
from PIL import Image

def run_ocr_check(image_path: str, labels: list[str]) -> dict:
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img).strip().lower()
    
    leaked_labels = [l for l in labels if l.lower() in text]
    has_text = len(text) > 0
    
    return {
        "has_text": has_text,
        "detected_text": text,
        "leaked_labels": leaked_labels,
        "flag_leak": len(leaked_labels) > 0
    }
```

---

### 3.2 Engine 2: Mistral Vision (VLM) Geometric Sanity Check
- **Model**: Mistral Vision / Pixtral 12B (accessible via Mistral API or local vLLM).
- **Prompt Design**:
  ```text
  You are an expert geometric data validator. Analyze the attached 2D image.
  Identify the primary 2D shape from this taxonomy:
  ['circle', 'ellipse', 'triangle', 'square', 'rectangle', 'pentagon', 'hexagon', 'octagon', 'star', 'diamond', 'none_or_corrupted'].

  Respond ONLY with a valid JSON object matching this schema:
  {
    "predicted_shape": "<shape_name>",
    "confidence": <float between 0.0 and 1.0>,
    "is_valid_geometric_shape": <true/false>,
    "rejection_reason": "<optional explanation if corrupted, jewelry, or ambiguous>"
  }
  ```
- **Evaluation Logic**:
  - If `is_valid_geometric_shape == False` $\implies$ discard image (e.g., drawing of a hand, ring, or blank frame).
  - If `predicted_shape != ground_truth_label` and `confidence >= 0.85` $\implies$ flag for mislabeling review.

---

## 4. Database Schema for QA Audit

Audit results are recorded in SQLite to ensure transparent tracking:

```sql
CREATE TABLE QualityAudit (
    image_id VARCHAR(100) PRIMARY KEY,
    ocr_has_text BOOLEAN NOT NULL DEFAULT 0,
    ocr_detected_text TEXT,
    vlm_predicted_label VARCHAR(50),
    vlm_confidence REAL,
    vlm_is_valid BOOLEAN,
    vlm_rejection_reason TEXT,
    qa_status VARCHAR(20) NOT NULL DEFAULT 'PASSED', -- 'PASSED', 'FLAGGED_LEAK', 'FLAGGED_MISLABEL', 'FLAGGED_CORRUPT'
    FOREIGN KEY (image_id) REFERENCES Image(image_id)
);
```

---

## 5. Cost & Performance Optimization (Tiered Filtering)
Running VLM inferences across 40,000 images would be computationally heavy. We use a **tiered filter**:
1. **Tier 1 (Fast OpenCV Heuristics, 100% of images)**: Filter out near-zero foreground ratio ($< 1\%$) and pure solid color images.
2. **Tier 2 (OCR Scan, 100% of images)**: Fast CPU OCR check; flags text leaks.
3. **Tier 3 (Mistral Vision Sampling & Discrepancy Audit, ~10-15% of images)**:
   - Run on 100% of Quick, Draw! `diamond` drawings (high jewelry false-positive rate).
   - Run on statistical outliers identified by contour Fourier descriptors.
   - Run on a 5% random audit sample across all other sources.

---

## 6. Integration into `phase1_report.tex`

1. **Section D (Data Preparation - Outlier Detection)**:
   - Add subsection: *"Automated Quality Assurance via OCR and Vision-Language Models (Mistral Vision)"*.
   - Describe the detection of text watermarks and the semantic pruning of invalid crowd-sourced sketches.
   - Include a figure showing before/after examples of caught anomalies (e.g. a diamond ring sketch vs. geometric diamond, text watermark caught by OCR).
2. **Section E (Tools and Systems)**:
   - Add `Mistral Vision / Pixtral` (VLM data validation) and `Tesseract OCR` (watermark & label leakage detection) to Table 3.

---

## 7. Action Items & Verification
- [ ] Create `scripts/sanity_check.py` implementing the OCR and Mistral API verification harness.
- [ ] Test the script on a subset of 50 sample images including synthetic test conflicts.
- [ ] Update Sections D and E of `phase1_report.tex` with methodology and tool descriptions.
- [ ] Compile and verify the LaTeX report formatting.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Checked against the course wording. 'Detect' means a data-quality check, not OCR (P02 in the functional-dependencies file).

## Our decision

Skipped by our decision: no OCR or AI-based checks in this project (plan 04 status). The draft did flag Quick, Draw! diamonds drawn as jewellery. That issue was only fixed later by visual review (F01, C01).

## Measured effect

None. The plan was not implemented.
