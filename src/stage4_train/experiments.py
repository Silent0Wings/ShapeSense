"""Validation-only experiments for CRISP-DM iteration 3.

    python -m src.stage4_train.experiments [--phase train|score|all]

The designs and run counts are fixed in docs/crisp_dm/iteration_3/preregistration.md.
Trials live under ``artifacts/stage4/tuning_iter3/`` and resume when stopped.
Summaries go to docs/crisp_dm/iteration_3/experiments/. Only the train and
validation splits are touched, plus aggregate counts in ``split_stats.csv``.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy import ndimage
from skimage.morphology import skeletonize

from src.common.config import DEFAULT_CONFIG, REPO_ROOT, class_names, load_config, resolve, set_dotted
from src.stage2_augment import build_transform
from src.stage4_train.bn import recalibrated
from src.stage4_train.sampling import to_float
from src.stage4_train.search import SEEDS, _spec, execute, out_dir
from src.stage4_train.sweep import load_stores
from src.stage4_train.train import macro_f1_points

ARMS = ("A0", "A1", "B", "A2", "P")
FRACTIONS = (0.1, 0.25, 0.5, 1.0)
BUDGET_ARMS = ("A0", "A1", "A2")
BUDGETS = {"e60": {"train.max_epochs": 60}, "e30_nostop": {"train.early_stopping_patience": 999},
           "e60_nostop": {"train.max_epochs": 60, "train.early_stopping_patience": 999}}
SHAPES = ("rectangle", "square", "diamond", "circle", "ellipse")
ADOPT_GAIN = 0.5        # validation points every tested arm must gain to change the budget
EVAL_BATCH = 1024
ZERO = {"augment.rotate_deg": 0, "augment.scale": [1.0, 1.0], "augment.nonuniform_scale": 0.0, "augment.shear_deg": 0,
        "augment.translate_px": 0.0, "augment.noise_p": 0.0, "augment.blur_p": 0.0, "taxonomy.rotate_limit_deg": {}}
OUT = REPO_ROOT / "docs" / "crisp_dm" / "iteration_3" / "experiments"


def base(config: dict, arm: str) -> tuple[dict, dict]:
    spec = config["arms"][arm]
    return dict(spec.get("overrides", {})), dict(spec["hparams"])


def scarcity_specs(config: dict, path) -> list[dict]:
    out = []
    for arm in ARMS:
        overrides, hparams = base(config, arm)
        for fraction in FRACTIONS:
            for seed in SEEDS:
                out.append(_spec(config, path, "exp_scarcity", f"{arm}_f{int(fraction * 100)}_s{seed}", arm, seed,
                                 {**overrides, "train.real_fraction": fraction}, hparams))
    return out


def equal_real_specs(config: dict, path) -> list[dict]:
    out = []
    for arm in ("B", "A2"):
        overrides, hparams = base(config, arm)
        out += [_spec(config, path, "exp_equal_real", f"{arm}_s{seed}", arm, seed,
                      {**overrides, f"arms.{arm}.equal_real": True}, hparams) for seed in SEEDS]
    return out


def budget_specs(config: dict, path) -> list[dict]:
    out = []
    for arm in BUDGET_ARMS:
        overrides, hparams = base(config, arm)
        for name, change in BUDGETS.items():
            out += [_spec(config, path, "exp_budget", f"{arm}_{name}_s{seed}", arm, seed, {**overrides, **change}, hparams)
                    for seed in SEEDS]
    return out


def one_on_specs(config: dict, path) -> list[dict]:
    overrides, hparams = base(config, "A1")
    variants = {
        "rotation": {"augment.rotate_deg": overrides["augment.rotate_deg"],
                     "taxonomy.rotate_limit_deg": overrides["taxonomy.rotate_limit_deg"]},
        "scale": {"augment.scale": overrides["augment.scale"]},
        "noise": {"augment.noise_p": overrides["augment.noise_p"]},
        "blur": {"augment.blur_p": overrides["augment.blur_p"]},
        "reframe_only": {},
    }
    return [_spec(config, path, "exp_one_on", f"{name}_s{seed}", "A1", seed, {**ZERO, **change}, hparams)
            for name, change in variants.items() for seed in SEEDS]


def all_specs(config: dict, path) -> list[dict]:
    return scarcity_specs(config, path) + equal_real_specs(config, path) + budget_specs(config, path) + one_on_specs(config, path)


def _predict(model, images: np.ndarray, device: str) -> np.ndarray:
    out = []
    with torch.no_grad():
        for start in range(0, len(images), EVAL_BATCH):
            out.append(model(torch.from_numpy(to_float(images[start:start + EVAL_BATCH])).to(device)).argmax(1).cpu().numpy())
    return np.concatenate(out)


def _load(run_dir: Path, device: str):
    return torch.jit.load(str(run_dir / "model.pt"), map_location=device).eval()


def score_model(model, clean: np.ndarray, sets: dict[str, np.ndarray], labels: np.ndarray, k: int, device: str) -> dict:
    """Validation macro-F1 clean, and averaged over the pre-registered damage levels."""
    return {"clean": macro_f1_points(labels, _predict(model, clean, device), k),
            "perturbed": float(np.mean([macro_f1_points(labels, _predict(model, im, device), k) for im in sets.values()]))}


def _table(rows: dict[str, list[dict]]) -> dict:
    """condition -> mean and std of each score over its seeds."""
    out = {}
    for name, items in rows.items():
        out[name] = {"n": len(items)}
        for key in items[0]:
            values = [item[key] for item in items]
            out[name][key] = {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0}
    return out


def _measure(image: np.ndarray) -> tuple[float, float]:
    """(long side / short side of the bounding box, mean stroke width in pixels)."""
    ink = image < 128
    if not ink.any():
        return 1.0, 0.0
    points = np.argwhere(ink)
    sides = points.max(0) - points.min(0) + 1
    skeleton = skeletonize(ink)
    widths = 2.0 * ndimage.distance_transform_edt(ink)[skeleton]
    return float(sides.max() / sides.min()), float(widths.mean()) if widths.size else 0.0


def _profile(images: np.ndarray, labels: np.ndarray, names: list[str]) -> dict:
    out = {}
    for name in SHAPES:
        measured = np.array([_measure(im) for im in images[labels == names.index(name)]])
        out[name] = {key: {"mean": float(col.mean()), "p10": float(np.percentile(col, 10)), "p90": float(np.percentile(col, 90))}
                     for key, col in (("aspect_ratio", measured[:, 0]), ("stroke_px", measured[:, 1]))}
    return out


def _transformed(images: np.ndarray, labels: np.ndarray, transform, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.stack([np.asarray(transform(im, int(c), rng), dtype=np.uint8) for im, c in zip(images, labels)])


def _with(config: dict, overrides: dict) -> dict:
    out = json.loads(json.dumps(config))
    for key, value in overrides.items():
        set_dotted(out, key, value)
    return out


def _load_sets(config: dict) -> dict[str, np.ndarray]:
    root = resolve(config["paths"]["artifacts_dir"]) / "robustness" / "val_sets"
    out = {}
    for level in config["evaluation"]["robust"]["levels"]:
        with np.load(root / f"{level}.npz", allow_pickle=False) as saved:
            out[level] = saved["images"]
    return out


def _write(name: str, document: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")


def _val_vs_test(config: dict) -> dict:
    """Class and source shares in validation and test, from the aggregate counts only."""
    totals: dict[str, dict[str, dict[str, int]]] = {"class": defaultdict(lambda: defaultdict(int)),
                                                    "source": defaultdict(lambda: defaultdict(int))}
    path = resolve(config["paths"]["artifacts_dir"]) / "stage1" / "split_stats.csv"
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["split"] in ("val", "test"):
                totals["class"][row["label_name"]][row["split"]] += int(row["n"])
                totals["source"][row["source_id"]][row["split"]] += int(row["n"])
    out = {}
    for kind, table in totals.items():
        sum_val = sum(v["val"] for v in table.values())
        sum_test = sum(v["test"] for v in table.values())
        rows = {k: {"val_share": v["val"] / sum_val, "test_share": v["test"] / sum_test} for k, v in table.items()}
        out[kind] = {"rows": rows, "total_variation": 0.5 * sum(abs(r["val_share"] - r["test_share"]) for r in rows.values())}
    return out


def score_all(config: dict) -> dict:
    """Summarise every experiment, using saved models and the fixed validation sets."""
    root = out_dir(config)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train, val, _ids = load_stores(config)
    names, k = class_names(config), val.n_classes
    sets = _load_sets(config)
    scored: dict[Path, dict] = {}

    def rows_for(folder: Path, names_seeds: dict[str, str]) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for label, stem in names_seeds.items():
            items = []
            for seed in SEEDS:
                run = folder / f"{stem}_s{seed}"
                scored[run] = scored.get(run) or score_model(_load(run, device), val.images, sets, val.labels, k, device)
                info = json.loads((run / "result.json").read_text(encoding="utf-8"))
                items.append({**scored[run], "epochs_run": float(info["epochs_run"])})
            out[label] = items
        return out

    full = {arm: f"{arm}_f100" for arm in ARMS}
    scarcity = {f"{arm}/{int(f * 100)}": f"{arm}_f{int(f * 100)}" for arm in ARMS for f in FRACTIONS}
    scarcity_rows = rows_for(root / "exp_scarcity", scarcity)
    _write("scarcity", {"fractions": [int(f * 100) for f in FRACTIONS], "arms": list(ARMS), "scores": _table(scarcity_rows)})

    equal = {f"{arm}/equal_real": arm for arm in ("B", "A2")}
    equal_rows = rows_for(root / "exp_equal_real", equal)
    equal_rows.update({f"{arm}/normal": scarcity_rows[f"{arm}/100"] for arm in ("B", "A2")})
    _write("equal_real", {"scores": _table(equal_rows)})

    budgets = {f"{arm}/{name}": f"{arm}_{name}" for arm in BUDGET_ARMS for name in BUDGETS}
    budget_rows = rows_for(root / "exp_budget", budgets)
    budget_rows.update({f"{arm}/e30": scarcity_rows[f"{arm}/100"] for arm in BUDGET_ARMS})
    table = _table(budget_rows)
    gains = {name: {arm: table[f"{arm}/{name}"]["clean"]["mean"] - table[f"{arm}/e30"]["clean"]["mean"] for arm in BUDGET_ARMS}
             for name in BUDGETS}
    adopted = [name for name, by_arm in gains.items() if all(g >= ADOPT_GAIN for g in by_arm.values())]
    best = max(adopted, key=lambda name: np.mean(list(gains[name].values()))) if adopted else None
    _write("budget", {"scores": table, "gains_over_e30": gains, "adopted": best, "rule_points": ADOPT_GAIN})

    bn_rows: dict[str, list[dict]] = {}
    for arm in ("B", "A2"):
        for seed in SEEDS:
            run = root / "exp_scarcity" / f"{arm}_f100_s{seed}"
            dropout = float(config["arms"][arm]["hparams"]["dropout"])
            bn_rows.setdefault(f"{arm}/recalibrated", []).append(score_model(
                recalibrated(run / "model.pt", config, k, dropout, train.images, device), val.images, sets, val.labels, k, device))
            bn_rows.setdefault(f"{arm}/saved", []).append(scored[run])
    _write("batchnorm", {"scores": _table(bn_rows)})

    reframe = build_transform(_with(config, ZERO))
    tuned = build_transform(_with(config, base(config, "A1")[0]))
    reframed = _transformed(val.images, val.labels, reframe, 11)
    augmented = _transformed(val.images, val.labels, tuned, 12)
    preprocess: dict[str, list[dict]] = {}
    for arm in ("A0", "A1", "B", "A2"):
        for seed in SEEDS:
            model = _load(root / "exp_scarcity" / f"{arm}_f100_s{seed}", device)
            preprocess.setdefault(arm, []).append({
                "raw": macro_f1_points(val.labels, _predict(model, val.images, device), k),
                "reframed_only": macro_f1_points(val.labels, _predict(model, reframed, device), k)})
    _write("preprocess", {"scores": _table(preprocess),
                          "profiles": {"real": _profile(val.images, val.labels, names),
                                       "reframed": _profile(reframed, val.labels, names),
                                       "augmented": _profile(augmented, val.labels, names)}})

    one_on = {name: name for name in ("rotation", "scale", "noise", "blur", "reframe_only")}
    one_rows = rows_for(root / "exp_one_on", one_on)
    one_rows["all_on"] = scarcity_rows["A1/100"]
    _write("one_transform_on", {"scores": _table(one_rows)})
    _write("val_vs_test", _val_vs_test(config))
    return {"adopted": best, "gains": gains, "full": full}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--phase", default="all", choices=("train", "score", "all"))
    args = parser.parse_args()
    config = load_config(args.config)
    if args.phase in ("train", "all"):
        execute(config, all_specs(config, args.config))
    if args.phase in ("score", "all"):
        print(json.dumps(score_all(config), indent=1))


if __name__ == "__main__":
    main()
