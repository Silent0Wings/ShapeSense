"""The fresh holdout analysis for CRISP-DM iteration 2.

The test split was read in iteration 1, so it is weaker evidence the second
time. The fresh holdout has never been seen by any choice in the project. This
applies the same locked rule to it and writes its own tables; predictions come
from ``evaluate_models`` with the fresh-holdout reader.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np

from src.stage5_eval import criterion, evaluate, tables
from src.stage5_eval.metrics import accuracy, group_accuracy, macro_f1, per_class_f1
from src.stage5_eval.stats import analysis_rng, cluster_bootstrap, mcnemar_test


def _thresholds(y: np.ndarray, k: int, noise_accuracy: float, min_drop: float) -> np.ndarray:
    """Per-class drop threshold from this holdout's own class sizes."""
    counts = np.bincount(y, minlength=k)
    bands = [criterion.noise_band_points(int(n), noise_accuracy) if n else 0.0 for n in counts]
    return criterion.class_thresholds(bands, min_drop)


def analyse(models: Mapping[str, dict], specs: Sequence[evaluate.ModelSpec], arms: Sequence[str],
            arm_of: Callable, names: Sequence[str], reference: str, candidate: str, min_gain: float,
            min_drop: float, n_boot: int, seed: int, ci_level: float,
            ev_cfg: Mapping, tables_dir: Path) -> tuple[dict, list[Path]]:
    """Ensembles per arm, the primary comparison and tables on the fresh holdout."""
    k = len(names)
    ens = {arm: evaluate.ensemble([models[s.name] for s in specs if arm_of(s) == arm]) for arm in arms}
    y = ens[candidate]["labels"]
    sources = ens[candidate]["source_ids"]
    boot = cluster_bootstrap(y, ens[reference]["preds"], ens[candidate]["preds"], ens[candidate]["group_ids"], k, n_boot,
                             analysis_rng(seed, "fresh/primary"), ci_level)
    thresholds = _thresholds(y, k, float(ev_cfg["noise_band_accuracy"]), min_drop)
    verdict = criterion.verdict(boot, thresholds, min_gain, report_drop_points=min_drop)
    mc = mcnemar_test(ens[reference]["preds"] == y, ens[candidate]["preds"] == y)

    by_arm = {arm: {"accuracy": accuracy(y, ens[arm]["preds"], k), "macro_f1": macro_f1(y, ens[arm]["preds"], k),
                    "per_class_f1": per_class_f1(y, ens[arm]["preds"], k).tolist(),
                    "per_source": group_accuracy(y, ens[arm]["preds"], sources)} for arm in arms}
    outputs: list[Path] = []
    columns = ("arm", "accuracy_pct", "macro_f1_points")
    rows = [[arm, f"{by_arm[arm]['accuracy'] * 100:.1f}", f"{by_arm[arm]['macro_f1']:.1f}"] for arm in arms]
    outputs.extend(tables.write_table(tables_dir, "fresh_metrics", columns, rows))
    per_class_columns = ("class", "n", *(f"f1_{arm}" for arm in arms))
    counts = np.bincount(y, minlength=k)
    per_class_rows = [[name, str(int(counts[c])), *(f"{by_arm[arm]['per_class_f1'][c]:.1f}" for arm in arms)]
                      for c, name in enumerate(names)]
    outputs.extend(tables.write_table(tables_dir, "fresh_per_class", per_class_columns, per_class_rows))
    result = {"n": int(y.size), "label": f"{candidate} vs {reference}", "verdict": verdict["verdict"],
              "delta": verdict["delta"], "ci": verdict["ci"], "reasons": verdict["reasons"],
              "harmful_classes": verdict["harmful_classes"], "mcnemar": mc,
              "arms": {a: {"accuracy": v["accuracy"], "macro_f1": v["macro_f1"]} for a, v in by_arm.items()},
              "per_class_f1": {a: v["per_class_f1"] for a, v in by_arm.items()},
              "per_source": {a: v["per_source"] for a, v in by_arm.items()},
              "counts": counts.tolist()}
    return result, outputs
