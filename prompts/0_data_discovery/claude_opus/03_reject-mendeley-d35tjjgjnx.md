

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [01_evidence_opus-fact-checks-gemini-dataset-claims.md](../cross_critique/01_evidence_opus-fact-checks-gemini-dataset-claims.md), [09_evidence_more-datasets-draft.md](../gemini_4_neon/09_evidence_more-datasets-draft.md)

# 0_data_discovery - S03 - Rejected Mendeley d35tjjgjnx without downloading

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: Reconstructed exchange grounded in docs/source.md, docs/data_sets.md, configs/taxonomy.yaml and inferred_prompts.md. The original Phase 1 chat transcript was not saved. The Mendeley d35tjjgjnx page was re-checked on 2026-11-20.

## Prompt
> Does the Mendeley dataset d35tjjgjnx fill any class we are missing (pentagon, hexagon, octagon)?

## Response (augmented)

No. It looks attractive on paper, but it doesn't fill the gaps you care about.

### What it is

- Mendeley `d35tjjgjnx/1`, licensed **CC BY 4.0**, so the license itself is fine. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- **380,000 black and white images** at a fixed resolution of **200 x 200 pixels**. The live page confirms this count and resolution. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- Built from **7 base shapes** (Circle, Triangle, Square, Rectangle, Rhombus, Parallelogram, Trapezium) combined with **property labels** (diagonal, perpendicular, chord, radius, diameter, symbol showing sides are equal). The live page confirms these 7 base shapes and 5 property types. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- This gives **76 total classes** (7 shapes x some property combinations). The live page confirms the 76-class count. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- Its base shapes don't include **pentagon**, **hexagon** or **octagon**, which are exactly the classes you asked about. The live page confirms the 7 base shapes and none of them are pentagon, hexagon or octagon. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)

### Why the size doesn't help

- The large image count comes from combining a few shapes with many properties. That gives you lots of variations of shapes you already have, not new classes.
- Pentagon is your weakest class: only El Korchi has it. This dataset doesn't change that.
- Hexagon and octagon are also not in the 7 base shapes, so they get no new coverage either.
- Downloading and auditing 380,000 files costs disk space, hashing time and cleaning effort, for no gain in coverage.

### Style and build implications

- The images are **black and white** (white background, black foreground), which is a different visual style from your other sources. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- Random rotation between -180° and 180°, random shape perimeter, and random shape position inside the image. The live page confirms these augmentation properties. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- The 200x200 resolution matches El Korchi, so no resizing would be needed if you ever did include it. The live page confirms the 200x200 resolution. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- The property labels (diagonal, perpendicular, chord, radius, diameter, equal-sides symbol) are annotations drawn on the shape, not separate shape types. This means the images are not clean shape-only images; they have extra marks that would need to be handled if you ever used them.

### Criterion table

| Criterion | d35tjjgjnx/1 | Needed? |
|---|---|---|
| License | CC BY 4.0 | OK |
| Pentagon / hexagon / octagon | None of the 7 base shapes | **Missing, which is the reason you'd want it** |
| Classes beyond current coverage | None | No gain |
| Cost to adopt | 380,000 images to download, hash and clean | High |
| Style match | Black and white, property annotations on shapes | Mismatch with your other sources |
| Resolution | 200x200 | Matches El Korchi, but irrelevant since it's rejected |

### Recommendation

Reject it without downloading. List it in the source map under "identified, evaluated, not downloaded" with the reason (no pentagon, hexagon or octagon, so no gap filled), so nobody evaluates it again.

## Validation
- Checked against docs/source.md, as summarised in inferred_prompts.md S03.
- Re-checked against the live Mendeley d35tjjgjnx page: 380,000 images, 200x200, 7 base shapes, 5 property types, 76 total classes, CC BY 4.0, black and white, random rotation/position/perimeter. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- Confirmed: none of the 7 base shapes are pentagon, hexagon or octagon. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)

## Our decision
Rejected without download. CC BY 4.0, but only 7 base shapes with property labels and no pentagon, hexagon or octagon, so it fills no gap. Size: 380,000 synthetic images.

## Measured effect
Not downloaded. No macro F1 change applies.

## Notes on the log

- **7 base shapes confirmed:** the live page lists Circle, Triangle, Square, Rectangle, Rhombus, Parallelogram, Trapezium. None of these are pentagon, hexagon or octagon, which confirms the rejection reason. [data.mendeley](https://data.mendeley.com/datasets/d35tjjgjnx/1)
- **76 classes explained:** 7 shapes x property combinations = 76 total classes. This is more granular than your 10-class taxonomy, so even if you did use it, you'd need to collapse the property variants back to base shapes.
- **Property annotations are a hidden cost:** the images have diagonal, perpendicular, chord, radius, diameter, and equal-sides symbols drawn on them. This means they are not clean shape-only images. If you ever did include this dataset, you'd need to either crop out the annotations or accept them as part of the style.
- **Black and white style mismatch:** your other sources are colour (RGB). This dataset is black and white. This is another reason it doesn't fit your unified dataset even if the classes did match.
- **No download needed:** the decision to reject without downloading is correct, since the class coverage gap is visible from the metadata alone. No need to spend disk space or hashing time on a dataset that fills no gap.