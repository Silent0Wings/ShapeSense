"""Stage 4 run records, for the run names Stage 4 itself reports."""

from __future__ import annotations

import csv
import json

from studio.allowlist import stage4_run_path
from studio.data.tables import read_json


def run_names() -> list[str]:
    status = read_json("status4")
    if status is None:
        return []
    return [r["name"] for r in status["metrics"]["runs"]]


def record(run: str) -> dict | None:
    """run.json plus its per-epoch log. None for anything not in the run list."""
    if run not in run_names():
        return None
    info = json.loads(stage4_run_path(run, "run.json").read_text(encoding="utf-8"))
    with open(stage4_run_path(run, "train_log.csv"), newline="", encoding="utf-8") as f:
        log = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    return {"info": info, "log": log}


def summary() -> list[dict]:
    """One row per run, from Stage 4's status file."""
    status = read_json("status4")
    return [] if status is None else status["metrics"]["runs"]
