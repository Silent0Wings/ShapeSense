"""E17: the guards are real, not theater (stages/stage_0.md R9, D4, M1, M3).

Each test plants a temporary violation, runs the actual tool, and removes
the probe in a `finally` block so a failing test never leaves a violation
in the tree.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LINT = [sys.executable, "-c",
        "import sys; from importlinter.cli import lint_imports_command as c; "
        "sys.argv=['lint-imports', '--no-cache']; c()"]


def _lint() -> subprocess.CompletedProcess:
    return subprocess.run(LINT, cwd=ROOT, capture_output=True, text=True)


def _with_probe(rel: str, code: str):
    probe = ROOT / rel
    assert not probe.exists(), f"probe path already exists: {rel}"
    probe.write_text(code, encoding="utf-8")
    try:
        return _lint()
    finally:
        probe.unlink()


def test_committed_tree_passes_lint():
    r = _lint()
    assert r.returncode == 0, r.stdout + r.stderr


def test_forbidden_stage_import_fails_lint():
    """M1 item 2: stage2_augment importing stage3_synth is a violation."""
    r = _with_probe("src/stage2_augment/_probe_violation.py",
                    "import src.stage3_synth  # deliberate violation\n")
    assert r.returncode != 0
    assert "BROKEN" in r.stdout


def test_demo_importing_training_code_fails_lint():
    """M1 item 4: the demo must use the exported bundle, not training code."""
    r = _with_probe("demo/_probe_violation.py",
                    "import src.stage4_train  # deliberate violation\n")
    assert r.returncode != 0


def test_common_importing_a_stage_fails_lint():
    r = _with_probe("src/common/_probe_violation.py",
                    "import src.stage1_freeze  # deliberate violation\n")
    assert r.returncode != 0


def test_stage4_may_import_transform_and_generate():
    """M1 item 1 is allowed (the only cross-stage exception)."""
    r = _with_probe("src/stage4_train/_probe_allowed.py",
                    "from src.stage2_augment import build_transform\n"
                    "from src.stage3_synth import build_generator\n")
    assert r.returncode == 0, r.stdout


def test_fake_test_read_is_blocked(tmp_path):
    """D4: reading the test split from a non-Stage-5 module raises."""
    from src.common.splits import TestSplitAccessError, load_split
    (tmp_path / "test.csv").write_text(
        "image_id,md5,label_id,source_id,phash_group,split\n", encoding="utf-8")
    with pytest.raises(TestSplitAccessError):
        load_split("test", splits_dir=tmp_path, log_path=tmp_path / "log")
