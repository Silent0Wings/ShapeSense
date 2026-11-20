# 1_data_integration - Record the findings in the todo list and plans

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is verbatim from the session log (recorded in `docs/prompts.csv` of the snapshot); the reply was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt P06 (verbatim, 2026-10-19)

> did you update the plans ? and did you take any steps ? / ok at least add your finidngs as new entirs in the todo md file + plan md for each

_Source: Claude Code session 2026-10-19, user messages 62-63. Confidence: medium. Matches the commit title (dataset findings and analysis documentation)._

## Response (the reply was not saved; the work it produced, verbatim)

### `docs/findings.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Phase 1 findings

All numbers are from the build of 2026-10-19
(`python scripts/build_unified_dataset.py`). Sources and licenses:
[source.md](source.md).

## 1. Dataset claims (verified on the source pages)

| Source | Draft said | Actually |
|---|---|---|
| swastikarajkower (Kaggle) | MIT, ~5,000 images | a 1,200-row CSV, no images, no license |
| Mendeley d35tjjgjnx | real photos, pentagon/hexagon/octagon | 380,000 synthetic images, 7 base shapes, none of those |
| Mendeley ypfcrfxjgk | same | 9,000 synthetic, circles/triangles/stripes only |
| Dinesh (Kaggle) | CC0, grayscale | license "Unknown", RGB |
| Hand-drawn (GitHub) | ~1,200 images, 5 classes | 27,292 images, 4 classes (rectangle, ellipse, triangle, other) |

Lesson: verify dataset facts on the source page, not secondhand summaries.

## 2. Sources used

| Source | Images on disk | Native | Classes used |
|---|---|---|---|
| Quick, Draw! (subset) | 3,500 (7 NDJSON) | vector strokes | 7 of 7 |
| Kaggle reevald | 20,000 | 224x224 RGB JPG | 5 of 8 |
| Mendeley El Korchi | 90,000 | 200x200 RGB PNG | 7 of 9 |
| Hand-drawn (GitHub) | 27,292 (+20,005 vertex CSVs) | 70x70 RGBA PNG | 3 of 4 |

Excluded: Dinesh (license "Unknown"; only circle/square/triangle, already covered).

## 3. Incompatibilities found and how they are fixed

| Problem | Fix |
|---|---|
| 4 native sizes (256, 224, 200, 70) | crop to shape, pad to square, resize to 64x64 |
| RGB, RGBA, vector | flatten alpha on white; rasterize strokes 3 px wide |
| random background colors (El Korchi, Dinesh) | shape = pixels far from background color, adaptive threshold |
| filled vs outline vs dashed | closed shapes redrawn as 2-px outline; open/dashed kept |
| shapes down to ~10 px | crop before resize |
| label names differ | label map (rhombus -> diamond; drop kite, trapezoid, parallelogram, heptagon, nonagon, other) |

12,490 of 18,500 images (67.5%) were redrawn as outlines.
Residual: reevald's dashed outlines still hint at the source.

## 4. Bugs caught by looking at the output (counts alone hid them)

1. Thick rings became double lines -> fill holes before deciding closed vs open.
2. Hollow-centred stars kept solid arms -> same fix.
3. 333 visible low-contrast shapes rejected as "blank" -> contrast measured
   as strongest local contrast (3x3 median filter), floor lowered to 8.
4. Test set had only 34 pentagons -> split assigns near-duplicate groups
   largest-first to the split furthest below target.

## 5. Unified dataset

- 18,500 images, 10 classes, 12.1 MB, 64x64 single channel PNG.
- Split by near-duplicate group: 12,761 train / 2,890 val / 2,849 test.
- Capped at 1,000 per source/class.
- SQLite catalog: 5 tables, 18 columns (matches the ERD).

## 6. Null data (schema-level)

| Missing field | Handling | Images |
|---|---|---|
| label_id (no matching class) | dropped | 34,787 |
| label (no metadata: reevald, El Korchi, hand-drawn) | from folder / file name | all |
| width, height (Quick, Draw! vectors) | 256x256 canvas | 3,500 |
| per-image license | from Source table | all |
| license "Unknown" (Dinesh) | source excluded | 30,000 |

## 7. Outliers and duplicates

- No contrast: 1 rejected.
- Exact duplicates: 32 removed before the split.
- Near duplicates (pHash, Hamming <= 2): 2,972 images grouped, each group kept in one split.
- Low diversity: El Korchi pentagon/star/triangle collapse into ~4
  near-identical templates each once standardized (largest pentagon group: 175).
- Not filtered: Quick, Draw! `diamond` includes gemstone drawings.

## 8. Functional dependencies (`scripts/discover_fds.py`)

27 minimal exact FDs over 11 columns, LHS of 1-2 columns. No approximate
FDs under 5% error. Discovered (not designed):

- `original_label -> label_id`: no cross-source label conflicts; the
  designed key (source_id, original_label) is larger than needed.
- `native_width -> source_id`: image size alone reveals the source
  (shortcut removed by resizing).
- `(source_id, label_id) -> original_label`: one name per class per source.

Injected wrong label_id: caught (`scripts/check_fds.py`).

## 9. Label set and augmentation rule (`scripts/taxonomy.py`)

10 fixed classes: circle, ellipse, triangle, square, rectangle, pentagon,
hexagon, octagon, star, diamond. Ambiguous pairs resolved by definition
(square vs diamond, square vs rectangle, circle vs ellipse).
Shear and non-uniform scaling change the class for circle, ellipse,
square, rectangle, diamond, so they are disabled for those.

## 10. Citation correction

arXiv 2108.02497 is Lones, "How to avoid machine learning pitfalls",
not Whalen et al. (misattributed in the research notes).

## Reproduce

```
python scripts/build_unified_dataset.py   # dataset + summary.json
python scripts/check_fds.py               # designed FDs + injected test
python scripts/discover_fds.py            # FD discovery
python scripts/audit_dataset.py           # report figures
.\build.ps1                               # PDF
```
````

### `ignore/todo.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
- [x] [more details about data set used  .](plan/01_dataset_details.md)
  - done: Section B now has measured stats for all 4 used sources (files, tables, columns, MB, classes) + the built unified set, a class/source chart, and an "evaluated and not used" paragraph. Numbers come from `data_set/unified/summary.json`.
- [x] [need more cases and example covered for how we we do data integration  .for handling the edge cases normalisation , dimension difference , gray scale vs color ranges , prefered diagram examples , and how the syntethic data plug into this , and how augementation plug in into this cas  in section C .](plan/02_data_integration_cases.md)
  - done: Section C "Integration cases" table (dimensions, color mode, background/polarity, fill vs outline, scale, label names, duplicates), fill-to-outline filter + figure, before/after figure. Synthetic and augmentation plug in after the split, train side only (Sections B, D).
- [x] [need more data sets to include in the repport  .](plan/03_more_datasets.md)
  - done: El Korchi (pentagon/hexagon/octagon/star) and hand-drawn (ellipse) added and used; all 10 classes now have real data.
- [x] ~~[add todo that we are using mistral vision + ocr as data sanity check .](plan/04_mistral_vision_ocr_sanity_check.md)~~
  - skipped by decision: no OCR / AI-based checks in this project.
- [x] [add tools for data visualisation to check the data sets](plan/05_data_visualization_tools.md)
  - done: `scripts/audit_dataset.py` (Matplotlib) produces the class/source chart, before/after grid, fill-to-outline and outlier figures used in the report.
- [x] new data sets were added handle them , [text](../data_set) + [text](../docs/source.md)
  - done: duplicates removed (verified by MD5), folders renamed to source ids, `docs/source.md` maps every folder to its origin. Dinesh kept on disk but excluded (license "Unknown").
- [x] deep-research found 4 of 5 drafted dataset claims are wrong, including one "dataset" that's actually a CSV with no images and is currently miscited in the real report's bibliography — needs correcting before submission. [plan/06_dataset_claims_correction.md](plan/06_dataset_claims_correction.md)
  - done: bibliography and Section B corrected (swastikarajkower = CSV, Mendeley sets = synthetic, Dinesh license = Unknown).
- [x] deep-research found a new CC BY 4.0 dataset that covers pentagon/hexagon/octagon/star in one source, plus a fallback for ellipse (dSprites) — evaluate for inclusion. [plan/07_new_candidate_datasets.md](plan/07_new_candidate_datasets.md)
  - done: El Korchi included. dSprites not needed: hand-drawn set covers ellipse.
- [x] deep-research grounded the data integration techniques (letterboxing, BT.601 grayscale, pHash dedup, and the critical augment-only-after-split rule) in real, citable sources, replacing the uncited version in plan 02. [plan/08_integration_techniques_grounded.md](plan/08_integration_techniques_grounded.md)
  - done: implemented in `scripts/standardize.py` / `build_unified_dataset.py`; pHash (Zauner) and augment-after-split (Lones) cited in Section D.
- [x] deep-research produced a tiered, cost-aware visualization/auditing toolset grounded in real docs, replacing the uncited version in plan 05. [plan/09_visualization_tools_grounded.md](plan/09_visualization_tools_grounded.md)
  - done: Tier 1 (Matplotlib) implemented; Tier 2/3 not needed for Phase 1.
- [x] fix the label set as the actual classification labels (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond)
  - done: `scripts/taxonomy.py` is the single source of truth; definitions table in Section A; shear / non-uniform scale disabled for angle-defined classes (Section D).

Still open (needs you):
- [ ] fill in the 6 student IDs in `phase1_report.tex` (Table 1)
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Every number in findings.md comes from the 2026-10-19 build (`python scripts/build_unified_dataset.py`).

## Our decision

Findings were added as new todo entries plus one plan file for each.

## Measured effect

Documentation only.
