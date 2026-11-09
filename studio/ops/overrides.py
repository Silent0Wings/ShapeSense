"""Apply slider values to a private copy of the config, then validate it.

Stage 2 and Stage 3 read every number from the config, so a slider is just a
changed value in a deep copy. The committed config is never touched.
"""

from __future__ import annotations

from src.common.config import arm_config, validate_pipeline

from studio.context import config

PREVIEW_ARM = "A2"   # previews start from the settings chosen for the primary candidate


def tuned() -> dict:
    """A private copy of the config with the preview arm's tuned settings applied."""
    return arm_config(config(), PREVIEW_ARM)


def _checked(cfg: dict) -> dict:
    validate_pipeline(cfg)
    return cfg


def augment_config(values: dict, uncapped: bool = False) -> dict:
    """A config whose ``augment`` section holds the given slider values."""
    cfg = tuned()
    a = cfg["augment"]
    a["rotate_deg"] = float(values["rotate_deg"])
    a["scale"] = [float(values["scale_lo"]), float(values["scale_hi"])]
    a["nonuniform_scale"] = float(values["nonuniform_scale"])
    a["shear_deg"] = float(values["shear_deg"])
    a["translate_px"] = float(values["translate_px"])
    a["noise_p"] = float(values["noise_p"])
    a["blur_p"] = float(values["blur_p"])
    if uncapped:
        cfg["taxonomy"]["rotate_limit_deg"] = {}
    return _checked(cfg)


def synth_config(values: dict) -> dict:
    """A config whose ``synth`` section holds the given slider values."""
    cfg = tuned()
    s = cfg["synth"]
    s["radius_px"] = [float(values["radius_lo"]), float(values["radius_hi"])]
    s["center_jitter_px"] = float(values["center_jitter_px"])
    s["vertex_jitter_px"] = float(values["vertex_jitter_px"])
    s["ellipse_max_axis_ratio"] = float(values["ellipse_max_axis_ratio"])
    s["rectangle_max_side_ratio"] = float(values["rectangle_max_side_ratio"])
    s["diamond_acute_angle_deg"] = [float(values["diamond_lo"]), float(values["diamond_hi"])]
    s["star_inner_ratio"] = [float(values["star_lo"]), float(values["star_hi"])]
    return _checked(cfg)


def default_augment_values() -> dict:
    a = tuned()["augment"]
    return {"rotate_deg": a["rotate_deg"], "scale_lo": a["scale"][0], "scale_hi": a["scale"][1],
            "nonuniform_scale": a["nonuniform_scale"], "shear_deg": a["shear_deg"],
            "translate_px": a["translate_px"], "noise_p": a["noise_p"], "blur_p": a["blur_p"]}


def default_synth_values() -> dict:
    s = tuned()["synth"]
    return {"radius_lo": s["radius_px"][0], "radius_hi": s["radius_px"][1],
            "center_jitter_px": s["center_jitter_px"], "vertex_jitter_px": s["vertex_jitter_px"],
            "ellipse_max_axis_ratio": s["ellipse_max_axis_ratio"],
            "rectangle_max_side_ratio": s["rectangle_max_side_ratio"],
            "diamond_lo": s["diamond_acute_angle_deg"][0], "diamond_hi": s["diamond_acute_angle_deg"][1],
            "star_lo": s["star_inner_ratio"][0], "star_hi": s["star_inner_ratio"][1]}
