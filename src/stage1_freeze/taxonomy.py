"""
The fixed label set for the classification task. Single source of truth is
configs/taxonomy.yaml; this module exposes it in the Phase 1 shape so the
moved build keeps producing identical label ids (label_id = index).

Definitions remove the three ambiguous pairs (square/diamond,
square/rectangle, circle/ellipse). ANGLE_DEFINED lists the classes whose
identity depends on exact angles or equal sides/axes: augmentation must
not apply shear or non-uniform scaling to them, because that changes the
true label (a sheared square is a diamond, a stretched circle an ellipse).
"""

from src.common.config import load_default_config

_TAX = load_default_config()["taxonomy"]

TAXONOMY = [_TAX["classes"][i] for i in range(len(_TAX["classes"]))]

ANGLE_DEFINED = set(_TAX["no_shear_no_nonuniform_scale"])

# Safe for every class: rotation, uniform scale, translation, noise, blur.
# Unsafe for ANGLE_DEFINED classes: shear, non-uniform scale.
SAFE_FOR_ALL = ["rotation", "uniform_scale", "translation", "noise", "blur"]
LABEL_CHANGING = ["shear", "non_uniform_scale"]
