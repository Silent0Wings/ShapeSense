"""Validation-only search and experiment runner (CRISP-DM iterations 2 and 3).

    python -m src.stage4_train.search

Implements the budgets in the iteration pre-registrations. Each trial trains one
run with dotted config overrides, under ``artifacts/stage4/tuning_iter3/<phase>/<trial>/``. A finished trial is
reused only when its settings match, so a stopped search resumes. The test
split is never touched: stores come from ``load_stores`` (train and val only).
"""

from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from src.common.config import DEFAULT_CONFIG, REPO_ROOT, class_names, load_config, resolve, set_dotted, validate_pipeline
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.folds import grouped_folds, pooled
from src.stage4_train.sweep import load_stores, run_specs
from src.stage4_train.train import VAL_PROBS_FILE, train_one

SEED = 20261109
OUT_NAME = "tuning_iter3"
SUBSET_SEED = 20261109   # the same real-image subset for every arm
RESULT_JSON = "result.json"
WINNERS_JSON = "winners.json"
START_HPARAMS = {"lr": 0.003, "dropout": 0.2}   # the iteration 1 winner
ORIENTATION_CLASSES = ("square", "rectangle", "diamond")
ROTATIONS = (0, 5, 10, 15, 20, 30, 45, 90, 180)
ROTATION_CAPS = (None, 0, 5, 10, 15, 30)
SEEDS = (0, 1, 2)
N_AUGMENT, N_SYNTH, N_SHARES, N_PRETRAIN = 24, 16, 12, 12
N_FOLDS, CV_EPOCHS = 3, 15
BUDGET_CHOICES = {"e60": {"train.max_epochs": 60}, "e30_nostop": {"train.early_stopping_patience": 999},
                  "e60_nostop": {"train.max_epochs": 60, "train.early_stopping_patience": 999}}
TOP_K = 5
GRID_LR = (0.0003, 0.001, 0.003)
GRID_DROPOUT = (0.2, 0.4)
ARMS = ("A0", "A1", "B", "A2", "P")
BUDGET_RESULT = REPO_ROOT / "docs" / "crisp_dm" / "iteration_3" / "experiments" / "budget.json"

_STORES: dict = {}


def out_dir(config: dict) -> Path:
    return resolve(config["paths"]["artifacts_dir"]) / "stage4" / OUT_NAME


def _per_class(run_dir: Path, names: list[str]) -> dict[str, float]:
    with np.load(run_dir / VAL_PROBS_FILE, allow_pickle=False) as z:
        preds, labels = z["probs"].argmax(axis=1), z["labels"]
    out = {}
    for c, name in enumerate(names):
        tp = int(np.sum((preds == c) & (labels == c)))
        denom = 2 * tp + int(np.sum((preds == c) & (labels != c))) + int(np.sum((preds != c) & (labels == c)))
        out[name] = 200.0 * tp / denom if denom else 0.0
    return out


def run_trial(spec: dict) -> dict:
    """Worker entry point: train one trial, or return its finished result."""
    run_dir = Path(spec["out_dir"])
    done_path = run_dir / RESULT_JSON
    settings = {k: spec.get(k) for k in ("arm", "seed", "overrides", "hparams", "fold")}
    if done_path.is_file():
        done = json.loads(done_path.read_text(encoding="utf-8"))
        if done.get("settings") == settings:
            return done
    config = copy.deepcopy(load_config(spec["config_path"]))
    threadpool_limits(int(config["train"]["num_threads"]))
    for key, value in spec["overrides"].items():
        set_dotted(config, key, value)
    validate_pipeline(config)
    if "stores" not in _STORES:
        _STORES["stores"] = load_stores(config)
    train, val, ids = _STORES["stores"]
    if spec.get("fold") is not None:
        n_folds, index, fold_seed = spec["fold"]
        pool = pooled(train, val)
        kept, held = grouped_folds(pool, n_folds, fold_seed)[index]
        train, val, ids = pool.take(kept), pool.take(held), None
    train = train.real_subset(float(config["train"].get("real_fraction", 1.0)), SUBSET_SEED)
    info = train_one(spec["run_name"], spec["arm"], spec["seed"], config, train, val,
                     build_transform(config), build_generator(config), spec["hparams"], run_dir,
                     steps_per_epoch=int(config["train"]["steps_per_epoch"]), val_image_ids=ids)
    result = {"name": spec["run_name"], "settings": settings, "val_macro_f1": info["val_macro_f1"],
              "best_epoch": info["best_epoch"], "epochs_run": info["epochs_run"],
              "per_class": _per_class(run_dir, class_names(config))}
    done_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _spec(config: dict, config_path, phase: str, name: str, arm: str, seed: int,
          overrides: dict, hparams: dict) -> dict:
    return {"run_name": f"{phase}_{name}", "arm": arm, "seed": int(seed), "overrides": overrides,
            "hparams": dict(hparams), "config_path": str(config_path),
            "out_dir": str(out_dir(config) / phase / name)}


def _uniform(rng: random.Random, lo: float, hi: float, digits: int = 3) -> float:
    return round(rng.uniform(lo, hi), digits)


def sample_augment(rng: random.Random) -> dict:
    scale_lo = _uniform(rng, 0.75, 1.0)
    overrides = {
        "augment.rotate_deg": rng.choice(ROTATIONS),
        "augment.scale": [scale_lo, _uniform(rng, scale_lo, 1.1)],
        "augment.nonuniform_scale": _uniform(rng, 0.0, 0.2),
        "augment.shear_deg": _uniform(rng, 0.0, 20.0, 1),
        "augment.translate_px": _uniform(rng, 0.0, 6.0, 1),
        "augment.noise_p": _uniform(rng, 0.0, 0.5),
        "augment.blur_p": _uniform(rng, 0.0, 0.5),
    }
    cap = rng.choice(ROTATION_CAPS)
    overrides["taxonomy.rotate_limit_deg"] = {} if cap is None else {c: cap for c in ORIENTATION_CLASSES}
    return overrides


def sample_pretrain(rng: random.Random) -> dict:
    return {"arms.P.pretrain_fraction": _uniform(rng, 0.1, 0.6), **sample_generator(rng)}


def sample_synth(rng: random.Random, arm: str) -> dict:
    return {f"arms.{arm}.synthetic_fraction": _uniform(rng, 0.1, 0.5), **sample_generator(rng)}


def sample_generator(rng: random.Random) -> dict:
    return {
        "synth.radius_px": [_uniform(rng, 12.0, 20.0, 1), _uniform(rng, 22.0, 30.0, 1)],
        "synth.center_jitter_px": _uniform(rng, 0.0, 8.0, 1),
        "synth.vertex_jitter_px": _uniform(rng, 0.0, 2.0, 1),
        "synth.ellipse_max_axis_ratio": _uniform(rng, 1.5, 4.0, 2),
        "synth.rectangle_max_side_ratio": _uniform(rng, 1.5, 4.0, 2),
        "synth.diamond_acute_angle_deg": [_uniform(rng, 40.0, 60.0, 1), _uniform(rng, 60.0, 80.0, 1)],
        "synth.star_inner_ratio": [_uniform(rng, 0.35, 0.45), _uniform(rng, 0.5, 0.6)],
    }


def sample_shares(rng: random.Random) -> dict:
    while True:
        clean, synthetic = _uniform(rng, 0.1, 0.6), _uniform(rng, 0.1, 0.4)
        if clean + synthetic <= 0.8:
            return {"arms.A2.clean_fraction": clean, "arms.A2.synthetic_fraction": synthetic}


def random_specs(config: dict, path, phase: str, n: int, arm: str, sample, base: dict, offset: int) -> list[dict]:
    rng = random.Random(SEED + offset)
    return [_spec(config, path, phase, f"t{i:02d}", arm, SEEDS[0], {**base, **sample(rng)}, START_HPARAMS)
            for i in range(n)]


def grid_specs(config: dict, path, bases: dict[str, dict]) -> list[dict]:
    return [_spec(config, path, "grid", f"{arm}_lr{lr}_d{dropout}", arm, SEEDS[0], base, {"lr": lr, "dropout": dropout})
            for arm, base in bases.items() for lr in GRID_LR for dropout in GRID_DROPOUT]


def execute(config: dict, specs: list[dict]) -> list[dict]:
    done = run_specs(config, specs, job_runner=run_trial)
    return [done[s["run_name"]] for s in specs]


def save(config: dict, name: str, results: list[dict]) -> None:
    path = out_dir(config) / f"phase_{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


def best(results: list[dict]) -> dict:
    return max(results, key=lambda r: r["val_macro_f1"])


def top_settings(results: list[dict]) -> list[dict]:
    """The ``TOP_K`` distinct settings with the highest single-seed score."""
    ranked = sorted(results, key=lambda r: -r["val_macro_f1"])
    seen, out = set(), []
    for r in ranked:
        key = json.dumps({"o": r["settings"]["overrides"], "h": r["settings"]["hparams"]}, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(r)
        if len(out) == TOP_K:
            break
    return out


def adopted_budget() -> dict:
    """The epoch-budget overrides chosen by the pre-registered budget rule, if any."""
    path = BUDGET_RESULT
    if not path.is_file():
        raise FileNotFoundError("run the iteration 3 experiments first: the budget rule decides the search budget")
    adopted = json.loads(path.read_text(encoding="utf-8"))["adopted"]
    return dict(BUDGET_CHOICES[adopted]) if adopted else {}


def cv_specs(config: dict, path, arm: str, settings: list[dict]) -> list[dict]:
    """Each setting on every fold, at the short pre-registered budget."""
    out = []
    for i, r in enumerate(settings):
        for fold in range(N_FOLDS):
            spec = _spec(config, path, "cv", f"{arm}_c{i}_f{fold}", arm, SEEDS[0],
                         {**r["settings"]["overrides"], "train.max_epochs": CV_EPOCHS}, r["settings"]["hparams"])
            spec["fold"] = [N_FOLDS, fold, SEED]
            out.append(spec)
    return out


def run_search(config_path=DEFAULT_CONFIG) -> dict:
    config = load_config(config_path)
    args = (config, config_path)
    budget = adopted_budget()
    augment = execute(config, random_specs(*args, "augment", N_AUGMENT, "A1", sample_augment, budget, 1))
    save(config, "augment", augment)
    best_aug = best(augment)["settings"]["overrides"]
    synth_b = execute(config, random_specs(*args, "synth", N_SYNTH, "B", lambda r: sample_synth(r, "B"), best_aug, 2))
    save(config, "synth", synth_b)
    best_b = best(synth_b)["settings"]["overrides"]
    synth_a2 = execute(config, random_specs(*args, "synth_a2", N_SYNTH, "A2", lambda r: sample_synth(r, "A2"), best_aug, 4))
    save(config, "synth_a2", synth_a2)
    best_a2 = best(synth_a2)["settings"]["overrides"]
    shares = execute(config, random_specs(*args, "shares", N_SHARES, "A2", sample_shares, best_a2, 3))
    save(config, "shares", shares)
    best_shares = best(shares)["settings"]["overrides"]
    pretrain = execute(config, random_specs(*args, "pretrain", N_PRETRAIN, "P", sample_pretrain, best_aug, 5))
    save(config, "pretrain", pretrain)
    best_p = best(pretrain)["settings"]["overrides"]
    bases = {"A0": budget, "A1": best_aug, "B": best_b, "A2": best_shares, "P": best_p}
    grid = execute(config, grid_specs(*args, bases))
    save(config, "grid", grid)
    pools = {"A0": [], "A1": augment, "B": synth_b, "A2": synth_a2 + shares, "P": pretrain}
    winners, counts, cv_scores = {}, {}, {}
    for arm in ARMS:
        candidates = pools[arm] + [r for r in grid if r["settings"]["arm"] == arm]
        counts[arm] = len(candidates)
        top = top_settings(candidates)
        folded = execute(config, cv_specs(*args, arm, top))
        save(config, f"cv_{arm}", folded)
        means = [float(np.mean([r["val_macro_f1"] for r in folded[i * N_FOLDS:(i + 1) * N_FOLDS]])) for i in range(len(top))]
        chosen = top[int(np.argmax(means))]
        cv_scores[arm] = means
        specs = [_spec(config, config_path, "confirm", f"{arm}_s{seed}", arm, seed,
                       chosen["settings"]["overrides"], chosen["settings"]["hparams"]) for seed in SEEDS]
        confirmed = execute(config, specs)
        save(config, f"confirm_{arm}", confirmed)
        winners[arm] = {"overrides": chosen["settings"]["overrides"], "hparams": chosen["settings"]["hparams"],
                        "cv_macro_f1": max(means), "mean_val_macro_f1": float(np.mean([x["val_macro_f1"] for x in confirmed])),
                        "val_macro_f1_by_seed": [x["val_macro_f1"] for x in confirmed], "trial": chosen["name"]}
    result = {"winners": winners, "trials_per_arm": counts, "cv_macro_f1_top5": cv_scores, "budget": budget,
              "grid": {arm: [{"lr": r["settings"]["hparams"]["lr"], "dropout": r["settings"]["hparams"]["dropout"],
                              "val_macro_f1": r["val_macro_f1"], "best_epoch": r["best_epoch"]}
                             for r in grid if r["settings"]["arm"] == arm] for arm in ARMS}}
    (out_dir(config) / WINNERS_JSON).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    print(json.dumps(run_search(args.config), indent=2))


if __name__ == "__main__":
    main()
