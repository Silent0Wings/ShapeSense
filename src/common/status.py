"""artifacts/stageN/status.json: schema, fail-closed writer, run_id, cache.

Every stage writes its status through `run_stage`, never by hand
(implementation.md § Shared conventions). `status` says whether the stage
*worked*; results such as Stage 5's verdict live in `metrics`.

- one `run_id` per run_pipeline.py invocation, shared by every stage
  (env SHAPESENSE_RUN_ID, minted by the runner);
- a stage that raises is recorded as `failed` and the exception is
  re-raised, so a stale `passed` can never survive a broken rerun;
- a stub raising NotImplementedError is recorded as `not_run`, never
  `passed`;
- `is_cached` is true only for a `passed` status whose recorded inputs
  equal the current ones exactly.
"""

from __future__ import annotations

import json
import os
import secrets
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.common.config import resolve
from src.common.hashing import sha256_path

RUN_ID_ENV = "SHAPESENSE_RUN_ID"
STATUS_VALUES = ("not_run", "passed", "failed")
DEFAULT_ARTIFACTS = Path("artifacts")
REQUIRED_FIELDS = {
    "stage": str, "owner": str, "run_id": str, "status": str,
    "started_at": str, "finished_at": str, "inputs": dict,
    "outputs": list, "metrics": dict, "checks": dict,
}
RESULT_KEYS = {"status", "outputs", "metrics", "checks", "error"}
# Keys the writer owns; a stage result may not override them.
RESERVED_KEYS = {"stage", "owner", "run_id", "inputs", "started_at", "finished_at",
                 "artifacts_dir", "output_hashes", "traceback"}


class StatusSchemaError(ValueError):
    """Raised when a status dict does not match the shared schema."""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_run_id() -> str:
    return f"{now_iso()}/{secrets.token_hex(3)}"


def current_run_id() -> str:
    """The run id of this invocation; minted once if the runner did not set one."""
    rid = os.environ.get(RUN_ID_ENV)
    if not rid:
        rid = "adhoc-" + new_run_id()
        os.environ[RUN_ID_ENV] = rid
    return rid


def validate_status(d: dict) -> None:
    for key, typ in REQUIRED_FIELDS.items():
        if key not in d:
            raise StatusSchemaError(f"status.json missing field {key!r}")
        if not isinstance(d[key], typ):
            raise StatusSchemaError(f"status.json field {key!r} must be {typ.__name__}")
    if d["status"] not in STATUS_VALUES:
        raise StatusSchemaError(f"status must be one of {STATUS_VALUES}, got {d['status']!r}")


def status_path(stage: str, artifacts_dir: str | Path = DEFAULT_ARTIFACTS) -> Path:
    return Path(artifacts_dir) / stage / "status.json"


def read_status(stage: str, artifacts_dir: str | Path = DEFAULT_ARTIFACTS) -> dict | None:
    p = status_path(stage, artifacts_dir)
    if not p.is_file():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_status(stage: str, *, artifacts_dir: str | Path = DEFAULT_ARTIFACTS,
                 **fields: Any) -> dict:
    """Validate and atomically write status.json (tmp file + replace)."""
    d = {"stage": stage, "owner": "", "run_id": current_run_id(), "inputs": {},
         "outputs": [], "metrics": {}, "checks": {}}
    d.update(fields)
    validate_status(d)
    p = status_path(stage, artifacts_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, sort_keys=False, default=str)
        f.write("\n")
    os.replace(tmp, p)
    return d


def output_hashes(outputs: list) -> dict[str, str]:
    """Content hash of every recorded output (repo-relative or absolute paths)."""
    return {str(o): sha256_path(resolve(o)) for o in outputs}


def is_cached(stage: str, inputs: dict, artifacts_dir: str | Path = DEFAULT_ARTIFACTS) -> bool:
    """True only for a `passed` status whose inputs are unchanged AND whose
    recorded outputs still exist with the same content (a hand-edited or
    deleted manifest is never served from the cache)."""
    prev = read_status(stage, artifacts_dir)
    if not prev or prev.get("status") != "passed" or prev.get("inputs") != inputs:
        return False
    recorded = prev.get("output_hashes")
    if recorded is None:
        return False
    return all(h != "missing" and sha256_path(resolve(o)) == h for o, h in recorded.items())


def run_stage(stage: str, fn: Callable[[], dict | None], *, inputs: dict,
              artifacts_dir: str | Path = DEFAULT_ARTIFACTS, owner: str = "") -> dict:
    """Run fn and always leave a valid status.json behind (Mission M2)."""
    started = now_iso()
    base = dict(artifacts_dir=artifacts_dir, owner=owner, inputs=inputs,
                started_at=started)
    try:
        result = fn() or {}
    except NotImplementedError as exc:
        return write_status(stage, status="not_run", finished_at=now_iso(),
                            metrics={}, checks={}, outputs=[], error=str(exc), **base)
    except BaseException as exc:
        write_status(stage, status="failed", finished_at=now_iso(),
                     error=f"{type(exc).__name__}: {exc}",
                     traceback=traceback.format_exc(limit=8), **base)
        raise
    unknown = set(result) - RESULT_KEYS - RESERVED_KEYS
    extra = {k: result[k] for k in unknown}
    outputs = list(result.get("outputs", []))
    return write_status(stage, status=result.get("status", "passed"),
                        finished_at=now_iso(),
                        outputs=outputs, output_hashes=output_hashes(outputs),
                        metrics=dict(result.get("metrics", {})),
                        checks=dict(result.get("checks", {})),
                        **({"error": result["error"]} if "error" in result else {}),
                        **extra, **base)
