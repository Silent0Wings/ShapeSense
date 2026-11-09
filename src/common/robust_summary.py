"""Summarise model scores on perturbed image sets, per arm and per perturbation family."""

from __future__ import annotations

import numpy as np

from src.common.perturb import SETS

NOISE_FAMILIES = ("gaussian", "salt_pepper", "blur", "jpeg", "brightness", "contrast", "occlusion")


def _summary(values: list[float]) -> dict[str, float]:
    return {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1))}


def family_drop(scores: dict, names: list[str]) -> float:
    """Mean of clean accuracy minus perturbed accuracy over ``names``, in points."""
    clean = scores["clean"]["accuracy"]
    return float(np.mean([clean - scores[name]["accuracy"] for name in names]))


def summarise(per_run: dict, seeds: list[int], labels: list[str], n_images: int, split: str, seed: int, note: str) -> dict:
    """``per_run[arm][seed][set] = {accuracy, macro_f1, matrix, recall}`` -> the results document."""
    present = list(next(iter(next(iter(per_run.values())).values())))
    used = {name: SETS[name] for name in SETS if name in present}
    rotated = [n for n, s in used.items() if s[0] == "rotated" and n != "rot0"]
    noisy = [n for n, s in used.items() if s[0] in NOISE_FAMILIES]
    by_arm, families, per_class, matrices = {}, {}, {}, {}
    for arm, runs in per_run.items():
        by_arm[arm] = {name: {"accuracy": _summary([runs[s][name]["accuracy"] for s in seeds]),
                              "macro_f1": _summary([runs[s][name]["macro_f1"] for s in seeds]),
                              "drop": _summary([runs[s]["clean"]["accuracy"] - runs[s][name]["accuracy"] for s in seeds])}
                       for name in used}
        families[arm] = {"clean": _summary([runs[s]["clean"]["accuracy"] for s in seeds]),
                         "rotated_drop": _summary([family_drop(runs[s], rotated) for s in seeds]),
                         "noisy_drop": _summary([family_drop(runs[s], noisy) for s in seeds])}
        for family in NOISE_FAMILIES:
            names = [n for n, v in used.items() if v[0] == family]
            if names:
                families[arm][f"{family}_drop"] = _summary([family_drop(runs[s], names) for s in seeds])
        per_class[arm] = {name: np.mean([runs[s][name]["recall"] for s in seeds], axis=0).round(2).tolist() for name in used}
        matrices[arm] = {name: np.sum([runs[s][name]["matrix"] for s in seeds], axis=0).tolist() for name in rotated}
    return {"note": note, "split": split, "seed": seed, "n_images": n_images, "training_seeds": seeds, "classes": labels,
            "sets": [{"name": n, "family": v[0], "level": v[1]} for n, v in used.items()],
            "by_arm": by_arm, "families": families, "per_class": per_class, "confusion_summed_over_seeds": matrices}
