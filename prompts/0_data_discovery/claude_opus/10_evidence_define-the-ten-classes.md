# 0_data_discovery - Fix the label set to the ten classes

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19
- Owner: 40256377
- Worksheet entries: S07
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is the user's own todo entry, verbatim, which was handed to the LLM as the task; the exact chat message was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (the user's todo entry, verbatim)

```text
- [x] fix the label set as the actual classification labels (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond)
```

_Kept as plain text: the links inside it point to the local plan folder, which is not in the repo. The linked plan is quoted below._

## Response (saved output, verbatim)

### `scripts/taxonomy.py`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````python
"""
The fixed label set for the classification task. Single source of truth:
every script imports TAXONOMY from here, and label_id is the index.

Definitions remove the three ambiguous pairs (square/diamond,
square/rectangle, circle/ellipse). ANGLE_DEFINED lists the classes whose
identity depends on exact angles or equal sides/axes: augmentation must
not apply shear or non-uniform scaling to them, because that changes the
true label (a sheared square is a diamond, a stretched circle an ellipse).
"""

TAXONOMY = [
    "circle",     # 0  closed curve, equal axes
    "ellipse",    # 1  closed curve, clearly unequal axes
    "triangle",   # 2  3 vertices
    "square",     # 3  4 equal sides, right angles, any rotation
    "rectangle",  # 4  4 sides, right angles, clearly unequal sides
    "pentagon",   # 5  5 vertices
    "hexagon",    # 6  6 vertices
    "octagon",    # 7  8 vertices
    "star",       # 8  star polygon (alternating outer/inner vertices)
    "diamond",    # 9  rhombus WITHOUT right angles, any rotation
]

ANGLE_DEFINED = {"circle", "ellipse", "square", "rectangle", "diamond"}

# Safe for every class: rotation, uniform scale, translation, noise, blur.
# Unsafe for ANGLE_DEFINED classes: shear, non-uniform scale.
SAFE_FOR_ALL = ["rotation", "uniform_scale", "translation", "noise", "blur"]
LABEL_CHANGING = ["shear", "non_uniform_scale"]
````

### `configs/taxonomy.yaml`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````yaml
# 10-class taxonomy — matches phase1_report.tex, Table 1 (labels and
# definitions). The index is the training label.

classes:
  0: circle      # closed curve, equal axes
  1: ellipse     # closed curve, clearly unequal axes
  2: triangle    # 3 vertices
  3: square      # 4 equal sides, right angles, any rotation
  4: rectangle   # 4 sides, right angles, clearly unequal sides
  5: pentagon    # 5 vertices (single source: El Korchi)
  6: hexagon     # 6 vertices
  7: octagon     # 8 vertices
  8: star        # star polygon, alternating outer/inner vertices
  9: diamond     # rhombus WITHOUT right angles, any rotation

# Ambiguity margins the Stage 3 generator must respect so a synthetic
# image can never land on the wrong side of an ambiguous pair
# (square/diamond, square/rectangle, circle/ellipse).
ambiguity_margins:
  ellipse_min_axis_ratio: 1.2
  rectangle_min_side_ratio: 1.2
  diamond_min_angle_offset_deg: 10   # stay clearly off 90 deg

# Transforms that would change the geometric class are disabled for
# these labels (implementation.md, Stage 2).
no_shear_no_nonuniform_scale:
  - circle
  - ellipse
  - square
  - rectangle
  - diamond
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Ambiguous pairs were resolved by definition (square vs diamond, square vs rectangle, circle vs ellipse) (findings.md section 9).

## Our decision

`scripts/taxonomy.py` is the single source of truth. We disabled shear and non-uniform scaling for circle, ellipse, square, rectangle and diamond, because those transforms change the class.

## Measured effect

Ten fixed classes for every later stage. No model at this stage.
