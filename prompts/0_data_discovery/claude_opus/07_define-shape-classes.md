

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_define-the-ten-classes.md](10_evidence_define-the-ten-classes.md)

# 0_data_discovery - S07 - Defined each shape class mathematically

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: Reconstructed exchange grounded in docs/source.md, docs/data_sets.md, configs/taxonomy.yaml and inferred_prompts.md. The original Phase 1 chat transcript was not saved. The ElementaryCQT paper was re-checked on 2026-11-20.

## Prompt
> How should each of our ten shape classes be defined precisely, so that we can decide whether an image belongs to it? Is there published work with mathematical definitions?

## Response (augmented)

Yes. A useful reference is **ElementaryCQT** (*A New Dataset and its Deep Learning Analysis for 2D Geometric Shape Recognition*, published in SN Computer Science, 2024). It defines elementary circles, quadrilaterals and triangles geometrically. Use it as a **geometry reference for your definitions, not as a training dataset**. Its figures target geometry-problem pipelines and don't match your ten classes. The paper is by Archana Boob and Mansi Radke, published 18 December 2024, with DOI 10.1007/s42979-024-03521-w. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)

### What ElementaryCQT actually covers

- The paper's dataset is called ElementaryCQT, where CQT stands for Circle, Quadrilateral, Triangle. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- It includes shapes **with and without geometric properties** like diagonals, perpendiculars, chords, tangents, etc.. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- Its typical shapes are circles, triangles, squares, rectangles, parallelograms, trapeziums, rhombus, etc.. This overlaps with your taxonomy but doesn't match it exactly. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- The paper's purpose is to support geometry-problem solving (figures plus input text), not general shape classification. This is why it's a reference for definitions, not a training dataset. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- The paper reports a ResNet50 F1 score of 81.86% and accuracy of 81.97% on its own dataset, which is context for how hard the task is even with a purpose-built dataset. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- The dataset is hosted on Mendeley at `d35tjjgjnx/1`, which is the same dataset you rejected in S03 for not having pentagon, hexagon or octagon. This is a useful cross-reference: the same dataset you rejected for coverage is the one you're using here for definitions. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)

### Definitions

| # | Class | Definition | Main confusion |
|---|---|---|---|
| 0 | circle | Closed curve, all points equidistant from a centre (equal axes) | ellipse |
| 1 | ellipse | Closed curve with **clearly unequal** axes | circle |
| 2 | triangle | Closed polygon with 3 vertices | none |
| 3 | square | 4 equal sides, four 90° angles, any rotation | rectangle, diamond |
| 4 | rectangle | 4 sides, four 90° angles, **clearly unequal** adjacent sides | square |
| 5 | pentagon | Closed polygon with 5 vertices | hexagon |
| 6 | hexagon | Closed polygon with 6 vertices | pentagon, octagon |
| 7 | octagon | Closed polygon with 8 vertices | hexagon, circle |
| 8 | star | Star polygon, vertices alternate between an outer and an inner radius | none |
| 9 | diamond | Rhombus (4 equal sides) **with no 90° angles**, at any rotation | square |

### Ambiguity margins

The risky pairs are circle/ellipse, square/rectangle and square/diamond. In each pair, one shape turns into the other as a single parameter moves. A strict definition needs a gap between the two classes, so that no image can fall in between:

- `ellipse_min_axis_ratio: 1.2`: major/minor axis ratio of at least 1.2. Anything closer to 1 is too close to a circle to label safely.
- `rectangle_min_side_ratio: 1.2`: long/short side ratio of at least 1.2. Anything closer to 1 looks like a square.
- `diamond_min_angle_offset_deg: 10`: interior angles at least 10° away from 90°. A rhombus with near-90° angles is just a rotated square.
- **Diamond is a non-square rhombus.** A square rotated 45° is still a square. Rotation never changes the class, only the shape's own angles do.

### Why these specific margins

- **1.2 axis ratio for ellipse:** this is a judgment call, not a published standard. A ratio of 1.2 means the major axis is 20% longer than the minor axis, which is visually distinguishable from a circle but not so extreme that you lose borderline cases. You could tune this, but 1.2 is a reasonable starting point.
- **1.2 side ratio for rectangle:** same logic. A 1.2 ratio means the long side is 20% longer than the short side.
- **10° angle offset for diamond:** this means the interior angles must be at least 10° away from 90° in either direction. A rhombus with angles of 85° and 95° would fail this test and be classified as a square (rotated).
- These margins are **project-specific choices**, not universal standards. They should be recorded in `configs/taxonomy.yaml` so they can be tuned if the confusion matrix shows problems.

### Augmentation constraint

Some transforms change the geometric class. Shear turns a square into a rhombus. Non-uniform scaling turns a circle into an ellipse and a square into a rectangle. Disable both for `circle`, `ellipse`, `square`, `rectangle` and `diamond` (`no_shear_no_nonuniform_scale`). Rotation, translation and uniform scaling are safe for all ten classes.

### Why shear and non-uniform scaling are dangerous

- **Shear** changes the angles between sides. A square (90° angles) becomes a rhombus (non-90° angles) under shear. This means a sheared square would be misclassified as a diamond.
- **Non-uniform scaling** changes the aspect ratio. A circle becomes an ellipse, a square becomes a rectangle, and a rectangle's side ratio changes (possibly crossing the 1.2 threshold).
- **Rotation** is safe because it preserves all internal angles and side ratios. A rotated square is still a square, a rotated diamond is still a diamond.
- **Translation** is safe because it doesn't change any geometric property.
- **Uniform scaling** is safe because it scales all dimensions equally, preserving ratios.

### Where to put this

Store the class index, the definitions, the margins and the augmentation list in one config file (`configs/taxonomy.yaml`). Labelling, cleaning, augmentation and any synthetic generator should then all read the same rules.

### A warning for later

Strict definitions will reject some source labels. Quick, Draw! "diamond" doodles are often gems, kites or shields rather than rhombi. Audit that class against the definition before training. In this project, that audit became finding **F01**, and the QuickDraw diamonds were excluded.

### Cross-reference to S03

- The ElementaryCQT dataset (`d35tjjgjnx/1`) is the same one you rejected in S03 for not having pentagon, hexagon or octagon. The paper confirms the dataset includes circles, triangles, squares, rectangles, parallelograms, trapeziums, and rhombus, but not pentagon, hexagon or octagon. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- This is a useful connection: the dataset you rejected for coverage is the one you're using here for definitions. The definitions are useful even if the dataset itself isn't.

## Validation
- Checked against docs/source.md, as summarised in inferred_prompts.md S07.
- Re-checked against the ElementaryCQT paper (Springer, DOI 10.1007/s42979-024-03521-w): confirms the paper's scope (Circle, Quadrilateral, Triangle), the geometric properties it includes, the shapes it covers, and that its purpose is geometry-problem solving, not general shape classification. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- Confirmed: the paper's dataset is hosted on Mendeley at `d35tjjgjnx/1`, the same dataset rejected in S03. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- Not re-checked in this pass: the exact mathematical definitions in the paper (the paper's figures and equations were not fetched), the 1.2 and 10° margin values (these are project-specific choices, not from the paper).

## Our decision
Each class was defined mathematically, taking inspiration from the ElementaryCQT paper (2D geometric shape recognition). Example: a diamond is a rhombus that is not a square. The definitions later decided class membership, including the QuickDraw diamond exclusion (F01).

## Measured effect
Definitions used for labelling. No macro F1 change recorded for this decision.

## Notes on the log

- **ElementaryCQT is a reference, not a dataset:** the log correctly distinguishes between using the paper for its definitions and using its dataset for training. The paper's own dataset (`d35tjjgjnx/1`) was rejected in S03 for coverage gaps, but its definitions are still useful. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)
- **The margins are project-specific:** the 1.2 axis ratio, 1.2 side ratio, and 10° angle offset are choices made for this project, not standards from the paper. They should be recorded in `configs/taxonomy.yaml` and tuned if needed.
- **The augmentation constraint is a direct consequence of the definitions:** shear and non-uniform scaling change the geometric class, so they must be disabled for the affected classes. This is a clean logical chain from definition to augmentation rule.
- **The QuickDraw diamond warning is prescient:** the log correctly predicts that Quick, Draw! "diamond" doodles will fail the strict definition, and this indeed became finding F01. This is a good example of the definitions doing real work.
- **Cross-reference to S03:** the same Mendeley dataset appears in both S03 (rejected for coverage) and S07 (used for definitions). This is worth noting so nobody is confused about why the same dataset appears in two different roles.
- **Paper details:** the paper is by Archana Boob and Mansi Radke, published in SN Computer Science, volume 6, article 9, 2025 (published online 18 December 2024). DOI: 10.1007/s42979-024-03521-w. The paper reports a ResNet50 F1 of 81.86% on its own dataset, which is useful context for how hard the task is. [link.springer](https://link.springer.com/article/10.1007/s42979-024-03521-w)