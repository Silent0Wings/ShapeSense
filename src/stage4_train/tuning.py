"""Decision 7 tuning: one small grid on arm A1's validation split (R4).

``lr x dropout`` from ``configs/pipeline.yaml#train.tuning`` is trained
once each on ``train.tuning.arm`` with the first seed of ``seed_set``.
The winner is selected on validation macro-F1 ONLY and is then used for
every arm and every seed (no arm-specific tuning). The grid results are
recorded in ``artifacts/stage4/tuning.json``; a file whose ``spec`` (arm,
seed, grid, step budget) matches is reused so the grid never retrains.

The trainer is injectable (``trainer=``) so the selection rule can be
tested with preset scores instead of six CNN runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from src.stage4_train.sampling import GenerateLike, TransformLike
from src.stage4_train.train import completed_run, recipe_fingerprint, train_one

TUNING_JSON = "tuning.json"
TUNING_DIR = "tuning"           # artifacts/stage4/tuning/<lr>_<dropout>/
TUNING_RUN_PREFIX = "tuning"    # run_name recorded in each grid point's run.json

Trainer = Callable[..., dict]


def grid_points(tuning_cfg: dict) -> list[dict]:
    """``[{"lr", "dropout"}, ...]`` in config order (lr outer, dropout inner)."""
    lrs = [float(v) for v in tuning_cfg["lr"]]
    dropouts = [float(v) for v in tuning_cfg["dropout"]]
    if not lrs or not dropouts:
        raise ValueError("train.tuning.lr and train.tuning.dropout must be non-empty")
    return [{"lr": lr, "dropout": do} for lr in lrs for do in dropouts]


def point_dir_name(hparams: dict) -> str:
    """Folder name of one grid point: ``<lr>_<dropout>``."""
    return f"{float(hparams['lr'])}_{float(hparams['dropout'])}"


def select_winner(grid: list[dict]) -> dict:
    """Grid entry with the highest ``val_macro_f1``; ties keep the earlier entry (R4)."""
    if not grid:
        raise ValueError("grid must not be empty")
    best = grid[0]
    for entry in grid[1:]:
        if float(entry["val_macro_f1"]) > float(best["val_macro_f1"]):
            best = entry
    return {"lr": float(best["lr"]), "dropout": float(best["dropout"])}


def tuning_spec(config: dict, steps_per_epoch: int) -> dict:
    """What a cached tuning.json must match to be reused."""
    tuning_cfg = config["train"]["tuning"]
    return {
        "arm": str(tuning_cfg["arm"]),
        "seed": int(config["seed_set"][0]),
        "lr": [float(v) for v in tuning_cfg["lr"]],
        "dropout": [float(v) for v in tuning_cfg["dropout"]],
        "steps_per_epoch": int(steps_per_epoch),
        "selection_metric": str(config["train"]["selection_metric"]),
        "recipe": recipe_fingerprint(config),
    }


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_tuning(config: dict, train_store: Any, val_store: Any,
               transform: TransformLike | None, generate: GenerateLike | None,
               steps_per_epoch: int, out_dir: Path, *,
               trainer: Trainer | None = None,
               val_image_ids: np.ndarray | None = None,
               batch_runner: Callable[[list[dict]], dict[str, dict]] | None = None,
               config_path: str | Path | None = None) -> dict:
    """Run (or reuse) the Decision 7 grid and write ``<out_dir>/tuning.json``.

    Args:
        config: merged pipeline config.
        train_store, val_store: full ``ImageStore`` objects (arm A1 stream).
        transform, generate: Stage 2 / Stage 3 callables.
        steps_per_epoch: the frozen Decision 13 budget.
        out_dir: ``artifacts/stage4``; grid runs go to ``out_dir/tuning/<lr>_<dropout>/``.
        trainer: ``train_one``-compatible callable (keyword call); tests
            inject a fake returning preset ``val_macro_f1`` / ``best_epoch``.
        val_image_ids: forwarded to the trainer.
        batch_runner: optional ``specs -> {run_name: run.json}`` (the sweep's
            process pool, wired by run.py) so independent grid points train
            in parallel; used only when no ``trainer`` is injected.
        config_path: config file the parallel workers reload.

    Returns ``{"spec", "arm", "seed", "steps_per_epoch", "selection_metric",
    "grid": [{"lr", "dropout", "val_macro_f1", "best_epoch"}], "winner":
    {"lr", "dropout"}}``.
    """
    out_dir = Path(out_dir)
    spec = tuning_spec(config, steps_per_epoch)
    path = out_dir / TUNING_JSON
    existing = _load_json(path)
    if existing is not None and existing.get("spec") == spec and existing.get("winner"):
        return existing

    train = trainer or train_one
    arm = spec["arm"]
    seed = spec["seed"]
    points = grid_points(config["train"]["tuning"])
    recipe = recipe_fingerprint(config)
    infos: dict[str, dict] = {}
    if trainer is None and batch_runner is not None:
        specs = []
        for point in points:
            run_dir = out_dir / TUNING_DIR / point_dir_name(point)
            if completed_run(run_dir, point, steps_per_epoch, recipe) is None:
                specs.append({"run_name": f"{TUNING_RUN_PREFIX}_{point_dir_name(point)}",
                              "arm": arm, "seed": seed, "hparams": point,
                              "out_dir": str(run_dir), "steps_per_epoch": steps_per_epoch,
                              "config_path": str(config_path), "holdout_source": None})
        for s, info in batch_runner(specs).items():
            infos[s] = info
    grid: list[dict] = []
    for point in points:
        run_dir = out_dir / TUNING_DIR / point_dir_name(point)
        info = (infos.get(f"{TUNING_RUN_PREFIX}_{point_dir_name(point)}")
                or completed_run(run_dir, point, steps_per_epoch, recipe))
        if info is None:
            info = train(run_name=f"{TUNING_RUN_PREFIX}_{point_dir_name(point)}", arm=arm,
                         seed=seed, config=config, train_store=train_store,
                         val_store=val_store, transform=transform, generate=generate,
                         hparams=point, out_dir=run_dir, steps_per_epoch=steps_per_epoch,
                         val_image_ids=val_image_ids)
        grid.append({"lr": point["lr"], "dropout": point["dropout"],
                     "val_macro_f1": float(info["val_macro_f1"]),
                     "best_epoch": int(info["best_epoch"])})

    result = {
        "spec": spec,
        "arm": arm,
        "seed": seed,
        "steps_per_epoch": int(steps_per_epoch),
        "selection_metric": spec["selection_metric"],
        "grid": grid,
        "winner": select_winner(grid),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    return result
