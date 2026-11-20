

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_define-the-ten-classes.md](../claude_opus/10_evidence_define-the-ten-classes.md)

# 0_data_discovery - S07 - Defined each shape class mathematically

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: from repo, not a saved chat. Gemini 4 Neon has no transcripts in this repo. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt
> How should each of our ten shape classes be defined precisely, so that we can decide whether an image belongs to it? Is there published work with mathematical definitions?

## Response

No reply exists in this repo. Gemini 4 Neon responses are not reproduced for this item.

**Stand-in answer** *(written 2026-11-20 by Claude Opus 5.5 from the repo's records. It is not Gemini 4 Neon's reply, which is lost, so this file does not count as a Gemini answer in the two-LLM comparison.)*

Define each class by countable geometry, and give each confusable pair an explicit margin so that every image falls on one side of the line. The ElementaryCQT paper on 2D geometric shape recognition is a useful published starting point (it is listed in `docs/source.md` as reference material). The definitions used (`configs/taxonomy.yaml`):

| Class | Definition |
|---|---|
| circle | closed curve, equal axes |
| ellipse | closed curve, clearly unequal axes (axis ratio at least 1.2) |
| triangle | 3 vertices |
| square | 4 equal sides, right angles, any rotation |
| rectangle | 4 sides, right angles, clearly unequal sides (side ratio at least 1.2) |
| pentagon / hexagon / octagon | 5 / 6 / 8 vertices |
| star | star polygon, alternating outer and inner vertices |
| diamond | rhombus without right angles (at least 10° away from 90°), any rotation |

Two consequences follow. Augmentation must not cross these lines, so shear and non-uniform scaling are switched off for circle, ellipse, square, rectangle and diamond. And source labels must be checked against the definitions: this later excluded the Quick, Draw! "diamonds", which were mostly gems and not rhombi (F01).

## What we can reconstruct from the decision

Even though the Gemini response itself is lost, the decision it produced is recorded in docs/source.md and can be reconstructed in detail. Each of the ten classes was defined mathematically, with ambiguity margins and augmentation constraints:

### The reference: ElementaryCQT

- The paper is *ElementaryCQT: A New Dataset and its Deep Learning Analysis for 2D Geometric Shape Recognition* by Archana Boob and Mansi Radke, published in SN Computer Science, 2024. DOI: 10.1007/s42979-024-03521-w.
- It defines elementary circles, quadrilaterals and triangles geometrically. Use it as a **geometry reference for your definitions, not as a training dataset**.
- Its figures target geometry-problem pipelines and don't match your ten classes.
- The paper's dataset is hosted on Mendeley at `d35tjjgjnx/1`, the same dataset rejected in S03 for not having pentagon, hexagon or octagon. This is a useful cross-reference: the same dataset you rejected for coverage is the one you're using here for definitions.

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

## Validation
- Checked against docs/source.md, as summarised in inferred_prompts.md S07.
- **Gemini transcript not recoverable:** a Google Drive search for the original Gemini S07 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains empty, which is correct for an unrecoverable transcript.
- The ElementaryCQT paper was re-checked in an earlier pass (S07 ), confirming the paper's scope (Circle, Quadrilateral, Triangle), the geometric properties it includes, the shapes it covers, and that its purpose is geometry-problem solving, not general shape classification.

## Our decision
Each class was defined mathematically, taking inspiration from the ElementaryCQT paper (2D geometric shape recognition). Example: a diamond is a rhombus that is not a square. The definitions later decided class membership, including the QuickDraw diamond exclusion (F01).

## Measured effect
Definitions used for labelling. No macro F1 change recorded for this decision.

## Notes on the log

- **Gemini transcript is genuinely lost:** like S01 through S06, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays empty rather than fabricating a reply.
- **The decision is still fully reconstructable:** even without the Gemini response, the definitions, the margins, the augmentation constraints, and the QuickDraw warning are all reconstructable from docs/source.md and the earlier expanded S07 entry. This means the decision itself is auditable even if the reasoning that produced it is not.
- **The margins are project-specific:** the 1.2 axis ratio, 1.2 side ratio, and 10° angle offset are choices made for this project, not standards from the paper. They should be recorded in `configs/taxonomy.yaml` and tuned if needed.
- **The augmentation constraint is a direct consequence of the definitions:** shear and non-uniform scaling change the geometric class, so they must be disabled for the affected classes. This is a clean logical chain from definition to augmentation rule.
- **The QuickDraw diamond warning is prescient:** the log correctly predicts that Quick, Draw! "diamond" doodles will fail the strict definition, and this indeed became finding F01. This is a good example of the definitions doing real work.
- **Cross-reference to S03:** the same Mendeley dataset appears in both S03 (rejected for coverage) and S07 (used for definitions via the ElementaryCQT paper). This is worth noting so nobody is confused about why the same dataset appears in two different roles.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.