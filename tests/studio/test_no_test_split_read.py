"""The studio never opens the sealed test split (implementation.md, Decision 3)."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "studio"
ACCESS_LOG = ROOT / "artifacts" / "test_access.log"


def _sources():
    return [p for p in STUDIO.rglob("*.py") if "out" not in p.parts]


@pytest.mark.skipif(not (ROOT / "artifacts" / "stage5" / "status.json").is_file(),
                    reason="needs a finished Stage 5")
def test_sweep_of_every_endpoint_opens_nothing_forbidden():
    before = ACCESS_LOG.read_bytes()
    done = subprocess.run([sys.executable, str(Path(__file__).parent / "_audit_sweep.py")], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert done.returncode == 0, done.stderr[-2000:]
    report = json.loads(done.stdout.split("RESULT", 1)[1])
    assert report["hook_works"], "the audit hook did not see a planted open"
    assert report["n_opens"] > 100
    assert report["forbidden"] == []
    assert ACCESS_LOG.read_bytes() == before


def test_no_source_mentions_the_test_manifest_or_loads_a_split_directly():
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        assert "test.csv" not in text, path
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "load_split", path
            if isinstance(node, ast.Constant):
                assert node.value != "image_ids", path


def test_only_samples_imports_the_catalog():
    importers = [p.name for p in _sources() if "src.common.catalog" in p.read_text(encoding="utf-8")]
    assert importers == ["samples.py"]
