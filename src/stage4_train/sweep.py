"""The arm x seed sweep, optional leave-one-source-out runs, seed disagreement.

* ``job_specs`` turns ``configs/pipeline.yaml#runs`` into one job per
  entry (``<arm>_<seed>``) with the SAME frozen ``steps_per_epoch`` and the
  SAME Decision 7 ``hparams`` for every job (R1-R3). When the Stage 1
  source-shortcut trigger fired (Decision 12, R14), two more jobs train
  A1 and B with the first seed on train/val stores WITHOUT the Hand-Drawn
  source (``<arm>_loso_handdrawn_<seed>``), still at the A0 step budget.
* ``run_sweep`` executes the jobs with a ``ProcessPoolExecutor``
  (``train.parallel_runs`` workers). Windows uses the spawn start method,
  so the worker ``run_job`` is a top-level function that rebuilds config,
  stores, transform and generator from the config path it is handed. A
  job whose ``run.json`` already exists with the same hparams and budget
  is skipped (resume).
* ``seed_disagreement`` measures, per arm, the mean pairwise fraction of
  validation images whose argmax differs between seeds (R11). This is a
  robustness number for the report, NOT the power check: Decision 10
  moved that to Stage 5's paired bootstrap over validation probabilities.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path
from typing import Callable

import numpy as np
from threadpoolctl import threadpool_limits

from src.common.catalog import load_split_rows
from src.common.config import DEFAULT_CONFIG, LOSO_ARMS, load_config, resolve
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.data import ImageStore
from src.stage4_train.train import (VAL_PROBS_FILE, completed_run, recipe_fingerprint,
                                    train_one)

STAGE_DIR_NAME = "stage4"
TRAIN_SPLIT = "train"
VAL_SPLIT = "val"
IMAGE_ID_COLUMN = "image_id"           # manifest column (common.splits.MANIFEST_COLUMNS)
# Decision 12: the Hand-Drawn source held out in the leave-one-source-out runs
# (catalog source_id of the frobertpixto Hand-Drawn Shapes Dataset).
LOSO_HOLDOUT_SOURCE = "github_handdrawn"
LOSO_RUN_TAG = "loso_handdrawn"
SEED_DISAGREEMENT_JSON = "seed_disagreement.json"
SEED_DISAGREEMENT_NOTE = ("Robustness number only (stage_4.md R11): mean pairwise fraction of "
                          "validation images whose argmax differs between seeds of the same "
                          "arm. It is NOT the power check; Decision 10 moved that to Stage 5's "
                          "paired bootstrap over validation probabilities.")

JobRunner = Callable[[dict], dict]


# --------------------------------------------------------------------------- #
# Stores
# --------------------------------------------------------------------------- #

def val_image_ids(config: dict) -> np.ndarray:
    """str array (n_val,) of validation ``image_id`` in manifest order."""
    rows = load_split_rows(config, VAL_SPLIT)
    return np.array([row[IMAGE_ID_COLUMN] for row in rows], dtype=str)


def load_stores(config: dict, holdout_source: str | None = None
                ) -> tuple[ImageStore, ImageStore, np.ndarray]:
    """Train and val ``ImageStore`` plus val image ids, optionally without one source.

    With ``holdout_source`` (Decision 12 leave-one-source-out) every image
    of that source is dropped from BOTH stores and from the id array, so
    ``val_probs.npz`` stays aligned. Never touches the test split (R8).
    """
    train = ImageStore.from_split(config, TRAIN_SPLIT)
    val = ImageStore.from_split(config, VAL_SPLIT)
    ids = val_image_ids(config)
    if ids.shape[0] != len(val):
        raise ValueError(f"val has {len(val)} images but {ids.shape[0]} manifest ids")
    if holdout_source:
        keep = val.source_ids != str(holdout_source)
        ids = ids[keep]
        train = train.filter_out_source(holdout_source)
        val = val.filter_out_source(holdout_source)
    return train, val, ids


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #

def run_name(arm: str, seed: int, holdout_source: str | None = None) -> str:
    """``<arm>_<seed>`` or ``<arm>_loso_handdrawn_<seed>`` for the held-out runs."""
    if holdout_source:
        return f"{arm}_{LOSO_RUN_TAG}_{int(seed)}"
    return f"{arm}_{int(seed)}"


def job_specs(config: dict, steps_per_epoch: int, hparams: dict, loso: bool,
              config_path: str | Path, out_dir: Path) -> list[dict]:
    """One picklable job dict per run; identical budget and hparams everywhere."""
    hp = {"lr": float(hparams["lr"]), "dropout": float(hparams["dropout"])}
    out_dir = Path(out_dir)
    jobs: list[dict] = []

    def add(arm: str, seed: int, holdout: str | None, name_prefix: str | None = None) -> None:
        name = run_name(name_prefix or arm, seed, holdout)
        jobs.append({
            "run_name": name,
            "arm": str(arm),
            "seed": int(seed),
            "holdout_source": holdout,
            "hparams": hp,
            "steps_per_epoch": int(steps_per_epoch),
            "config_path": str(config_path),
            "out_dir": str(out_dir / name),
        })

    for run in config["runs"]:
        add(run["arm"], run["seed"], run.get("holdout_source") or None, run.get("name"))
    if loso:
        seed0 = int(config["seed_set"][0])
        for arm in LOSO_ARMS:
            add(arm, seed0, LOSO_HOLDOUT_SOURCE)
    return jobs


def classes_lost_to_holdout(train_store: ImageStore) -> tuple[int, ...]:
    """Classes with no training image left once a source is held out (P-61).

    Hand-Drawn is the only source of ellipse, so its LOSO runs train on the
    other nine classes. Call this for held-out runs only: an empty class in
    an ordinary run must keep failing.
    """
    return tuple(int(c) for c in np.flatnonzero(train_store.class_counts() == 0))


def run_job(spec: dict) -> dict:
    """Worker entry point (top-level so Windows ``spawn`` can pickle it).

    Rebuilds everything from ``spec["config_path"]``, skips a finished run
    with identical settings, otherwise trains it and returns ``run.json``.
    """
    config = load_config(spec["config_path"])
    # One pool per worker process, sized like torch's (see run.py).
    threadpool_limits(int(config["train"]["num_threads"]))
    run_dir = Path(spec["out_dir"])
    done = completed_run(run_dir, spec["hparams"], spec["steps_per_epoch"],
                         recipe_fingerprint(config))
    if done is not None:
        return done
    holdout = spec.get("holdout_source")
    train_store, val_store, ids = load_stores(config, holdout)
    excluded = classes_lost_to_holdout(train_store) if holdout else ()
    transform = build_transform(config)
    generate = build_generator(config)
    return train_one(spec["run_name"], spec["arm"], spec["seed"], config, train_store, val_store,
                     transform, generate, spec["hparams"], run_dir,
                     steps_per_epoch=spec["steps_per_epoch"], val_image_ids=ids,
                     excluded_classes=excluded)


def run_sweep(config: dict, steps_per_epoch: int, hparams: dict, loso: bool, *,
              config_path: str | Path = DEFAULT_CONFIG, out_dir: Path | None = None,
              job_runner: JobRunner = run_job) -> list[dict]:
    """Train every job of ``job_specs`` and return their ``run.json`` dicts in job order.

    Finished runs (same hparams + budget) are reused. With
    ``train.parallel_runs > 1`` and more than one pending job the jobs run
    in a ``ProcessPoolExecutor``; each process stays deterministic from
    (arm, seed) because every seed lives inside the job (R9).
    """
    out_dir = Path(out_dir) if out_dir is not None else \
        resolve(config["paths"]["artifacts_dir"]) / STAGE_DIR_NAME
    jobs = job_specs(config, steps_per_epoch, hparams, loso, config_path, out_dir)
    results: dict[str, dict] = {}
    pending: list[dict] = []
    for spec in jobs:
        done = completed_run(Path(spec["out_dir"]), spec["hparams"], spec["steps_per_epoch"],
                             recipe_fingerprint(config))
        if done is not None:
            results[spec["run_name"]] = done
        else:
            pending.append(spec)

    results.update(run_specs(config, pending, job_runner=job_runner))
    return [results[spec["run_name"]] for spec in jobs]


def run_specs(config: dict, specs: list[dict], *,
              job_runner: JobRunner = run_job) -> dict[str, dict]:
    """Train the given job specs, ``train.parallel_runs`` at a time.

    Shared by the sweep and the Decision 7 tuning grid. Returns
    ``{run_name: run.json dict}``.
    """
    workers = int(config["train"]["parallel_runs"])
    out: dict[str, dict] = {}
    if workers <= 1 or len(specs) <= 1:
        for spec in specs:
            out[spec["run_name"]] = job_runner(spec)
    else:
        with ProcessPoolExecutor(max_workers=min(workers, len(specs))) as pool:
            for spec, info in zip(specs, pool.map(job_runner, specs)):
                out[spec["run_name"]] = info
    return out


# --------------------------------------------------------------------------- #
# Seed disagreement (R11)
# --------------------------------------------------------------------------- #

def pairwise_disagreement(preds_a: np.ndarray, preds_b: np.ndarray) -> float:
    """Fraction of positions where two int label arrays (N,) differ."""
    preds_a = np.asarray(preds_a)
    preds_b = np.asarray(preds_b)
    if preds_a.shape != preds_b.shape:
        raise ValueError(f"prediction shapes differ: {preds_a.shape} vs {preds_b.shape}")
    if preds_a.size == 0:
        return 0.0
    return float(np.mean(preds_a != preds_b))


def seed_disagreement(results_dir: Path, runs: list[dict]) -> dict:
    """Per arm, mean pairwise argmax disagreement between seeds on validation.

    Args:
        results_dir: ``artifacts/stage4``; each run's ``val_probs.npz`` is read
            from ``results_dir/<run_name>/``.
        runs: dicts with ``run_name`` (or ``name``), ``arm``, ``seed`` and
            optionally ``holdout_source``; leave-one-source-out runs are
            skipped because their validation set differs.

    Returns ``{"per_arm": {arm: {"runs", "n_val", "pairs": [{"a", "b",
    "disagreement"}], "mean_pairwise_disagreement"}}, "note"}``. An arm
    with fewer than two seeds gets ``mean_pairwise_disagreement: None``.
    """
    results_dir = Path(results_dir)
    by_arm: dict[str, list[tuple[int, str, np.ndarray]]] = {}
    for run in runs:
        if run.get("holdout_source"):
            continue
        name = run.get("run_name") or run["name"]
        with np.load(results_dir / name / VAL_PROBS_FILE) as data:
            preds = np.asarray(data["probs"]).argmax(axis=1)
        by_arm.setdefault(str(run["arm"]), []).append((int(run["seed"]), name, preds))

    per_arm: dict[str, dict] = {}
    for arm, entries in by_arm.items():
        entries.sort(key=lambda e: e[0])
        pairs = [{"a": a_name, "b": b_name, "disagreement": pairwise_disagreement(a_pred, b_pred)}
                 for (_, a_name, a_pred), (_, b_name, b_pred) in combinations(entries, 2)]
        per_arm[arm] = {
            "runs": [name for _, name, _ in entries],
            "n_val": int(entries[0][2].shape[0]),
            "pairs": pairs,
            "mean_pairwise_disagreement": (float(np.mean([p["disagreement"] for p in pairs]))
                                           if pairs else None),
        }
    return {"per_arm": per_arm, "note": SEED_DISAGREEMENT_NOTE}


def write_seed_disagreement(results_dir: Path, runs: list[dict]) -> tuple[dict, Path]:
    """``seed_disagreement`` plus writing ``results_dir/seed_disagreement.json``."""
    result = seed_disagreement(results_dir, runs)
    path = Path(results_dir) / SEED_DISAGREEMENT_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return result, path
