# 6_verification/dataset_awareness - Four sources, sandboxed replication
- LLM: Gemini 4 Neon (`gemini-4-neon-medium`), Antigravity CLI `agy` in print mode with `--sandbox --new-project`, started from an empty scratch folder outside the repository
- Category: Pipeline vs. direct LLM prediction (verification)
- Date: 2026-11-20

A second, independent run of the same eight prompts, word for word as in the Claude run
([../claude_opus/01_four-sources.md](../claude_opus/01_four-sources.md)). The session had no project files: it started
in an empty folder, in the sandbox, and was told that using any tool would void the test. The first run
([01_four-sources.md](01_four-sources.md)) was made in Antigravity inside the workspace. The reply below is unedited.

## Prompt

The eight prompts of [PROMPT.md](../PROMPT.md) (1A to 1D describe, 2A to 2D complete), with the same real row and folder
paths as the Claude run.

## Response

Model: Gemini 4 Neon (Medium)

### Prompt 1A

> Without searching the web, describe the dataset "Quick, Draw! dataset" (https://github.com/googlecreativelab/quickdraw-dataset). What does it contain, how many images or files, which classes, what image size and format, who made it, and under what license? If you do not know it, say so instead of guessing.

- **What it contains**: Over **50 million** hand-drawn vector doodles collected from players of the online game *Quick, Draw!*, where participants were given 20 seconds to draw a prompted object or concept. Each drawing includes stroke trajectories and metadata (such as the prompted word, country code, timestamp, whether the game's classifier recognized it, and a unique key ID).
- **Number of images / files**: ~50 million drawings in total, organized into **345 files per data format** (one file per class). The exact number of drawings varies by class (typically ~100,000–200,000+ per class).
- **Classes**: **345 categories** of everyday objects, animals, shapes, and concepts (e.g., `airplane`, `apple`, `bicycle`, `cat`, `circle`, `house`, `star`, `triangle`, etc.).
- **Image size and format**: Distributed in four formats:
  1. **Raw files (`.ndjson`)**: Full vector stroke sequences with original coordinates and per-point timestamps, plus metadata.
  2. **Simplified drawings (`.ndjson`)**: Vector strokes aligned to the top-left, scaled to a **256×256** bounding box (values in `0–255`), resampled, and simplified using the Ramer–Douglas–Peucker algorithm (`epsilon = 2.0`), without timestamps.
  3. **Binary files (`.bin`)**: Custom compact binary encoding of the simplified drawings.
  4. **NumPy bitmaps (`.npy`)**: Simplified drawings rendered as **28×28 grayscale** raster images (`uint8`, stored as flattened 784-element rows, similar to MNIST).
- **Creator**: **Google Creative Lab** (with Google AI / Data Arts Team).
- **License**: **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

---

### Prompt 1B

> Without searching the web, describe the dataset "Geometric Shapes Mathematics (Kaggle, reevald)" (https://www.kaggle.com/datasets/reevald/geometric-shapes-mathematics). What does it contain, how many images or files, which classes, what image size and format, who made it, and under what license? If you do not know it, say so instead of guessing.

I do not know the full specifications of this dataset reliably.

- **What it contains**: An image classification dataset of 2D mathematical/geometric shapes hosted on Kaggle (uncertain whether the images are synthetically generated, hand-drawn, or mixed).
- **Creator**: Kaggle user **`reevald`** (I do not know their real name or affiliation).
- **Classes**: Uncertain — I have a faint recollection that it may contain **8** standard 2D geometric shape classes (such as circle, kite, parallelogram, rectangle, rhombus, square, trapezoid, and triangle), but I am **uncertain** of the exact class list and count.
- **Number of images / files**: Unknown.
- **Image size and format**: Unknown (uncertain whether PNG or JPEG, and unknown resolution).
- **License**: Unknown.

---

### Prompt 1C

> Without searching the web, describe the dataset "2D geometric shapes dataset (Mendeley, El Korchi)" (https://data.mendeley.com/datasets/wzr2yv7r53/1). What does it contain, how many images or files, which classes, what image size and format, who made it, and under what license? If you do not know it, say so instead of guessing.

- **What it contains**: Synthetically generated images of 2D geometric shapes with randomized variations in shape color, background color, rotation angle, size/scale, and position within the canvas.
- **Number of images / files**: **90,000 images** total (**10,000 images per class** across 9 classes).
- **Classes**: **9 classes**: `Circle`, `Square`, `Triangle`, `Pentagon`, `Hexagon`, `Heptagon`, `Octagon`, `Nonagon`, and `Star`.
- **Image size and format**: **200×200 pixels**, **PNG** format (RGB color images; exact channel depth e.g. RGB vs. RGBA is slightly uncertain).
- **Creator**: **El Korchi** (uncertain of exact first name, possibly Abdeljalil El Korchi), published on Mendeley Data (around 2020, uncertain of exact publication date).
- **License**: **CC BY 4.0** (uncertain if a different CC variant was selected, though CC BY 4.0 is the standard license I recall for this Mendeley entry).

---

### Prompt 1D

> Without searching the web, describe the dataset "hand-drawn-shapes-dataset (GitHub, frobertpixto)" (https://github.com/frobertpixto/hand-drawn-shapes-dataset). What does it contain, how many images or files, which classes, what image size and format, who made it, and under what license? If you do not know it, say so instead of guessing.

I do not know the detailed specifications of this dataset reliably.

- **What it contains**: A GitHub-hosted dataset of hand-drawn 2D shapes contributed by multiple users (organized per user).
- **Creator**: GitHub user **`frobertpixto`** (I do not know their full name or organization with certainty).
- **Number of images / files**: Unknown.
- **Classes**: Unknown (presumably basic hand-drawn geometric shapes such as circles, squares, triangles, etc., but I do not know the exact class list or count).
- **Image size and format**: Unknown (likely PNG, uncertain of exact pixel dimensions and color mode).
- **License**: Unknown.

---

### Prompt 2A

> Here is the start of a row from a metadata file. Complete the missing fields if you know this dataset; if you do not, say so.
> `{"word":"circle","countrycode":"US","timestamp":"2017-01-25 03:11:35.55071 UTC", ...`

This is a JSON object (one line) from a Google **Quick, Draw!** `.ndjson` file (`circle.ndjson`). While I do not know the exact literal values for this specific drawing record, the remaining fields in the schema are:

1. **`"recognized"`**: boolean (`true` or `false`) — whether the *Quick, Draw!* neural network recognized the drawing during gameplay.
2. **`"key_id"`**: string — a unique 64-bit integer identifier serialized as a JSON string (e.g., `"5152802093400064"`).
3. **`"drawing"`**: nested array representing the vector strokes:
   - **Simplified `.ndjson` format**: `[[[x0, x1, ...], [y0, y1, ...]], ...]` — a list of strokes, each containing two arrays (`x` and `y` coordinates, integers in `0–255`).
   - **Raw `.ndjson` format**: `[[[x0, x1, ...], [y0, y1, ...], [t0, t1, ...]], ...]` — a list of strokes, each containing three arrays (`x`, `y`, and timestamps `t` in milliseconds).

Completed structure:
```json
{"word":"circle","countrycode":"US","timestamp":"2017-01-25 03:11:35.55071 UTC","recognized":true,"key_id":"<unique_numeric_id>","drawing":[[[x0,x1,...],[y0,y1,...]],...]}
```
*(Exact values of `"recognized"`, `"key_id"`, and `"drawing"` for this specific timestamp are unknown.)*

---

### Prompt 2B

> Here is a real folder path from a dataset. Complete the missing fields if you know this dataset; if you do not, say so. What file-name pattern do the files in it use, and how many files are in it?
> `kaggle_reevald/dataset/test/circle/` (from the Kaggle dataset "Geometric Shapes Mathematics" by reevald)

I do not know the exact file-name pattern or the exact number of files in `kaggle_reevald/dataset/test/circle/` for the Kaggle dataset "Geometric Shapes Mathematics" by `reevald`.

---

### Prompt 2C

> Here is a real folder path from a dataset. Complete the missing fields if you know this dataset; if you do not, say so. What file-name pattern do the files in it use, and how many files are in it?
> `2D geometric shapes dataset/output/` (from the Mendeley dataset "2D geometric shapes dataset" by El Korchi)

- **Number of files**: **90,000 files** (all 9 classes × 10,000 images each are placed together directly inside the `output/` directory, rather than in separate per-class subdirectories).
- **File-name pattern**: `<ClassName>_<uuid>.png` — the capitalized shape class name (`Circle`, `Square`, `Triangle`, `Pentagon`, `Hexagon`, `Heptagon`, `Octagon`, `Nonagon`, or `Star`), followed by an underscore and a unique identifier (UUID / hex string), with a `.png` extension (e.g., `Circle_<uuid>.png`). *(Uncertain whether the unique ID is a hyphenated UUID v1/v4 or a plain hex string.)*

---

### Prompt 2D

> Here is a real folder path from a dataset. Complete the missing fields if you know this dataset; if you do not, say so. What file-name pattern do the files in it use, and how many files are in it?
> `hand-drawn-shapes-dataset/data/user.aly/images/` (from the GitHub dataset by frobertpixto)

I do not know the exact file-name pattern or the exact number of files in `hand-drawn-shapes-dataset/data/user.aly/images/` from `frobertpixto/hand-drawn-shapes-dataset`.

## Validation

Scored against [`docs/source.md`](../../../../docs/source.md) and the files on disk, as in the first run.

| Source | This run (sandboxed, empty folder) | First run (inside the workspace) | Truth |
|---|---|---|---|
| Quick, Draw! | Knows it: maker, ~50M drawings, 345 classes, formats, CC BY 4.0, row field order; declined to invent values | Same | CC BY 4.0, field order as given |
| Kaggle reevald | Partly: "faint recollection" of the 8 class names, marked uncertain. Count, size, format, license unknown | Partly: 8 classes **and 224x224 size** | 20,000 JPG 224x224, CC0 |
| Mendeley El Korchi | Knows it: 9 classes, 90,000, 200x200 PNG, CC BY 4.0, `<ClassName>_<uuid>.png` all in one folder | Same | Matches |
| GitHub frobertpixto | **Does not know it**: per-user folders only. Classes, size, format and license unknown | Partly: **4 classes and 70x70 PNG** | 27,292 PNG 70x70, 4 classes |

**Finding:** in the clean run Gemini knew less. It did not recall frobertpixto's classes or size, or reevald's image
size, which the in-workspace run reported. The first run's extra details may therefore have come from the workspace
(for example `docs/source.md` or earlier context in the session), not from the model's own knowledge. The clean run's
answers are the safer measure. In both runs Gemini invented nothing with confidence: it marked what it did not know.
It named El Korchi's first name as "possibly Abdeljalil". That name is not in the repo's records and was not checked.

## Our decision

No dataset change, as the course allows. For the verification table, this clean run counts as Gemini's result for
reevald and frobertpixto.

## Measured effect

None. Verification only.
