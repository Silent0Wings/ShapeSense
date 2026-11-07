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
