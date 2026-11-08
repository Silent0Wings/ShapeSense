"""Read-only Streamlit dashboard for the ShapeSense pipeline (Stage 6, R9-R11).

Reads artifacts/ and configs/pipeline.yaml only. It never computes results,
never trains and never reads configs/splits/ (the test split).

Start from the repo root so that both `dashboard` and `src` are importable:
    python -m streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from dashboard.view_model import (
    GREEN,
    GREY,
    RED,
    STAGES,
    TAB_NAMES,
    VERDICT_STAGE,
    glob_files,
    leaked_test_reads,
    load_statuses,
    overview_rows,
    stage5_test_reads,
    stage_files,
    status_notes,
    verdict_of,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "pipeline.yaml"
LIGHT_EMOJI = {GREEN: "🟢", RED: "🔴", GREY: "⚪"}


def _load_paths() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg["paths"]


def _show_file(name: str, path: Path | None) -> None:
    if path is None:
        st.info(f"{name}: not run yet")
        return
    try:
        if path.suffix == ".json":
            with open(path, encoding="utf-8") as f:
                st.json(json.load(f))
        elif path.suffix == ".csv":
            st.dataframe(pd.read_csv(path, encoding="utf-8"))
        elif path.suffix == ".png":
            st.image(str(path), caption=name)
        elif path.suffix == ".md":
            st.markdown(path.read_text(encoding="utf-8"))
        elif path.suffix == ".pdf":
            st.download_button(f"Download {name}", data=path.read_bytes(),
                               file_name=name, mime="application/pdf")
    except (OSError, ValueError) as exc:
        st.warning(f"{name} could not be read: {exc}")


def _show_many(paths: list[Path], empty_message: str) -> None:
    if not paths:
        st.info(empty_message)
    for path in paths:
        _show_file(path.name, path)


def _test_access_block(info: dict, log_path: Path, *, expect_zero: bool) -> None:
    """Stage 4 (expect_zero): reads by anything but Stage 5 are a leak.
    Stage 5: show its own, legitimate reads (one per evaluated model)."""
    run_id = info.get("run_id") or ""
    try:
        if expect_zero:
            reads = leaked_test_reads(log_path, run_id)
        else:
            reads = stage5_test_reads(log_path, run_id)
    except OSError as exc:
        st.warning(f"test_access.log unreadable: {exc}")
        return
    if not expect_zero:
        st.metric("Test-split reads by Stage 5 in this run", reads)
        return
    st.metric("Test-split reads outside Stage 5 in this run", reads)
    if reads == 0:
        st.success("No test-split reads outside Stage 5 in this run.")
    else:
        st.error("The test split was read outside Stage 5 in this run.")


def _render_overview(statuses: dict, notes: dict) -> None:
    rows = overview_rows(statuses)
    st.table([
        {
            "light": LIGHT_EMOJI[row["light"]],
            "stage": row["stage"],
            "owner": row["owner"] or "-",
            "status": row["status"],
            "last run": row["finished_at"] or "-",
            "verdict": row["verdict"] or "-",
        }
        for row in rows
    ])
    st.caption("A 'fail' verdict is shown separately; the light tracks whether the stage ran.")
    for stage, note in notes.items():
        st.warning(f"{stage}: {note}")
    for row in rows:
        with st.expander(f"{row['stage']} input hashes"):
            if row["inputs"]:
                st.json(row["inputs"])
            else:
                st.write("no inputs recorded")


def _render_stage(stage: str, statuses: dict, notes: dict,
                  artifacts_dir: Path, log_path: Path) -> None:
    info = statuses.get(stage)
    if stage in notes:
        st.warning(notes[stage])
    if info is None:
        st.info(f"{stage}: not run yet")
    else:
        st.json(info)

    for name, path in stage_files(artifacts_dir, stage).items():
        _show_file(name, path)

    if stage == "stage4":
        _show_many(glob_files(artifacts_dir, stage, "*/val_curve.png"),
                   "no validation curves yet")
        if info is None:
            st.info("stage4: test-access count not available (not run yet)")
        else:
            _test_access_block(info, log_path, expect_zero=True)

    if stage == VERDICT_STAGE:
        _show_many(glob_files(artifacts_dir, stage, "tables/*.csv"),
                   "no result tables yet")
        _show_many(glob_files(artifacts_dir, stage, "figures/*.png"),
                   "no figures yet")
        if info is None:
            st.info("stage5: no verdict yet (not run)")
        else:
            st.metric("Verdict", verdict_of(info) or "-")
            st.caption("Separate from the status light: a 'fail' verdict on a "
                       "passed stage is still a green light.")
            _test_access_block(info, log_path, expect_zero=False)


def main() -> None:
    st.set_page_config(page_title="ShapeSense pipeline")
    paths = _load_paths()
    artifacts_dir = REPO_ROOT / paths["artifacts_dir"]
    log_path = REPO_ROOT / paths["test_access_log"]

    statuses = load_statuses(artifacts_dir)
    notes = status_notes(artifacts_dir)

    overview_tab, *stage_tabs = st.tabs(TAB_NAMES)
    with overview_tab:
        _render_overview(statuses, notes)
    for stage, tab in zip(STAGES, stage_tabs):
        with tab:
            _render_stage(stage, statuses, notes, artifacts_dir, log_path)


main()
