"""Stage 0 — infrastructure and reproducibility (stages/stage_0.md).

Stage 0 supplies the rails, not the experiment. Its status records:
- the migration-equivalence check (R2, D3) from artifacts/stage0/migration_check.json;
- the raw-data archive SHA-256 (R12) in artifacts/stage0/data_archive_sha256.txt;
- the environment pins (R11): Python version and requirements.txt;
- the result of the guards the runner ran before this stage (R9).
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

from src.common.config import REPO_ROOT, load_config, resolve
from src.common.hashing import sha256_path
from src.stage0_infra.data_archive import archive_sha256
from src.stage0_infra.migration import compare, record, write_check

STAGE = "stage0"
DEPENDS: list[str] = []
GUARDS_FILE = "guards.json"
BUILD_MODULE = "src.stage1_freeze.build_unified_dataset"  # run as a process
# Code whose change must rerun this stage: its own, the shared helpers and
# the build the migration check reruns (hashed, not imported).
CODE_DIRS = {"code": "src/stage0_infra", "common": "src/common",
             "build_code": "src/stage1_freeze"}


def _stage_dir(config: dict) -> Path:
    return resolve(config["paths"]["artifacts_dir"]) / STAGE


def _posix(p: Path) -> str:
    """Repo-relative posix path; absolute when the artefacts dir lies outside the repo."""
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def raw_fingerprint(root: str | Path, exclude: list[str] | None = None) -> str:
    """'files=<n>;bytes=<total>' over root, skipping top-level names in exclude.

    A size fingerprint, NOT a content hash: the raw tree holds ~187k files
    and hashing them on every invocation is too slow for an inputs() call.
    The full content SHA-256 (R12) is computed by run() itself.
    """
    root = Path(root)
    skip = set(exclude or [])
    n_files = n_bytes = 0
    if root.is_dir():
        for top in root.iterdir():
            if top.name in skip:
                continue
            for p in ([top] if top.is_file() else top.rglob("*")):
                if p.is_file():
                    n_files += 1
                    n_bytes += p.stat().st_size
    return f"files={n_files};bytes={n_bytes}"


def inputs(config: dict) -> dict[str, str]:
    """What the checks depend on; never a file run() itself writes (no cache churn)."""
    paths = config["paths"]
    d = {key: sha256_path(resolve(p)) for key, p in CODE_DIRS.items()}
    d.update({
        "requirements": sha256_path(resolve("requirements.txt")),
        "python_version_pin": sha256_path(resolve(".python-version")),
        "catalog": sha256_path(resolve(paths["catalog"])),
        "raw_data": raw_fingerprint(resolve(paths["raw_dir"]),
                                    exclude=[Path(paths["unified_dir"]).name]),
    })
    return d


def migration_check(raw: Path, unified: Path, stage_dir: Path, max_hamming: int,
                    out_path: Path) -> dict:
    """R2/D3: rebuild the unified set with the moved code into artifacts/ and
    compare it with the copy in data_set/ (data_set/ is never written)."""
    rebuild = stage_dir / "rebuild"
    before = record(unified, max_hamming)
    # A separate process, not an import: Stage 0 may not import Stage 1
    # (import-linter independence contract); the build is Stage 1's code.
    subprocess.run([sys.executable, "-m", BUILD_MODULE, "--out", str(rebuild),
                    "--data", str(raw)], cwd=REPO_ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    result = compare(before, record(rebuild, max_hamming))
    result["catalog_file_identical"] = (result["before"]["catalog_file"]
                                        == result["after"]["catalog_file"])
    result["note"] = (f"before = {unified} (pulled data); after = rebuild by "
                      "src/stage1_freeze/build_unified_dataset.py into " + str(rebuild))
    write_check(result, out_path)
    return result


def run(config: dict) -> dict:
    d = _stage_dir(config)
    d.mkdir(parents=True, exist_ok=True)
    mig_path = d / "migration_check.json"
    raw = resolve(config["paths"]["raw_dir"])
    unified = resolve(config["paths"]["unified_dir"])
    if not unified.is_dir():
        raise FileNotFoundError(f"{unified} not found: pull the data first (README section 3)")
    # Always recomputed when the stage runs: the runner's input cache decides
    # whether the stage runs at all, so a stale file is never reused.
    migration_check(raw, unified, d, int(config["split"]["phash_hamming_max"]), mig_path)
    migration = json.loads(mig_path.read_text(encoding="utf-8"))

    sha_path = d / "data_archive_sha256.txt"
    digest, n_files = archive_sha256(raw, exclude=[Path(config["paths"]["unified_dir"]).name])
    sha_path.write_text(f"{digest}  {n_files} files  data_set/ (excluding unified/)\n",
                        encoding="utf-8")
    archive = sha_path.read_text(encoding="utf-8").split()[0]

    guards_path = d / GUARDS_FILE
    guards = json.loads(guards_path.read_text(encoding="utf-8")) if guards_path.is_file() else {}
    pin = resolve(".python-version")
    pinned = pin.read_text(encoding="utf-8").strip() if pin.is_file() else None
    running = platform.python_version()

    checks = {
        "migration_equivalent": bool(migration and migration.get("equal")),
        "python_matches_pin": bool(pinned) and running.startswith(pinned),
        "requirements_pinned": resolve("requirements.txt").is_file(),
        "guards_passed": bool(guards) and all(guards.values()),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "outputs": [_posix(p) for p in (mig_path, sha_path) if p.is_file()],
        "metrics": {"python": running, "python_pin": pinned, "platform": sys.platform,
                    "data_archive_sha256": archive,
                    "migration_differences": (migration or {}).get("differences"),
                    "guards": guards},
        "checks": checks,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    run(load_config(parser.parse_args().config))


if __name__ == "__main__":
    main()
