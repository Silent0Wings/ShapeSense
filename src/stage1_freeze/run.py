"""Stage 1 — data freeze and splits. Owner: ______

Contract (stages/stage_1.md, implementation.md § Stage 1):
  Input:  data_set/unified/catalog.sqlite + metadata.csv (pHash), the
          standardized PNGs (md5 pass), configs/gemstone_ids.csv,
          configs/pipeline.yaml (split, filter_gemstones).
  Output: configs/splits/{train,val,test}.csv (committed, Decision 16);
          artifacts/stage1/: contact sheets, split_stats.csv,
          noise_bands.csv, fd_check.json, source_classifier.json,
          report_counts.tex, stage6_note.md (+ NOTICE_shortcut.md if the
          Decision 12 trigger fires). status.json is written by the runner.
  Fail-closed: if any leakage check fails the stage returns
          status: failed and writes NO manifests (R9).
  Stage 1 decides membership, so it may read every image; it never calls
  load_split("test"). The test split is locked here; only Stage 5 reads it.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from src.common.catalog import read_png
from src.common.config import REPO_ROOT, class_names, load_config, resolve
from src.common.hashing import config_subtree_hash, sha256_obj, sha256_path
from src.stage1_freeze.check_fds import check_rows
from src.stage1_freeze.contact_sheet import (REVIEW_CLASS_NAME, write_contact_sheets,
                                             write_template)
from src.stage1_freeze.exclusions import apply_source_label_exclusions
from src.stage1_freeze.gemstones import apply_gemstone_filter, read_exclusions
from src.stage1_freeze.identity import load_unified, read_metadata
from src.stage1_freeze.leakage import freeze, leakage_checks
from src.stage1_freeze.report_snippets import (FILTER_APPLIED, FILTER_PENDING, FILTER_SUPERSEDED,
                                               write_report_counts)
from src.stage1_freeze.source_check import shortcut_check
from src.stage1_freeze.splitting import (SPLIT_NAMES, global_groups, group_labels,
                                         group_sizes, group_split, mixed_label_groups)
from src.stage1_freeze.stats import fd_rows, noise_bands, split_stats, source_test_share

STAGE = "stage1"
DEPENDS = ["stage0"]

QUICKDRAW_DIAMONDS = "quickdraw/diamond"   # key in the exclusion counts
CONFIG_SUBTREES = ("split", "filter_gemstones", "exclude_source_labels", "paths", "taxonomy", "evaluation",
                   "success_criterion")
PHASE1_COUNTS = {"train": 12761, "val": 2890, "test": 2849}  # report Split paragraph, images
FD_EXAMPLE_LIMIT = 3            # violating groups listed per FD in fd_check.json
SPLIT_STATS_COLUMNS = ("split", "label_id", "label_name", "source_id", "n")
NOISE_BAND_COLUMNS = ("label_id", "label_name", "n_test", "noise_band_points", "threshold_points")
NOTICE_FILE = "NOTICE_shortcut.md"


def _stage_dir(config: dict) -> Path:
    return resolve(config["paths"]["artifacts_dir"]) / STAGE


def _posix(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def inputs(config: dict) -> dict[str, str]:
    """Content hashes of everything the manifests depend on (seed via config.split).

    The exclusion list is hashed as its PARSED rows, not its bytes: a
    missing file and the header-only template run() creates both hash to
    [], so creating the template never invalidates the cache.
    """
    paths = config["paths"]
    d = {
        "catalog": sha256_path(resolve(paths["catalog"])),
        "metadata": sha256_path(resolve(paths["metadata"])),
        "unified_images": sha256_path(resolve(paths["unified_dir"])),
        "gemstone_ids": sha256_obj(read_exclusions(resolve(paths["gemstone_ids"]))),
        "code": sha256_path(resolve("src/stage1_freeze")),
        "common": sha256_path(resolve("src/common")),
    }
    for key in CONFIG_SUBTREES:
        d[f"config.{key}"] = config_subtree_hash(config, key)
    return d


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> Path:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(columns), lineterminator="\n")
        w.writeheader()
        w.writerows({c: r[c] for c in columns} for r in rows)
    return path


def _write_json(path: Path, obj: dict) -> Path:
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def _load_images(rows: list[dict], unified_dir: Path) -> np.ndarray:
    """uint8 (N, S, S) for the given rows, via their catalog paths."""
    return np.stack([read_png(unified_dir / r["path"]) for r in rows])


def _fd_report(results: dict) -> dict:
    out = {}
    for name, (n_groups, violations) in results.items():
        out[name] = {
            "n_groups": n_groups,
            "n_violations": len(violations),
            "holds": not violations,
            "examples": [f"{k} -> {sorted(v)}" for k, v in list(violations.items())[:FD_EXAMPLE_LIMIT]],
        }
    return out


def _stage6_note(counts: dict, removed: int, filter_state: str, n_groups: int,
                 largest: int, mixed: int, seed: int, shares: dict, ratios: list) -> str:
    total = sum(counts.values())
    lines = [
        "# Stage 1 -> Stage 6: new split counts",
        "",
        "Use these in the report's **Split** paragraph (phase1_report.tex:466-467);",
        "`tab:stats` holds per-source file counts and is unaffected.",
        "",
        "| Split | Phase 1 | Stage 1 | Change |",
        "|---|---:|---:|---:|",
    ]
    for s in SPLIT_NAMES:
        lines.append(f"| {s} | {PHASE1_COUNTS[s]:,} | {counts[s]:,} | {counts[s] - PHASE1_COUNTS[s]:+,} |")
    p1_total = sum(PHASE1_COUNTS.values())
    lines += [
        f"| total | {p1_total:,} | {total:,} | {total - p1_total:+,} |",
        "",
        "## Why the numbers moved",
        "",
        f"1. Gemstone filter (Decision 1): {filter_state}; {removed} image(s) removed.",
        f"2. pHash near-duplicate groups are now formed over ALL sources (Decision 15): "
        f"{n_groups:,} groups, largest {largest} images, {mixed} group(s) carry more than one label.",
        f"3. Groups are assigned whole, stratified by (class, source), targets "
        f"{'/'.join(str(r) for r in ratios)}, seed {seed}. A large group lands in one split, "
        "so single-source classes can sit off the target ratios.",
        "",
        "## Each source's share of the test split",
        "",
    ]
    lines += [f"- {src}: {share:.3f}" for src, share in shares.items()]
    lines += ["", "Macros: `artifacts/stage1/report_counts.tex` (\\SplitTrain, \\SplitVal, ...)."]
    return "\n".join(lines) + "\n"


def _notice_text(result: dict) -> str:
    return (
        "# NOTICE: source shortcut detected (Decision 12, stage_1.md R14)\n\n"
        f"A source classifier on standardized pixels reached pooled accuracy "
        f"{result['pooled_accuracy']:.3f} against a majority-source rate of "
        f"{result['pooled_majority_rate']:.3f} (gain {result['gain_points']:.1f} points > "
        f"trigger {result['trigger_points']:.0f}).\n\n"
        "Consequences for Stages 4-6 (now REQUIRED, not optional):\n"
        "- Stage 5: per-source accuracy tables for every arm.\n"
        "- Stage 4/5: leave-one-source-out runs for A1 and B without the Hand-Drawn "
        "source (`github_handdrawn`), tested on Hand-Drawn only.\n"
        "- Stage 6: pentagon and ellipse results keep their single-source asterisk.\n\n"
        f"Classes that come from one source only: {', '.join(result['skipped_classes']) or 'none'}. "
        "A leave-one-source-out run that holds out such a source has no real images of that "
        "class, so it must train and score without it (P-61).\n\n"
        "Details: artifacts/stage1/source_classifier.json\n"
    )


def exclusions_tex(excluded: dict[str, int]) -> str:
    """LaTeX macro with the number of images excluded by rule (report input)."""
    total = sum(excluded.values())
    return ("% Generated by src/stage1_freeze/run.py - do not edit.\n"
            "\\providecommand{\\ExcludedByRule}{" + f"{total:,}".replace(",", "{,}") + "}\n")


def plan_freeze(config: dict, rows: list[dict]) -> tuple[dict[str, bool], dict]:
    """Every check and statistic that needs only the split-assigned `rows`.

    Runs BEFORE anything touches configs/splits (R9): the leakage checks,
    the Decision 10 noise bands (raises if a class has no test rows), the
    FD check on the filtered frame and the source-shortcut check on
    train/val pixels. Nothing here writes a file.

    Returns (checks, artefacts) with
      checks:    {"no_id_in_two_splits", "no_md5_in_two_splits",
                  "no_phash_group_spans", "fd_all_hold"} -> bool
      artefacts: {"split_stats", "noise_bands", "fd_check",
                  "source_classifier", "source_test_share"}
    """
    names = class_names(config)
    unified_dir = resolve(config["paths"]["unified_dir"])
    seed = int(config["split"]["seed"])

    checks: dict[str, bool] = dict(leakage_checks(rows))
    artefacts: dict = {}
    artefacts["split_stats"] = split_stats(rows, names)
    artefacts["noise_bands"] = noise_bands(
        rows, names, config["evaluation"]["noise_band_accuracy"],
        config["success_criterion"]["max_class_f1_drop_points"])

    metadata_rows = read_metadata(resolve(config["paths"]["metadata"]))
    fd = _fd_report(check_rows(fd_rows(rows, metadata_rows, {r["image_id"]: r["split"] for r in rows})))
    checks["fd_all_hold"] = all(v["holds"] for v in fd.values())
    artefacts["fd_check"] = fd

    train = [r for r in rows if r["split"] == "train"]
    val = [r for r in rows if r["split"] == "val"]
    artefacts["source_classifier"] = shortcut_check(
        _load_images(train, unified_dir), [r["label_id"] for r in train], [r["source_id"] for r in train],
        _load_images(val, unified_dir), [r["label_id"] for r in val], [r["source_id"] for r in val],
        trigger_points=config["evaluation"]["shortcut_trigger_points"], rng_seed=seed,
        class_names=names)
    artefacts["source_test_share"] = source_test_share(rows)
    return checks, artefacts


def _write_artefacts(out_dir: Path, artefacts: dict) -> list[Path]:
    """Write the plan_freeze artefacts under artifacts/stage1 (never the manifests)."""
    outputs = [
        _write_csv(out_dir / "split_stats.csv", SPLIT_STATS_COLUMNS, artefacts["split_stats"]),
        _write_csv(out_dir / "noise_bands.csv", NOISE_BAND_COLUMNS, artefacts["noise_bands"]),
        _write_json(out_dir / "fd_check.json", artefacts["fd_check"]),
        _write_json(out_dir / "source_classifier.json", artefacts["source_classifier"]),
    ]
    source = artefacts["source_classifier"]
    notice = out_dir / NOTICE_FILE
    if source["shortcut_detected"]:
        notice.write_text(_notice_text(source), encoding="utf-8")
        outputs.append(notice)
    elif notice.exists():
        notice.unlink()  # a stale notice from an earlier run must not survive
    return outputs


def run(config: dict) -> dict:
    """Freeze the data: md5 pass, gemstone filter, global groups, split, checks, stats.

    Order matters (R9, fail-closed): every check runs in plan_freeze()
    first; freeze() is the LAST step and the only one that touches
    configs/splits. A failed check (leakage or FD) returns status failed
    and writes no manifest. Does not write status.json; the runner does.
    """
    out_dir = _stage_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    unified_dir = resolve(config["paths"]["unified_dir"])
    splits_dir = resolve(config["paths"]["splits_dir"])
    gemstone_path = resolve(config["paths"]["gemstone_ids"])
    names = class_names(config)
    split_cfg = config["split"]
    seed = int(split_cfg["seed"])
    ratios = list(split_cfg["ratios"])
    outputs: list[Path] = []

    rows = load_unified(config)

    outputs += write_contact_sheets(rows, unified_dir, out_dir,
                                    label_id=names.index(REVIEW_CLASS_NAME))
    write_template(gemstone_path)

    # CRISP-DM iteration 1 (Decision 1 amendment): rule-based exclusions
    # before the split; the contact sheets above still show what was dropped.
    rows, excluded = apply_source_label_exclusions(rows, config["exclude_source_labels"], names)
    (out_dir / "exclusions.tex").write_text(exclusions_tex(excluded), encoding="utf-8")
    outputs.append(out_dir / "exclusions.tex")

    if config["filter_gemstones"]:
        exclusions = read_exclusions(gemstone_path)
        if not exclusions:
            raise ValueError("gemstone review not done: filter_gemstones is true but "
                             f"{_posix(gemstone_path)} lists no md5")
        rows, removed = apply_gemstone_filter(rows, exclusions)
        filter_state, filter_metric = FILTER_APPLIED, "applied"
    elif QUICKDRAW_DIAMONDS in excluded:
        removed, filter_state, filter_metric = 0, FILTER_SUPERSEDED, "superseded_by_rule"
    else:
        removed, filter_state, filter_metric = 0, FILTER_PENDING, "dry_run"

    members = global_groups([r["phash"] for r in rows], int(split_cfg["phash_hamming_max"]))
    for r, gid in zip(rows, group_labels(members)):
        r["phash_group"] = gid
    for r, split in zip(rows, group_split(rows, ratios, seed)):
        r["split"] = split

    sizes = group_sizes(rows)
    n_groups, largest = len(sizes), max(sizes.values(), default=0)
    mixed = mixed_label_groups(rows)
    counts = Counter(r["split"] for r in rows)
    count_metrics = {s: int(counts.get(s, 0)) for s in SPLIT_NAMES}

    # All checks and statistics first; nothing below has touched configs/splits yet.
    checks, artefacts = plan_freeze(config, rows)
    outputs += _write_artefacts(out_dir, artefacts)
    source = artefacts["source_classifier"]
    shares = artefacts["source_test_share"]

    if not all(checks.values()):
        return {"status": "failed", "outputs": [_posix(p) for p in outputs],
                "metrics": {**count_metrics, "total": len(rows), "gemstones_removed": removed,
                            "gemstone_filter": filter_metric, "seed": seed},
                "checks": checks}

    # Last step: the only one that writes configs/splits (R9).
    frozen = freeze(rows, splits_dir)
    checks.update(frozen["checks"])
    if frozen["status"] != "passed":
        return {"status": "failed", "outputs": [_posix(p) for p in outputs],
                "metrics": {**count_metrics, "total": len(rows), "gemstones_removed": removed,
                            "gemstone_filter": filter_metric, "seed": seed},
                "checks": checks}
    outputs += frozen["outputs"]

    outputs.append(write_report_counts(out_dir / "report_counts.tex", count_metrics, removed,
                                       filter_state, n_groups, largest))
    note = out_dir / "stage6_note.md"
    note.write_text(_stage6_note(count_metrics, removed, filter_state, n_groups, largest, mixed,
                                 seed, shares, ratios), encoding="utf-8")
    outputs.append(note)

    return {
        "status": "passed",
        "outputs": [_posix(p) for p in outputs],
        "metrics": {
            **count_metrics,
            "total": len(rows),
            "gemstones_removed": removed,
            "gemstone_filter": filter_metric,
            "excluded_by_rule": excluded,
            "near_dup_groups": n_groups,
            "largest_group": largest,
            "mixed_label_groups": mixed,
            "shortcut_detected": source["shortcut_detected"],
            "source_test_share": shares,
            "seed": seed,
        },
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
