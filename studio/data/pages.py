"""One JSON bundle per page, composed from allow-listed documents."""

from __future__ import annotations

from studio.context import classes, config, confusion_pairs, no_shear_classes
from studio.crisp_map import STAGE_PHASE, phases
from studio.data import access_log, architecture, cache_check, lights, runs, samples
from studio.data.tables import read_csv, read_json, read_text
from studio.inference import arms
from studio.ops.overrides import default_augment_values, default_synth_values


def _home() -> dict:
    return {"phases": phases(), "lights": lights.rows(), "verdict": lights.verdict(),
            "arms": arms.available()}


def _business() -> dict:
    return {"criterion": config()["success_criterion"], "verdict": lights.verdict(),
            "phases": phases()}


def _stage0() -> dict:
    return {"lights": lights.rows(), "guards": read_json("guards"),
            "migration": read_json("migration"), "archive": read_text("archive_hash"),
            "hashes": cache_check.rows(), "access": access_log.summary()}


def _pool_note() -> dict:
    return {s: samples.pool_counts(s) for s in ("train", "val")}


def _stage1() -> dict:
    return {"split_stats": read_csv("split_stats"), "noise_bands": read_csv("noise_bands"),
            "source_check": read_json("source_classifier"), "fd": read_json("fd_check"),
            "shortcut": read_text("shortcut_notice"), "iteration": read_json("iteration1"),
            "duplicates": samples.largest_groups("train", 8), "pool": _pool_note(),
            "ratios": config()["split"]["ratios"], "contact_sheets": 5}


def _stage2() -> dict:
    return {"defaults": default_augment_values(), "no_shear": list(no_shear_classes()),
            "qa_review": read_text("qa_review2"), "pool": _pool_note(),
            "blur_sigma": config()["augment"]["blur_sigma"]}


def _stage3() -> dict:
    return {"defaults": default_synth_values(), "ranges": read_json("param_ranges"),
            "margins": config()["taxonomy"]["ambiguity_margins"],
            "qa_review": read_text("qa_review3")}


def _stage4() -> dict:
    status = read_json("status4") or {"metrics": {}, "checks": {}}
    return {"tuning": read_json("tuning"), "seed": read_json("seed_disagreement"),
            "baselines": read_json("baselines"), "benchmark": read_json("loader_benchmark"),
            "runs": runs.summary(), "layers": architecture.layers(),
            "checks": status.get("checks", {}), "train": config()["train"]}


def _stage5() -> dict:
    status = read_json("status5") or {"metrics": {}, "checks": {}}
    return {"verdict": lights.verdict(), "metrics": status["metrics"], "checks": status["checks"],
            "table_metrics": read_csv("metrics"), "per_class": read_csv("per_class"),
            "comparisons": read_csv("comparisons"), "per_source": read_csv("per_source"),
            "power": read_json("power"), "access": access_log.summary(),
            "pairs": [list(p) for p in confusion_pairs()], "criterion": config()["success_criterion"]}


def _stage6() -> dict:
    status = read_json("status6") or {"metrics": {}, "checks": {}}
    return {"metrics": status["metrics"], "checks": status["checks"], "card": read_json("model_card"),
            "labels": read_json("labels"), "arms": arms.provenance(), "live": arms.available()}


def _live() -> dict:
    return {"arms": arms.available(), "provenance": arms.provenance()}


BUILDERS = {"home": _home, "business": _business, "stage0": _stage0, "stage1": _stage1,
            "stage2": _stage2, "stage3": _stage3, "stage4": _stage4, "stage5": _stage5,
            "stage6": _stage6, "live": _live}


def build(name: str) -> dict | None:
    builder = BUILDERS.get(name)
    return None if builder is None else builder()


def meta() -> dict:
    return {"classes": list(classes()), "phases": phases(), "stage_phase": STAGE_PHASE,
            "arms": arms.available()}
