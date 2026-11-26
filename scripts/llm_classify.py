"""Direct LLM classification: Claude and Gemini fill in a label CSV for the same 200 test images.

    scripts\\llm_classify.bat                          both models, all 10 batches
    scripts\\llm_classify.bat --models gemini          one model
    scripts\\llm_classify.bat --batches 1,2            some batches only
    scripts\\llm_classify.bat --dry-run                print the commands only

For each model and each batch, a new empty temporary folder outside the repository gets exactly three files:
fewshot_examples.png (50 labelled training images), batch_NN.png (20 test images behind blind IDs) and
predictions.csv (blind_id,predicted_label with the label column empty). The true labels never enter the folder.
The model is called through its CLI with the same prompt, prompts/5_direct_llm_prediction/cli_prompt.txt, and fills
in predictions.csv itself:

- Claude Code: `claude -p --tools Read,Edit,Write --permission-mode acceptEdits`, no settings files, no MCP servers.
  The file tools only reach the working folder.
- Antigravity: `agy -p --sandbox --new-project --mode accept-edits`.

The script then checks the filled CSV (every blind ID once, every label one of the 10 classes), checks that the two
images are unchanged and that no other file appeared, maps the blind IDs back to image IDs with blind_id_map.csv and
scores macro F1. The trained CNN and the recorded 2026-11-19 run are scored on the same images for comparison.

Outputs, never overwriting anything:
- results/direct_llm_prediction/cli_runs/<run>/<model>_predictions.csv (image_id,true_label,predicted_label)
- results/direct_llm_prediction/cli_runs/<run>/summary.json
- prompts/5_direct_llm_prediction/<model>/NN_cli-run-<date>.md: command, CLI version, each batch's reply and CSV
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from sklearn.metrics import f1_score

from scripts.llm_check import cli_version, next_number, shown_command

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "direct_llm_prediction"
SHEETS = RESULTS / "sheets"
PROMPTS = ROOT / "prompts" / "5_direct_llm_prediction"
PROMPT_FILE = PROMPTS / "cli_prompt.txt"
CLASSES = ("circle", "ellipse", "triangle", "square", "rectangle", "pentagon", "hexagon", "octagon", "star", "diamond")
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
            return [self.exe, "-p", prompt, "--model", self.model_id, "--effort", "medium",
                    "--tools", "Read,Edit,Write", "--permission-mode", "acceptEdits",
                    "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence"]
        return [self.exe, "-p", prompt, "--model", self.model_id, "--sandbox", "--new-project",
                "--disable-slash-commands", "--mode", "accept-edits"]


MODELS = {
    "claude": Model("claude", "Claude Opus 5.5", "claude_opus", "claude", "claude-opus-5-5"),
    "gemini": Model("gemini", "Gemini 4 Neon", "gemini_4_neon", "agy", "gemini-4-neon-medium"),
}


MAX_ATTEMPTS = 2  # a batch that comes back with no valid label at all is run once more; every attempt is logged


@dataclass
class BatchResult:
    batch: str
    attempt: int
    exit_code: int
    seconds: float
    reply: str
    stderr: str
    filled_csv: str
    answers: dict[str, str]
    issues: list[str] = field(default_factory=list)


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_batches() -> dict[str, list[dict[str, str]]]:
    """batch name -> rows of blind_id_map.csv, in blind-ID order."""
    batches: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(RESULTS / "blind_id_map.csv"):
        batches.setdefault(row["batch"], []).append(row)
    return {b: sorted(rows, key=lambda r: r["blind_id"]) for b, rows in sorted(batches.items())}


def render_prompt(template: str, batch: str, rows: list[dict[str, str]]) -> str:
    return (template.replace("{batch}", batch).replace("{first}", rows[0]["blind_id"])
            .replace("{last}", rows[-1]["blind_id"]))


def blank_csv(rows: list[dict[str, str]]) -> str:
    return "blind_id,predicted_label\n" + "".join(f"{r['blind_id']},\n" for r in rows)


def parse_filled(text: str, blind_ids: list[str]) -> tuple[dict[str, str], list[str]]:
    """Answers per blind ID and the problems found. A missing or invalid label is left out of the answers."""
    issues: list[str] = []
    answers: dict[str, str] = {}
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    if reader.fieldnames is None or [h.strip() for h in reader.fieldnames] != ["blind_id", "predicted_label"]:
        issues.append(f"header changed: {reader.fieldnames}")
    for row in reader:
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        bid, label = row.get("blind_id", ""), row.get("predicted_label", "").lower()
        if bid not in blind_ids:
            issues.append(f"unexpected row {bid!r}")
        elif bid in answers:
            issues.append(f"{bid} answered twice")
        elif label not in CLASSES:
            issues.append(f"{bid}: invalid label {label!r}")
        else:
            answers[bid] = label
    missing = [b for b in blind_ids if b not in answers]
    if missing:
        issues.append(f"no valid label for {', '.join(missing)}")
    return answers, issues


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_batch(model: Model, exe: str, template: str, batch: str, rows: list[dict[str, str]],
              attempt: int = 1) -> BatchResult:
    workdir = Path(tempfile.mkdtemp(prefix="shapesense_llm_classify_"))
    try:
        images = ["fewshot_examples.png", f"{batch}.png"]
        for name in images:
            shutil.copy2(SHEETS / name, workdir / name)
        (workdir / "predictions.csv").write_text(blank_csv(rows), encoding="utf-8", newline="\n")
        before = {name: sha256(workdir / name) for name in images}

        cmd = model.command(render_prompt(template, batch, rows))
        cmd[0] = exe
        started = dt.datetime.now()
        done = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=TIMEOUT_S, stdin=subprocess.DEVNULL)
        seconds = (dt.datetime.now() - started).total_seconds()

        filled = (workdir / "predictions.csv").read_text(encoding="utf-8", errors="replace") \
            if (workdir / "predictions.csv").exists() else ""
        answers, issues = parse_filled(filled, [r["blind_id"] for r in rows])
        if done.returncode != 0:
            issues.insert(0, f"exit code {done.returncode}")
        if "no output produced" in done.stderr or "auto-denied" in done.stderr:
            issues.insert(0, "the CLI reported a refused tool call (see stderr)")
        for name in images:
            if not (workdir / name).exists() or sha256(workdir / name) != before[name]:
                issues.append(f"{name} was changed or removed")
        extra = sorted(p.name for p in workdir.iterdir() if p.name not in {*images, "predictions.csv"})
        if extra:
            issues.append(f"extra files: {', '.join(extra)}")
        return BatchResult(batch, attempt, done.returncode, seconds, done.stdout, done.stderr, filled, answers,
                           issues)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def macro_f1(truth: list[str], pred: list[str]) -> float:
    return round(100 * f1_score(truth, pred, labels=sorted(set(truth)), average="macro", zero_division=0), 2)


def score(rows: list[dict[str, str]], answers: dict[str, str]) -> dict:
    """Missing answers count as wrong."""
    truth = [r["true_label"] for r in rows]
    pred = [answers.get(r["blind_id"], "missing") for r in rows]
    correct = sum(t == p for t, p in zip(truth, pred))
    return {"n": len(rows), "answered": sum(r["blind_id"] in answers for r in rows), "correct": correct,
            "accuracy": round(100 * correct / len(rows), 2), "macro_f1": macro_f1(truth, pred)}


def recorded_score(csv_name: str, rows: list[dict[str, str]]) -> dict | None:
    path = RESULTS / csv_name
    if not path.exists():
        return None
    by_image = {r["image_id"]: r["predicted_label"] for r in read_csv(path)}
    return score(rows, {r["blind_id"]: by_image[r["image_id"]] for r in rows if r["image_id"] in by_image})


def write_log(model: Model, version: str, cmd_shown: str, prompt_sha: str, run_name: str,
              results: list[BatchResult], scores: dict) -> Path:
    folder = PROMPTS / model.folder
    out = folder / f"{next_number(folder):02d}_cli-run-{run_name[:10]}.md"
    lines = [
        f"# 5_direct_llm_prediction - CLI classification run ({run_name})",
        f"- LLM: {model.label} (`{model.model_id}`), run by `scripts/llm_classify.py`",
        "- Category: Pipeline vs. direct LLM prediction",
        f"- CLI: `{version}`",
        f"- Command, once per batch, from a new temporary folder holding only `fewshot_examples.png`, the batch image and "
        f"an unlabelled `predictions.csv`: `{cmd_shown}`",
        f"- Prompt: [`cli_prompt.txt`](../cli_prompt.txt) (SHA-256 `{prompt_sha}`), with the batch name and blind-ID "
        "range filled in. The same for both models.",
        f"- Predictions: `results/direct_llm_prediction/cli_runs/{run_name}/{model.folder}_predictions.csv`",
        "",
        "## Result",
        "",
        f"{scores['correct']} of {scores['n']} correct, macro F1 {scores['macro_f1']:.2f} "
        f"({scores['answered']} of {scores['n']} answered with a valid label; missing answers count as wrong).",
        "",
    ]
    retried = [r.batch for r in results if r.attempt > 1]
    if retried:
        lines += [f"Run again after an attempt with no valid label: {', '.join(retried)}. Both attempts are below; "
                  "the last attempt of each batch is the one scored.", ""]
    for r in results:
        lines += [f"## {r.batch}" + (f" (attempt {r.attempt})" if r.attempt > 1 or r.batch in retried else ""), "",
                  f"Exit code {r.exit_code}, {r.seconds:.0f} s. Issues: {'; '.join(r.issues) if r.issues else 'none'}.",
                  "", "Reply:", "", "```text", r.reply.strip() or "(empty)", "```", "",
                  "Filled `predictions.csv`:", "", "```csv", r.filled_csv.strip() or "(missing)", "```", ""]
        if r.stderr.strip():
            lines += ["CLI messages (stderr):", "", "```text", r.stderr.strip(), "```", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:  # never overwrite a record
        f.write("\n".join(lines))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", default="claude,gemini", help="comma-separated: claude, gemini")
    parser.add_argument("--batches", default="all", help="all, or comma-separated batch numbers such as 1,2")
    parser.add_argument("--dry-run", action="store_true", help="print the commands, call nothing")
    args = parser.parse_args(argv)

    keys = [k.strip() for k in args.models.split(",") if k.strip()]
    if unknown := [k for k in keys if k not in MODELS]:
        parser.error(f"unknown model(s): {', '.join(unknown)}")
    batches = load_batches()
    if args.batches != "all":
        wanted = {f"batch_{int(n):02d}" for n in args.batches.split(",") if n.strip()}
        if missing := wanted - batches.keys():
            parser.error(f"unknown batch(es): {', '.join(sorted(missing))}")
        batches = {b: rows for b, rows in batches.items() if b in wanted}

    template = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_sha = hashlib.sha256(template.encode("utf-8")).hexdigest()
    rows = [r for b in batches.values() for r in b]
    print(f"prompt: {PROMPT_FILE.relative_to(ROOT)} sha256 {prompt_sha[:16]}...  batches: {len(batches)}  "
          f"images: {len(rows)}")

    if args.dry_run:
        for key in keys:
            print(f"[{key}] {shown_command(MODELS[key].command('<prompt>'))}  (x{len(batches)} batches)")
        return 0

    run_name = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = RESULTS / "cli_runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    summary = {"run": run_name, "prompt_file": str(PROMPT_FILE.relative_to(ROOT).as_posix()),
               "prompt_sha256": prompt_sha, "batches": list(batches), "n_images": len(rows),
               "trained_cnn": recorded_score("trained_cnn_predictions.csv", rows), "models": {}}
    failed = False
    for key in keys:
        model = MODELS[key]
        exe = shutil.which(model.exe)
        if exe is None:
            raise SystemExit(f"{model.exe} is not installed or not on PATH")
        version = cli_version(exe)
        results: list[BatchResult] = []
        final: list[BatchResult] = []
        for batch, batch_rows in batches.items():
            for attempt in range(1, MAX_ATTEMPTS + 1):
                print(f"[{key}] {batch} attempt {attempt} ...", end=" ", flush=True)
                r = run_batch(model, exe, template, batch, batch_rows, attempt)
                print(f"exit {r.exit_code}, {r.seconds:.0f} s, {len(r.answers)}/{len(batch_rows)} labels"
                      + (f", issues: {r.issues[0]}" + (f" (+{len(r.issues) - 1} more)" if len(r.issues) > 1 else "")
                         if r.issues else ""))
                results.append(r)
                if r.answers:
                    break
            final.append(r)
        answers = {bid: label for r in final for bid, label in r.answers.items()}
        with open(run_dir / f"{model.folder}_predictions.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["image_id", "true_label", "predicted_label"])
            for r in sorted(rows, key=lambda r: r["image_id"]):
                w.writerow([r["image_id"], r["true_label"], answers.get(r["blind_id"], "")])
        scores = score(rows, answers)
        log = write_log(model, version, shown_command(model.command("<prompt>")), prompt_sha, run_name, results,
                        scores)
        summary["models"][model.folder] = {
            "model_id": model.model_id, "cli_version": version, **scores,
            "recorded_2026_11_19": recorded_score(f"{model.folder}_predictions.csv", rows),
            "batch_issues": {r.batch: r.issues for r in final if r.issues},
            "retried_batches": [r.batch for r in results if r.attempt > 1],
            "log": str(log.relative_to(ROOT).as_posix())}
        failed |= any(r.issues for r in final)
        cnn = summary["trained_cnn"]
        print(f"[{key}] macro F1 {scores['macro_f1']:.2f} ({scores['correct']}/{scores['n']}); trained CNN on the "
              f"same images {cnn['macro_f1']:.2f}  -> {log.relative_to(ROOT)}")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary -> {(run_dir / 'summary.json').relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
