"""Stage 6 report build without PowerShell: pdflatex directly (Linux, Colab)."""

import subprocess
from pathlib import Path

from src.stage6_report import run as stage6


def _no_powershell(monkeypatch, pdflatex: str | None) -> None:
    monkeypatch.setattr(stage6.shutil, "which",
                        lambda name: pdflatex if name == stage6.PDFLATEX else None)


def test_no_powershell_and_no_pdflatex_fails_with_a_clear_message(monkeypatch, tmp_path):
    _no_powershell(monkeypatch, None)
    build = stage6.build_report(tmp_path)
    assert build["ok"] is False
    assert "pdflatex" in build["output"]


def test_pdflatex_runs_twice_keeps_the_pdf_and_removes_aux_files(monkeypatch, tmp_path):
    _no_powershell(monkeypatch, "/usr/bin/pdflatex")
    calls = []

    def fake_run(cmd, cwd, **kwargs):
        calls.append(cmd)
        (Path(cwd) / stage6.REPORT_PDF).write_bytes(b"%PDF")
        (Path(cwd) / "phase2_report.aux").write_text("aux")
        return subprocess.CompletedProcess(cmd, 0, "ok", "")

    monkeypatch.setattr(stage6.subprocess, "run", fake_run)
    build = stage6.build_report(tmp_path)
    assert build["ok"] is True
    assert len(calls) == stage6.PDFLATEX_PASSES
    assert calls[0][0] == "/usr/bin/pdflatex" and calls[0][-1] == stage6.REPORT_TEX
    assert not (tmp_path / "phase2_report.aux").exists()


def test_a_failing_pdflatex_pass_stops_the_build(monkeypatch, tmp_path):
    _no_powershell(monkeypatch, "/usr/bin/pdflatex")
    calls = []

    def fake_run(cmd, cwd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, "! LaTeX Error: File `booktabs.sty' not found.", "")

    monkeypatch.setattr(stage6.subprocess, "run", fake_run)
    build = stage6.build_report(tmp_path)
    assert build["ok"] is False and build["returncode"] == 1
    assert len(calls) == 1
    assert "booktabs.sty" in build["output"]
