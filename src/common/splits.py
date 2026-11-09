"""The only way to read a split: `load_split(name)`.

configs/splits/{train,val,test}.csv are the frozen manifests written by
Stage 1 (Decision 16). For name == "test" this raises unless the calling
module lives in src.stage5_eval, and every test read appends one line to
the append-only access log (never truncated):

    iso_timestamp, run_id, caller_module, split, n_rows

Checks count only lines carrying the current run_id, so reruns never
poison the log (implementation.md § Separation of concerns 2).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from src.common.status import current_run_id, now_iso

SPLITS = ("train", "val", "test")
FRESH_SPLIT = "fresh_holdout"   # iteration 2 holdout, written by src/stage1_freeze/fresh_holdout.py
FRESH2_SPLIT = "fresh_holdout_2"  # iteration 3 holdout, written by src/stage1_freeze/fresh_holdout_2.py
TEST_SPLIT = "test"
SEALED_SPLITS = (TEST_SPLIT, FRESH_SPLIT, FRESH2_SPLIT)  # only Stage 5 reads these, and every read is logged
ALLOWED_TEST_READER = "src.stage5_eval"
DEFAULT_SPLITS_DIR = Path("configs/splits")
DEFAULT_LOG = Path("artifacts/test_access.log")
MANIFEST_COLUMNS = ["image_id", "md5", "label_id", "source_id", "phash_group", "split"]


class TestSplitAccessError(PermissionError):
    """Raised when anything outside src.stage5_eval asks for the test split."""

    __test__ = False  # not a pytest test class


def _caller() -> tuple[str, str | None]:
    """(module name, module file) of the first frame outside src.common."""
    frame = sys._getframe(1)
    while frame is not None:
        name = frame.f_globals.get("__name__", "")
        if not name.startswith("src.common"):
            return name, frame.f_globals.get("__file__")
        frame = frame.f_back
    return "<unknown>", None


STAGE5_DIR = Path(__file__).resolve().parents[1] / "stage5_eval"


def _allowed_test_reader(module: str, module_file: str | None = None) -> bool:
    if module == ALLOWED_TEST_READER or module.startswith(ALLOWED_TEST_READER + "."):
        return True
    # `python -m src.stage5_eval.run` runs as __main__: accept it by file location.
    if module == "__main__" and module_file:
        try:
            Path(module_file).resolve().relative_to(STAGE5_DIR)
            return True
        except ValueError:
            return False
    return False


def load_split(name: str, *, splits_dir: str | Path | None = None,
               log_path: str | Path | None = None) -> list[dict]:
    """Return the manifest rows of one split as dicts (columns as strings)."""
    if name not in SPLITS + (FRESH_SPLIT, FRESH2_SPLIT):
        raise ValueError(f"unknown split {name!r}; expected one of {SPLITS + (FRESH_SPLIT, FRESH2_SPLIT)}")
    caller, caller_file = _caller()
    if name in SEALED_SPLITS and not _allowed_test_reader(caller, caller_file):
        raise TestSplitAccessError(
            f"{caller} may not read the test split; only {ALLOWED_TEST_READER} may "
            "(implementation.md § Separation of concerns 2)")
    path = Path(splits_dir or DEFAULT_SPLITS_DIR) / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found; run Stage 1 "
                                "(python run_pipeline.py --stages 1) to write the manifests")
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if name in SEALED_SPLITS:
        log = Path(log_path or DEFAULT_LOG)
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8", newline="") as f:
            f.write(f"{now_iso()},{current_run_id()},{caller},{name},{len(rows)}\n")
    return rows


def reads_outside(run_id: str, reader: str, *, log_path: str | Path | None = None) -> int:
    """Sealed reads logged under run_id by anything other than ``reader``."""
    log = Path(log_path or DEFAULT_LOG)
    if not log.is_file():
        return 0
    with open(log, encoding="utf-8") as f:
        fields = [line.rstrip("\n").split(",") for line in f]
    return sum(1 for parts in fields if len(parts) >= 5 and parts[1] == run_id and parts[2] != reader)


def count_test_reads(run_id: str, *, log_path: str | Path | None = None) -> int:
    """Number of test-split reads logged under run_id."""
    log = Path(log_path or DEFAULT_LOG)
    if not log.is_file():
        return 0
    n = 0
    with open(log, encoding="utf-8") as f:
        for line in f:
            # timestamps contain no commas; run ids never do either
            parts = line.rstrip("\n").split(",")
            if len(parts) >= 5 and parts[1] == run_id:
                n += 1
    return n
