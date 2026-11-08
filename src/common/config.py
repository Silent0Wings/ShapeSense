"""Config loading shared by all stages.

Two files, one rule each (implementation.md, "Two config files"):
  configs/pipeline.yaml  every experimental setting
  configs/taxonomy.yaml  what a class *is* (names, margins, safety rules)

`load_config` returns the pipeline dict with the taxonomy merged in under
the key "taxonomy", after validating both. Validation errors name the
exact key path, so a typo fails at load time instead of deep in a stage.
Configs are frozen after Stage 1; changing them needs team agreement.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

RATIO_TOLERANCE = 1e-9  # split ratios must sum to 1 within this
LOSO_ARMS = ("A1", "B")  # Decision 12: "retrain A1 and B without Hand-Drawn"


class ConfigError(ValueError):
    """Raised when a config file is missing a key or holds a bad value."""


def _read_yaml(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def _get(d: dict, dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise ConfigError(f"missing key: {dotted}")
        cur = cur[part]
    return cur


def _require_number(d: dict, dotted: str, lo: float | None = None,
                    hi: float | None = None) -> float:
    v = _get(d, dotted)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ConfigError(f"{dotted}: expected a number, got {v!r}")
    if lo is not None and v < lo:
        raise ConfigError(f"{dotted}: {v} is below {lo}")
    if hi is not None and v > hi:
        raise ConfigError(f"{dotted}: {v} is above {hi}")
    return v


def _require_range(d: dict, dotted: str) -> list:
    v = _get(d, dotted)
    if (not isinstance(v, list) or len(v) != 2
            or not all(isinstance(x, (int, float)) for x in v) or v[0] > v[1]):
        raise ConfigError(f"{dotted}: expected [low, high] with low <= high, got {v!r}")
    return v


def validate_taxonomy(tax: dict) -> None:
    """Check names, indices, margins and the label-safety list."""
    classes = _get(tax, "classes")
    if not isinstance(classes, dict) or not classes:
        raise ConfigError("classes: expected a non-empty index -> name mapping")
    idx = sorted(classes)
    if idx != list(range(len(idx))):
        raise ConfigError(f"classes: indices must be 0..{len(idx) - 1}, got {idx}")
    names = list(classes.values())
    if len(set(names)) != len(names):
        raise ConfigError("classes: duplicate class names")
    _require_number(tax, "ambiguity_margins.ellipse_min_axis_ratio", lo=1.0)
    _require_number(tax, "ambiguity_margins.rectangle_min_side_ratio", lo=1.0)
    _require_number(tax, "ambiguity_margins.diamond_min_angle_offset_deg", lo=0, hi=90)
    disabled = _get(tax, "no_shear_no_nonuniform_scale")
    unknown = [c for c in disabled if c not in names]
    if unknown:
        raise ConfigError(f"no_shear_no_nonuniform_scale: unknown classes {unknown}")


def validate_pipeline(cfg: dict) -> None:
    """Check every key the stages read. Raises ConfigError on the first problem."""
    seeds = _get(cfg, "seed_set")
    if (not isinstance(seeds, list) or not seeds
            or not all(isinstance(s, int) and not isinstance(s, bool) for s in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ConfigError(f"seed_set: expected a list of distinct ints, got {seeds!r}")
    _require_number(cfg, "image_size", lo=8)
    _require_number(cfg, "image_channels", lo=1, hi=1)
    _require_number(cfg, "synthetic_fraction", lo=0, hi=1)
    if not isinstance(_get(cfg, "filter_gemstones"), bool):
        raise ConfigError("filter_gemstones: expected true or false")
    excl = _get(cfg, "exclude_source_labels")
    if not isinstance(excl, list) or not all(
            isinstance(e, list) and len(e) == 2 and all(isinstance(x, str) for x in e)
            for e in excl):
        raise ConfigError("exclude_source_labels: expected a list of [source_id, class] pairs")
    if "taxonomy" in cfg:
        known = set(cfg["taxonomy"]["classes"].values())
        bad = sorted({e[1] for e in excl} - known)
        if bad:
            raise ConfigError(f"exclude_source_labels: unknown classes {bad}")

    ratios = _get(cfg, "split.ratios")
    if (not isinstance(ratios, list) or len(ratios) != 3
            or not all(isinstance(r, (int, float)) and r > 0 for r in ratios)):
        raise ConfigError(f"split.ratios: expected three positive numbers, got {ratios!r}")
    if not math.isclose(sum(ratios), 1.0, abs_tol=RATIO_TOLERANCE):
        raise ConfigError(f"split.ratios: must sum to 1, got {sum(ratios)}")
    _require_number(cfg, "split.phash_hamming_max", lo=0, hi=64)
    seed = _get(cfg, "split.seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ConfigError(f"split.seed: expected an int, got {seed!r}")

    for key in ("catalog", "metadata", "unified_dir", "raw_dir", "taxonomy",
                "gemstone_ids", "splits_dir", "artifacts_dir", "test_access_log"):
        if not isinstance(_get(cfg, f"paths.{key}"), str):
            raise ConfigError(f"paths.{key}: expected a path string")

    arms = _get(cfg, "arms")
    for arm, spec in arms.items():
        for flag in ("augment", "synthetic"):
            if not isinstance(_get(cfg, f"arms.{arm}.{flag}"), bool):
                raise ConfigError(f"arms.{arm}.{flag}: expected true or false")
    runs = _get(cfg, "runs")
    if not isinstance(runs, list) or not runs:
        raise ConfigError("runs: expected a non-empty list of {arm, seed}")
    seen = set()
    for i, run in enumerate(runs):
        if not isinstance(run, dict):
            raise ConfigError(f"runs[{i}]: expected a mapping")
        extra = set(run) - {"arm", "seed", "name", "holdout_source"}
        if extra:
            # S4 Mission M1: per-run epochs/steps/lr would make arms unfair.
            raise ConfigError(f"runs[{i}]: only arm and seed may vary per run, "
                              f"found {sorted(extra)}")
        if run.get("arm") not in arms:
            raise ConfigError(f"runs[{i}].arm: {run.get('arm')!r} is not in arms")
        if run.get("seed") not in seeds:
            raise ConfigError(f"runs[{i}].seed: {run.get('seed')!r} is not in seed_set "
                              "(paired design needs the same seeds for every arm)")
        key = (run.get("name") or run["arm"], run["seed"])
        if key in seen:
            raise ConfigError(f"runs[{i}]: duplicate run {key}")
        seen.add(key)
        if run.get("holdout_source") and key[0] in LOSO_ARMS and run["seed"] == seeds[0]:
            raise ConfigError(f"runs[{i}]: {key[0]} seed {run['seed']} with a holdout_source "
                              "collides with the automatic leave-one-source-out run")

    _require_number(cfg, "augment.rotate_deg", lo=0, hi=180)
    _require_range(cfg, "augment.scale")
    _require_number(cfg, "augment.nonuniform_scale", lo=0, hi=1)
    _require_number(cfg, "augment.shear_deg", lo=0, hi=45)
    _require_number(cfg, "augment.translate_px", lo=0)
    _require_number(cfg, "augment.noise_p", lo=0, hi=1)
    _require_number(cfg, "augment.noise_fraction", lo=0, hi=1)
    _require_number(cfg, "augment.blur_p", lo=0, hi=1)
    _require_range(cfg, "augment.blur_sigma")
    _require_number(cfg, "augment.ink_threshold", lo=1, hi=254)
    _require_number(cfg, "augment.frame_margin", lo=0, hi=0.4)

    _require_range(cfg, "synth.radius_px")
    _require_number(cfg, "synth.stroke_px", lo=1)
    _require_number(cfg, "synth.center_jitter_px", lo=0)
    _require_number(cfg, "synth.ellipse_max_axis_ratio", lo=1)
    _require_number(cfg, "synth.rectangle_max_side_ratio", lo=1)
    _require_range(cfg, "synth.diamond_acute_angle_deg")
    _require_range(cfg, "synth.star_inner_ratio")
    _require_number(cfg, "synth.vertex_jitter_px", lo=0)
    _require_number(cfg, "synth.supersample", lo=1)

    for key in ("batch_size", "max_epochs", "early_stopping_patience", "num_threads",
                "parallel_runs", "benchmark_batches"):
        _require_number(cfg, f"train.{key}", lo=1)
    _require_number(cfg, "train.dropout", lo=0, hi=1)
    _require_number(cfg, "train.lr", lo=0)
    _require_number(cfg, "train.weight_decay", lo=0)
    spe = _get(cfg, "train.steps_per_epoch")
    if spe is not None and (not isinstance(spe, int) or spe < 1):
        raise ConfigError(f"train.steps_per_epoch: expected null or a positive int, got {spe!r}")
    if _get(cfg, "train.tuning.arm") not in arms:
        raise ConfigError("train.tuning.arm: must name an arm")

    for key in ("lr", "dropout"):
        grid = _get(cfg, f"train.tuning.{key}")
        if (not isinstance(grid, list) or not grid
                or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in grid)):
            raise ConfigError(f"train.tuning.{key}: expected a non-empty list of numbers")
    channels = _get(cfg, "train.channels")
    if not isinstance(channels, list) or not all(isinstance(c, int) and c > 0 for c in channels):
        raise ConfigError("train.channels: expected a list of positive ints")
    bseed = _get(cfg, "evaluation.bootstrap_seed")
    if isinstance(bseed, bool) or not isinstance(bseed, int):
        raise ConfigError("evaluation.bootstrap_seed: expected an int")
    pairs = _get(cfg, "evaluation.confusion_pairs")
    if not isinstance(pairs, list) or not all(isinstance(p, list) and len(p) == 2 for p in pairs):
        raise ConfigError("evaluation.confusion_pairs: expected a list of [a, b] class pairs")
    if "taxonomy" in cfg:  # merged config: names must exist
        known = set(cfg["taxonomy"]["classes"].values())
        unknown = sorted({c for p in pairs for c in p} - known)
        if unknown:
            raise ConfigError(f"evaluation.confusion_pairs: unknown classes {unknown}")
    _require_number(cfg, "evaluation.alpha", lo=0, hi=1)
    _require_number(cfg, "evaluation.n_boot", lo=100)
    _require_number(cfg, "evaluation.shortcut_trigger_points", lo=0)
    _require_number(cfg, "evaluation.power_halfwidth_limit_points", lo=0)
    _require_number(cfg, "evaluation.noise_band_accuracy", lo=0, hi=1)
    _require_number(cfg, "success_criterion.macro_f1_min_gain_points", lo=0)
    _require_number(cfg, "success_criterion.ci_level", lo=0, hi=1)
    _require_number(cfg, "success_criterion.max_class_f1_drop_points", lo=0)


def class_names(config: dict) -> list[str]:
    """Class names in label-index order, from the merged taxonomy."""
    classes = config["taxonomy"]["classes"]
    return [classes[i] for i in range(len(classes))]


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "pipeline.yaml"
_DEFAULT_CACHE: dict = {}


def load_default_config() -> dict:
    """The committed config (merged + validated), loaded once per process.

    Used by module-level conveniences such as stage2_augment.transform and
    stage3_synth.generate. Callers must not mutate the returned dict.
    """
    if "cfg" not in _DEFAULT_CACHE:
        _DEFAULT_CACHE["cfg"] = load_config(DEFAULT_CONFIG)
    return _DEFAULT_CACHE["cfg"]


def resolve(path: str | Path) -> Path:
    """Resolve a config path (relative to the repo root) to an absolute Path."""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    """Load + validate the pipeline config and merge the taxonomy into it."""
    cfg = _read_yaml(path)
    validate_pipeline(cfg)
    tax = _read_yaml(resolve(cfg["paths"]["taxonomy"]))
    validate_taxonomy(tax)
    cfg["taxonomy"] = tax
    validate_pipeline(cfg)  # again, now that class names can be checked
    return cfg
