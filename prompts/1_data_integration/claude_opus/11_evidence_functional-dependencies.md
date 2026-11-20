# 1_data_integration - Detect functional dependencies in the collected datasets

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-08
- Owner: 40256377
- Worksheet entries: I05
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is verbatim from the session log (recorded in `docs/prompts.csv` of the snapshot); the reply was not saved. The Response quotes the LLM's saved output files verbatim.
- Reconstructions of the same entries: [I05](08_I05_functional-dependencies-on-filtered-rows.md), [I05](../gemini_4_neon/07_I05_fd-check-coverage-and-injected-violation-test.md)

## Prompt P01 (verbatim, 2026-10-08)

> from your audit which part is missing and we still havent adressed ? / 1 dont have them , 2 dosent matter , 3 =[FD "detection" is still just assertion ... ] i dont understand what are my option s? / 4-- ignore / 5 what are my options ? / 6- do we need to download all data sets ? / i will revert the repo , and you need to explain to me what is this =["Detect function dependencies in the collected datasets and show some examples"]

_Source: Claude Code session 2026-10-08, user messages 16, 17 and 23 (pasted audit text trimmed). Confidence: high. Matches the commit title (FD results and check script). Bracketed pasted text is shortened with ...; the full paste is in the session log._

## Prompt P02 (verbatim, 2026-10-08)

> so by detect i am not runing some visual llm or ocr , its a data quality check ? / but the project dosent have any ocr or detection of labels at all and that by detection they are talking about a quality check / make sure no ocr or optical recognition idea , proposal or tools are mentioned in the project

_Source: Claude Code session 2026-10-08, user messages 24-26. Confidence: high. Sets the meaning of 'detect' used in the FD check._

## Response (the reply was not saved; the work it produced, verbatim)

### `scripts/discover_fds.py`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````python
"""
Functional-dependency DISCOVERY on the unified metadata (Section C).

Instead of only checking FDs we designed, this tests every left-hand side
of 1 or 2 columns against every other column and reports:
  - exact FDs   X -> Y holds on every row (minimal X only)
  - approx FDs  X -> Y holds after removing at most MAX_ERROR of rows
                (g3 error: share of rows that break it)

    python scripts/discover_fds.py
"""
import csv
import itertools
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "data_set", "unified", "metadata.csv")

# Categorical columns. Per-image unique ids (image_id, path, phash) and
# continuous measurements are left out: a unique column determines
# everything trivially.
COLS = ["source_id", "domain", "license", "original_label", "label_id",
        "label_name", "split", "native_width", "native_height",
        "native_mode", "outline_redrawn"]
MAX_ERROR = 0.05


def g3(rows, lhs, rhs):
    """Share of rows to delete so lhs -> rhs holds exactly."""
    groups = defaultdict(Counter)
    for r in rows:
        groups[tuple(r[c] for c in lhs)][r[rhs]] += 1
    keep = sum(c.most_common(1)[0][1] for c in groups.values())
    return 1 - keep / len(rows)


def main():
    with open(META, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    exact, approx = [], []
    for k in (1, 2):
        for lhs in itertools.combinations(COLS, k):
            for rhs in COLS:
                if rhs in lhs:
                    continue
                # skip if a smaller lhs already determines rhs (not minimal)
                if any(set(e[0]) < set(lhs) and e[1] == rhs for e in exact):
                    continue
                err = g3(rows, lhs, rhs)
                if err == 0:
                    exact.append((lhs, rhs))
                elif err <= MAX_ERROR and k == 1:
                    approx.append((lhs, rhs, err))
    print(f"Rows: {len(rows)}\n\n--- Exact minimal FDs ---")
    for lhs, rhs in exact:
        print(f"{', '.join(lhs)} -> {rhs}")
    print(f"\n--- Approximate FDs (error <= {MAX_ERROR:.0%}) ---")
    for lhs, rhs, err in sorted(approx, key=lambda a: a[2]):
        print(f"{', '.join(lhs)} -> {rhs}   error {err:.2%}")


if __name__ == "__main__":
    main()
````

### `scripts/check_fds.py`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````python
"""
Functional-dependency check for the Phase 1 report (Section C).

Reads the unified metadata built by build_unified_dataset.py and checks
each candidate FD by grouping on the left-hand side and verifying the
right-hand side is constant within every group. Also runs an
injected-violation test to confirm the check catches conflicts.

    python scripts/check_fds.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "data_set", "unified", "metadata.csv")

CHECKS = [
    ("source_id -> domain", ["source_id"], ["domain"]),
    ("source_id -> license", ["source_id"], ["license"]),
    ("(source_id, original_label) -> label_id", ["source_id", "original_label"], ["label_id"]),
    ("label_id -> label_name", ["label_id"], ["label_name"]),
    ("image_id -> (path, split)", ["image_id"], ["path", "split"]),
    ("source_id -> (native_width, native_height)", ["source_id"], ["native_width", "native_height"]),
]


def check_fd(rows, lhs, rhs):
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r[c] for c in lhs), set()).add(tuple(r[c] for c in rhs))
    violations = {k: v for k, v in groups.items() if len(v) > 1}
    return len(groups), violations


def main():
    with open(META, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Rows: {len(rows)}\n")
    for name, lhs, rhs in CHECKS:
        n, v = check_fd(rows, lhs, rhs)
        status = "HOLDS" if not v else f"VIOLATED in {len(v)} group(s), e.g. {next(iter(v.items()))}"
        print(f"{name}: {n} groups, {status}")

    print("\n--- Injected-violation test ---")
    bad = dict(rows[0], label_id="999")
    _, v = check_fd(rows + [bad], ["source_id", "original_label"], ["label_id"])
    print(f"1 injected row -> {len(v)} violating group(s): {v}")


if __name__ == "__main__":
    main()
````

### `data_set/fd_log.txt`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````text
Rows: 18500

source_id -> domain: 4 groups, HOLDS
source_id -> license: 4 groups, HOLDS
(source_id, original_label) -> label_id: 22 groups, HOLDS
label_id -> label_name: 10 groups, HOLDS
image_id -> (path, split): 18500 groups, HOLDS
source_id -> (native_width, native_height): 4 groups, HOLDS

--- Injected-violation test ---
1 injected row -> 1 violating group(s): {('github_handdrawn', 'ellipse'): {('1',), ('999',)}}
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

An injected wrong `label_id` was caught by `scripts/check_fds.py` (fd_log.txt).

## Our decision

The user ruled that 'detect' means a data-quality check, so no OCR or optical recognition is used anywhere (P02). We also kept the FDs that were discovered rather than designed: `native_width -> source_id` shows that image size alone reveals the source.

## Measured effect

27 minimal exact FDs over 11 columns, with no approximate FDs under 5% error. The size shortcut is removed by resizing. No model at this stage.
