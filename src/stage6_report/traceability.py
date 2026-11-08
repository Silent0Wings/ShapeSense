"""Number-traceability check for the Phase 2 report (stages/stage_6.md Done-when 2,
Mission M1; plan 35).

Every quantitative statement in ``phase2_report.tex`` must come from an
artifact through ``\\input`` / ``\\InputIfFileExists`` or a generated macro,
never be typed by hand. ``scan`` is a pragmatic text pass, not a LaTeX parser.
It flags:

(a) digits in the running text of the document body that are not in an allowed
    context (file paths of ``\\input`` / ``\\includegraphics`` and their guards,
    ``\\label`` / ``\\ref`` / ``\\cite`` keys, lengths such as ``0.6\\linewidth``
    or ``2pt``, identifiers such as ``A0`` or ``md5``, "Decision 13"-style
    references, license versions) and not one of the plan constants in
    ``ALLOWED_NUMBERS``. A number next to a hedge word ("about 2 points") or a
    result verb ("improved ... by 2 points") is never allowed, even when the bare
    number would be, because that is exactly Mission M1 sentence 3.
(b) the Phase 1 split counts 12,761 / 2,890 / 2,849 anywhere in the file
    (Mission M1 sentence 5; Decision 15 invalidates them).
(c) in ``check_report``: an ``\\input`` target that is still a Stage 0
    placeholder table, or that is missing.

The preamble (before ``\\begin{document}``) and the bibliography
(``thebibliography``) are out of scope for (a): macro definitions, page
geometry and publication years live there.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Re-declared on purpose: stages may not import each other (.importlinter
# "stages-independent"), so this text is copied from
# src/stage5_eval/placeholders.py::PLACEHOLDER_MARK and must stay identical.
PLACEHOLDER_MARK = "% PLACEHOLDER (Stage 0): Stage 5 has not run yet"

# Phase 1 split counts (phase1_report.tex before Stage 1 recomputed the split).
PHASE1_COUNTS = frozenset({"12,761", "2,890", "2,849"})
_PHASE1_PLAIN = frozenset(c.replace(",", "") for c in PHASE1_COUNTS)

# Plan constants that may appear as bare numbers in the body. Everything that
# is a *result* (accuracy, F1, counts, CIs, p-values, throughput) must come
# from an artifact instead. Numbers here are design facts fixed before any
# model was trained (implementation.md Decisions 8-13, configs/pipeline.yaml).
ALLOWED_NUMBERS = frozenset({
    "70/15/15",                       # split ratios
    "70", "15", "30", "50",           # split shares; synthetic share; ablation ratios 0/15/30/50
    "0", "1", "2", "3", "4", "5", "6", "8", "10",   # small counts: classes, seeds, vertices, steps
    "64", "256",                      # image side; canvas side; batch size
    "32", "128",                      # CNN channel widths (Decision 8)
    "0.05", "95",                     # alpha; CI level in percent
    "0.5",                            # "not sure" confidence threshold (R16)
    "0.7",                            # real share of a B batch (1 - synthetic share)
})

WINDOW_CHARS = 40   # characters of context inspected on each side of a number
CONTEXT_CHARS = 80  # characters of the line kept in a finding

KIND_HAND_TYPED = "hand_typed_number"
KIND_PHASE1 = "phase1_count"
KIND_PLACEHOLDER = "placeholder"
KIND_MISSING = "missing_input"
FAILING_KINDS = frozenset({KIND_HAND_TYPED, KIND_PHASE1, KIND_PLACEHOLDER})

TEX_SUFFIX = ".tex"
ARTIFACTS_PREFIX = "artifacts/"

_BEGIN_DOCUMENT = r"\begin{document}"
_BEGIN_BIBLIOGRAPHY = r"\begin{thebibliography}"
_COMMENT = re.compile(r"(?<!\\)%.*$")

# Commands whose (first) brace argument is a path, key or option list, never prose.
_PATH_CMDS = re.compile(
    r"\\(?:input|include|InputIfFileExists|IfFileExists|GuardedGraphic|includegraphics|"
    r"label|ref|pageref|autoref|eqref|cite|url|nolinkurl|href|hypersetup|setlength|"
    r"addcontentsline|usetikzlibrary|providecommand|newcommand|renewcommand|"
    r"captionsetup|pagestyle|thispagestyle)\*?(?:\[[^\]]*\])?\{[^{}]*\}")
# Guards and graphics commands take several brace groups that are all paths/lengths.
_MULTI_ARG_CMDS = re.compile(
    r"\\(?:InputIfFileExists|IfFileExists|GuardedGraphic|MissingFigure)(?:\{[^{}]*\})+")
_ENV = re.compile(r"\\(?:begin|end)\{[^{}]*\}(?:\[[^\]]*\]|\{[^{}]*\})*")
_LENGTH = re.compile(
    r"-?\d*\.?\d+\s*(?:\\(?:linewidth|textwidth|columnwidth|textheight|paperwidth|"
    r"paperheight|baselineskip|fboxsep)\b|(?:pt|cm|mm|in|em|ex|px|bp|sp)\b)")
_REFERENCE = re.compile(
    r"\b(?:Decisions?|Stages?|Phases?|Sections?|Figures?|Tables?|Steps?|steps?|Missions?|"
    r"Plans?|COMP|Requirements?|Weeks?|Lectures?|slides?|Appendix|Appendices|Items?)"
    r"~?\s*\d+[a-z]?(?:\s*(?:,|and|--|–|to|/|&)\s*\d+[a-z]?)*")
_IDENT = re.compile(r"\b[A-Za-z_]+\d\w*|\b\d+[A-Za-z_]\w*")   # A0, md5, R8b, 2D, 1e-3's "1e"
_COORD = re.compile(r"\(\s*-?[\d.]+\s*,\s*-?[\d.]+\s*\)")      # TikZ coordinates (6.5,5)
# key=value options are only scrubbed INSIDE a TikZ/graphicx option list
# ``[...]`` that holds an "=", or a TikZ ``/.style={...}`` body. Prose such as
# "macro-F1 = 91.2 points" or "CI = [0.6, 3.0]" must stay visible to the scan.
_OPTIONS = re.compile(r"\[[^\[\]=]*=[^\[\]]*\]")
_TIKZ_STYLE = re.compile(r"/\.style=\{[^{}]*\}")
_LICENSE = re.compile(r"\bCC\s+BY(?:-[A-Z]{2})*\s+\d+(?:\.\d+)?")
_RATIO = re.compile(r"\d+(?:\s*/\s*\d+)+")                      # 70/15/15
_NUMBER = re.compile(r"(?<![\w.])\d+(?:(?:,|\{,\}|\.)\d+)*(?![\w])")

_HEDGE_BEFORE = re.compile(
    r"\b(?:about|around|approximately|approx\.?|roughly|nearly|almost|circa)"
    r"\s*[~$]?\s*$|~\s*$", re.IGNORECASE)
_UNIT_AFTER = re.compile(
    r"^\s*(?:points?|pp|percent|percentage\s+points?|\\%|%|img/s|images?\s+per|"
    r"s(?:econds?)?\b|ms\b|minutes?|hours?|images?\b|drawings?\b|groups?\b)", re.IGNORECASE)
_RESULT_BEFORE = re.compile(
    r"\b(?:improv\w*|gain\w*|drop\w*|reach\w*|rose|fell|increas\w*|decreas\w*|chang\w*|"
    r"differ\w*|delta|lost|los\w*|higher|lower|better|worse|scored?|achiev\w*|"
    r"measured|observed|took|ran at|removed)\b",
    re.IGNORECASE)
_CRITERION_BEFORE = re.compile(
    r"\b(?:at least|more than|less than|no more than|exceed\w*|limit|threshold|criterion|"
    r"locked|pre-registered|guardrail|may drop|must|target|band)\b", re.IGNORECASE)

_INPUT_TARGET = re.compile(r"\\(?:input|InputIfFileExists)\{([^{}]*)\}")


def _strip_comment(line: str) -> str:
    return _COMMENT.sub("", line)


def _normalize(token: str) -> str:
    return token.replace("{,}", ",")


def is_phase1_count(token: str) -> bool:
    """True for 12,761 / 2,890 / 2,849 in any of their spellings."""
    t = _normalize(token)
    return t in PHASE1_COUNTS or t.replace(",", "") in _PHASE1_PLAIN


def is_allowed_number(token: str, before: str = "", after: str = "") -> bool:
    """May this bare number stay in the running text?

    ``before`` / ``after`` are the characters around the token on its line.
    A hedged number ("about 2") or a result statement ("improved by 2 points")
    is never allowed; otherwise the normalized token must be in ALLOWED_NUMBERS.
    """
    t = _normalize(token)
    if is_phase1_count(t):
        return False
    if _HEDGE_BEFORE.search(before):
        return False
    if (_UNIT_AFTER.match(after) and _RESULT_BEFORE.search(before)
            and not _CRITERION_BEFORE.search(before)):
        return False
    return t in ALLOWED_NUMBERS


def _scrub(line: str) -> str:
    """Blank out the allowed contexts so only prose digits remain (same length not kept)."""
    line = _MULTI_ARG_CMDS.sub(" ", line)
    line = _PATH_CMDS.sub(" ", line)
    line = _ENV.sub(" ", line)
    line = _LICENSE.sub(" ", line)
    line = _REFERENCE.sub(" ", line)
    line = _COORD.sub(" ", line)
    line = _TIKZ_STYLE.sub(" ", line)
    line = _OPTIONS.sub(" ", line)
    line = _IDENT.sub(" ", line)
    line = _LENGTH.sub(" ", line)
    line = _RATIO.sub(lambda m: " " if re.sub(r"\s", "", m.group(0)) in ALLOWED_NUMBERS
                      else m.group(0), line)
    return line


def _finding(kind: str, lineno: int, token: str, line: str) -> dict[str, Any]:
    return {"kind": kind, "line": lineno, "token": token,
            "context": line.strip()[:CONTEXT_CHARS]}


def _body_line_range(lines: list[str]) -> tuple[int, int]:
    """(first, last) 0-based line indexes of the document body, bibliography excluded."""
    start = 0
    for i, line in enumerate(lines):
        if _BEGIN_DOCUMENT in _strip_comment(line):
            start = i + 1
            break
    end = len(lines)
    for i, line in enumerate(lines):
        if _BEGIN_BIBLIOGRAPHY in _strip_comment(line):
            end = i
            break
    return start, end


def scan(tex_text: str) -> list[dict[str, Any]]:
    """Findings for hand-typed numbers and Phase 1 counts in ``tex_text``.

    Each finding is ``{"kind", "line" (1-based), "token", "context"}``. Kinds:
    ``phase1_count`` (anywhere in the file) and ``hand_typed_number`` (document
    body only, bibliography excluded).
    """
    lines = tex_text.splitlines()
    findings: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    # (b) Phase 1 counts anywhere, comments included.
    for i, line in enumerate(lines):
        for m in _NUMBER.finditer(line):
            if is_phase1_count(m.group(0)):
                key = (i, m.group(0))
                if key not in seen:
                    seen.add(key)
                    findings.append(_finding(KIND_PHASE1, i + 1, _normalize(m.group(0)), line))

    # (a) bare digits in the body.
    start, end = _body_line_range(lines)
    for i in range(start, end):
        raw = _strip_comment(lines[i])
        if not raw.strip():
            continue
        scrubbed = _scrub(raw)
        for m in _NUMBER.finditer(scrubbed):
            token = m.group(0)
            if is_phase1_count(token):
                continue  # already reported by pass (b)
            before = scrubbed[max(0, m.start() - WINDOW_CHARS):m.start()]
            after = scrubbed[m.end():m.end() + WINDOW_CHARS]
            if is_allowed_number(token, before, after):
                continue
            findings.append(_finding(KIND_HAND_TYPED, i + 1, _normalize(token), lines[i]))
    return findings


def input_targets(tex_text: str) -> list[str]:
    """Targets of every ``\\input`` / ``\\InputIfFileExists`` outside comments, in order."""
    targets: list[str] = []
    for line in tex_text.splitlines():
        for m in _INPUT_TARGET.finditer(_strip_comment(line)):
            t = m.group(1).strip()
            if t and t not in targets:
                targets.append(t)
    return targets


def resolve_input(target: str, base_dir: Path, artifacts_dir: Path | None) -> Path | None:
    """Locate an ``\\input`` target like pdflatex would (relative to the .tex dir).

    Also tries ``artifacts_dir`` for ``artifacts/...`` targets, so a report can be
    checked against a different artifacts root. Returns None when nothing exists.
    """
    candidates = [base_dir / target, base_dir / (target + TEX_SUFFIX)]
    if artifacts_dir is not None and target.startswith(ARTIFACTS_PREFIX):
        rel = target[len(ARTIFACTS_PREFIX):]
        candidates += [Path(artifacts_dir) / rel, Path(artifacts_dir) / (rel + TEX_SUFFIX)]
    for p in candidates:
        if p.is_file():
            return p
    return None


def is_placeholder_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").startswith(PLACEHOLDER_MARK)


def check_report(tex_path: str | Path, artifacts_dir: str | Path | None = None) -> dict[str, Any]:
    """Scan the report and its ``\\input`` targets.

    Returns ``{"ok": bool, "findings": [...], "n_failing": int,
    "placeholders": [targets still holding a Stage 0 placeholder],
    "missing_inputs": [targets that do not exist]}``. ``ok`` is False when any
    finding is a hand-typed number, a Phase 1 count or a placeholder table; a
    missing input is reported but does not fail the check (the report falls
    back to ``--`` and the stage records the gap).
    """
    tex_path = Path(tex_path)
    text = tex_path.read_text(encoding="utf-8")
    findings = scan(text)
    base = tex_path.resolve().parent
    art = Path(artifacts_dir) if artifacts_dir is not None else None
    placeholders: list[str] = []
    missing: list[str] = []
    for target in input_targets(text):
        p = resolve_input(target, base, art)
        if p is None:
            missing.append(target)
            findings.append({"kind": KIND_MISSING, "line": 0, "token": target,
                             "context": "input target not found"})
        elif is_placeholder_file(p):
            placeholders.append(target)
            findings.append({"kind": KIND_PLACEHOLDER, "line": 0, "token": target,
                             "context": "Stage 0 placeholder table still in place"})
    n_failing = sum(1 for f in findings if f["kind"] in FAILING_KINDS)
    return {"ok": n_failing == 0, "findings": findings, "n_failing": n_failing,
            "placeholders": placeholders, "missing_inputs": missing}
