# 0_data_discovery - Opus 5.5 fact-checks Gemini 4 Neon's dataset claims

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Critiqued output: Gemini 4 Neon (its draft plan, linked in the Response)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-10-19
- Owner: 40256377
- Worksheet entries: S02, S03, S04, S05
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.
- Reconstructions of the same entries: [S02](../claude_opus/02_exclude-kaggle-dinesh.md), [S02](../gemini_4_neon/02_exclude-kaggle-dinesh.md), [S03](../claude_opus/03_reject-mendeley-d35tjjgjnx.md), [S03](../gemini_4_neon/03_reject-mendeley-d35tjjgjnx.md), [S04](../claude_opus/04_reject-mendeley-ypfcrfxjgk.md), [S04](../gemini_4_neon/04_reject-mendeley-ypfcrfxjgk.md), [S05](../claude_opus/05_reject-kaggle-swastikarajkower.md), [S05](../gemini_4_neon/05_reject-kaggle-swastikarajkower.md)

## Prompt (inferred, not saved)

> _Inferred:_ Fact-check the five candidate datasets drafted in plans 01 and 03 against each dataset's own source page (license, size, classes, data type).

## Response (saved output, verbatim)

### `research_notes/Shape dataset integration and tooling/dataset_verification.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Dataset Fact-Check: 2D Shape Image Datasets

Verified against each dataset's own source page (Kaggle "About this dataset" / Data Explorer, GitHub README, Mendeley Data metadata page). Kaggle pages are JavaScript-rendered; standard WebFetch returned only page titles, so Kaggle content below was retrieved via a text-rendering proxy (r.jina.ai) of the live page and cross-checked with web search snippets. Where a page did not state a value, this is marked explicitly rather than guessed.

---

## 1. "Geometric Shapes Dataset" by dineshpiyasamara (Kaggle)
URL: https://www.kaggle.com/datasets/dineshpiyasamara/geometric-shapes-dataset

**Verified facts (from the Kaggle page itself):**
- **License:** stated as **"Unknown"** on the Kaggle license field.
- **Size/file count:** "30.0k files" / **28.87 MB** total (Data Explorer summary).
- **Format/resolution:** **200 x 200 RGB** images ("each shape is drawn randomly on a 200 x 200 RGB image"). Format (PNG/JPG) is **not stated** on the page.
- **Classes:** 3 classes — **Triangle, Square, Circle** — each with **10,000** generated images ("Each class is composed of 10 000 generated image").
- Other metadata: author Dinesh Piyasamara, last updated ~5 years ago, 15.2K views, 2,709 downloads.

**Verdict on draft claim:** **Significantly wrong on two points, close on others.**
- "CC0 Public Domain license" — **WRONG**. The page states license = **Unknown**, not CC0. This is a material discrepancy for a project that needs to document legal reuse rights.
- "grayscale" — **WRONG**. Images are stated to be **RGB** (color), not grayscale.
- 30,000 total images across 3 classes (10,000 each: Circle, Square, Triangle) — **confirmed correct**.
- ~28 MB — **confirmed correct** (28.87 MB).
- PNG / 200x200 — resolution (200x200) confirmed; file format (PNG) is not actually stated on the page, so that detail is unverified, not confirmed.

**Flag:** License and color-mode claims in the draft are incorrect and should be corrected before citing this dataset as CC0/grayscale in the project writeup.

---

## 2. "Hand-Drawn Shapes Dataset" by frobertpixto (GitHub)
URL: https://github.com/frobertpixto/hand-drawn-shapes-dataset

**Verified facts (from the GitHub README):**
- **License:** README states two separate licenses — **data**: "Hand-drawn Shapes (HDS) Dataset © 2022 by Francois Robert is licensed under CC BY 4.0"; **code** (the notebooks): licensed under **MIT**. So the draft's "MIT / CC BY 4.0 (uncertain which)" is actually correct in substance — it's both, applied to different parts (code vs. data), not an either/or ambiguity.
- **Size:** **27,292 images** total.
- **Format/resolution:** PNG files, **70px x 70px, 1 gray channel** (grayscale).
- **Classes:** **4 classes**, not 5: **Rectangle (6,956), Ellipse (6,454), Triangle (6,595), Other (7,287)**.

**Verdict on draft claim:** **Significantly wrong on image count and class list; license split is now confirmed rather than uncertain.**
- "~1,200 images" — **WRONG**, actual total is **27,292** (over 22x higher).
- "circle/square/triangle/ellipse/rectangle" (5 classes) — **WRONG**. Actual classes are **Rectangle, Ellipse, Triangle, Other** (4 classes). There is no distinct Circle or Square class; "Other" is a catch-all, not a named shape.
- "hand-drawn on touch devices and paper" — plausible per the dataset's name/purpose but not independently re-confirmed word-for-word in this pass; treat as unverified detail (low risk, but flagged).
- License: now resolved, not uncertain — CC BY 4.0 applies to the **data**, MIT applies to the **code/notebooks**.

**Flag:** Class list and total image count in the draft are materially wrong and must be corrected.

---

## 3. Mendeley Data geometric shapes dataset #1 — "2D Geometric shapes with properties"
URL: https://data.mendeley.com/datasets/d35tjjgjnx/1

**Verified facts (from the Mendeley Data page):**
- **Title:** "2D Geometric shapes with properties" (not simply "geometric shapes" — it's property-annotated shapes).
- **License:** **CC BY 4.0** (confirmed, matches draft).
- **Size:** page states **"3,80,000 black and white images"** — this is Indian-style digit grouping for **380,000 images**, not a 2,500–4,000 image pool. Fixed resolution **200 x 200 pixels**, black-and-white (binary, not grayscale photographs).
- **File listing:** The Files section on the page did not show individual file names/sizes in this capture — total file count/download size beyond "380,000 images" is **not independently confirmed**.
- **Classes:** **76 classes total**, combining base shapes (**Circle, Triangle, Square, Rectangle, Rhombus, Parallelogram, Trapezium**) with geometric properties (diagonal, perpendicular, chord, radius, diameter, equal-sides marking). No pentagon, hexagon, or octagon classes appear anywhere in the description.
- Contributor: Archana Boob, Visvesvaraya National Institute of Technology. Version 1, published 1 May 2024, DOI 10.17632/d35tjjgjnx.1.
- Nothing on the page indicates the images are "real-world photographs/scans" — the description describes them as **synthetically generated** (random rotation, perimeter, position of a drawn shape on a white background), not photographed/scanned.

**Verdict on draft claim:** **Significantly wrong.**
- "real-world photographs/scans of geometric shapes" — **WRONG**. These are synthetically generated black-and-white line/fill drawings, not photos or scans.
- "part of a ~2,500-4,000 image combined pool across triangle/rectangle/pentagon/hexagon/octagon" — **WRONG**. This single dataset alone contains **380,000 images** (two orders of magnitude larger than the draft's whole combined-pool estimate), and its class set has no pentagon/hexagon/octagon — instead it's 76 shape+property combinations over 7 base shapes (circle, triangle, square, rectangle, rhombus, parallelogram, trapezium).
- "CC BY 4.0" — **confirmed correct**.

**Flag:** The draft's size estimate, class list, and "real-world photo" description are all incorrect for this specific dataset. It appears the draft notes may have conflated this dataset with a different one (possibly a pentagon/hexagon/octagon dataset found elsewhere, e.g. the EL KORCHI Anas Mendeley "2D geometric shapes dataset" turned up in search results, which does list Triangle/Square/Pentagon/Hexagon/Heptagon/Octagon/Nonagon/Circle/Star — but that is a different dataset/URL than the one given, so it does not rescue this claim).

---

## 4. Mendeley Data geometric shapes dataset #2 — "Geometrical shapes datasets"
URL: https://data.mendeley.com/datasets/ypfcrfxjgk/1

**Verified facts (from the Mendeley Data page):**
- **Title:** "Geometrical shapes datasets" (by Serge Dolgikh, Nacional'nij Aviacijnij Universitet / National Aviation University).
- **License:** **CC BY 4.0** (confirmed, matches draft).
- **Size:** **9,000 images total**, split into two subsets:
  - `bw_shapes_3_1800`: **1,800 grayscale images, 64x64**, 3 classes, 600 images/class — **Circle, Triangle, Background**.
  - `col_shapes_9_7200`: **7,200 color images, 64x64**, 9 classes, 800 images/class — labels 0/1 red/blue circle, 2/3 red/blue triangle, 4/5 red/blue horizontal stripes, 6/7 red/blue vertical stripes, 8 background.
- Format noted on the page: "Use pickle, zip to extract raw images and labels" — i.e. images are packaged as pickle/zip archives, not loose PNG/JPG files; exact image file format inside is **not stated**.
- Category: Image Analysis.

**Verdict on draft claim:** **Significantly wrong.**
- "real-world photographs/scans" — **WRONG**. These are synthetic, small (64x64) generated shape images (circles, triangles, and striped patterns), not photographs/scans.
- "pentagon/hexagon/octagon" classes — **WRONG**. Actual classes are limited to **circle, triangle, striped patterns, and background** (plus color variants). No pentagon, hexagon, or octagon class exists in this dataset.
- "part of a ~2,500-4,000 image combined pool" — total here is **9,000 images**, which doesn't fit neatly into the draft's combined-pool estimate; combined with dataset #3's 380,000 images, the two Mendeley sets alone total ~389,000 images, vastly exceeding the draft's 2,500–4,000 figure.
- "CC BY 4.0" — **confirmed correct**.

**Flag:** Same pattern as #3 — this looks like a mismatch between the draft notes and the actual dataset at this URL. Neither Mendeley dataset given supports the "pentagon/hexagon/octagon, real-world photo" description; both are synthetic and center on circle/triangle (plus properties or stripes/colors), and both are far larger than estimated.

---

## 5. "Geometric Shapes Classification Dataset" by swastikarajkower (Kaggle)
URL: https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset

**Verified facts (from the Kaggle page):**
- **This is NOT an image dataset.** It is a single **CSV file**, `geometry_shapes_dataset.csv`, containing **1,200 synthetically generated tabular observations** (rows), each describing one geometric figure via numeric/categorical features: side counts, vertices, side lengths, interior angles, perimeter, area, equal-sides flags, right-angle presence, radius, diameter (unused fields set to 0).
- **License:** The page has **no "License" field populated** / no named license (e.g., no MIT, no CC0, no CC BY). There is a "License and Usage" blurb only stating the data is "suitable for educational, academic, and experimental machine learning purposes" — this is a usage note, not a license grant.
- **Classes:** The `Shape` column holds **12 classes**, including "Equilateral Triangle," "Circle," "Ellipse," and others (full list not fully captured in this pass, but confirmed to be 12 distinct shape labels, not 9).
- No per-class image counts exist because there are no images.

**Verdict on draft claim:** **Severely/fundamentally wrong — wrong data modality entirely.**
- "MIT License" — **WRONG**. No license is stated on the page at all.
- "textured/colored 2D/3D geometric renders, ~5,000 images across 9 classes including star/pentagon/hexagon/octagon" — **WRONG on every count**. There are **no images whatsoever** in this dataset — it is tabular/CSV data describing shape geometry numerically. Total record count is **1,200**, not ~5,000. Class count is **12**, not 9, and star/pentagon/hexagon/octagon were not confirmed among the visible class examples (Equilateral Triangle, Circle, Ellipse were seen).

**Flag:** This dataset cannot be used as an image dataset at all for a 2D-shape image classification project — it is structured/tabular data, not pictures. This is the single largest discrepancy found and should be escalated to whoever is scoping the project's dataset pool, since using it as planned (as an image source) is not possible.

---

## Summary Table

| # | Dataset | Draft License | Verified License | Draft Size | Verified Size | Draft Classes | Verified Classes | Overall |
|---|---|---|---|---|---|---|---|---|
| 1 | dineshpiyasamara (Kaggle) | CC0 | **Unknown** (stated on page) | 30,000 imgs, ~28MB, grayscale | 30,000 imgs, 28.87MB, **RGB** (confirmed count/size, wrong license & color mode) | Circle/Square/Triangle, 10k each | Confirmed: Triangle/Square/Circle, 10k each | Close, 2 wrong details |
| 2 | frobertpixto (GitHub) | MIT/CC BY 4.0 (uncertain) | **Both, resolved**: data=CC BY 4.0, code=MIT | ~1,200 images | **27,292 images** | circle/square/triangle/ellipse/rectangle (5) | **Rectangle/Ellipse/Triangle/Other (4)** | Significantly wrong (size, classes) |
| 3 | Mendeley d35tjjgjnx | CC BY 4.0, real photos, 2,500-4,000 pool, tri/rect/pent/hex/oct | CC BY 4.0 confirmed; **synthetic, not photos**; **380,000 images**; 76 classes over circle/triangle/square/rectangle/rhombus/parallelogram/trapezium (no pentagon/hexagon/octagon) | Wrong | Wrong | Wrong | Wrong | Significantly wrong |
| 4 | Mendeley ypfcrfxjgk | CC BY 4.0, real photos, pent/hex/oct | CC BY 4.0 confirmed; **synthetic, not photos**; **9,000 images**; classes limited to circle/triangle/stripes/background (no pentagon/hexagon/octagon) | Wrong | Wrong | Wrong | Wrong | Significantly wrong |
| 5 | swastikarajkower (Kaggle) | MIT, textured 2D/3D renders, ~5,000 imgs, 9 classes | **No license stated**; **CSV tabular data, not images**; 1,200 rows; 12 classes | Wrong | Wrong | Wrong | Wrong | Fundamentally wrong (wrong data type) |

## Unverified / Could Not Confirm
- Exact image file format (PNG vs. JPEG) for dataset #1 (dineshpiyasamara) — resolution and color mode are stated, but the literal file extension is not shown on the Kaggle page text captured.
- Exact byte-size/file count for datasets #3 and #4 (Mendeley) — the "Files" section did not render file names/sizes in the proxy capture; only the description's stated image counts (380,000 and 9,000 respectively) are confirmed.
- The claim in the GitHub README (#2) that drawings were made "on touch devices and paper" was not re-confirmed verbatim in this pass (plausible given the dataset's known purpose, but not directly quoted from the page in this research session) — flagged as a minor unverified detail, not a contradiction.
- Full 12-class list for dataset #5's `Shape` column beyond Equilateral Triangle, Circle, and Ellipse was not fully enumerated in the captured text.

## Note on methodology/limitations
Kaggle's dataset pages are JavaScript-rendered; a direct WebFetch of the raw URL returned only the page `<title>` with no body content. Kaggle data in this report was obtained by fetching a text-rendering proxy of the live page, which did successfully surface the "About this dataset," license field, and Data Explorer summary. No login was required to view any of the five pages at the level of detail reported above; no paywalled or private content was encountered.
````

### `reports/Shape dataset integration and tooling.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Fact-checking exposes a flawed shape-dataset plan

The Phase 1 draft's dataset citations contain fundamental errors severe enough to require revision before publication: one "candidate dataset" is not an image dataset at all but a 1,200-row CSV of numeric shape descriptors, two "real-world photograph" Mendeley sources are actually synthetic renders with no pentagon/hexagon/octagon classes, and a dataset described as "~1,200 hand-drawn images across 5 classes" is in fact 27,292 images across 4 classes (Rectangle, Ellipse, Triangle, Other — no distinct circle or square). For the project's stated 10-class taxonomy (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond), the single most valuable net-new source identified is a CC BY 4.0 Mendeley dataset by Anas El Korchi that covers four of the five hardest-to-source classes (pentagon, hexagon, octagon, star) in one 90,000-image collection, while ellipse remains the taxonomy's weakest link, served best by DeepMind's dSprites benchmark rather than any classification-style dataset. On the engineering side, well-documented, citable conventions exist for every integration step the project needs — aspect-preserving "letterbox" resizing, ITU-R BT.601 grayscale conversion, foreground/background polarity normalization, and perceptual-hash deduplication — plus a hard methodological rule, backed by an empirical case study showing up to a 66-percentage-point metric inflation, that augmentation and synthetic generation must happen only after the train/test split and only inside the training path. Finally, a tiered toolset from zero-dependency Matplotlib grids up to full FiftyOne/CleanVision pipelines gives the team a low-cost way to audit the merged dataset visually before training ever starts.

## Draft dataset citations are wrong on license, size, class list, or data type

Five datasets drafted into the project plan were checked directly against their source pages, and four of the five contained material errors. The Kaggle "Geometric Shapes Dataset" by dineshpiyasamara is **30,000 RGB images (10,000 each of triangle, square, circle) at 200×200, totaling 28.87 MB**, but its license field reads **"Unknown," not CC0** as drafted, and the images are **RGB, not grayscale** ([Kaggle dataset page](https://www.kaggle.com/datasets/dineshpiyasamara/geometric-shapes-dataset)). The GitHub "Hand-Drawn Shapes Dataset" by frobertpixto turned out to be over 22 times larger than estimated — **27,292 PNG images at 70×70, single-channel grayscale** — split into **Rectangle (6,956), Ellipse (6,454), Triangle (6,595), and Other (7,287)**, not the five named shape classes assumed in the draft; its licensing is **not actually ambiguous**, since the README cleanly splits CC BY 4.0 for the data and MIT for the accompanying code/notebooks ([GitHub README](https://github.com/frobertpixto/hand-drawn-shapes-dataset)).

The two Mendeley entries are the most consequential errors. "2D Geometric shapes with properties" (DOI 10.17632/d35tjjgjnx.1) is **CC BY 4.0-licensed but contains 380,000 synthetically generated black-and-white images at a fixed 200×200**, spanning **76 classes** that combine seven base shapes (circle, triangle, square, rectangle, rhombus, parallelogram, trapezium) with geometric-property labels — not real-world photographs, and with **no pentagon, hexagon, or octagon class at all** ([Mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)). "Geometrical shapes datasets" by Serge Dolgikh (DOI 10.17632/ypfcrfxjgk) is likewise CC BY 4.0 but is a **9,000-image synthetic set (1,800 grayscale 64×64 + 7,200 color 64×64)** limited to circles, triangles, striped patterns, and background — again, **no pentagon/hexagon/octagon**, and no real photographs ([Mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk)). Both datasets are two to three orders of magnitude larger than the draft's "~2,500–4,000 image combined pool" estimate, and together they total roughly 389,000 images that do not cover the gap classes the draft implied they filled. Most seriously, the Kaggle "Geometric Shapes Classification Dataset" by swastikarajkower is **not an image dataset** — it is a single CSV of **1,200 rows of numeric/categorical shape geometry** (side counts, angles, perimeter, area) across 12 shape labels, with **no license stated at all**, contradicting the draft's claim of an "MIT-licensed, ~5,000-image, 9-class render set" ([Kaggle dataset page](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)). This dataset cannot serve the project's image-classification goal under any interpretation and should be struck from the plan entirely rather than merely corrected.

## One Mendeley source closes most of the taxonomy gap; ellipse stays unsolved

Beyond the drafted list, the strongest net-new candidate is the Mendeley "2D geometric shapes dataset" by Anas El Korchi (DOI 10.17632/wzr2yv7r53.1), licensed **CC BY 4.0** with **10,000 generated 200×200 RGB images per class across nine classes** — Triangle, Square, Pentagon, Hexagon, Heptagon, Octagon, Nonagon, Circle, and Star — directly supplying four of the taxonomy's five underrepresented classes (pentagon, hexagon, octagon, star) in one well-documented, redistributable package, and it even links to the generator source code for producing additional samples ([Mendeley](https://data.mendeley.com/datasets/wzr2yv7r53/1)). Supplementary single- or few-class sources exist on Roboflow Universe under CC BY 4.0, including sets that cover hexagon and pentagon together ([Roboflow "line new"](https://universe.roboflow.com/babag/line-new)) or pentagon alongside circle/triangle/star ([Roboflow "shapes"](https://universe.roboflow.com/edhitha2024/shapes-fquuk)), though none independently supplies a complete 10-class set and each would need its own CC BY attribution carried through the merged corpus. A Hugging Face 8-class dataset (`itshemantkmr/2D_Shape_Image_Datasets`, Apache-2.0, 20,000 JPEGs at 224×224) was also surfaced, but its class list could not be fully confirmed from the dataset card and a related model card suggests its classes (circle, kite, parallelogram, rectangle, rhombus, square, trapezoid, triangle) do **not** actually cover pentagon/hexagon/octagon/star, so it should not be assumed to close the gap without direct verification.

Ellipse is the one target class with no good classification-dataset fit. The most credible source is **dSprites**, DeepMind's well-known disentangled-representation-learning benchmark containing only three shapes — square, ellipse, and heart — combined exhaustively with color, scale, rotation, and position across 737,280 images ([GitHub](https://github.com/google-deepmind/dsprites-dataset)). Its licensing requires care: the original GitHub repository uses permissive, zlib-style language granting unrestricted use including commercial applications, but two Hugging Face mirrors instead label it Apache-2.0 and restrict use to "non-commercial research purposes" ([Hugging Face mirror README](https://huggingface.co/datasets/TalBarami/msd_dsprites_static/blob/main/README.md)) — a direct conflict that means the project should treat the upstream GitHub repository, not any mirror, as the authoritative license source. A separate, confirmed gap is photograph-based (as opposed to rendered or sketched) shape data: the only credible candidate, the Kaggle/HyperAI "Four Shapes" dataset of physically cut, painted poster-board shapes photographed and cropped, covers just four classes (square, star, circle, triangle) and its license could not be confirmed from available snippets ([HyperAI mirror](https://vercel.hyper.ai/en/datasets/29901)). If a photographic domain matters to the project, road-sign datasets (which naturally include octagons via stop signs and pentagons via other sign shapes) are an unexplored but promising lead that the current research pass did not check.

## Letterboxing, BT.601 grayscale, and hash-based dedup are the citable integration defaults

For merging images of differing native resolution, the de facto cross-framework standard is **letterboxing**: rescale the image so its longest side matches the target size while preserving aspect ratio, then pad the remaining space with a constant fill color. This is implemented directly as Albumentations' `LetterBox` transform (documented as equivalent to chaining `LongestMaxSize` + `PadIfNeeded`, defaulting to the YOLO pad value of 114) and is the opposite of a naive non-aspect-preserving resize, which distorts shape geometry — a serious risk for a project where the geometric silhouette *is* the label ([Albumentations LetterBox docs](https://albumentations.ai/explore/transform/LetterBox/docs/); [Albumentations resize API](https://albumentations.ai/docs/api-reference/albumentations/augmentations/geometric/resize/)). The same pattern is achievable in plain torchvision by passing an integer (not a tuple) to `Resize`, which scales the shorter edge proportionally, followed by a manually computed `Pad` ([PyTorch Discuss](https://discuss.pytorch.org/t/how-to-resize-and-pad-in-a-torchvision-transforms-compose/71850)).

For color-mode unification, both OpenCV and Pillow default to the legacy **ITU-R BT.601 luma weights** (Y = 0.299R + 0.587G + 0.114B) when converting RGB to grayscale, even though BT.709 (0.2126/0.7152/0.0722) is the technically more modern HDTV-consistent standard — OpenCV's docs state the BT.601 formula explicitly for `COLOR_RGB2GRAY`/`COLOR_BGR2GRAY`, and Pillow's `Image.convert('L')` documentation names the same "ITU-R 601-2 luma transform" ([OpenCV docs](https://docs.opencv.org/4.0.0/de/d25/imgproc_color_conversions.html); [Pillow docs](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.convert)). Because the project is merging sources with inconsistent foreground/background polarity (some shapes drawn dark-on-light, others light-on-dark), a defensible approach — adapted from, rather than directly copied from, a single named standard — is to compute a per-image polarity signal (e.g., border-pixel mean intensity, or which histogram mode holds the majority of pixels) and invert any image that disagrees with the dataset's chosen convention, mirroring the explicit `ForegroundPolarity` parameter MATLAB exposes in `imbinarize` and the inverse-threshold modes common across thresholding libraries ([MathWorks imbinarize docs](https://www.mathworks.com/help/images/ref/imbinarize.html)). Deduplication across merged sources is well served by **perceptual hashing (pHash)**: the Python `imagehash` library computes a compact fingerprint (commonly via grayscale-resize-then-DCT, keeping the low-frequency 8×8 block) such that visually similar images hash to similar bit patterns, and near-duplicates are flagged by Hamming distance between hashes ([imagehash GitHub](https://github.com/JohannesBuchner/imagehash)); the algorithm's primary academic grounding is Christoph Zauner's 2010 master's thesis ([phash.org thesis PDF](https://phash.org/docs/pubs/thesis_zauner.pdf)).

## Augmentation belongs only inside the training loader, strictly after splitting

On pipeline architecture, PyTorch's own tutorial establishes the canonical pattern for plugging in both augmentation and synthetic generation without ever materializing extra files to disk: a custom `Dataset` subclass defers all image loading and transformation to `__getitem__`, which executes lazily on each access rather than up front, and documentation explicitly frames this as memory-efficient because "all the images are not stored in memory at once but read as required" ([PyTorch tutorial](https://docs.pytorch.org/tutorials/beginner/data_loading_tutorial.html)). Albumentations' `Compose` pipeline is designed to slot into that same `__getitem__` call, re-evaluating each transform's random parameters fresh on every invocation via call-local random generators, so repeated epochs over the same image yield different augmented variants without any precomputed cache ([Albumentations pipelines docs](https://albumentations.ai/docs/2-core-concepts/pipelines/)). No official documentation uses the phrase "synthetic data generation" integrated into this exact pattern, but architecturally a synthetic-generation function occupies the identical slot — a sample-producing callable invoked by `__getitem__` — making this the defensible extension to cite rather than a directly-sourced claim.

The more important rule, and one with unusually strong, mutually corroborating sourcing, is that augmentation and synthetic generation must be applied **only to the training split, after splitting** — never to the full dataset beforehand. An academic ML-pitfalls guide states flatly that augmentation "should be applied only to training data" ([Whalen et al., arXiv](https://arxiv.org/pdf/2108.02497)), and a 2025 reproducible case study empirically demonstrated that pre-split augmentation inflated reported detection accuracy (mAP50) by **up to 66 percentage points** compared to correctly post-split augmentation ([Mendeley case-study dataset](https://data.mendeley.com/datasets/f9k79z29rp/1)). The same leakage logic extends to deduplication and oversampling: near-duplicate images should be identified and removed **before** the train/test split so that near-identical shapes don't land on both sides of it ([Towards Data Science](https://towardsdatascience.com/an-introduction-to-data-leakage-f1c58f7c1d64)), and any fitted transformation (a scaler, SMOTE, or an augmentation pipeline) must be scoped to the training fold only ([Medium, "Split Smart"](https://medium.com/@pacosun/split-smart-avoiding-data-leakage-in-cross-validation-894863a93553)). Combining these findings yields a clean, citable pipeline order for the Phase 1 report: deduplicate the merged raw images first, split into train/test on the deduplicated set, and only then apply synthetic generation and augmentation inside the training `Dataset.__getitem__` — never before the split, and never allowing augmented derivatives of one source image to appear on both sides of it.

## A tiered, mostly free toolset covers visualization needs without a dashboard build

For a student project's scope, the lowest-cost and most directly applicable audit tool is plain Matplotlib: a grid of `imshow` calls comparing images before and after preprocessing catches resize, grayscale, and padding bugs by direct inspection, with zero new dependencies beyond what the ML pipeline already needs. Class and per-source balance is a one-line check with `seaborn.countplot(x="class", hue="source")`, which the official docs describe as a categorical-variable histogram sharing its API with `barplot` ([seaborn docs](https://seaborn.pydata.org/generated/seaborn.countplot.html)); Yellowbrick's purpose-built `ClassBalance` visualizer is a documented alternative that warns imbalance "may be masked by relatively good F1 and accuracy scores" if not checked visually ([Yellowbrick docs](https://yellowbrick.readthedocs.io/en/v1.5/api/target/class_balance.html)). Resolution and channel consistency across merged sources is best checked with a width-vs-height scatter plot and per-channel pixel-intensity histograms, either hand-rolled in a dozen lines of Matplotlib or produced automatically by the small open-source CLI `basic-image-eda`, which scans a directory and reports per-channel pixel statistics, aspect-ratio summaries, and recommended input sizes — though it coerces everything to 3-channel RGB internally, so a dataset deliberately mixing grayscale and color sources should run it per-source-subset to avoid losing channel information ([basic-image-eda GitHub](https://github.com/Soongja/basic-image-eda)).

Two free, more specialized tools round out the toolkit at modest additional setup cost. **CleanVision**, part of the Cleanlab ecosystem, operates directly on raw image files with no model or embeddings required and automatically flags near-duplicates, blur, and over/under-exposure — a near-zero-setup safety net specifically relevant to a multi-source merge, where an independent academic study of retinal-imaging datasets used the same Cleanlab duplicate-detection approach to confirm 638 duplicate images across six merged sources and flagged the resulting train/test leakage risk ([CleanVision README](https://github.com/cleanlab/cleanvision/blob/main/README.md); [retinal-imaging preprint](https://www.researchsquare.com/article/rs-10775714)). **FiftyOone** (Voxel51) is the most complete turnkey option for interactive browsing, filtering, and tagging — installable via `pip install fiftyone` and launchable with a few lines of code to open a browser-based app — but it carries the heaviest footprint of the options surveyed (its own server process, optional FFmpeg, OS-level build prerequisites), making it worth adopting only if the team anticipates repeated, ongoing dataset triage rather than a one-time preprocessing sanity check ([FiftyOne installation docs](https://docs.voxel51.com/installation/index.html)). Cluster-level checks of whether different sources occupy separable regions of feature space are a reasonable nice-to-have via scikit-learn's `TSNE` (with PCA pre-reduction to ~50 dimensions, as scikit-learn's own docs recommend for high-dimensional inputs) or `umap-learn`'s `UMAP`, both scikit-learn-API compatible ([scikit-learn TSNE docs](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html); [umap-learn basic usage](https://umap-learn.readthedocs.io/en/latest/basic_usage.html)), but this answers a different question than basic corruption/balance auditing and should be treated as a later-stage addition, not part of the minimal toolset.

## Conclusion

The research surfaces a pattern worth flagging explicitly in the Phase 1 report: every one of the draft's dataset citations that claimed "real-world photographs" or a specific pentagon/hexagon/octagon class list turned out, on direct verification, to describe a different and usually synthetic dataset — suggesting the draft notes were assembled from secondhand summaries or conflated across similarly-named Mendeley entries rather than from the source pages themselves, a methodological lesson as important as any individual correction. Practically, the path forward is narrow but clear: adopt the El Korchi Mendeley set to cover pentagon/hexagon/octagon/star, accept dSprites (sourced from its original GitHub repository, not a Hugging Face mirror) as the stopgap for ellipse, drop the swastikarajkower CSV entirely, and build the integration pipeline around letterbox resizing, BT.601 grayscale conversion, hash-based pre-split deduplication, and strictly post-split augmentation — each a documented, citable convention rather than an improvised choice. The auditing side needs no new infrastructure investment: Matplotlib, seaborn, and CleanVision together close the gap between "the data looks merged" and "the data is verifiably merged correctly," reserving heavier tools like FiftyOne or UMAP clustering for if the project's scope grows beyond a single-report deliverable.
````

### `06_dataset_claims_correction.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE: bibliography and Section B corrected.

# Plan 06: Correct Verified Errors in Plans 01 & 03 (and the real report's bibliography)

## 1. Why this exists
A deep-research pass fact-checked the five candidate datasets drafted in
`01_dataset_details.md` / `03_more_datasets.md` against their actual source
pages. Four of five contained material errors. Full sourcing:
`research_notes/Shape dataset integration and tooling/dataset_verification.md`
and `reports/Shape dataset integration and tooling.md`.

## 2. Verified corrections

### 2.1 dineshpiyasamara (Kaggle) — license and color mode wrong
- Draft said: CC0, grayscale.
- Verified: license field reads **"Unknown," not CC0**; images are **RGB**,
  not grayscale. File count (30,000; 10,000 each of Circle/Square/Triangle,
  200×200, 28.87 MB) is correct.
- Source: https://www.kaggle.com/datasets/dineshpiyasamara/geometric-shapes-dataset

### 2.2 frobertpixto hand-drawn-shapes-dataset (GitHub) — size and classes wrong
- Draft said: ~1,200 images, 5 classes (circle/square/triangle/ellipse/rectangle).
- Verified: **27,292 PNG images, 70×70, single-channel grayscale**, across
  **4 classes: Rectangle (6,956), Ellipse (6,454), Triangle (6,595), Other
  (7,287)** — no distinct circle or square class.
- License is not actually ambiguous: **CC BY 4.0 for the data, MIT for the
  code/notebooks** (both apply, to different parts of the repo).
- Source: https://github.com/frobertpixto/hand-drawn-shapes-dataset

### 2.3 Mendeley d35tjjgjnx ("2D Geometric shapes with properties") — wrong on everything but license
- Draft said: real-world photos/scans, ~2,500-4,000 images, covers
  pentagon/hexagon/octagon.
- Verified: **CC BY 4.0** confirmed, but it is **380,000 synthetic
  black-and-white 200×200 images across 76 classes** (7 base shapes x
  property combinations: circle, triangle, square, rectangle, rhombus,
  parallelogram, trapezium) — **no pentagon, hexagon, or octagon class at
  all**, and not real photographs.
- Source: https://data.mendeley.com/datasets/d35tjjgjnx/1

### 2.4 Mendeley ypfcrfxjgk ("Geometrical shapes datasets") — wrong on everything but license
- Draft said: same as 2.3.
- Verified: **CC BY 4.0** confirmed, but it is a **9,000-image synthetic set**
  (1,800 grayscale 64×64 + 7,200 color 64×64) limited to **circle, triangle,
  stripe patterns, and background** — no pentagon/hexagon/octagon, not real
  photographs.
- Source: https://data.mendeley.com/datasets/ypfcrfxjgk/1

### 2.5 swastikarajkower (Kaggle) — not an image dataset; currently miscited in the real report
- Draft said: MIT license, ~5,000 images, 9 classes of textured/colored
  renders.
- Verified: **this is not an image dataset.** It is a single CSV of
  **1,200 rows of numeric shape geometry** (side counts, angles, perimeter,
  area) across 12 shape labels. **No license is stated on the page at all**
  (the draft's "MIT" is unsupported).
- **Action required beyond this plan file:** `phase1_report.tex` currently
  cites this as reference [3], described as an image dataset. It must be
  either removed from the bibliography or re-described accurately (as a
  non-image, geometry-descriptor dataset that cannot serve the
  classification task) before the report is considered final.
- Source: https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset

## 3. Likely root cause
Every error above shares a pattern: claims of "real-world photos" or a
specific pentagon/hexagon/octagon class list, each time contradicted by
direct inspection. This suggests the original drafts were written from
secondhand summaries or conflated between similarly-named Mendeley entries,
not from the source pages themselves — worth remembering before trusting
future unverified dataset claims in this project.

## 4. Action items
- [ ] Update `01_dataset_details.md` and `03_more_datasets.md` with the
      corrected facts above (or mark the old entries superseded by this file).
- [ ] Remove or correct citation [3] (`kaggleswastika`) in
      `phase1_report.tex` — it cannot be presented as an image source.
- [ ] Correct the license field for `kagglereevald`-adjacent dataset
      (dineshpiyasamara, if it is reintroduced) to "Unknown," not CC0.
- [ ] If the hand-drawn GitHub set is adopted, update any taxonomy-mapping
      table to use its real 4 classes (Rectangle/Ellipse/Triangle/Other),
      not the previously assumed 5.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Every fact was read from the dataset's own page (Kaggle About and Data Explorer, GitHub README, Mendeley metadata).

## Our decision

We corrected the bibliography and Section B. swastikarajkower is a CSV with no images, the two Mendeley sets are synthetic, and Dinesh's license is 'Unknown', so Dinesh was excluded (plan 06, todo).

## Measured effect

4 of 5 drafted dataset claims were corrected before submission. No model at this stage.
