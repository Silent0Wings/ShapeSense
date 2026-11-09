"""Package boundaries: the import contract holds, the pages stay offline."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "studio" / "web"
LINT = ("import sys; from importlinter.cli import lint_imports_command as c; "
        "sys.argv=['lint-imports']; c()")
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def _run(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_import_contract_holds():
    done = _run("-c", LINT)
    assert done.returncode == 0, done.stdout[-1500:]
    assert "studio uses only" in done.stdout


def test_a_forbidden_import_breaks_the_contract():
    probe = ROOT / "studio" / "_probe_forbidden.py"
    probe.write_text("import src.stage5_eval.evaluate\n", encoding="utf-8")
    try:
        done = _run("-c", LINT)
    finally:
        probe.unlink()
    assert done.returncode != 0


def test_the_server_does_not_load_torch():
    done = _run("-c", "import sys; import studio.server.app; print('torch' in sys.modules)")
    assert done.returncode == 0, done.stderr[-1500:]
    assert done.stdout.strip() == "False"


def test_pages_make_no_external_requests():
    for path in WEB.rglob("*"):
        if path.suffix in {".html", ".js", ".css"}:
            text = path.read_text(encoding="utf-8").replace(SVG_NAMESPACE, "")
            assert not re.search(r"https?://|//cdn\.", text), path


def test_no_leftover_stubs():
    for path in list(WEB.rglob("*.js")) + list((ROOT / "studio").rglob("*.py")):
        if "out" in path.parts:
            continue
        assert not re.search(r"\b(TODO|FIXME|XXX|NotImplemented)\b", path.read_text(encoding="utf-8")), path


def test_every_page_loads_its_script():
    for path in WEB.glob("*.html"):
        match = re.search(r'src="(js/pages/[a-z0-9]+\.js)"', path.read_text(encoding="utf-8"))
        assert match and (WEB / match.group(1)).is_file(), path
