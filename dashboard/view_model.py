"""Pure view-model for the read-only dashboard (Stage 6, R9-R11).

No Streamlit import. Artifacts are read through `src.common.status` only,
the one src module `dashboard/` may import. This module never reads
configs/splits/ (the test split) and never computes results.
"""

from __future__ import annotations

from pathlib import Path

from src.common.status import read_status

REPO_ROOT = Path(__file__).resolve().parents[1]

STAGES = [f"stage{i}" for i in range(7)]
TAB_NAMES = ["Overview", "0 Infra", "1 Data", "2 Augment", "3 Synthetic",
             "4 Training", "5 Evaluation", "6 Report"]

GREY = "grey"
GREEN = "green"
RED = "red"
STATUS_NOT_RUN = "not_run"
VERDICT_STAGE = "stage5"
ACCESS_LOG_FIELDS = 5  # iso_timestamp, run_id, caller_module, split, n_rows
LOG_RUN_ID_FIELD = 1  # index of run_id in an access-log line
LOG_CALLER_FIELD = 2  # index of caller_module in an access-log line
STAGE5_MODULE_PREFIX = "src.stage5_eval"  # the only package allowed to read the test split
REPORT_PDF = "phase2_report.pdf"

# Fixed artifact names per stage, relative to artifacts/<stage>/.
_STAGE_FILES: dict[str, tuple[str, ...]] = {
    "stage0": ("migration_check.json",),
    "stage1": ("split_stats.csv", "noise_bands.csv", "source_classifier.json",
               "stage6_note.md"),
    "stage2": ("qa/qa_sheet.png",),
    "stage3": ("qa/qa_sheet.png", "param_ranges.json"),
    "stage4": ("loader_benchmark.json", "baselines/baselines.json",
               "tuning.json", "seed_disagreement.json"),
    "stage5": ("power_check.json",),
    "stage6": (),
}


def light(status: dict | None) -> str:
    """Map one stage's status dict to a light: grey, green or red."""
    if status is None:
        return GREY
    value = status.get("status")
    if value == "passed":
        return GREEN
    if value == "failed":
        return RED
    return GREY


def verdict_of(info: dict | None) -> str | None:
    """Stage 5's verdict from metrics.verdict; None when absent."""
    if info is None:
        return None
    metrics = info.get("metrics")
    if not isinstance(metrics, dict):
        return None
    value = metrics.get("verdict")
    return None if value is None else str(value)


def overview_rows(statuses: dict[str, dict | None]) -> list[dict]:
    """One row per stage. A missing or unreadable status shows as not_run."""
    rows = []
    for stage in STAGES:
        info = statuses.get(stage)
        if info is None:
            status_value = STATUS_NOT_RUN
            owner = ""
            finished_at = None
            inputs: dict = {}
            run_id = None
        else:
            status_value = info.get("status", STATUS_NOT_RUN)
            owner = info.get("owner", "")
            finished_at = info.get("finished_at")
            raw_inputs = info.get("inputs")
            inputs = raw_inputs if isinstance(raw_inputs, dict) else {}
            run_id = info.get("run_id")
        rows.append({
            "stage": stage,
            "light": light(info),
            "status": status_value,
            "owner": owner,
            "finished_at": finished_at,
            "run_id": run_id,
            "inputs": inputs,
            "verdict": verdict_of(info) if stage == VERDICT_STAGE else None,
        })
    return rows


def _read_one(artifacts_dir: Path, stage: str) -> tuple[dict | None, str | None]:
    """Return (status, note). A corrupt file gives (None, note), never an exception."""
    try:
        data = read_status(stage, artifacts_dir)
    except (OSError, ValueError) as exc:
        return None, f"status.json unreadable: {exc}"
    if data is None:
        return None, None
    if not isinstance(data, dict):
        return None, "status.json is not a JSON object"
    return data, None


def load_statuses(artifacts_dir: Path) -> dict[str, dict | None]:
    """Status dict per stage; None for missing or unreadable files."""
    return {stage: _read_one(Path(artifacts_dir), stage)[0] for stage in STAGES}


def status_notes(artifacts_dir: Path) -> dict[str, str]:
    """Error notes for stages whose status.json exists but cannot be read."""
    notes = {}
    for stage in STAGES:
        _, note = _read_one(Path(artifacts_dir), stage)
        if note:
            notes[stage] = note
    return notes


def _existing(path: Path) -> Path | None:
    return path if path.is_file() else None


def stage_files(artifacts_dir: Path, stage: str,
                repo_root: Path = REPO_ROOT) -> dict[str, Path | None]:
    """Known artifacts of one stage; None where the file is missing."""
    base = Path(artifacts_dir) / stage
    files: dict[str, Path | None] = {
        name: _existing(base / name) for name in _STAGE_FILES.get(stage, ())
    }
    if stage == "stage6":
        files[REPORT_PDF] = _existing(Path(repo_root) / REPORT_PDF)
    return files


def glob_files(artifacts_dir: Path, stage: str, pattern: str) -> list[Path]:
    """Sorted files matching pattern under artifacts/<stage>/; empty if none."""
    root = Path(artifacts_dir) / stage
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob(pattern) if p.is_file())


def test_reads_for_run(log_path: Path, run_id: str, *,
                       caller_prefix: str | None = None,
                       exclude_caller_prefix: str | None = None) -> int:
    """Count access-log lines that carry run_id. Missing log means 0 reads.

    Line format: iso_timestamp,run_id,caller_module,split,n_rows. Malformed
    lines are skipped. Parsed here rather than via src.common.splits, which
    dashboard/ may not import. ``caller_prefix`` keeps only lines whose
    caller_module starts with it; ``exclude_caller_prefix`` drops those.
    """
    path = Path(log_path)
    if not path.is_file():
        return 0
    count = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            fields = line.rstrip("\r\n").split(",")
            if len(fields) != ACCESS_LOG_FIELDS or fields[LOG_RUN_ID_FIELD] != run_id:
                continue
            caller = fields[LOG_CALLER_FIELD]
            if caller_prefix is not None and not caller.startswith(caller_prefix):
                continue
            if exclude_caller_prefix is not None and caller.startswith(exclude_caller_prefix):
                continue
            count += 1
    return count


def leaked_test_reads(log_path: Path, run_id: str) -> int:
    """Test-split reads in this run by anything OTHER than src.stage5_eval.

    Stage 5's reads are legitimate (one per evaluated model) and share the
    run_id with every other stage of the same invocation, so the Stage 4 leak
    check must not count them.
    """
    return test_reads_for_run(log_path, run_id, exclude_caller_prefix=STAGE5_MODULE_PREFIX)


def stage5_test_reads(log_path: Path, run_id: str) -> int:
    """Test-split reads in this run performed by src.stage5_eval."""
    return test_reads_for_run(log_path, run_id, caller_prefix=STAGE5_MODULE_PREFIX)
