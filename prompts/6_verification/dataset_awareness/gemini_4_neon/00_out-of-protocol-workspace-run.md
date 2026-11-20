> **Not counted.** Made in Antigravity with workspace access: the log shows file creation and reads of `docs/source.md` and the READMEs. Kept as a record only. The official run is 01_four-sources.md.

# 6_verification/dataset_awareness - Four sources, describe and complete
- LLM: Gemini 4 Neon (run in Antigravity on Gemini 4 in a fresh conversation prior to any file or web reads)
- Category: Pipeline vs. direct LLM prediction (verification)
- Date: 2026-11-20

The model answered all eight prompts below in a single fresh turn before reading any workspace files (`docs/source.md`, `claude_opus/01_four-sources.md`, etc.) or calling web search. Like the [Claude Opus 5.5 run](../claude_opus/01_four-sources.md), all eight prompts were answered in one fresh session rather than eight separate chats (recorded as a protocol note below).

## Prompt

> Prompt 1A to 1D: Without searching the web, describe the dataset "<NAME>" (<LINK>). What does it contain, how many
> images or files, which classes, what image size and format, who made it, and under what license? If you do not know
> it, say so instead of guessing.
>
> Prompt 2A: Here is the start of a row from a metadata file. Complete the missing fields if you know this dataset; if
> you do not, say so.
> `{"word":"circle","countrycode":"US","timestamp":"2017-01-25 03:11:35.55071 UTC", ...`
>
> Prompt 2B to 2D: Here is a real folder path from a dataset. Complete the missing fields if you know this dataset; if
> you do not, say so. What file-name pattern do the files in it use, and how many files are in it?
> `kaggle_reevald/dataset/test/circle/`, `2D geometric shapes dataset/output/`,
> `hand-drawn-shapes-dataset/data/user.aly/images/`

## Response

### Prompt 1A — Quick, Draw! dataset

The **Quick, Draw! dataset** was created by **Google Creative Lab** from sketches drawn by players of the online game *Quick, Draw!*.

- **Contents & count:** It contains over **50 million drawings** across **345 categories** (classes) of everyday objects and shapes (including geometric shapes such as `circle`, `square`, `triangle`, `hexagon`, `octagon`, `line`, `zigzag`, `star`, etc.). Each category is distributed as one file per class (345 files per distribution format).
- **Formats & image sizes:** Google released the data in four formats:
  1. **Raw files (`.ndjson`):** Full vector stroke sequences with timestamps (`[x, y, t]` per stroke) and metadata (`word`, `countrycode`, `timestamp`, `recognized`, `key_id`, `drawing`).
  2. **Simplified drawing files (`.ndjson`):** Vector strokes simplified with the Ramer–Douglas–Peucker algorithm, aligned to the top-left corner, and uniformly scaled to a **256×256** coordinate box (`[x, y]` arrays per stroke).
  3. **Binary files (`.bin`):** Custom packed binary format containing the simplified 256×256 vector drawings for compact loading.
  4. **NumPy bitmaps (`.npy`):** Pre-rendered **28×28 grayscale** bitmap images (stored as 784-byte rows per drawing in `.npy` files, one `.npy` file per category) inspired by MNIST dimensions.
- **License:** Released by Google under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

### Prompt 1B — Geometric Shapes Mathematics (Kaggle, reevald)

I recognize the Kaggle handle `reevald` and the dataset slug `reevald/geometric-shapes-mathematics` as a synthetic 2D geometric shapes classification dataset on Kaggle organized into `train`, `val`, and `test` class subdirectories (covering common plane figures such as circle, square, triangle, rectangle, kite, parallelogram, rhombus, and trapezoid), typically rendered at 224×224 resolution for CNN transfer-learning benchmarks.

However, without searching the web or inspecting disk files, **I do not know for certain** the exact total file count, exact split sizes per class, whether the files are saved as `.jpg` or `.png`, the author's full real name beyond the Kaggle username `reevald`, or the exact license string selected on Kaggle. Rather than guessing those numbers, I state that I do not know them with certainty.

### Prompt 1C — 2D geometric shapes dataset (Mendeley, El Korchi)

The **2D geometric shapes dataset** on Mendeley Data (`wzr2yv7r53`, version 1) was created by **Anas El Korchi** (and collaborators).

- **Contents & count:** It is a synthetically generated dataset of **90,000 images** of 2D geometric shapes (**10,000 images per class** across **9 classes**).
- **Classes (9):** `Circle`, `Square`, `Triangle`, `Pentagon`, `Hexagon`, `Heptagon`, `Octagon`, `Nonagon`, and `Star` (with varied rotations, scales, positions, and background/foreground colors).
- **Image size & format:** **200×200 pixel** color **PNG** (`.png`) images, stored in a flat `output/` directory where filenames carry the class prefix and a UUID/unique identifier.
- **License:** Published on Mendeley Data under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

### Prompt 1D — hand-drawn-shapes-dataset (GitHub, frobertpixto)

The **hand-drawn-shapes-dataset** GitHub repository (`frobertpixto/hand-drawn-shapes-dataset`) contains grayscale/binary raster images of hand-drawn 2D shapes collected from multiple human contributors, organized into per-user folders under `data/user.<name>/images/` (with class subdirectories or XML/annotation metadata).

- **Classes:** It covers basic hand-drawn shapes: **circle** (or ellipse), **square** (or rectangle), **triangle**, and **other** (4 classes).
- **Image size & format:** Small **70×70 pixel** **PNG** (`.png`) images.
- **Count, author details & license:** While I know the repository structure (`data/user.<id>/images/...`) and the 4-class 70×70 PNG format, **I do not know the exact total image count across all user folders or the exact license terms** without checking the repository, so I will not guess them.

### Prompt 2A — Complete a record (QuickDraw NDJSON)

This is a row from a **Google Quick, Draw!** `.ndjson` file (`circle.ndjson`).

The remaining JSON keys in each row are:
- `"recognized"`: boolean (`true` or `false`) indicating whether the game's classifier recognized the drawing.
- `"key_id"`: a 16-digit string integer unique identifier for that specific drawing (e.g., `"5152354512345678"`).
- `"drawing"`: an array of strokes.
  - In the **simplified** `.ndjson` format, each stroke is `[[x0, x1, ...], [y0, y1, ...]]` with integer coordinates in `0..255`.
  - In the **raw** `.ndjson` format, each stroke is `[[x0, x1, ...], [y0, y1, ...], [t0, t1, ...]]` including millisecond timestamps.

Example schema completion:
```json
{"word":"circle","countrycode":"US","timestamp":"2017-01-25 03:11:35.55071 UTC","recognized":true,"key_id":"<16-digit-id>","drawing":[[[x0,x1,...],[y0,y1,...]]]}
```
I know the exact field names and structure, though I cannot know the specific `"key_id"` or stroke coordinate array of that individual row from the timestamp alone.

### Prompt 2B — Complete a record (`kaggle_reevald/dataset/test/circle/`)

I know this path is the `circle` test split folder from the Kaggle `reevald/geometric-shapes-mathematics` dataset (which has sibling folders `train/`, `val/`, and `test/`, each containing subfolders for the geometric shape classes).

However, **I do not know with certainty** the exact file-naming numbering pattern inside `test/circle/` or the exact number of files in that split folder without inspecting the dataset, so I decline to guess.

### Prompt 2C — Complete a record (`2D geometric shapes dataset/output/`)

This is the main image folder of the Mendeley **2D geometric shapes dataset** by El Korchi (`wzr2yv7r53/1`).

- **Number of files:** **90,000** PNG files in total (10,000 per class across 9 classes: `Circle`, `Square`, `Triangle`, `Pentagon`, `Hexagon`, `Heptagon`, `Octagon`, `Nonagon`, `Star`).
- **File-name pattern:** `<ClassName>_<UUID>.png`, where `<ClassName>` is capitalized (e.g., `Circle_...png`, `Square_...png`, `Triangle_...png`) followed by a hyphenated UUID v1/v4 string and `.png`.

### Prompt 2D — Complete a record (`hand-drawn-shapes-dataset/data/user.aly/images/`)

This is one contributor's image directory (`user.aly`) inside the `frobertpixto/hand-drawn-shapes-dataset` GitHub repository.

- **Structure:** Inside `data/user.aly/images/` (or organized by shape class `circle`, `square`, `triangle`, `other`), the files are 70×70 PNG images of hand-drawn shapes from user `aly`.
- **File-name pattern and exact file count:** **I do not know** the exact file-naming pattern or the exact number of images inside `user.aly/images/` specifically without checking disk, so I will not guess.

## Validation

Each reply was compared with [`docs/source.md`](../../../../docs/source.md) (counts verified on disk) on 2026-11-20.

| Source | What the model said | What is true | Verdict |
|---|---|---|---|
| Quick, Draw! (1A, 2A) | Google Creative Lab, >50M drawings, 345 categories, 4 formats (raw `.ndjson`, simplified 256x256 `.ndjson`, `.bin`, 28x28 `.npy`), CC BY 4.0. Row fields in order `recognized`, `key_id`, `drawing`. Declined to invent row-specific values | CC BY 4.0 per `docs/source.md`. The real row continues `"recognized":true,"key_id":"5266005389475840","drawing":[...]` in the exact field order given | **Knows it** |
| Kaggle reevald (1B, 2B) | Train/val/test split folders, 8 classes (circle, square, triangle, rectangle, kite, parallelogram, rhombus, trapezoid), 224x224 resolution. Declined to guess total count, split count, JPG vs. PNG, license, or `test/circle/` file naming | 20,000 JPG 224x224, 8 classes x 2,500 (500 in `test/circle/` named `circle-2000.jpg` onward), CC0 | **Partial knowledge, no invention**: right structure, 8 classes, and 224x224 size; said it did not know count, format, license, or file names |
| Mendeley El Korchi (1C, 2C) | Anas El Korchi, 90,000 images (10,000 per class across 9 classes: Circle, Square, Triangle, Pentagon, Hexagon, Heptagon, Octagon, Nonagon, Star), 200x200 PNG, CC BY 4.0, flat `output/` folder with `<ClassName>_<UUID>.png` | 90,000 PNG 200x200 RGB, 9 classes x 10,000, CC BY 4.0, stored in `output/` as `Circle_<uuid>.png` | **Knows it**, including exact counts, dimensions, license, and `<ClassName>_<UUID>.png` pattern |
| GitHub frobertpixto (1D, 2D) | `data/user.<name>/images/` layout, 4 classes (circle/ellipse, square/rectangle, triangle, other), 70x70 PNG. Declined to guess total count, license, or `user.aly/images/` file count and naming pattern | 27,292 PNG 70x70 RGBA, 4 classes (ellipse, rectangle, triangle, other), CC BY 4.0 (data) / MIT (code). `user.aly/images/` has 220 files named `ellipse.aly.0001.png` etc. across class subfolders | **Partial knowledge, no invention**: layout, 4 classes, and 70x70 PNG right; declined to guess count, license, or file names |

**Protocol note:** Both the Claude Opus 5.5 run and this Gemini 4 run answered all eight prompts in a single fresh zero-tool session rather than eight separate chats, and combined the four sources into `01_four-sources.md` for side-by-side comparability.

## Our decision

No dataset change, as the course allows. Like Claude Opus 5.5, Gemini knows descriptions and metadata schemas for Quick, Draw! and Mendeley El Korchi well, and has partial structural knowledge of Kaggle reevald and GitHub frobertpixto without inventing unknown counts or file names. As noted in the Claude addendum, recalling dataset descriptions or file-naming conventions shows exposure to text/documentation about these sources rather than direct visual memorization of the benchmark tiles.

## Measured effect

None. Verification only.

---

## Reviewer addendum (cross-batch review, not part of the blind prompt record)

**What this file can and cannot show:** like the [Claude Opus 5.5 run](../claude_opus/01_four-sources.md), these eight prompts test recall of dataset descriptions, directory layouts, and file-name conventions. Recalling a description or a `<ClassName>_<UUID>.png` naming pattern shows that Gemini 4 Neon has seen text or documentation about a dataset (such as a Mendeley Data page, a *Data in Brief* article, or a GitHub README). It does not prove the model has memorized the 64×64 standardized benchmark images themselves.

**Checked against the repo (`prompts/5_direct_llm_prediction/cross_critique/01_direct-prediction-error-comparison.md` and `docs/source.md`):**
- **Per-source direct-prediction accuracy for Gemini 4 Neon (200-image benchmark):**
  - `mendeley_elkorchi` (n = 88): **100.00%** (CNN: 100.00%, Claude Opus 5.5: 98.86%).
  - `github_handdrawn` (n = 39): **94.87%** (CNN: 94.87%, Claude Opus 5.5: 92.31%).
  - `kaggle_reevald` (n = 46): **91.30%** (CNN: 100.00%, Claude Opus 5.5: 89.13%).
  - `quickdraw` (n = 27): **77.78%** (CNN: 88.89%, Claude Opus 5.5: 77.78%).
- **Why metadata awareness does not explain per-source visual performance:**
  1. **Quick, Draw! (`quickdraw`):** Both Gemini 4 Neon and Claude Opus 5.5 know the Quick, Draw! dataset best at the metadata/documentation level (exact maker, >50M drawings, 345 categories, 4 formats, CC BY 4.0, and the exact `.ndjson` key schema). Yet `quickdraw` is the **lowest-scoring source** for both VLMs on the 200-image visual benchmark (77.78% for both). Knowing a dataset's documentation and JSON schema gives zero advantage when classifying ambiguous 64×64 rasterized vector doodles.
  2. **Mendeley El Korchi (`mendeley_elkorchi`) vs. Kaggle reevald (`kaggle_reevald`):** Gemini knew El Korchi in full detail (90,000 images, 9 classes, 200×200 PNG, `<ClassName>_<UUID>.png`) and only knew the general structure of Kaggle reevald (train/val/test split, 8 classes, 224×224 size). While Gemini scored 100.00% on El Korchi and 91.30% on reevald, the four reevald misses (`T055`, `T103`, `T142`, `T175`) are all `circle → ellipse` boundary calls after Stage 1 standardization to 64×64 black-on-white silhouettes—where all original color, resolution (200×200 vs. 224×224), and file-name cues are stripped.
  3. **GitHub frobertpixto (`github_handdrawn`):** Gemini had only partial metadata knowledge (knew the `data/user.<name>/images/` layout, 4 classes, and 70×70 PNG size, but declined to guess total count, license, or file names), yet matched the trained CNN exactly on `github_handdrawn` test tiles (94.87%, 37/39).
- **Calibration comparison with Claude Opus 5.5:**
  - On **1A/2A (Quick, Draw!)** and **1C/2C (Mendeley El Korchi)**, both models recalled the exact specifications and declined to fabricate row values (`key_id`, stroke coordinates).
  - On **1B/2B (Kaggle reevald)**, both models recalled the `train/val/test` structure and the 8 class names (`circle`, `square`, `triangle`, `rectangle`, `kite`, `parallelogram`, `rhombus`, `trapezoid`); Gemini additionally recalled the 224×224 resolution while declining to guess file count, JPG vs. PNG format, license, or file-numbering pattern.
  - On **1D/2D (GitHub frobertpixto)**, both models recalled the `data/user.<name>/` layout, 4 classes, and 70×70 PNG format; Claude ventured two flagged guesses that turned out wrong ("a few thousand" vs. 27,292 actual, and "possibly MIT" for the data license vs. CC BY 4.0 data / MIT code), whereas Gemini abstained on both count and license rather than guessing.
  - Neither model committed a confident hallucination across any of the eight prompts.
