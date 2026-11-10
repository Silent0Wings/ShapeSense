"""The exact files the studio may read. Nothing else is reachable by name.

Requests carry a short key, never a path. A key outside these tables is a 404,
so no request can reach the test manifest, the image folders, or the Stage 0
rebuild copy.
"""

from __future__ import annotations

from pathlib import Path

from src.common.config import REPO_ROOT

_A = "artifacts"


def _status(n: int) -> str:
    return f"{_A}/stage{n}/status.json"


DOCS: dict[str, str] = {
    **{f"status{n}": _status(n) for n in range(7)},
    "guards": f"{_A}/stage0/guards.json",
    "migration": f"{_A}/stage0/migration_check.json",
    "archive_hash": f"{_A}/stage0/data_archive_sha256.txt",
    "split_stats": f"{_A}/stage1/split_stats.csv",
    "noise_bands": f"{_A}/stage1/noise_bands.csv",
    "source_classifier": f"{_A}/stage1/source_classifier.json",
    "fd_check": f"{_A}/stage1/fd_check.json",
    "shortcut_notice": f"{_A}/stage1/NOTICE_shortcut.md",
    "iteration1": "docs/crisp_dm/iteration_1_quickdraw_diamonds.json",
    "iteration_log": "docs/crisp_dm/iteration_log.json",
    "robustness": "docs/crisp_dm/iteration_2/robustness/results.json",
    "winners": f"{_A}/stage4/tuning_iter3/winners.json",
    "robust_sealed": f"{_A}/stage5/robust_results.json",
    "fresh_metrics": f"{_A}/stage5/tables/fresh_metrics.csv",
    "fresh_per_class": f"{_A}/stage5/tables/fresh_per_class.csv",
    **{f"exp_{n}": f"docs/crisp_dm/iteration_3/experiments/{n}.json" for n in ("scarcity", "equal_real", "budget", "batchnorm", "preprocess", "one_transform_on", "val_vs_test")},
    "iter2_status": "docs/crisp_dm/iteration_2/data/stage5_status.json",
    "iter2_per_class": "docs/crisp_dm/iteration_2/data/per_class.csv",
    "iter2_comparisons": "docs/crisp_dm/iteration_2/data/comparisons.csv",
    "iter2_fresh_per_class": "docs/crisp_dm/iteration_2/data/fresh_per_class.csv",
    "iter1_status": "docs/crisp_dm/iteration_1/data/stage5_status.json",
    "iter1_metrics": "docs/crisp_dm/iteration_1/data/metrics.csv",
    "iter1_per_class": "docs/crisp_dm/iteration_1/data/per_class.csv",
    "iter1_comparisons": "docs/crisp_dm/iteration_1/data/comparisons.csv",
    "param_ranges": f"{_A}/stage3/param_ranges.json",
    "qa_review2": f"{_A}/stage2/qa/qa_review.md",
    "qa_review3": f"{_A}/stage3/qa/qa_review.md",
    "tuning": f"{_A}/stage4/tuning.json",
    "seed_disagreement": f"{_A}/stage4/seed_disagreement.json",
    "baselines": f"{_A}/stage4/baselines/baselines.json",
    "loader_benchmark": f"{_A}/stage4/loader_benchmark.json",
    "metrics": f"{_A}/stage5/tables/metrics.csv",
    "per_class": f"{_A}/stage5/tables/per_class.csv",
    "comparisons": f"{_A}/stage5/tables/comparisons.csv",
    "per_source": f"{_A}/stage5/tables/per_source.csv",
    "power": f"{_A}/stage5/power_check.json",
    "model_card": "export/model_card.json",
    "labels": "export/labels.json",
    "access_log": f"{_A}/test_access.log",
}

IMAGES: dict[str, str] = {
    **{f"contact{n}": f"{_A}/stage1/gemstone_contact_sheet_{n}.png" for n in range(5)},
    "robustness_examples": "docs/crisp_dm/iteration_2/robustness/examples.png",
    "inv_square_sources": "docs/crisp_dm/iteration_2/investigation/sheet_train_square_by_source.png",
    "qa2": f"{_A}/stage2/qa/qa_sheet.png",
    "qa3": f"{_A}/stage3/qa/qa_sheet.png",
    "smoke_hexagon": f"{_A}/stage6/smoke_hexagon.png",
    **{f"confusion_{arm}": f"{_A}/stage5/figures/confusion_{arm}.png" for arm in ("A0", "A1", "B", "A2", "P")},
    **{f"iter2_confusion_{arm}": f"docs/crisp_dm/iteration_2/figures/confusion_{arm}.png" for arm in ("A0", "A1", "B", "A2")},
    **{f"iter1_confusion_{arm}": f"docs/crisp_dm/iteration_1/figures/confusion_{arm}.png" for arm in ("A0", "A1", "B")},
}

FILES: dict[str, tuple[str, str]] = {
    "report": ("phase2_report.pdf", "application/pdf"),
    "report_phase1": ("phase1_report.pdf", "application/pdf"),
}

# The only prediction files that may be opened; each has one reader in studio.data.
PREDICTION_FILES: dict[str, str] = {
    **{arm: f"{_A}/stage5/predictions/ensemble_{arm}.npz" for arm in ("A0", "A1", "B", "A2", "P")},
    "errors": f"{_A}/stage5/predictions/ensemble_A2_errors.npz",
}


def doc_path(key: str) -> Path:
    """Absolute path of an allow-listed document. Raises KeyError for anything else."""
    return REPO_ROOT / DOCS[key]


def image_path(key: str) -> Path:
    return REPO_ROOT / IMAGES[key]


def prediction_path(key: str) -> Path:
    return REPO_ROOT / PREDICTION_FILES[key]


def stage4_run_path(run: str, name: str) -> Path:
    """A file of one Stage 4 run. Callers check ``run`` against the run list first."""
    if name not in ("run.json", "train_log.csv"):
        raise KeyError(name)
    return REPO_ROOT / _A / "stage4" / run / name
