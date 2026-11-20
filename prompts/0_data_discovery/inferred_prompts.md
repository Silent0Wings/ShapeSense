#  prompts: 0_data_discovery

> **These are reconstructions, not the original prompts.** The original prompts are not reproduced here.
> Each prompt below was inferred afterwards from the source map (`docs/source.md`) and the Phase 1 report.
> The decision and its reason are copied from that source map. Where no LLM is recorded, the prompt is the question
> the team worked on. No LLM response is reproduced here.

> Each **Answer** below was written on 2026-11-20 from the recorded cause, outcome and results. It is not the original LLM reply.

<a id="s01"></a>

## S01 - Chose four complementary public sources: Google QuickDraw, Kaggle reevald, Mendeley El Korchi and GitHub frobertpixto hand-drawn shapes.

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> We need images of ten 2D shapes (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond). Which public datasets cover these classes, under what license, with what image style and size? Which combination covers every class?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No single public dataset covers all ten classes, but four openly licensed sources do together (`docs/source.md`):

- **Google Quick, Draw!** (CC BY 4.0): 7 NDJSON stroke files, 500 recognized drawings each, for circle, diamond, hexagon, octagon, square, star and triangle. Sketch style; you rasterise the strokes yourself.
- **Kaggle reevald** (CC0): 20,000 JPG at 224x224 RGB, 8 classes x 2,500. Clean rendered shapes, and the only source with a rhombus folder for diamond. Its kite, trapezoid and parallelogram folders fall outside the taxonomy.
- **Mendeley El Korchi** `wzr2yv7r53/1` (CC BY 4.0): 90,000 PNG at 200x200 RGB, 9 classes x 10,000. Synthetic polygons, and the only source of pentagon. Drop its heptagon and nonagon.
- **GitHub frobertpixto** (CC BY 4.0 data, MIT code): 27,292 PNG at 70x70 RGBA in 4 classes (ellipse, rectangle, triangle, other). Hand-drawn, and the only source of ellipse. Drop `other`.

Use all four. Opus recommended exactly this set (`claude_opus/01_four-public-sources.md`). Its caveats were: ellipse and pentagon are single-source classes, so report them with that flag; sizes differ (vector, 70, 200 and 224 px), so standardise them in the build; counts are very uneven, so cap per source and class; and keep a `source` column so you can measure per-source accuracy. The repo later confirmed that the source risk is real. A classifier told an image's source 91.7% of the time (F05, `results/phase2_snapshot/shortcut_notice.md`).

**Documented reason:** No single source covers all ten classes, so the sources were chosen to cover them together and to mix sketches, printed and rendered shapes. Licenses: CC BY 4.0 or CC0.

<a id="s02"></a>

## S02 - Excluded the Kaggle dinesh geometric shapes dataset after downloading it (30,000 PNG).

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> Here is a dataset we downloaded: <Kaggle dinesh geometric shapes>. Can we use it legally, and does it add any class or style our other sources lack?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No on both counts, so exclude it. Its Kaggle license field reads "Unknown" (`docs/source.md`). Downloading the files gives you no redistribution right, and every other source is CC0 or CC BY 4.0. Its content is 30,000 PNG at 200x200 RGB: circle, square and triangle, 10,000 each. Three other sources already cover those classes, so it adds no class. Opus noted that its synthetic, flat-filled style is close to El Korchi's, so it adds no new style either, and 30,000 more images of the best-covered classes would only worsen the imbalance (`claude_opus/02_exclude-kaggle-dinesh.md`). To check, read the license field on the Kaggle page and compare its class list against the coverage of the four kept sources. Record the exclusion and its reason in the source map, which now lists it under "Installed but excluded".

**Documented reason:** Its Kaggle license field reads Unknown, and it adds only circle, square and triangle, which three other sources already cover.

<a id="s03"></a>

## S03 - Rejected Mendeley d35tjjgjnx (380,000 synthetic images) without downloading it.

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> Does the Mendeley dataset d35tjjgjnx fill any class we are missing (pentagon, hexagon, octagon)?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No. It is CC BY 4.0, so the license is fine, but its 380,000 synthetic images come from only 7 base shapes combined with property labels, and none of those shapes is a pentagon, hexagon or octagon (`docs/source.md`). Opus re-checked the Mendeley page and listed the base shapes as circle, triangle, square, rectangle, rhombus, parallelogram and trapezium, giving 76 classes of black-and-white 200x200 images with marks such as diagonals and radii drawn on the shapes (`claude_opus/03_reject-mendeley-d35tjjgjnx.md`). It would add more copies of classes you already have, plus annotation marks you would have to clean away. Pentagon stays single-source (El Korchi only). The metadata alone settles the question, so reject it without downloading and list it under "Identified, evaluated, not downloaded" so nobody evaluates it again.

**Documented reason:** CC BY 4.0, but only 7 base shapes with property labels and no pentagon, hexagon or octagon, so it fills no gap.

<a id="s04"></a>

## S04 - Rejected Mendeley ypfcrfxjgk (9,000 synthetic 64x64 images) without downloading it.

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> Is the Mendeley dataset ypfcrfxjgk useful for a ten-class shape classifier?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No. It is CC BY 4.0, but its 9,000 synthetic 64x64 images contain only circles, triangles, stripes and empty backgrounds (`docs/source.md`). Circle and triangle are already the best-covered classes. Stripes and background are not shapes in the taxonomy, and the taxonomy has no reject class to put them in. The other eight classes are missing. Opus added that 64x64 is smaller than any kept source, that the colour subset uses only red, blue and grey, and that the files ship as pickles inside a zip, which means an extra conversion step for no gain (`claude_opus/04_reject-mendeley-ypfcrfxjgk.md`). Reject it without downloading and record the reason in the source map.

**Documented reason:** CC BY 4.0, but only circles, triangles, stripes and background.

<a id="s05"></a>

## S05 - Rejected the Kaggle swastikarajkower geometric shapes classification dataset.

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> Is the Kaggle swastikarajkower geometric shapes dataset made of images we can train a CNN on?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No. Despite its name, it is not an image dataset. It is a 1,200-row CSV of numeric shape measurements (`docs/source.md`). Opus listed the 20 columns: side counts, side lengths, angles, perimeter, area, radius and similar values (`claude_opus/05_reject-kaggle-swastikarajkower.md`). A CNN needs pixels, and these measurements cannot be turned back into images, so the data is unusable for this classifier even though it names pentagon, hexagon and ellipse. Reject it. One fact is unsettled: `docs/source.md` says "no license stated", but the Opus and Gemini re-checks of the Kaggle page report an MIT license (`claude_opus/05_...`, `gemini_4_neon/05_...`). The repo has not reconciled the two. The rejection stands on the data type alone, whatever the license.

**Documented reason:** Not an image dataset: a 1,200-row CSV of numeric shape measurements, with no license stated.

<a id="s06"></a>

## S06 - Removed duplicate downloads on 2026-10-19.

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> Several folders in data_set/ look like copies of each other. How do we prove two folders are identical before deleting one?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Compare file content, not names, counts or total size, because two folders can match on all three and still differ. The steps:

1. For each folder, build a manifest of (relative path, size, MD5) for every file, sorted by path.
2. Compare file counts and total bytes first, since that catches partial copies cheaply.
3. Diff the manifests. Every pair must appear on both sides. For renamed copies, such as Windows `(2)` suffixes, match by MD5 instead of by name.
4. For a zip, hash each entry inside it and compare entry by entry with the extracted folder. Never hash the zip file itself.
5. Do a dry run that lists what would be deleted and which kept copy each one matches. Then delete, and log each removal in the source map.

MD5 is fine here: the goal is to catch accidental copies, not to resist attack. `data_set/` is git-ignored, so check that each kept dataset can be re-downloaded before deleting anything (Opus, `claude_opus/06_remove-duplicate-folders.md`). That is what was done. `docs/source.md` records four removals on 2026-10-19, each verified by the MD5 of every file: `archive/` (30,000 files), `test/` (4,000 files), the nested QuickDraw copy and the 5 raw zips.

**Documented reason:** Four duplicate folders (archive/, test/, a nested QuickDraw copy, raw zips) were verified identical to the kept copy by the MD5 of every file, then deleted.

<a id="s07"></a>

## S07 - Defined each shape class mathematically, taking inspiration from the ElementaryCQT paper (2D geometric shape recognition).

- Kind: decision (data discovery, Phase 1)
- LLM: 

** prompt**

> How should each of our ten shape classes be defined precisely, so that we can decide whether an image belongs to it? Is there published work with mathematical definitions?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes. The ElementaryCQT paper (2D geometric shape recognition, listed in `docs/source.md`) defines circles, quadrilaterals and triangles geometrically. Use it as a reference for the definitions, not as training data: it does not cover all ten classes, and Opus noted that its dataset is the Mendeley `d35tjjgjnx` set rejected in S03 (`claude_opus/07_define-shape-classes.md`). The definitions recorded in `configs/taxonomy.yaml` are:

- **Circle:** a closed curve with equal axes.
- **Ellipse:** a closed curve with clearly unequal axes.
- **Triangle, pentagon, hexagon, octagon:** 3, 5, 6 and 8 vertices.
- **Square:** 4 equal sides and right angles, at any rotation.
- **Rectangle:** right angles and clearly unequal sides.
- **Star:** a star polygon whose vertices alternate between an outer and an inner radius.
- **Diamond:** a rhombus without right angles, at any rotation.

The three ambiguous pairs get margins so that no image can sit between two classes: `ellipse_min_axis_ratio: 1.2`, `rectangle_min_side_ratio: 1.2` and `diamond_min_angle_offset_deg: 10`. Shear and non-uniform scaling are disabled for circle, ellipse, square, rectangle and diamond, because those transforms change the class. Keep all of this in one config so that labelling, cleaning, augmentation and the generator all read the same rules. To check it, audit each source's labels against the definitions. That audit flagged the QuickDraw diamonds, and they were excluded (F01).

**Documented reason:** The definitions (for example, a diamond is a rhombus that is not a square) later decided which images belong to a class, including the QuickDraw diamond exclusion (F01).
