"""Stage 6 — report, figures, dashboard and packaging (stages/stage_6.md).

Turns the artifacts of Stages 0–5 into the Phase 2 report, the exported
model bundle (export/) and their status. Every number in the report comes
from an artifact, never typed by hand.

run(config):
  1. requires Stage 5 to have passed (else StageNotReady -> not_run);
  2. builds export/ (ONNX + standardize.py + labels.json + model_card.json);
  3. writes the generated LaTeX snippets (param_ranges.tex, pipeline_facts.tex);
  4. smoke-tests the bundle in a subprocess on a procedurally drawn hexagon;
  5. compiles phase2_report.tex through build.ps1 -File phase2_report.tex (R8);
  6. runs the number-traceability check and the attribution grep.
It does not write status.json; the runner does that through common.status.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.common.config import REPO_ROOT, class_names, load_config, resolve
from src.common.hashing import sha256_obj, sha256_path
from src.common.status import StageNotReady
from src.stage6_report.snippets import write_snippets
from src.stage6_report.traceability import check_report

STAGE = "stage6"
DEPENDS = ["stage0", "stage1", "stage3", "stage4", "stage5"]

STAGE5_DIR = "stage5"
STATUS_FILE = "status.json"
STATUS_PASSED = "passed"
REPORT_TEX = "phase2_report.tex"
REPORT_PDF = "phase2_report.pdf"
BUILD_SCRIPT = "build.ps1"
POWERSHELL_CANDIDATES = ("powershell", "pwsh")   # Windows PowerShell first, then pwsh
EXPORT_DIR = "export"
EXPORT_README = "README.md"
EXPORT_REQUIRED = ("model.onnx", "labels.json", "standardize.py", "predict.py")
SMOKE_IMAGE_NAME = "smoke_hexagon.png"   # written under artifacts/stage6/
SMOKE_IMAGE_SIZE = (300, 200)            # pixels (w, h): a fresh RGB image, not 64x64
SMOKE_STROKE_PX = 12                     # pixels; thick coloured outline
SMOKE_RADIUS_FRACTION = 0.4              # of the shorter side
SMOKE_SIDES = 6                          # hexagon
SMOKE_EXPECTED_CLASS = "hexagon"         # the class the smoke image is drawn as
SMOKE_COLOUR = (0, 0, 255)               # RGB; colour must not matter after standardize
SMOKE_BACKGROUND = (255, 255, 255)
BUILD_TIMEOUT_S = 900                    # pdflatex, two passes, MiKTeX may install packages
SMOKE_TIMEOUT_S = 300                    # onnxruntime import + one prediction
OUTPUT_TAIL_CHARS = 2000                 # of build/smoke output kept in the status
# Source names that must appear in the report and export/README.md (R21).
SOURCE_NAMES = ("Quick, Draw!", "reevald", "El Korchi", "Hand-Drawn")

# Runs inside the smoke-test subprocess: only export/ is imported (R12, R15).
SMOKE_CODE = (
    "import sys\n"
    "from PIL import Image\n"
    "from export import predict\n"
    "print(predict.predict(Image.open(sys.argv[1])))\n"
)


def inputs(config: dict) -> dict[str, str]:
    art = resolve(config["paths"]["artifacts_dir"])
    return {
        "code": sha256_path(resolve("src/stage6_report")),
        "common": sha256_path(resolve("src/common")),
        "report_tex": sha256_path(resolve("phase2_report.tex")),
        "phase1_tex": sha256_path(resolve("phase1_report.tex")),
        "stage1": sha256_path(art / "stage1"),
        "stage3": sha256_path(art / "stage3" / "param_ranges.json"),
        "stage3_status": sha256_path(art / "stage3" / "status.json"),
        "standardize": sha256_path(resolve("src/stage1_freeze/standardize.py")),
        "stage4_runs": sha256_path(art / "stage4" / "status.json"),
        "stage5": sha256_path(art / "stage5"),
        "export_code": sha256_path(resolve("export/predict.py")),
        "config": sha256_obj(config),
        "iteration_log": sha256_path(resolve("docs/crisp_dm/iteration_log.json")),
    }


def _rel(path: Path) -> str:
    """Repo-relative POSIX path for status.json outputs (absolute if outside the repo)."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _tail(text: str) -> str:
    return text[-OUTPUT_TAIL_CHARS:]


def stage5_status(config: dict) -> dict:
    """The Stage 5 status dict; StageNotReady (-> not_run) until Stage 5 passed."""
    path = resolve(config["paths"]["artifacts_dir"]) / STAGE5_DIR / STATUS_FILE
    if not path.is_file():
        raise StageNotReady("Stage 5 results missing")
    with open(path, encoding="utf-8") as f:
        status = json.load(f)
    if status.get("status") != STATUS_PASSED:
        raise StageNotReady("Stage 5 results missing")
    return status


def draw_hexagon(path: Path) -> Path:
    """Write a fresh RGB image (SMOKE_IMAGE_SIZE) with a thick coloured hexagon outline."""
    from PIL import Image, ImageDraw  # Pillow only here, so importing run.py stays light

    w, h = SMOKE_IMAGE_SIZE
    img = Image.new("RGB", (w, h), SMOKE_BACKGROUND)
    draw = ImageDraw.Draw(img)
    cx, cy, r = w / 2, h / 2, SMOKE_RADIUS_FRACTION * min(w, h)
    pts = [(cx + r * math.cos(2 * math.pi * k / SMOKE_SIDES),
            cy + r * math.sin(2 * math.pi * k / SMOKE_SIDES)) for k in range(SMOKE_SIDES)]
    draw.line(pts + pts[:1], fill=SMOKE_COLOUR, width=SMOKE_STROKE_PX, joint="curve")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def smoke_verdict(returncode: int, stdout: str, labels: list[str],
                  expected: str = SMOKE_EXPECTED_CLASS) -> dict[str, Any]:
    """Interpret the smoke subprocess: ``predicted``, ``ok``, ``matches_expected``.

    ``ok`` means "the bundle loads and predicts a valid class" (exit 0 and a
    known class name). ``matches_expected`` says whether that class is the
    one the image was drawn as; a wrong class is surfaced, not a failure.
    """
    predicted = stdout.strip().splitlines()[-1].strip() if stdout.strip() else ""
    ok = returncode == 0 and predicted in labels
    return {"predicted": predicted or None, "ok": ok,
            "matches_expected": bool(ok and predicted == expected)}


def smoke_test(config: dict, export_dir: Path, image_path: Path) -> dict[str, Any]:
    """Load the bundle in a fresh interpreter and predict one fresh image (R12).

    Returns ``{"ok", "predicted", "matches_expected", "missing_files",
    "returncode", "output"}``. ``ok`` requires every bundle file, exit code 0
    and a known class name; ``matches_expected`` additionally requires the
    procedurally drawn hexagon to be predicted ``SMOKE_EXPECTED_CLASS``.
    """
    missing = [name for name in EXPORT_REQUIRED if not (export_dir / name).is_file()]
    result: dict[str, Any] = {"ok": False, "predicted": None, "matches_expected": False,
                              "missing_files": missing, "returncode": None, "output": ""}
    if missing:
        result["output"] = f"export bundle incomplete: {missing}"
        return result
    proc = subprocess.run([sys.executable, "-c", SMOKE_CODE, str(image_path)],
                          cwd=REPO_ROOT, capture_output=True, text=True,
                          timeout=SMOKE_TIMEOUT_S)
    result["returncode"] = proc.returncode
    result["output"] = _tail(proc.stdout + proc.stderr)
    result.update(smoke_verdict(proc.returncode, proc.stdout, class_names(config)))
    return result


def powershell_exe() -> str | None:
    for name in POWERSHELL_CANDIDATES:
        exe = shutil.which(name)
        if exe:
            return exe
    return None


def build_report(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """``powershell -ExecutionPolicy Bypass -File build.ps1 -File phase2_report.tex`` (R8).

    The ``-File phase2_report.tex`` argument is mandatory: build.ps1 defaults to
    phase1_report.tex. Returns ``{"ok", "exe", "returncode", "output", "pdf"}``.
    """
    exe = powershell_exe()
    pdf = repo_root / REPORT_PDF
    if exe is None:
        return {"ok": False, "exe": None, "returncode": None, "pdf": _rel(pdf),
                "output": "neither powershell nor pwsh found on PATH"}
    cmd = [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", BUILD_SCRIPT,
           "-File", REPORT_TEX]
    # errors="replace": PowerShell pipes in the OEM code page, Python decodes in the ANSI
    # one, and a byte undefined there must not crash the stage over a log line.
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True,
                          errors="replace", timeout=BUILD_TIMEOUT_S)
    return {"ok": proc.returncode == 0 and pdf.is_file(), "exe": exe,
            "returncode": proc.returncode, "pdf": _rel(pdf),
            "output": _tail(proc.stdout + proc.stderr)}


def attribution_present(*paths: Path, names: tuple[str, ...] = SOURCE_NAMES) -> bool:
    """True when every source name appears in every given file (R21)."""
    for p in paths:
        if not Path(p).is_file():
            return False
        text = Path(p).read_text(encoding="utf-8")
        if not all(name in text for name in names):
            return False
    return True


def run(config: dict) -> dict:
    """Export, snippets, smoke test, report build, traceability; returns the status payload."""
    from src.stage6_report.export import build_bundle  # torch/onnxruntime: import lazily

    s5 = stage5_status(config)
    art = resolve(config["paths"]["artifacts_dir"])
    stage_dir = art / STAGE
    stage_dir.mkdir(parents=True, exist_ok=True)
    export_dir = resolve(EXPORT_DIR)
    tex_path = resolve(REPORT_TEX)

    bundle = build_bundle(config, export_dir)
    selection = {k: bundle["selection"].get(k) for k in ("run_name", "arm", "seed", "val_macro_f1")}

    snippets = write_snippets(config, art, export_dir)

    image_path = draw_hexagon(stage_dir / SMOKE_IMAGE_NAME)
    smoke = smoke_test(config, export_dir, image_path)

    build = build_report()

    trace = check_report(tex_path, art)
    attribution = attribution_present(tex_path, export_dir / EXPORT_README)

    outputs = [build["pdf"]] if build["ok"] else []
    outputs += [_rel(bundle[k]) for k in ("onnx", "standardize", "labels", "model_card")]
    outputs += [_rel(snippets["param_ranges"]), _rel(snippets["pipeline_facts"]), _rel(image_path)]

    checks = {
        "report_built": bool(build["ok"]),
        "traceable": bool(trace["ok"]),
        "no_placeholders": not trace["placeholders"],
        "export_smoke_test": bool(smoke["ok"]),
        "attribution_present": bool(attribution),
    }
    result: dict[str, Any] = {
        "outputs": outputs,
        "metrics": {
            "selection": selection,
            "traceability_findings": len(trace["findings"]),
            "traceability_failing": trace["n_failing"],
            "traceability_kinds": sorted({f["kind"] for f in trace["findings"]}),
            "missing_inputs": sorted(set(snippets["missing"]) | set(trace["missing_inputs"])),
            "placeholders": trace["placeholders"],
            "verdict": (s5.get("metrics") or {}).get("verdict"),
            "test_reads": (s5.get("checks") or {}).get("test_reads"),
            "smoke_prediction": smoke["predicted"],
            "smoke_expected": SMOKE_EXPECTED_CLASS,
            "smoke_prediction_matches": bool(smoke["matches_expected"]),
            "build_exe": build["exe"],
        },
        "checks": checks,
    }
    problems = []
    if not checks["report_built"]:
        problems.append(f"report build failed: {build['output'][-400:]}")
    if not checks["export_smoke_test"]:
        problems.append(f"export smoke test failed: {smoke['output'][-400:]}")
    if not checks["traceable"]:
        problems.append(f"{trace['n_failing']} report numbers failed the traceability check")
    if not checks["attribution_present"]:
        problems.append("source attribution is missing from the report or export README")
    if problems:
        result["status"] = "failed"
        result["error"] = " | ".join(problems)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    run(load_config(parser.parse_args().config))


if __name__ == "__main__":
    main()
