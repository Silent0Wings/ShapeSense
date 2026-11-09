"""Iteration 3's primary analysis: perturbed copies of fresh holdout 2.

The perturbed sets are built once from the first read of the holdout, saved with
their hashes and never rewritten, so every model scores identical images. The
rule, the levels and the comparisons are fixed in
docs/crisp_dm/iteration_3/preregistration.md.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np

from src.common.hashing import sha256_path
from src.common.perturb import build_set
from src.common.robust_summary import summarise
from src.stage5_eval import criterion, evaluate, tables
from src.stage5_eval.metrics import accuracy, confusion, macro_f1
from src.stage5_eval.stats import analysis_rng, cluster_bootstrap, holm, mcnemar_test, per_seed_differences

RESULTS_FILE = "robust_results.json"
NOTE = "Perturbed copies of fresh holdout 2, built once inside Stage 5."


def sets_for(images: np.ndarray | None, levels: Sequence[str], seed: int, out_dir: Path,
             manifest_hash: str) -> dict[str, np.ndarray]:
    """Each perturbed set: built on the first call, then read back and checked."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    stored = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {"sets": {}}
    if stored.get("manifest_hash", manifest_hash) != manifest_hash:
        raise RuntimeError("the saved perturbed sets were built from another holdout manifest")
    stored["manifest_hash"] = manifest_hash
    out = {}
    for name in levels:
        path = out_dir / f"{name}.npz"
        if name in stored["sets"]:
            if sha256_path(path) != stored["sets"][name]:
                raise RuntimeError(f"saved perturbed set {name} changed on disk")
        else:
            if images is None:
                raise RuntimeError(f"perturbed set {name} is missing and no holdout read is available")
            np.savez_compressed(path, images=build_set(name, images, seed))
            stored["sets"][name] = sha256_path(path)
        with np.load(path, allow_pickle=False) as saved:
            out[name] = saved["images"]
    manifest_path.write_text(json.dumps(stored, indent=2) + "\n", encoding="utf-8")
    return out


def predict_levels(specs: Sequence[evaluate.ModelSpec], sets: Mapping[str, np.ndarray], clean: Mapping[str, dict],
                   out_dir: Path, manifest_hash: str,
                   predictors: Mapping[str, Callable] | None = None) -> dict[str, dict[str, dict]]:
    """model -> level -> record, cached per model and level. Reads no sealed manifest."""
    out: dict[str, dict[str, dict]] = {}
    for spec in specs:
        predict = (predictors or {}).get(spec.name) or evaluate.default_predictor(spec)
        out[spec.name] = {}
        reference = clean[spec.name]
        for level, images in sets.items():
            path = evaluate.cache_path(out_dir / spec.name, level)
            record = evaluate.cached_for(path, spec.fingerprint, manifest_hash)
            if record is None:
                probs, preds = predict(images)
                preds = np.asarray(preds, dtype=np.int64)
                evaluate.save_predictions(path, probs=probs, preds=preds, labels=reference["labels"],
                                          image_ids=reference["image_ids"], source_ids=reference["source_ids"],
                                          group_ids=reference["group_ids"], model_hash=spec.fingerprint,
                                          manifest_hash=manifest_hash)
                record = evaluate.load_predictions(path)
            out[spec.name][level] = record
    return out


def _scores(y: np.ndarray, preds: np.ndarray, k: int) -> dict:
    matrix = confusion(y, preds, k)
    return {"accuracy": 100.0 * accuracy(y, preds, k), "macro_f1": macro_f1(y, preds, k), "matrix": matrix,
            "recall": 100.0 * np.diag(matrix) / np.maximum(matrix.sum(1), 1)}


def _family(y, preds, groups, pairs, k, n_boot, seed, ci_level, scope) -> dict:
    """Bootstrap comparisons of one Holm family; ``preds[arm]`` is (n,) or (levels, n)."""
    out = {}
    for ref, cand in pairs:
        out[f"{cand} vs {ref}"] = cluster_bootstrap(y, preds[ref], preds[cand], groups, k, n_boot,
                                                    analysis_rng(seed, f"{scope}/{cand}_vs_{ref}"), ci_level)
    adjusted = holm({label: boot["p_two_sided"] for label, boot in out.items()})
    return {label: {"delta": boot["delta"], "ci": boot["ci"], "p_raw": boot["p_two_sided"], "p_holm": adjusted[label]}
            for label, boot in out.items()}


def analyse(clean: Mapping[str, dict], levelled: Mapping[str, dict[str, dict]], specs: Sequence[evaluate.ModelSpec],
            arms: Sequence[str], arm_of: Callable, names: Sequence[str], levels: Sequence[str], reference: str,
            candidate: str, secondary: Sequence[tuple[str, str]], min_gain: float, min_drop: float, n_boot: int,
            seed: int, ci_level: float, tables_dir: Path, stage_dir: Path) -> tuple[dict, list[Path]]:
    """The primary verdict, the Holm families, per-seed differences and the results document."""
    k = len(names)
    members = {arm: [s for s in specs if arm_of(s) == arm] for arm in arms}
    clean_ens = {arm: evaluate.ensemble([clean[s.name] for s in members[arm]]) for arm in arms}
    first = clean_ens[candidate]
    y, groups, sources = first["labels"], first["group_ids"], first["source_ids"]
    perturbed = {arm: np.stack([evaluate.ensemble([levelled[s.name][level] for s in members[arm]])["preds"]
                                for level in levels]) for arm in arms}
    primary = cluster_bootstrap(y, perturbed[reference], perturbed[candidate], groups, k, n_boot,
                                analysis_rng(seed, "robust/primary"), ci_level)
    decided = criterion.robust_verdict(primary, min_drop, min_gain)
    by_source = cluster_bootstrap(y, perturbed[reference], perturbed[candidate], sources, k, n_boot,
                                  analysis_rng(seed, "robust/primary_by_source"), ci_level)
    pairs = [tuple(p) for p in secondary if p[0] in arms and p[1] in arms]
    clean_preds = {arm: clean_ens[arm]["preds"] for arm in arms}
    clean_family = [(reference, candidate), *pairs]

    per_run: dict[str, dict] = {arm: {} for arm in arms}
    mean_scores: dict[str, dict[int, float]] = {arm: {} for arm in arms}
    for arm in arms:
        for spec in members[arm]:
            run_seed = int(spec.extra["seed"])
            scores = {"clean": _scores(y, clean[spec.name]["preds"], k)}
            scores.update({level: _scores(y, levelled[spec.name][level]["preds"], k) for level in levels})
            per_run[arm][run_seed] = scores
            mean_scores[arm][run_seed] = float(np.mean([scores[level]["macro_f1"] for level in levels]))
    seeds = sorted(next(iter(per_run.values())))
    per_seed = {f"{cand} vs {ref}": per_seed_differences(mean_scores[ref], mean_scores[cand])
                for ref, cand in [(reference, candidate), *pairs]}
    result = {"n": int(y.size), "label": f"{candidate} vs {reference}", "levels": list(levels),
              "verdict": decided["verdict"], "delta": decided["delta"], "ci": decided["ci"],
              "reasons": decided["reasons"], "harmful_classes": decided["harmful_classes"],
              "strict_pass": decided["strict_pass"], "ci_clustered_by_source": by_source["ci"],
              "n_clusters": primary["n_clusters"],
              "secondary": _family(y, perturbed, groups, pairs, k, n_boot, seed, ci_level, "robust/secondary"),
              "clean": _family(y, clean_preds, groups, clean_family, k, n_boot, seed, ci_level, "robust/clean"),
              "mcnemar_clean": mcnemar_test(clean_preds[reference] == y, clean_preds[candidate] == y),
              "per_seed": per_seed,
              "ensembles": {arm: {"clean_macro_f1": macro_f1(y, clean_preds[arm], k),
                                  "perturbed_macro_f1": float(np.mean([macro_f1(y, p, k) for p in perturbed[arm]]))}
                            for arm in arms}}
    outputs: list[Path] = []
    rows = [[result["label"], "primary (perturbed)", f"{result['delta']:+.2f}",
             f"[{result['ci'][0]:.2f}, {result['ci'][1]:.2f}]", "--", "--"]]
    for scope, family in (("secondary (perturbed)", result["secondary"]), ("clean", result["clean"])):
        rows += [[label, scope, f"{c['delta']:+.2f}", f"[{c['ci'][0]:.2f}, {c['ci'][1]:.2f}]",
                  f"{c['p_raw']:.3f}", f"{c['p_holm']:.3f}"] for label, c in family.items()]
    outputs.extend(tables.write_table(tables_dir, "robust_comparisons",
                                      ("comparison", "role", "delta", "ci", "p_raw", "p_holm"), rows))
    path = Path(stage_dir) / RESULTS_FILE
    document = summarise(per_run, seeds, list(names), int(y.size), "fresh_holdout_2", seed, NOTE)
    path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    outputs.append(path)
    return result, outputs
