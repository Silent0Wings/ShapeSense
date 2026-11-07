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
