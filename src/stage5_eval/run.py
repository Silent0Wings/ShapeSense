"""Stage 5 — evaluation and statistics. Owner: ______

Contract (stages/stage_5.md R1-R10, R8b; implementation.md Decisions 9,
10, 12, 14; plan 30):
  Input:  artifacts/stage4/<arm>_<seed>/{model.pt,val_probs.npz},
          artifacts/stage4/baselines/, artifacts/stage1/noise_bands.csv,
          artifacts/stage1/source_classifier.json and the locked test
          split — the ONLY stage allowed to read it, once per model.
  Output: artifacts/stage5/{predictions,tables,figures}/, power_check.json;
          the runner writes status.json with metrics.verdict and
          checks.test_reads.
  Order:  power check on VALIDATION probabilities first (R8), then one
          test read per model (R1), ensembles from cache (R4), primary +
          Holm secondaries (R5/R6), locked criterion (R7), tables and
          figures, galleries (R8b), LOSO on Hand-Drawn if triggered (R10).
  A verdict of "fail" is still a stage status of "passed" (R9).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

from src.common.config import LOSO_ARMS, class_names, load_config, resolve
from src.common.hashing import config_subtree_hash, sha256_path
from src.common.splits import count_test_reads, reads_outside
from src.common.status import StageNotReady, current_run_id
from src.stage5_eval import criterion, evaluate, figures, fresh, robust, tables
from src.stage5_eval.metrics import (accuracy, confusion, group_accuracy, macro_f1,
                                     per_class_f1)
from src.stage5_eval.placeholders import write_placeholders
from src.stage5_eval.power import align_validation_probs, check_arm_alignment, power_check
from src.stage5_eval.stats import (analysis_rng, cluster_bootstrap, holm, mcnemar_test,
                                   per_seed_differences)

STAGE = "stage5"
DEPENDS = ["stage0", "stage1", "stage4"]

# Arm roles; the comparisons themselves come from the config's evaluation section.
ARM_CONTROL = "A0"  # real only
ARM_AUG = "A1"  # real + augmentation
ARM_SYNTH = "B"  # real + augmentation + synthetic
READER = "src.stage5_eval.evaluate"  # the only module whose sealed reads are accounted for
PRIMARY_LABEL = f"{ARM_SYNTH} vs {ARM_AUG}"
SECONDARY_PAIRS = ((ARM_CONTROL, ARM_AUG), (ARM_CONTROL, ARM_SYNTH))  # Holm over these two

BASELINE_KINDS = ("logreg_pixels", "svm_hog")  # Decision 14 (Stage 4 file stems)
BASELINE_PREFIX = "baseline_"
LOSO_SOURCE = "github_handdrawn"  # Decision 12 held-out source (source_id in the catalog)
LOSO_TAG = "loso_handdrawn"  # Stage 4 run-name infix for the leave-one-source-out models
MODEL_FILE = "model.pt"
VAL_PROBS_FILE = "val_probs.npz"
NOISE_BANDS_FILE = "noise_bands.csv"
SOURCE_CLASSIFIER_FILE = "source_classifier.json"
POWER_FILE = "power_check.json"
ERRORS_CACHE = "ensemble_B_errors.npz"  # default name of the misclassified-images cache
UNKNOWN_DOMAIN = "unknown"
MISSING_HASH = "missing"  # what src.common.hashing.sha256_path returns for an absent path
GALLERIES_SKIPPED = "skipped (cache)"  # metrics.galleries when no images are available
GALLERIES_RENDERED = "rendered"
KIND_ABLATION = "ablation"  # metrics row kind for named / held-out runs


# --------------------------------------------------------------------------- #
# Paths and upstream artifacts
# --------------------------------------------------------------------------- #


def primary_roles(config: dict) -> tuple[str, str]:
    """(reference, candidate) arms of the primary comparison."""
    primary = config["evaluation"].get("primary") or {"reference": ARM_AUG, "candidate": ARM_SYNTH}
    return primary["reference"], primary["candidate"]


def secondary_pairs(config: dict) -> tuple[tuple[str, str], ...]:
    """(reference, candidate) pairs compared with a Holm correction."""
    return tuple(tuple(p) for p in config["evaluation"].get("secondary", SECONDARY_PAIRS))


def errors_cache(candidate: str) -> str:
    return f"ensemble_{candidate}_errors.npz"


def run_name(run: dict) -> str:
    """``<arm>_<seed>`` (or ``<name>_<seed>`` when a run carries a name).

    Mirrors Stage 4's ``sweep.run_name``: a run with ``holdout_source`` is
    stored as ``<name-or-arm>_loso_handdrawn_<seed>``.
    """
    base = run.get("name") or run["arm"]
    if run.get("holdout_source"):
        return f"{base}_{LOSO_TAG}_{run['seed']}"
    return f"{base}_{run['seed']}"


def is_arm_member(run: dict) -> bool:
    """Only a plain ``{arm, seed}`` run belongs to its arm's ensemble.

    A named run (an ablation such as ``B_equalreal``) or a held-out-source
    run trains on a different stream and must not be folded into the arm's
    soft vote, per-seed scores or power check. It is still evaluated once
    (one counted test read) and reported as its own ``ablation`` row.
    """
    return not run.get("name") and not run.get("holdout_source")


def arm_run_names(config: dict, arms: Sequence[str]) -> dict[str, list[str]]:
    """arm -> run names of its ensemble members (plain runs only), config order."""
    return {arm: [run_name(r) for r in config["runs"] if r["arm"] == arm and is_arm_member(r)]
            for arm in arms}


def _dirs(config: dict) -> dict[str, Path]:
    art = resolve(config["paths"]["artifacts_dir"])
    return {
        "artifacts": art,
        "stage1": art / "stage1",
        "stage4": art / "stage4",
        "stage5": art / STAGE,
        "predictions": art / STAGE / "predictions",
        "tables": art / STAGE / "tables",
        "figures": art / STAGE / "figures",
        "log": resolve(config["paths"]["test_access_log"]),
        "test_manifest": resolve(config["paths"]["splits_dir"]) / "test.csv",
        "fresh_manifest": resolve(config["paths"]["splits_dir"]) / "fresh_holdout.csv",
        "predictions_fresh": art / STAGE / "predictions_fresh",
        "fresh2_manifest": resolve(config["paths"]["splits_dir"]) / "fresh_holdout_2.csv",
        "predictions_fresh2": art / STAGE / "predictions_fresh2",
        "predictions_robust": art / STAGE / "predictions_robust",
        "perturbed": art / STAGE / "perturbed_fresh2",
    }


def inputs(config: dict) -> dict[str, str]:
    """Content hashes of everything this stage's outputs depend on.

    The test manifest is fingerprinted with ``sha256_path`` (file bytes);
    that is not a split read and writes no access-log line.
    """
    d = _dirs(config)
    out: dict[str, str] = {
        "code": sha256_path(resolve("src/stage5_eval")),
        "common": sha256_path(resolve("src/common")),
        "config.runs": config_subtree_hash(config, "runs"),
        "config.evaluation": config_subtree_hash(config, "evaluation"),
        "config.success_criterion": config_subtree_hash(config, "success_criterion"),
        "config.seed_set": config_subtree_hash(config, "seed_set"),
        "noise_bands": sha256_path(d["stage1"] / NOISE_BANDS_FILE),
        "source_classifier": sha256_path(d["stage1"] / SOURCE_CLASSIFIER_FILE),
        "test_manifest": sha256_path(d["test_manifest"]),
        "fresh_manifest": sha256_path(d["fresh_manifest"]),
        "fresh2_manifest": sha256_path(d["fresh2_manifest"]),
        "baselines": sha256_path(d["stage4"] / "baselines"),
    }
    for run in config["runs"]:
        name = run_name(run)
        out[f"stage4/{name}/{MODEL_FILE}"] = sha256_path(d["stage4"] / name / MODEL_FILE)
        out[f"stage4/{name}/{VAL_PROBS_FILE}"] = sha256_path(d["stage4"] / name / VAL_PROBS_FILE)
    return out


def read_noise_bands(path: Path, n_classes: int) -> dict:
    """``noise_bands.csv`` -> arrays indexed by label_id (n_test, band, threshold).

    Also records where the thresholds came from (``source_path``,
    ``source_sha256`` of the file actually read) so the status check
    ``thresholds_from_noise_bands`` is derived from the read, not asserted.
    """
    n_test = np.zeros(n_classes, dtype=np.int64)
    band = np.full(n_classes, np.nan)
    threshold = np.full(n_classes, np.nan)
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            c = int(row["label_id"])
            n_test[c] = int(float(row["n_test"]))
            band[c] = float(row["noise_band_points"])
            threshold[c] = float(row["threshold_points"])
    if np.isnan(threshold).any():
        raise ValueError(f"{path}: a class is missing from noise_bands.csv")
    return {"n_test": n_test, "noise_band_points": band, "threshold_points": threshold,
            "source_path": Path(path).as_posix(), "source_sha256": sha256_path(path)}


def check_class_counts(y: np.ndarray, n_test: np.ndarray) -> None:
    """The test labels must have exactly the per-class counts the thresholds were built for."""
    counts = np.bincount(np.asarray(y, dtype=np.int64), minlength=np.asarray(n_test).size)
    if not np.array_equal(counts, n_test):
        raise ValueError(f"test labels have counts {counts.tolist()}, noise_bands.csv says {list(n_test)}")


def thresholds_from_noise_bands(bands: dict) -> bool:
    """True when every class threshold is a finite number read from a hashed file."""
    thr = np.asarray(bands.get("threshold_points", []), dtype=np.float64)
    sha = str(bands.get("source_sha256") or "")
    return (thr.size > 0 and bool(np.isfinite(thr).all())
            and bool(sha) and sha != MISSING_HASH)


def read_shortcut_detected(path: Path) -> bool:
    return bool(json.loads(path.read_text(encoding="utf-8")).get("shortcut_detected", False))


def loso_runs(config: dict) -> list[tuple[str, int, str]]:
    """(arm, seed, run name) of every leave-one-source-out model."""
    seeds = config["seed_set"][:int(config["evaluation"].get("loso_seeds", 1))]
    arms = [a for a in LOSO_ARMS if a in config["arms"]]
    return [(arm, int(seed), f"{arm}_{LOSO_TAG}_{seed}") for seed in seeds for arm in arms]


def loso_run_names(config: dict) -> list[str]:
    return [name for _, _, name in loso_runs(config)]


def missing_upstream(config: dict, shortcut_detected: bool) -> list[Path]:
    """Every upstream file this stage needs that is not on disk."""
    d = _dirs(config)
    needed = [d["stage1"] / NOISE_BANDS_FILE, d["stage1"] / SOURCE_CLASSIFIER_FILE,
              d["stage4"] / "baselines" / "baselines.json"]
    needed += [d["stage4"] / "baselines" / f"{k}.joblib" for k in BASELINE_KINDS]
    for run in config["runs"]:
        needed += [d["stage4"] / run_name(run) / MODEL_FILE,
                   d["stage4"] / run_name(run) / VAL_PROBS_FILE]
    if shortcut_detected:
        needed += [d["stage4"] / name / MODEL_FILE for name in loso_run_names(config)]
    return [p for p in needed if not p.is_file()]


def build_specs(config: dict, shortcut_detected: bool) -> list[evaluate.ModelSpec]:
    """One ModelSpec per config run, per baseline and (if triggered) per LOSO model."""
    d = _dirs(config)
    specs: list[evaluate.ModelSpec] = []
    for run in config["runs"]:
        name = run_name(run)
        path = d["stage4"] / name / MODEL_FILE
        extra = {"arm": run["arm"], "seed": int(run["seed"])}
        if not is_arm_member(run):
            extra.update({"ablation": True, "name": run.get("name"),
                          "holdout_source": run.get("holdout_source")})
        specs.append(evaluate.ModelSpec(
            name=name, kind=evaluate.KIND_CNN, path=path,
            fingerprint=evaluate.model_fingerprint(path),
            source_filter=run.get("holdout_source") or None, extra=extra))
    bdir = d["stage4"] / "baselines"
    meta = json.loads((bdir / "baselines.json").read_text(encoding="utf-8"))
    for kind in BASELINE_KINDS:
        path = bdir / f"{kind}.joblib"
        info = meta.get(kind, {})
        specs.append(evaluate.ModelSpec(
            name=f"{BASELINE_PREFIX}{kind}", kind=evaluate.KIND_BASELINE, path=path,
            fingerprint=evaluate.model_fingerprint(path),
            features=info.get("features", evaluate.FEATURE_PIXELS),
            hog_pixels_per_cell=info.get("hog_pixels_per_cell"),
            extra={"baseline": kind}))
    if shortcut_detected:
        for arm, seed, name in loso_runs(config):
            path = d["stage4"] / name / MODEL_FILE
            specs.append(evaluate.ModelSpec(
                name=name, kind=evaluate.KIND_CNN, path=path,
                fingerprint=evaluate.model_fingerprint(path), source_filter=LOSO_SOURCE,
                excluded_labels=loso_excluded_classes(d["stage4"], name),
                extra={"arm": arm, "seed": seed, "loso": True}))
    return specs


def loso_excluded_classes(stage4_dir: Path, name: str) -> tuple[int, ...]:
    """Classes a LOSO model never trained on (P-61); their rows are not scored."""
    with open(Path(stage4_dir) / name / "run.json", encoding="utf-8") as f:
        return tuple(int(c) for c in json.load(f)["excluded_classes"])


def scored_macro_f1(y_true: np.ndarray, y_pred: np.ndarray, k: int) -> float:
    """Macro-F1 over the classes present in ``y_true`` (a held-out source has few)."""
    present = np.unique(y_true)
    return float(per_class_f1(y_true, y_pred, k)[present].mean())


def load_val_records(stage4_dir: Path, names: Sequence[str]) -> list[dict]:
    records = []
    for name in names:
        with np.load(stage4_dir / name / VAL_PROBS_FILE, allow_pickle=False) as z:
            records.append({"probs": z["probs"], "labels": z["labels"],
                            "image_ids": z["image_ids"]})
    return records


# --------------------------------------------------------------------------- #
# Orchestration skeleton (order is the contract: power before any test read)
# --------------------------------------------------------------------------- #


def stage5_pipeline(
    power_fn: Callable[[], dict],
    evaluate_fn: Callable[[dict], dict],
    analyse_fn: Callable[[dict, dict], dict],
) -> dict:
    """Run the three phases in the only allowed order.

    ``power_fn`` touches validation data only; ``evaluate_fn`` performs the
    test reads; ``analyse_fn`` works on cached predictions. Tests inject
    fakes that record the call order.
    """
    power = power_fn()
    evaluated = evaluate_fn(power)
    return analyse_fn(power, evaluated)


# --------------------------------------------------------------------------- #
# Analysis helpers
# --------------------------------------------------------------------------- #


def _arm_of(spec: evaluate.ModelSpec) -> str | None:
    """The arm whose ensemble this spec belongs to; None for LOSO, ablation and baselines."""
    if spec.extra.get("loso") or spec.extra.get("ablation"):
        return None
    return spec.extra.get("arm")


def is_full_split_spec(spec: evaluate.ModelSpec) -> bool:
    """Specs evaluated on the whole test split (arm members and baselines)."""
    return spec.source_filter is None


def _error_cache_current(err_path: Path, stamp: str) -> bool:
    """True when the stored error images were made by these models on this manifest."""
    err_path = Path(err_path)
    if not err_path.is_file():
        return False
    try:
        with np.load(err_path, allow_pickle=False) as z:
            return str(z["stamp"]) == stamp
    except (OSError, KeyError, ValueError):
        return False


def gallery_refresh_name(specs: Sequence[evaluate.ModelSpec], err_path: Path,
                         candidate: str = ARM_SYNTH, stamp: str = "") -> str | None:
    """Which model's prediction cache to invalidate so the galleries get images.

    The error galleries need test images. When every model is served from
    cache and the error cache is absent, the only read allowed is one tied to
    an evaluated model, so the first B-arm member is re-evaluated (its fresh,
    counted read supplies the images). Returns None when nothing is needed.
    """
    if _error_cache_current(err_path, stamp):
        return None
    for spec in specs:
        if _arm_of(spec) == candidate:
            return spec.name
    return None


def gallery_errors(images: np.ndarray | None, err_path: Path, y: np.ndarray,
                   pred_b: np.ndarray, image_ids: np.ndarray, stamp: str = "") -> tuple | None:
    """Misclassified B-ensemble images from the fresh read or the error cache.

    Never reads the test split. Returns ``(images, labels, preds)`` and writes
    the error cache when fresh images are available, loads the cache
    otherwise, and returns None when neither exists (galleries skipped).
    """
    wrong = pred_b != y
    err_path = Path(err_path)
    if images is not None:
        err_images, err_y, err_pred = np.asarray(images)[wrong], y[wrong], pred_b[wrong]
        err_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(err_path, images=err_images, labels=err_y, preds=err_pred,
                            image_ids=np.asarray(image_ids)[wrong], stamp=np.asarray(stamp))
        return err_images, err_y, err_pred
    if _error_cache_current(err_path, stamp):
        with np.load(err_path, allow_pickle=False) as z:
            return z["images"], z["labels"], z["preds"]
    return None


def test_reads_ok(test_reads: int, expected: int, extra_reads: int) -> bool:
    """The access log must show exactly the model-tied reads and nothing unaccounted."""
    return int(test_reads) == int(expected) and int(extra_reads) == 0


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    ddof = 1 if arr.size > 1 else 0
    return float(arr.mean()), float(arr.std(ddof=ddof))


def _compare(y: np.ndarray, pred_ref: np.ndarray, pred_cand: np.ndarray, groups: np.ndarray, k: int,
             n_boot: int, seed: int, name: str, ci_level: float) -> dict:
    boot = cluster_bootstrap(y, pred_ref, pred_cand, groups, k, n_boot, analysis_rng(seed, name), ci_level)
    mc = mcnemar_test(pred_ref == y, pred_cand == y)
    return {"boot": boot, "mcnemar": mc}


def _relative(p: Path) -> str:
    """Repo-relative POSIX path when possible, else the absolute path."""
    try:
        return Path(p).resolve().relative_to(resolve(".")).as_posix()
    except ValueError:
        return Path(p).as_posix()


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_jsonable(v) for v in obj.tolist()]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def single_source_classes(labels: np.ndarray, source_ids: np.ndarray,
                          names: Sequence[str]) -> list[str]:
    """Classes whose test images all come from one source (Should 1)."""
    out = []
    for c, name in enumerate(names):
        srcs = set(np.asarray(source_ids)[np.asarray(labels) == c].tolist())
        if len(srcs) == 1:
            out.append(name)
    return out


# --------------------------------------------------------------------------- #
# Stage entry
# --------------------------------------------------------------------------- #


def run(config: dict) -> dict:
    """Evaluate every model once on the test split and deliver the verdict.

    Does not write status.json; the runner does. Raises
    ``StageNotReady`` (recorded as ``not_run``) while upstream
    artifacts are missing, after writing the placeholder tables so the
    report still compiles.
    """
    d = _dirs(config)
    for key in ("stage5", "predictions", "predictions_fresh", "tables", "figures"):
        d[key].mkdir(parents=True, exist_ok=True)

    sc_path = d["stage1"] / SOURCE_CLASSIFIER_FILE
    shortcut_detected = read_shortcut_detected(sc_path) if sc_path.is_file() else False
    missing = missing_upstream(config, shortcut_detected)
    if missing:
        write_placeholders(d["tables"])
        rel = ", ".join(p.relative_to(d["artifacts"]).as_posix() for p in missing)
        which = "Stage 1" if any(p.parent == d["stage1"] for p in missing) else "Stage 4"
        raise StageNotReady(f"{which} artifacts missing: {rel}")

    names = class_names(config)
    k = len(names)
    reference, candidate = primary_roles(config)
    primary_label = f"{candidate} vs {reference}"
    pairs_secondary = secondary_pairs(config)
    ev_cfg = config["evaluation"]
    crit = config["success_criterion"]
    n_boot = int(ev_cfg["n_boot"])
    ci_level = float(crit["ci_level"])
    min_gain = float(crit["macro_f1_min_gain_points"])
    boot_seed = int(ev_cfg["bootstrap_seed"])
    run_id = current_run_id()
    bands = read_noise_bands(d["stage1"] / NOISE_BANDS_FILE, k)
    thresholds = bands["threshold_points"]
    n_test_published = int(bands["n_test"].sum())
    specs = build_specs(config, shortcut_detected)
    pairs = [tuple(p) for p in ev_cfg["confusion_pairs"]]
    manifest_hash = sha256_path(d["test_manifest"])  # file bytes, not a split read
    err_path = d["predictions"] / errors_cache(candidate)
    error_stamp = "+".join(s.fingerprint for s in specs if s.extra.get("arm") == candidate
                           and is_full_split_spec(s)) + "@" + manifest_hash
    outputs: list[Path] = []

    # ---- (a) power check on validation probabilities, before any test read
    def power_fn() -> dict:
        names_by_arm = arm_run_names(config, (reference, candidate))
        y_val, probs_a1, ids_a1 = align_validation_probs(
            load_val_records(d["stage4"], names_by_arm[reference]))
        y_val_b, probs_b, ids_b = align_validation_probs(
            load_val_records(d["stage4"], names_by_arm[candidate]))
        check_arm_alignment(y_val, ids_a1, y_val_b, ids_b)
        power = power_check(y_val, probs_a1, probs_b, n_test_published, k, n_boot,
                            analysis_rng(boot_seed, "power"), ci_level,
                            float(ev_cfg["power_halfwidth_limit_points"]))
        reads_now = count_test_reads(run_id, log_path=d["log"])
        power["before_first_test_read"] = reads_now == 0
        power["access_log_reads_at_power_check"] = int(reads_now)
        power["run_id"] = run_id
        p = d["stage5"] / POWER_FILE
        p.write_text(json.dumps(_jsonable(power), indent=2) + "\n", encoding="utf-8")
        outputs.append(p)
        return power

    # ---- (b) one test read per model (every read is tied to an evaluated model)
    def evaluate_fn(_power: dict) -> dict:
        refresh = gallery_refresh_name(specs, err_path, candidate, error_stamp)
        if refresh is not None:
            evaluate.cache_path(d["predictions"], refresh).unlink(missing_ok=True)
        ev = evaluate.evaluate_models(config, specs, evaluate.default_test_reader(config),
                                      d["predictions"], manifest_hash=manifest_hash)
        ev["fresh"] = None
        if d["fresh_manifest"].is_file():
            ev["fresh"] = evaluate.evaluate_models(
                config, [s for s in specs if _arm_of(s) is not None],
                evaluate.fresh_holdout_reader(config), d["predictions_fresh"],
                manifest_hash=sha256_path(d["fresh_manifest"]))
        ev["fresh2"] = ev["robust"] = None
        robust_cfg = ev_cfg.get("robust")
        if robust_cfg and d["fresh2_manifest"].is_file():
            arm_specs = [s for s in specs if _arm_of(s) is not None]
            fresh2_hash = sha256_path(d["fresh2_manifest"])
            ev["fresh2"] = evaluate.evaluate_models(
                config, arm_specs, evaluate.fresh_holdout_reader(config, robust_cfg["split"]),
                d["predictions_fresh2"], manifest_hash=fresh2_hash)
            sets = robust.sets_for(ev["fresh2"]["images"], robust_cfg["levels"], int(robust_cfg["seed"]),
                                   d["perturbed"], fresh2_hash)
            ev["robust"] = robust.predict_levels(arm_specs, sets, ev["fresh2"]["models"],
                                                 d["predictions_robust"], fresh2_hash)
        return ev

    # ---- (c)-(e) analysis on cached predictions
    def analyse_fn(power: dict, ev: dict) -> dict:
        models = ev["models"]
        extra_reads = reads_outside(run_id, READER, log_path=d["log"])  # must stay 0
        for spec in specs:
            outputs.append(models[spec.name]["path"])

        # every full-split record must pair row by row before any comparison
        evaluate.check_alignment(
            {s.name: models[s.name] for s in specs if is_full_split_spec(s)},
            reference_ids=ev["image_ids"])

        # per seed model (arm members only); named / held-out runs are ablation rows
        seed_models, scores_by_arm, ablations = [], {}, []
        for spec in specs:
            if spec.extra.get("ablation"):
                rec = models[spec.name]
                ablations.append({"name": spec.name, "kind": KIND_ABLATION,
                                  "arm": spec.extra["arm"], "seed": spec.extra["seed"],
                                  "holdout_source": spec.extra.get("holdout_source"),
                                  "n": int(rec["labels"].size),
                                  "accuracy": accuracy(rec["labels"], rec["preds"], k),
                                  "macro_f1": macro_f1(rec["labels"], rec["preds"], k)})
                continue
            arm = _arm_of(spec)
            if arm is None:
                continue
            rec = models[spec.name]
            f1 = macro_f1(rec["labels"], rec["preds"], k)
            seed_models.append({"name": spec.name, "arm": arm, "seed": spec.extra["seed"],
                                "accuracy": accuracy(rec["labels"], rec["preds"], k),
                                "macro_f1": f1})
            scores_by_arm.setdefault(arm, {})[spec.extra["seed"]] = f1
        arms = [a for a in config["arms"] if a in scores_by_arm]
        arm_summaries = []
        for arm in arms:
            accs = [m["accuracy"] for m in seed_models if m["arm"] == arm]
            f1s = [m["macro_f1"] for m in seed_models if m["arm"] == arm]
            am, asd = _mean_std(accs)
            fm, fsd = _mean_std(f1s)
            arm_summaries.append({"arm": arm, "acc_mean": am, "acc_std": asd,
                                  "f1_mean": fm, "f1_std": fsd})

        # ensembles from cache (no test read)
        ens: dict[str, dict] = {}
        for arm in arms:
            members = [models[s.name] for s in specs if _arm_of(s) == arm]
            rec = evaluate.ensemble(members)
            fp = "+".join(s.fingerprint for s in specs if _arm_of(s) == arm)
            path = evaluate.cache_path(d["predictions"], f"ensemble_{arm}")
            evaluate.save_predictions(path, probs=rec["probs"], preds=rec["preds"],
                                      labels=rec["labels"], image_ids=rec["image_ids"],
                                      source_ids=rec["source_ids"], group_ids=rec["group_ids"],
                                      model_hash=fp,
                                      manifest_hash=manifest_hash)
            outputs.append(path)
            rec["accuracy"] = accuracy(rec["labels"], rec["preds"], k)
            rec["macro_f1"] = macro_f1(rec["labels"], rec["preds"], k)
            rec["per_class_f1"] = per_class_f1(rec["labels"], rec["preds"], k)
            rec["confusion"] = confusion(rec["labels"], rec["preds"], k)
            ens[arm] = rec
        for needed in (reference, candidate):
            if needed not in ens:
                raise ValueError(f"arm {needed} has no runs; the primary comparison needs it")
        y = ens[candidate]["labels"]
        source_ids = ens[candidate]["source_ids"]
        group_ids = ens[candidate]["group_ids"]
        check_class_counts(y, bands["n_test"])

        baselines = []
        for spec in specs:
            if spec.kind == evaluate.KIND_BASELINE:
                rec = models[spec.name]
                baselines.append({"name": spec.name,
                                  "accuracy": accuracy(rec["labels"], rec["preds"], k),
                                  "macro_f1": macro_f1(rec["labels"], rec["preds"], k)})

        # the comparison on the test split, secondaries with Holm, per-seed differences
        primary = _compare(y, ens[reference]["preds"], ens[candidate]["preds"], group_ids, k, n_boot,
                           boot_seed, "test/primary", ci_level)
        primary["label"] = primary_label
        secondary: dict[str, dict] = {}
        for ref, cand in pairs_secondary:
            if ref in ens and cand in ens:
                secondary[f"{cand} vs {ref}"] = _compare(y, ens[ref]["preds"], ens[cand]["preds"], group_ids,
                                                         k, n_boot, boot_seed, f"test/{cand}_vs_{ref}", ci_level)
        adjusted = holm({lbl: c["boot"]["p_two_sided"] for lbl, c in secondary.items()})
        for lbl, p_adj in adjusted.items():
            secondary[lbl]["p_holm"] = p_adj
        per_seed: dict[str, dict] = {}
        for ref, cand in ((reference, candidate), *pairs_secondary):
            if ref in scores_by_arm and cand in scores_by_arm:
                per_seed[f"{cand} vs {ref}"] = per_seed_differences(scores_by_arm[ref],
                                                                    scores_by_arm[cand])

        verdict = criterion.verdict(primary["boot"], thresholds, min_gain,
                                    report_drop_points=float(crit["max_class_f1_drop_points"]))
        gap_closed = None
        if ARM_CONTROL in ens and ARM_AUG in ens and ARM_SYNTH in ens:
            gap_closed = tables.gap_closure(ens[ARM_CONTROL]["macro_f1"], ens[ARM_AUG]["macro_f1"],
                                            ens[ARM_SYNTH]["macro_f1"])

        # per source / per domain (descriptive), LOSO rows
        domains = evaluate.load_source_domains(config)
        domain_ids = np.asarray([domains.get(s, UNKNOWN_DOMAIN) for s in source_ids])
        per_source = {arm: group_accuracy(y, ens[arm]["preds"], source_ids) for arm in arms}
        per_domain = {arm: group_accuracy(y, ens[arm]["preds"], domain_ids) for arm in arms}
        src_counts = {str(s): int(n) for s, n in zip(*np.unique(source_ids, return_counts=True))}
        dom_counts = {str(s): int(n) for s, n in zip(*np.unique(domain_ids, return_counts=True))}
        loso = []
        for spec in specs:
            if spec.extra.get("loso"):
                rec = models[spec.name]
                loso.append({"name": spec.name, "arm": spec.extra["arm"], "source": LOSO_SOURCE,
                             "n": int(rec["labels"].size),
                             "accuracy": accuracy(rec["labels"], rec["preds"], k),
                             "seed": spec.extra.get("seed"),
                             "macro_f1": scored_macro_f1(rec["labels"], rec["preds"], k),
                             "label": tables.LOSO_LABEL})
        single = single_source_classes(y, source_ids, names)

        # ---- (d) tables
        t = d["tables"]
        outputs.extend(tables.write_table(t, "metrics", *tables.metrics_rows(
            seed_models, arm_summaries,
            [{"arm": a, "accuracy": ens[a]["accuracy"], "macro_f1": ens[a]["macro_f1"]} for a in arms],
            baselines, ablations)))
        outputs.extend(tables.write_table(t, "per_class", *tables.per_class_rows(
            names, bands["n_test"], {a: ens[a]["per_class_f1"] for a in arms},
            primary["boot"]["drop_observed"], primary["boot"]["drop_ci_lo"], thresholds,
            verdict["harmful_classes"], verdict["reported_drops"], shortcut_detected, single,
            arm_order=arms)))
        outputs.extend(tables.write_table(t, "comparisons",
                                          *tables.comparisons_rows(primary, secondary, per_seed)))
        outputs.extend(tables.write_table(t, "per_source", *tables.per_source_rows(
            per_source, per_domain, src_counts, dom_counts, loso)))
        outputs.extend(tables.write_table(t, "power", *tables.power_rows(power)))
        paragraph = tables.verdict_paragraph(verdict, names, power, min_gain, ci_level, gap_closed,
                                             shortcut_detected, primary_label=primary_label)
        outputs.extend(tables.write_paragraph(t, "verdict", paragraph,
                                              tables.verdict_kv_rows(verdict, power, gap_closed)))

        # ---- figures: confusion per arm ensemble, galleries for the B ensemble
        for arm in arms:
            outputs.append(figures.confusion_figure(
                ens[arm]["confusion"], names, f"{arm} ensemble (test)",
                d["figures"] / f"confusion_{arm}.png"))
        # No read happens here: images come from the fresh read of an evaluated
        # model (evaluate_fn invalidates one B cache when the error cache is
        # missing) or from the error cache; otherwise the galleries are skipped.
        errors = gallery_errors(ev["images"], err_path, y, ens[candidate]["preds"],
                                ens[candidate]["image_ids"], error_stamp)
        galleries = GALLERIES_SKIPPED
        if errors is not None:
            err_images, err_y, err_pred = errors
            galleries = GALLERIES_RENDERED
            outputs.append(err_path)
            idx = {n: i for i, n in enumerate(names)}
            for a, b in pairs:
                outputs.append(figures.error_gallery(err_images, err_y, err_pred, idx[a], idx[b],
                                                     names, d["figures"] / f"errors_{a}_{b}.png",
                                                     arm=candidate))

        # ---- (e) test-read accounting
        test_reads = count_test_reads(run_id, log_path=d["log"])
        fresh_result = None
        fresh_reads = 0
        if ev["fresh"] is not None:
            fresh_reads = int(ev["fresh"]["n_reads"])
            fresh_result, fresh_outputs = fresh.analyse(
                ev["fresh"]["models"], specs, arms, _arm_of, names, reference, candidate, min_gain,
                float(crit["max_class_f1_drop_points"]), n_boot, boot_seed, ci_level, ev_cfg, t)
            outputs.extend(fresh_outputs)
        robust_result = None
        fresh2_reads = 0
        if ev["robust"] is not None:
            fresh2_reads = int(ev["fresh2"]["n_reads"])
            robust_result, robust_outputs = robust.analyse(
                ev["fresh2"]["models"], ev["robust"], specs, arms, _arm_of, names, ev_cfg["robust"]["levels"],
                reference, candidate, pairs_secondary, min_gain, float(crit["max_class_f1_drop_points"]),
                n_boot, boot_seed, ci_level, t, d["stage5"])
            outputs.extend(robust_outputs)
        expected = int(ev["n_reads"]) + fresh_reads + fresh2_reads
        reads_ok = test_reads_ok(test_reads, expected, extra_reads)
        outputs.extend(tables.write_table(t, "test_reads",
                                          *tables.test_reads_rows(run_id, test_reads, expected)))

        result = {
            "outputs": [_relative(p) for p in outputs],
            "metrics": _jsonable({
                "verdict": verdict["verdict"],
                "delta": verdict["delta"],
                "ci": verdict["ci"],
                "reasons": verdict["reasons"],
                "harmful_classes": verdict["harmful_classes"],
                "reported_drops": verdict["reported_drops"],
                "primary": {"label": primary_label, "mcnemar": primary["mcnemar"]},
                "fresh_holdout": fresh_result,
                "robust": robust_result,
                "ensembles": {a: {"accuracy": ens[a]["accuracy"], "macro_f1": ens[a]["macro_f1"]}
                              for a in arms},
                "baselines": baselines,
                "ablations": ablations,
                "galleries": galleries,
                "noise_bands_source": {"path": bands["source_path"],
                                       "sha256": bands["source_sha256"]},
                "power": power,
                "per_seed": per_seed,
                "secondary": {lbl: {"delta": c["boot"]["delta"], "ci": c["boot"]["ci"],
                                    "p_raw": c["boot"]["p_two_sided"], "p_mcnemar": c["mcnemar"]["p_value"],
                                    "p_holm": c.get("p_holm")}
                              for lbl, c in secondary.items()},
                "gap_closed_fraction": gap_closed,
                "shortcut_detected": shortcut_detected,
                "loso": loso or None,
                "models_from_cache": [n for n, r in models.items() if r["from_cache"]],
            }),
            "checks": {
                "power_check_before_test": bool(power["before_first_test_read"]),
                "thresholds_from_noise_bands": thresholds_from_noise_bands(bands),
                "test_reads": int(test_reads),
                "test_reads_expected": int(expected),
                "extra_reads": int(extra_reads),
                "test_reads_ok": bool(reads_ok),
            },
        }
        if robust_result is not None:   # the pre-registered verdict; the test split stays descriptive
            metrics = result["metrics"]
            metrics["reused_test"] = {key: metrics[key] for key in ("verdict", "delta", "ci", "reasons", "harmful_classes")}
            metrics.update(_jsonable({key: robust_result[key] for key in ("verdict", "delta", "ci", "reasons", "harmful_classes")}))
            metrics["primary"] = {"label": robust_result["label"], "mcnemar": robust_result["mcnemar_clean"]}
        if not reads_ok:
            result["status"] = "failed"
            result["error"] = (f"test_access.log shows {test_reads} reads for run {run_id}, "
                               f"expected {expected} ({extra_reads} unaccounted)")
        return result

    return stage5_pipeline(power_fn, evaluate_fn, analyse_fn)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
