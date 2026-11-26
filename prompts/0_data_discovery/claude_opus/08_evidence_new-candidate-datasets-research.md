# 0_data_discovery - Deep research for datasets that cover the missing classes

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19
- Owner: 40256377
- Worksheet entries: S01
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.
-  [S01](01_four-public-sources.md), [S01](../gemini_4_neon/01_four-public-sources.md)

## Prompt (inferred, not saved)

> _Inferred:_ Search for public, freely licensed 2D geometric-shape datasets beyond the ones already identified, to cover the under-represented classes: ellipse, pentagon, hexagon, octagon and star.

## Response (saved output, verbatim)

### `research_notes/Shape dataset integration and tooling/additional_datasets.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Additional Public 2D Geometric Shape Datasets (Beyond Already-Identified Sources)

## What other public, freely licensed 2D geometric shape datasets exist (Kaggle, Hugging Face, Mendeley, GitHub, Papers With Code, academic repos)?

### Takeaway
Several additional candidates exist beyond the already-identified list, most usefully a Mendeley synthetic dataset (El Korchi) that directly covers pentagon, hexagon, octagon, and star in one set, plus a Hugging Face 8-class dataset and several Roboflow Universe CC BY 4.0 projects that individually cover pentagon/hexagon. No new Kaggle dataset was found that specifically adds pentagon/hexagon/octagon coverage beyond what's already identified — Kaggle search results kept surfacing the already-known "Four Shapes" dataset (square/star/circle/triangle only) or pointed back to the Mendeley/Roboflow sources below.

### Cited Findings
- **Mendeley "2D geometric shapes dataset" by Anas El Korchi** (DOI 10.17632/wzr2yv7r53.1) — License: **CC BY 4.0**. 9 classes: Triangle, Square, Pentagon, Hexagon, Heptagon, Octagon, Nonagon, Circle, Star. 10,000 generated images per class, each a 200×200 RGB image. Links to a generator source-code repo for creating more data. Directly covers 4 of the 5 underrepresented target classes (pentagon, hexagon, octagon, star) — only ellipse and diamond/rectangle are missing from this set. — [Mendeley](https://data.mendeley.com/datasets/wzr2yv7r53/1); generator code at [git.tdem.in/elkorchi/2DGeometricShapesGenerator](https://git.tdem.in/elkorchi/2DGeometricShapesGenerator)
  - Note: this may overlap with one of the two Mendeley datasets the project has already identified — the exact two prior Mendeley datasets were not specified in the research brief, so this should be cross-checked against the project's existing list before treating it as "new."
- **Mendeley "Geometrical shapes datasets" by Serge Dolgikh** (DOI 10.17632/ypfcrfxjgk) — a labeled dataset for supervised/unsupervised learning with a grayscale set (1,800 images, 64×64) and a color set (7,200 images). Labels cover circles, triangles, stripes, and blank backgrounds only — does **not** cover pentagon/hexagon/octagon/star/ellipse, so it is low priority for this project's gap. — [Mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk)
- **Mendeley "2D Geometric shapes with properties"** (DOI 10.17632/d35tjjgjnx.1) — License: **CC BY 4.0**. 76 classes combining 7 base shapes (circle, triangle, square, rectangle, rhombus, parallelogram, trapezium) each paired with a geometric property label (diagonal, perpendicular, chord, radius, diameter, equal-side marks). 380,000 black-and-white images, fixed 200×200 resolution; file format not stated on the page. Does not add pentagon/hexagon/octagon/star/ellipse coverage. — [Mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- **Hugging Face `itshemantkmr/2D_Shape_Image_Datasets`** — License: **Apache-2.0**. Image-classification dataset, imagefolder format, .jpg images at 224×224, 20,000 images total (12k train / 4k validation / 4k test). The dataset card states 8 classes; the only one confirmed from the preview was "circle" (other 7 not independently confirmed in this research pass — a related model card for the same 8-class set, `Jan358/Geometric-Shapes-Classification`, lists the classes as circle, kite, parallelogram, rectangle, rhombus, square, trapezoid, triangle, suggesting this dataset does **not** cover pentagon/hexagon/octagon/star/ellipse either). — [Hugging Face dataset](https://huggingface.co/datasets/itshemantkmr/2D_Shape_Image_Datasets); [related model](https://huggingface.co/Jan358/Geometric-Shapes-Classification)
- **Hugging Face `driesverachtert/basic_shapes_object_detection`** — License: **Apache-2.0**. Object-detection (not classification) parquet dataset, 1K–10K images. Noted as a small example set; shape-class coverage for the target taxonomy not confirmed. — [Hugging Face](https://huggingface.co/datasets/driesverachtert/basic_shapes_object_detection)
- **Roboflow Universe — "line new" (babag)** — License: **CC BY 4.0**. 12 classes including hexagon and pentagon, plus circle, triangle, square, and others. — [Roboflow](https://universe.roboflow.com/babag/line-new)
- **Roboflow Universe — "shapes" (Edhitha2024)** — License: **CC BY 4.0**. Classes: circle, triangle, cross, star, pentagon. — [Roboflow](https://universe.roboflow.com/edhitha2024/shapes-fquuk)
- **Roboflow Universe — "shape detection" (VisionModel)** — License: **CC BY 4.0**. Classes include hexagon variants ("hexagon, hexagon2, hexagon4, shapes"). — [Roboflow](https://universe.roboflow.com/visionmodel-5czit/shape-detection-vedft)
- **Roboflow Universe — "Shapes" (Object Detection, user vlltb)** — License: **CC BY 4.0**. Classes: cuboid, hexagon. — [Roboflow](https://universe.roboflow.com/object-detection-vlltb/shapes-xvtzb)
- **Roboflow Universe — "hexagon" (macaron)** — License: **CC BY 4.0**. Hexagon-focused dataset. — [Roboflow](https://universe.roboflow.com/macaron/hexagon-wi28y)
- **No octagon-specific Roboflow or Kaggle dataset was found** in this research pass; octagon coverage beyond the already-identified sources currently relies on the Mendeley El Korchi dataset above.
- **Kaggle "Four Shapes" dataset** (mirrored on HyperAI) — 16,000 images, 200×200, of square/star/circle/triangle only, shapes were physical poster-board cutouts painted green and photographed, then cropped/resized (i.e., this is a **photo-based**, not purely synthetic/render, dataset, though of cutouts rather than real-world objects). License was not confirmed in search snippets — the Kaggle page's license field should be checked directly before use. This appears to be the same or a near-duplicate of one of the project's already-identified star-containing sources; flagged for cross-check rather than treated as new. — [HyperAI mirror](https://vercel.hyper.ai/en/datasets/29901)

### Inferences
- The clearest net-new, well-licensed, high-value addition for the stated gap (ellipse, pentagon, hexagon, octagon, star) is the Mendeley El Korchi "2D geometric shapes dataset" (CC BY 4.0), since it is the only single dataset found that covers pentagon, hexagon, octagon, and star simultaneously with a large, balanced (10k/class), well-documented, redistributable set — pending confirmation it isn't already one of the project's two existing Mendeley sources.
- Ellipse remains the hardest class to source from a dedicated, well-known public image dataset; the only reliable fit found was the synthetic dSprites benchmark (see benchmark question below), not a Kaggle/Mendeley/HF classification set.
- Roboflow Universe listings are useful as supplementary, single- or few-class augmentation sources (e.g., a dedicated hexagon or pentagon set) rather than as one complete 10-class dataset, and each would need its CC BY 4.0 attribution carried through.

### Gaps
- Could not confirm the full 8-class list for `itshemantkmr/2D_Shape_Image_Datasets` directly from the dataset card (only "circle" was visible in the preview); the inferred class list comes from a related model card and should be verified against the dataset's actual folder listing before relying on it.
- Could not confirm the Kaggle "Four Shapes" dataset's license field directly (Kaggle page not fetched directly in this pass); flagged rather than stated as confirmed open license.
- Did not verify whether the two Mendeley datasets already identified by the project are the same as, or different from, El Korchi's `wzr2yv7r53` and/or Dolgikh's `ypfcrfxjgk` found here — the research brief did not specify which two Mendeley datasets were already known, so this needs a direct cross-check against the project's existing source list.
- Did not find any dedicated Papers With Code dataset page for a 10-class (or similar) 2D shape classification benchmark; Papers With Code search was not separately executed due to tool-call budget — this is a residual gap.

## Are there any well-known synthetic shape-generation benchmark datasets (used in geometry/shape-recognition papers) that are freely redistributable?

### Takeaway
Yes — dSprites, from DeepMind, is the most well-known synthetic shape benchmark used widely in disentangled-representation-learning papers, and its upstream license is permissive, though downstream mirrors describe it inconsistently.

### Cited Findings
- **dSprites** (DeepMind) — contains three shapes only: **square, ellipse, and heart** (not polygon shapes), each combined exhaustively with color, scale, rotation, and x/y position for 737,280 total images. — [GitHub](https://github.com/google-deepmind/dsprites-dataset); [TensorFlow Datasets catalog](https://www.tensorflow.org/datasets/catalog/dsprites)
- The original GitHub repository's license text is a permissive, zlib-style notice: "Permission is granted to anyone to use this software for any purpose, including commercial applications... and to alter it and redistribute it freely," with a request (not a license term) to cite a given BibTeX entry. — [GitHub](https://github.com/google-deepmind/dsprites-dataset)
- Two Hugging Face mirrors (`TalBarami/msd_dsprites_static`, `TalBarami/msd_dsprites_dynamic`) label the dataset as **Apache License 2.0** and state they redistribute it "solely for non-commercial research purposes" — this conflicts with the permissive, unrestricted wording in the original upstream repo. — [Hugging Face](https://huggingface.co/datasets/TalBarami/msd_dsprites_static/blob/main/README.md)
- dSprites would add the **ellipse** class (one of the five underrepresented target classes) but does not cover pentagon, hexagon, octagon, or star, and its "square" shape differs visually from the taxonomy's square/rectangle/diamond distinctions since dSprites objects are simple filled silhouettes without the richer stylistic variety of drawn/rendered shape datasets.

### Inferences
- Because of the conflicting license statements between the upstream GitHub repo (permissive/unrestricted) and the Hugging Face mirrors (Apache-2.0 + non-commercial-only framing), the project should treat the **original DeepMind GitHub repository** as the authoritative license source if dSprites is used, and should re-verify the current LICENSE file directly rather than relying on either secondary description.
- dSprites is best used narrowly, as a supplementary ellipse-class source, not as a general-purpose 10-class dataset.

### Gaps
- Did not find other widely-cited synthetic shape benchmark datasets beyond dSprites (e.g., no clear freely-redistributable CLEVR-shapes-only subset or "Tangram" dataset surfaced in this search pass as a standalone classification set); more targeted search for "shape-recognition paper benchmark dataset" was not performed due to tool-call budget and may be needed in follow-up research.

## Are there any photo-based (not just render/sketch) geometric shape datasets, since the project currently has no photograph-of-real-object domain?

### Takeaway
True photograph-based geometric shape datasets are rare; the one credible candidate found is the Kaggle/HyperAI "Four Shapes" dataset of physically cut poster-board shapes photographed with a camera, but it only covers 4 classes (square, star, circle, triangle) and its license was not confirmed. No photo-based dataset covering pentagon/hexagon/octagon/ellipse was found.

### Cited Findings
- **"Four Shapes" dataset** (Kaggle-sourced, mirrored on HyperAI) — 16,000 images at 200×200 pixels; shapes were physically cut from poster board, painted green, photographed with a camera, then cropped/resized from the photographs and sorted into folders by shape; covers square, star, circle, triangle only. License not confirmed from available snippets. — [HyperAI mirror](https://vercel.hyper.ai/en/datasets/29901)
- Broader web search for "real-world photograph geometric shapes dataset objects classification" mostly surfaced synthetic render datasets (the same Mendeley/El Korchi set, the "2D Geometric shapes with properties" set) rather than photographs, and two tangential real-photo datasets that are **not** abstract-shape classification: **GeoSetEnnea** (966 smartphone photos of physical geometric drafting tools — compasses, protractors, set squares — across 9 classes, aimed at object detection, not shape silhouette classification) and **GeoMat** (a material-recognition photo dataset of building/ground surfaces, unrelated to shape outlines). — [GeoSetEnnea, Mendeley](https://data.mendeley.com/datasets/fg97mhsdbr); [GeoMat paper](https://arxiv.org/pdf/1607.05338)

### Inferences
- There is a genuine, confirmed gap in publicly available, clearly-licensed photograph-based 2D shape classification datasets (as opposed to rendered/synthetic or hand-drawn/sketch datasets). If a photograph-of-real-object domain is a project priority, the most practical paths are either (a) using the Four Shapes dataset for partial (4-class) photo coverage pending its license being confirmed as open, or (b) the project collecting its own small photographed shape set (e.g., physical cutouts or real-world objects such as stop signs for octagon, street signs for pentagon, etc.), since no existing public dataset was found that fills this niche across all 10 target classes.

### Gaps
- Could not confirm the Kaggle "Four Shapes" dataset's exact license terms (page not fetched directly); this must be checked on the live Kaggle listing before use.
- No photo-based dataset covering pentagon, hexagon, octagon, or ellipse was found in this research pass. It remains possible such a dataset exists but was not surfaced by the queries used (e.g., datasets of photographed traffic/road signs, which naturally include octagon (stop signs), pentagon, and other polygon shapes, were not explicitly searched and are a promising follow-up lead — e.g., known road-sign datasets like the German Traffic Sign Recognition Benchmark (GTSRB) or Mapillary Traffic Sign Dataset were not checked for license/shape-label granularity in this pass).
````

### `07_new_candidate_datasets.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE: El Korchi included (verified 90,000 PNG, 9 classes). dSprites not needed (hand-drawn covers ellipse).

# Plan 07: New Candidate Datasets Found (Taxonomy Gap Coverage)

## 1. Why this exists
A deep-research pass searched for public 2D geometric-shape datasets beyond
the ones already identified, specifically to cover the taxonomy's
underrepresented classes: ellipse, pentagon, hexagon, octagon, star. Full
sourcing: `research_notes/Shape dataset integration and tooling/additional_datasets.md`.

## 2. Best find: El Korchi Mendeley set closes most of the gap
- **Name**: "2D geometric shapes dataset" by Anas El Korchi.
- **DOI / URL**: https://data.mendeley.com/datasets/wzr2yv7r53/1
- **License**: CC BY 4.0.
- **Scale**: 10,000 generated 200×200 RGB images **per class**, across
  **9 classes**: Triangle, Square, Pentagon, Hexagon, Heptagon, Octagon,
  Nonagon, Circle, Star (90,000 images total).
- **Why it matters**: directly supplies 4 of the 5 hardest-to-source target
  classes (pentagon, hexagon, octagon, star) in one well-documented,
  redistributable package. Also links to its own generator source code, so
  more samples could be produced if needed.
- **Caveat**: not yet downloaded or cross-checked against what's already in
  `data_set/`. The `data_set/Zip/2D geometric shapes dataset/` folder
  already present on disk has a generic-enough name that it might already be
  this dataset (or might not) — the folder was found empty on a quick check
  and needs proper extraction/verification before assuming it's this source.

## 3. Ellipse remains unsolved
No classification-style dataset with a clean ellipse class was found.
Closest option: **dSprites** (DeepMind), a disentangled-representation
benchmark with only 3 shapes (square, ellipse, heart) across 737,280 images
combining shape x color x scale x rotation x position.
- Source (authoritative): https://github.com/google-deepmind/dsprites-dataset
- **License warning**: the original GitHub repo uses permissive, zlib-style
  language (any use including commercial). Two Hugging Face mirrors instead
  label it Apache-2.0 "non-commercial only" — a direct conflict. **Always
  cite/use the GitHub repo as the license source, never a HF mirror.**

## 4. Smaller supplementary sources (single/few-class only, all CC BY 4.0)
Roboflow Universe projects — useful only as small top-ups, each needs its
own attribution carried through the merged corpus:
- "line new" (babag) — hexagon + pentagon: https://universe.roboflow.com/babag/line-new
- "shapes" (Edhitha2024) — pentagon + circle/triangle/star: https://universe.roboflow.com/edhitha2024/shapes-fquuk
- "shape detection" (VisionModel)
- "Shapes" (vlltb)
- "hexagon" (macaron)

## 5. Explicitly a dead end
- Hugging Face `itshemantkmr/2D_Shape_Image_Datasets` (Apache-2.0, 20k
  images, 224×224 JPG): class list could not be fully confirmed, but a
  related model card suggests its classes are circle/kite/parallelogram/
  rectangle/rhombus/square/trapezoid/triangle — **does not cover the
  pentagon/hexagon/octagon/star gap**. Do not assume it helps without direct
  verification of the dataset card.
- No octagon-specific standalone dataset was found beyond El Korchi's set.

## 6. Confirmed gap: no photo-domain dataset exists
No public dataset of photographs of real/physical shape objects covering
the full 10-class taxonomy was found. Closest: Kaggle/HyperAI "Four Shapes"
(physical poster-board cutouts, photographed, cropped) — only 4 classes
(square, star, circle, triangle), license unconfirmed.
**Unexplored lead, not yet checked**: road-sign photo datasets (e.g. GTSRB,
Mapillary Traffic Sign Dataset) naturally contain octagons (stop signs) and
pentagons (other sign shapes) — license and label granularity not checked
in this research pass.

## 7. Action items
- [ ] Verify whether `data_set/Zip/2D geometric shapes dataset/` is actually
      the El Korchi dataset; if not, download it properly from the Mendeley
      URL above.
- [ ] If adopted, add El Korchi as a new cited source in `phase1_report.tex`
      Section B, with real measured stats once extracted (don't reuse the
      page's claimed 10k/class figure without a local file count).
- [ ] Decide whether dSprites is worth adding for ellipse coverage, citing
      the GitHub repo specifically (not a HF mirror) for its license.
- [ ] If a photo domain is wanted, investigate road-sign datasets as a lead.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

The licence (CC BY 4.0) and the file count (90,000 PNG, 9 classes) of the El Korchi set were checked after download.

## Our decision

We included El Korchi. dSprites was not needed, because the hand-drawn set covers ellipse (plan 07 status).

## Measured effect

Pentagon, hexagon, octagon and star got real images. No model at this stage.
