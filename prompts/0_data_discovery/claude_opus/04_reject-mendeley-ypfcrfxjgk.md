

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [01_evidence_opus-fact-checks-gemini-dataset-claims.md](../cross_critique/01_evidence_opus-fact-checks-gemini-dataset-claims.md), [09_evidence_more-datasets-draft.md](../gemini_4_neon/09_evidence_more-datasets-draft.md)

# 0_data_discovery - S04 - Rejected Mendeley ypfcrfxjgk without downloading

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: Reconstructed exchange grounded in docs/source.md, docs/data_sets.md, configs/taxonomy.yaml and inferred_prompts.md. The original Phase 1 chat transcript was not saved. The Mendeley ypfcrfxjgk page was re-checked on 2026-11-20.

## Prompt
> Is the Mendeley dataset ypfcrfxjgk useful for a ten-class shape classifier?

## Response (augmented)

Not really. It's licensed openly, but its content barely overlaps with your taxonomy.

### What it contains

- Mendeley `ypfcrfxjgk/1`, licensed **CC BY 4.0**. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **9,000 synthetic images at 64x64**, split into two subsets. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Subset 1: `bw_shapes_3_1800`** — grayscale, 64x64, 3 distinct types, 600 per type, 1,800 total. Types are grayscale circles, grayscale triangles, and empty grey backgrounds. Labels are 0-2 (circle, triangle, background). The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Subset 2: `col_shapes_9_7200`** — colour, 64x64, 9 distinct types, 800 per type, 7,200 total. Types are red/blue circles, red/blue triangles, red/blue horizontal stripes (wide red, narrow blue), red/blue vertical stripes (narrow red, wide blue), and empty grey backgrounds. Labels are 0-8. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- Total across both subsets: **9,000 images** (1,800 + 7,200). The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- Classes: **circles, triangles, stripes (horizontal and vertical, in red and blue), and background**. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)

### How that maps to your ten classes

- **circle**, **triangle**: already covered by three or four of your sources. Adding more would only duplicate existing coverage.
- **stripes** (horizontal and vertical, in red and blue): not shapes in your taxonomy. You'd have to drop them.
- **background**: not a shape in your taxonomy. You'd have to drop it.
- ellipse, square, rectangle, pentagon, hexagon, octagon, star, diamond: **not present**. The live page confirms only circles, triangles, stripes, and background are in the dataset. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)

### Style and build implications

- **64x64 resolution** is smaller than any of your current sources (70x70 hand-drawn, 200x200 El Korchi, 224x224 reevald). Upscaling would blur edges and add a resolution artefact that's specific to this source.
- **Grayscale subset** (1,800 images) is black and white, which is a different visual style from your colour sources. The live page confirms the grayscale subset. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Colour subset** (7,200 images) uses only red, blue, and grey. This is a very limited colour palette compared to your other sources. The live page confirms the red/blue/grey palette. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Variation in shade, size, and background** is mentioned for both subsets, which means the images have some augmentation but not the rotation/position/scale augmentation of El Korchi. The live page confirms the variation types. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Stripes have width variation** (r > 0.5 size for wide, b < 0.5 size for narrow, and vice versa for vertical). This is a property of the stripes, not a separate shape type. The live page confirms this. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Format is pickle/zip**, not PNG or JPG. This means you'd need to extract and convert before using, adding a preprocessing step. The live page confirms the pickle/zip format. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)

### Other concerns

- Adding more circles and triangles would only make your existing class imbalance worse.
- The 64x64 resolution is a hard constraint. Even if you wanted the circles and triangles, you'd be adding a low-res source that needs upsampling.
- The stripes and background classes are pure noise for your taxonomy. They'd need to be filtered out, which is extra cleaning work for no gain.

### Criterion table

| Option | Effect | Recommendation |
|---|---|---|
| Download and use circle/triangle images | Duplicates well-covered classes, low resolution, adds no new class | No |
| Download for "background" negatives | Your taxonomy has no background or reject class | No |
| Download for "stripes" as a texture feature | Not a shape class; would need a separate taxonomy | No |
| Reject without downloading | No coverage loss, no cleaning effort | **Yes** |

### Recommendation

Reject it without downloading, and record the reason (circles, triangles, stripes and background only) in the source map.

## Validation
- Checked against docs/source.md, as summarised in inferred_prompts.md S04.
- Re-checked against the live Mendeley ypfcrfxjgk page: 9,000 images, 64x64, two subsets (grayscale 1,800 + colour 7,200), classes are circles/triangles/stripes/background, CC BY 4.0, pickle/zip format, red/blue/grey palette. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- Confirmed: ellipse, square, rectangle, pentagon, hexagon, octagon, star, diamond are not present. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)

## Our decision
Rejected without download. CC BY 4.0, but it contains only circles, triangles, stripes and background (9,000 synthetic 64x64 images).

## Measured effect
Not downloaded. No macro F1 change applies.

## Notes on the log

- **Two subsets, not one:** the original log entry treated this as a single 9,000-image dataset. The live page shows it is actually two subsets: `bw_shapes_3_1800` (1,800 grayscale) and `col_shapes_9_7200` (7,200 colour). This is a detail worth recording, since the grayscale subset has a different style from the colour subset. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Stripes have sub-types:** horizontal vs vertical, wide vs narrow, red vs blue. This means "stripes" is not one class but several, which makes the mismatch with your taxonomy even clearer. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Pickle/zip format:** this is a practical detail the original log missed. Extraction and conversion would be needed before the images could be used, adding a preprocessing step even if you did want the circles and triangles. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Limited colour palette:** red, blue, and grey only. This is much narrower than your other sources, which use full RGB. Another reason it doesn't fit. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)
- **Related papers:** the live page links to three papers and one NCBI article, which suggests this dataset was built for a specific research purpose (autoencoder-based geometric embedding), not as a general-purpose shape classifier dataset. This is context worth noting if anyone asks why it looks so different from your other sources. [data.mendeley](https://data.mendeley.com/datasets/ypfcrfxjgk/1)