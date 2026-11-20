

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [01_evidence_opus-fact-checks-gemini-dataset-claims.md](../cross_critique/01_evidence_opus-fact-checks-gemini-dataset-claims.md), [09_evidence_more-datasets-draft.md](../gemini_4_neon/09_evidence_more-datasets-draft.md)

# 0_data_discovery - S05 - Rejected the Kaggle swastikarajkower dataset

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: Reconstructed exchange grounded in docs/source.md, docs/data_sets.md, configs/taxonomy.yaml and inferred_prompts.md. The original Phase 1 chat transcript was not saved. The Kaggle swastikarajkower page was re-checked on 2026-11-20.

## Prompt
> Is the Kaggle swastikarajkower geometric shapes dataset made of images we can train a CNN on?

## Response (augmented)

No. Despite the name, it isn't an image dataset at all.

### What it actually is

- `swastikarajkower/geometric-shapes-classification-dataset` is a **CSV file with 1,200 rows of numeric shape measurements**: tabular features computed from shapes, with no pixels. The live page confirms this. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- The file is `geometry_shapes_dataset.csv`, 94.86 kB, with 20 columns. The live page confirms this. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **A CNN needs image tensors as input. There's nothing here to convolve over.** The live page confirms the dataset is tabular, not image-based. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- You also can't recover images from it. Measurements like these don't contain enough information to redraw the original shapes. The live page confirms the features are numerical properties (sides, angles, perimeter, area, radius, diameter), not pixel data. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- The dataset is **synthetically generated using mathematical properties and formulas**, not scanned or rendered images. The live page confirms this. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)

### What the 20 columns contain

| Column | Description |
|---|---|
| `Num_Sides` | Number of sides of the shape |
| `Num_Vertices` | Number of vertices or corners |
| `Side_1` to `Side_6` | Lengths of up to 6 sides; 0 if not applicable |
| `Angle_1` to `Angle_4` | Interior angles in degrees |
| `Perimeter` | Total boundary length |
| `Area` | Calculated area |
| `All_Sides_Equal` | Binary flag (1/0) |
| `All_Angles_Equal` | Binary flag (1/0) |
| `Has_Right_Angle` | Binary flag (1/0) |
| `Radius` | Radius for circular shapes; 0 otherwise |
| `Diameter` | Diameter for circular/curved shapes; 0 otherwise |
| `Shape` | Target class label |

The live page confirms all 20 columns and their descriptions. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)

### The 12 shape classes

The dataset has 12 classes, not 10. The live page confirms this. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)

| Class | In your taxonomy? |
|---|---|
| Equilateral Triangle | Yes (maps to `triangle`) |
| Isosceles Triangle | Yes (maps to `triangle`) |
| Right Triangle | Yes (maps to `triangle`) |
| Square | Yes |
| Rectangle | Yes |
| Rhombus | Yes (maps to `diamond`) |
| Parallelogram | No |
| Trapezium | No |
| Pentagon | Yes |
| Hexagon | Yes |
| Circle | Yes |
| Ellipse | Yes |

### Why the class coverage doesn't help

- Even though it has pentagon, hexagon, and ellipse (classes you care about), the data is **tabular features, not images**. You can't train a CNN on it.
- The 3 triangle sub-types (equilateral, isosceles, right) would need to be collapsed back to one `triangle` class if you ever used this data.
- The `parallelogram` and `trapezium` classes are not in your taxonomy and would need to be dropped.
- The `rhombus` to `diamond` mapping is a definition choice, not a label match.

### License

- The page **does state a license: MIT**. The live page confirms this. This is a correction to the original log entry, which said "no license stated". [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- MIT is a permissive license that allows redistribution with attribution. So the license itself is not a problem.
- The real problem is the modality: it's tabular, not image-based, so it can't be used for a CNN regardless of license.

### Criterion table

| Criterion | swastikarajkower | Needed for your CNN |
|---|---|---|
| Modality | Tabular CSV (1,200 rows, 20 columns) | Images |
| Usable as CNN input | No | Yes |
| License | MIT | CC0 / CC BY 4.0 or similar |
| New classes | Pentagon, hexagon, ellipse present but as features, not images | Pentagon/ellipse would help if they were images |
| Image recovery possible | No | Yes |

### Recommendation

Reject it. Record it in the source map as "not an image dataset, tabular CSV with MIT license", so the name doesn't draw someone back to it later.

## Validation
- Checked against docs/source.md, as summarised in inferred_prompts.md S05.
- Re-checked against the live Kaggle swastikarajkower page: 1,200 rows, 20 columns, 12 classes, CSV format, MIT license, synthetic tabular data, no images. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **Correction to original log:** the original entry said "no license stated". The live page shows **MIT**. This should be updated in the source map. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)

## Our decision
Rejected. It is not an image dataset: a 1,200-row CSV of numeric shape measurements, with MIT license.

## Measured effect
Not used. No macro F1 change applies.

## Notes on the log

- **License correction:** the original log entry said "no license stated". The live page clearly shows **MIT**. This is a factual correction that should be propagated to the source map and any downstream documentation. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **12 classes, not 10:** the original log entry didn't mention the class count. The live page confirms 12 classes, including 3 triangle sub-types and 2 classes not in your taxonomy (parallelogram, trapezium). [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **20 columns detailed:** the original log entry said "numeric shape measurements" without listing them. The live page gives a full column-by-column description, which is worth recording for anyone who might revisit this dataset. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **Synthetic, formula-based:** the live page explicitly says the data is "synthetically generated using mathematical properties and formulas", which explains why there are no images and why the features are so clean and structured. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)
- **Low engagement:** 123 views, 11 downloads, 0 comments, 0 discussions. This suggests the dataset is not widely used or reviewed, which is another (minor) reason to be cautious, though not a blocker since the modality mismatch is already decisive. [kaggle](https://www.kaggle.com/datasets/swastikarajkower/geometric-shapes-classification-dataset)