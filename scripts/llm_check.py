"""Run the dataset-awareness check on Claude and Gemini through their CLIs, the same way for both.

    scripts\\llm_check.bat                  both models
    scripts\\llm_check.bat --models claude  one model
    scripts\\llm_check.bat --dry-run        print the commands only

Both models get the same prompt, word for word: prompts/6_verification/dataset_awareness/cli_prompt.txt (its
SHA-256 is recorded with each reply). Each call runs in print mode from a new, empty temporary folder outside the
repository, so the model cannot see the project files:

- Claude Code: `claude -p --tools ""` disables every tool, and `--setting-sources ""` and `--strict-mcp-config`
  load no settings files and no MCP servers.
- Antigravity: `agy -p --sandbox --new-project`. agy has no switch that turns tools off, so the prompt says that
  using any tool voids the test, as in the 2026-11-20 sandboxed run.

Each reply is saved unedited, with the exact command, CLI version, time and exit code, as a new numbered file in
prompts/6_verification/dataset_awareness/<model folder>/. Existing files are never overwritten. A new run does not
replace the recorded results: it is scored against docs/source.md by hand, and the team decides whether it counts.
The script fails if the temporary folder holds any file after the call (the model wrote something).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_DIR = ROOT / "prompts" / "6_verification" / "dataset_awareness"
PROMPT_FILE = CHECK_DIR / "cli_prompt.txt"
TIMEOUT_S = 20 * 60


@dataclass(frozen=True)
class Model:
    key: str
    label: str
    folder: str
    exe: str
    model_id: str

    def command(self, prompt: str) -> list[str]:
        if self.key == "claude":
            return [self.exe, "-p", prompt, "--model", self.model_id, "--effort", "medium", "--tools", "",
                    "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence"]
        return [self.exe, "-p", prompt, "--model", self.model_id, "--sandbox", "--new-project",
                "--disable-slash-commands"]


MODELS = {
    "claude": Model("claude", "Claude Opus 5.5", "claude_opus", "claude", "claude-opus-5-5"),
    "gemini": Model("gemini", "Gemini 4 Neon", "gemini_4_neon", "agy", "gemini-4-neon-medium"),
}


def next_number(folder: Path) -> int:
    """One more than the highest NN_ prefix in the folder."""
    numbers = [int(m.group(1)) for p in folder.glob("*.md") if (m := re.match(r"(\d+)_", p.name))]
    return max(numbers, default=0) + 1


def shown_command(cmd: list[str]) -> str:
    """The command with the long prompt replaced by its file name, for the record. The executable is shown by name
    only, so no local install path ends up in the repository."""
    parts = [Path(cmd[0]).stem.lower()]
    parts += ["<cli_prompt.txt>" if i == 2 else (f'"{a}"' if a == "" else a) for i, a in enumerate(cmd) if i]
    return " ".join(parts)


def cli_version(exe: str) -> str:
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unknown"


def record(model: Model, cmd: list[str], version: str, started: dt.datetime, seconds: float,
           code: int, reply: str, stderr: str, prompt_sha: str, empty_after: bool) -> str:
    rel_prompt = "../cli_prompt.txt"
    lines = [
        f"# 6_verification/dataset_awareness - Four sources, CLI run ({started:%Y-%m-%d})",
        f"- LLM: {model.label} (`{model.model_id}`), run by `scripts/llm_check.py`",
        "- Category: Verification (dataset-awareness check)",
        f"- Date: {started.isoformat(timespec='seconds')}",
        f"- CLI: `{version}`",
        f"- Command, from a new empty temporary folder outside the repository: `{shown_command(cmd)}`",
        f"- Exit code: {code}. Time: {seconds:.0f} s. Folder still empty after the call: {'yes' if empty_after else 'NO'}",
        "",
        f"The prompt is [`cli_prompt.txt`]({rel_prompt}) (SHA-256 `{prompt_sha}`), the same for both models. "
        "The reply below is unedited.",
        "",
        "## Response",
        "",
        reply.strip() or "(empty reply)",
        "",
    ]
    if stderr.strip():
        lines += ["## CLI messages (stderr)", "", "```text", stderr.strip(), "```", ""]
    lines += [
        "## Validation",
        "",
        "Not scored yet. Score each answer against [`docs/source.md`](../../../../docs/source.md) as in "
        "[PROMPT.md](../PROMPT.md), and compare with the recorded runs in this folder.",
        "",
        "## Our decision",
        "",
        "Not counted until the team scores it. The recorded runs stay the reported result.",
        "",
    ]
    return "\n".join(lines)


def run_one(model: Model, prompt: str, prompt_sha: str, dry_run: bool) -> Path | None:
    cmd = model.command(prompt)
    if dry_run:
        print(f"[{model.key}] {shown_command(cmd)}")
        return None
    exe = shutil.which(model.exe)
    if exe is None:
        raise SystemExit(f"{model.exe} is not installed or not on PATH")
    cmd[0] = exe
    version = cli_version(exe)
    workdir = Path(tempfile.mkdtemp(prefix="shapesense_llm_check_"))
    try:
        started = dt.datetime.now().astimezone()
        print(f"[{model.key}] running {model.model_id} in {workdir} ...", flush=True)
        done = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=TIMEOUT_S, stdin=subprocess.DEVNULL)
        seconds = (dt.datetime.now().astimezone() - started).total_seconds()
        empty_after = not any(workdir.iterdir())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    folder = CHECK_DIR / model.folder
    out = folder / f"{next_number(folder):02d}_cli-run-{started:%Y-%m-%d}.md"
    with open(out, "x", encoding="utf-8", newline="\n") as f:  # "x": never overwrite a recorded run
        f.write(record(model, cmd, version, started, seconds, done.returncode, done.stdout, done.stderr,
                       prompt_sha, empty_after))
    print(f"[{model.key}] exit {done.returncode}, {seconds:.0f} s -> {out.relative_to(ROOT)}")
    if done.returncode != 0 or not empty_after:
        print(f"[{model.key}] check this run: "
              f"{'non-zero exit' if done.returncode else 'the model wrote files in its folder'}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", default="claude,gemini", help="comma-separated: claude, gemini")
    parser.add_argument("--dry-run", action="store_true", help="print the commands, call nothing")
    args = parser.parse_args(argv)

    keys = [k.strip() for k in args.models.split(",") if k.strip()]
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        parser.error(f"unknown model(s): {', '.join(unknown)}")
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    print(f"prompt: {PROMPT_FILE.relative_to(ROOT)} sha256 {prompt_sha[:16]}...")

    failed = False
    for key in keys:
        out = run_one(MODELS[key], prompt, prompt_sha, args.dry_run)
        if out is not None and ("Exit code: 0." not in out.read_text(encoding="utf-8")
                                or "empty after the call: NO" in out.read_text(encoding="utf-8")):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
