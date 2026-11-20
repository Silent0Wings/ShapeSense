# 4_testing - F28: Report Section K would have shown iteration 3 numbers. ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/38_F28_report-section-k-would-have-shown.md](../gemini_4_neon/38_F28_report-section-k-would-have-shown.md)
- Date: 2026-11-10
- Worksheet entry: F28 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 + 40253714 / opus_medium_5.5
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `phase2_report.tex`, `src/stage6_report/run.py`, `src/stage6_report/iteration2.py`, `docs/crisp_dm/iteration_2/frozen.sha256`, `tests/stage6/test_frozen_iteration2.py`, `docs/crisp_dm/iteration_log.json`, commits `d12a48e` and `4091dab`, `ShapeSense_Deployed/web/iteration2.html`, `ShapeSense_Deployed/web/failures.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Once Iteration 3 runs and overwrites `artifacts/stage5/`, will the Iteration 2 tables and numbers in report Section K silently change? Where is each Section K input actually reading from right now?

## Response ()

> **Opus 5.5:** Yes, Section K would have been overwritten by Iteration 3 numbers. Right now `phase2_report.tex` keeps Iteration 1 frozen (`docs/crisp_dm/iteration_1/...`), but Section K still reads live Stage 6 outputs regenerated from `artifacts/stage5/`:
>
> - **Where the leak happens:** `src/stage6_report/run.py` calls `write_iteration2(config, art)`, which reads live `artifacts/stage5/status.json` and overwrites `artifacts/stage6/generated/iteration2_facts.tex`, `iteration_log.tex`, `failures.tex`, and `changes.tex`. Meanwhile `phase2_report.tex` `\InputIfFileExists`s those four files from `artifacts/stage6/generated/` (and Section K's tables need to stay bound to Iteration 2 snapshots, not live `artifacts/stage5/tables/`).
> - **Why that breaks CRISP-DM provenance:** A closed iteration's report section must be immutable. Once Iteration 3 overwrites `artifacts/stage5/`, every Section K macro (`\ItwoDelta`, `\ItwoEns*`, `\ItwoVerdict`) and table would silently display Iteration 3 results under an Iteration 2 heading.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Keep regenerating Section K from `artifacts/stage5/` | Overwrites Iteration 2 numbers as soon as Iteration 3 runs | Skip |
> | Archive a copy of Iteration 2 files under `docs/crisp_dm/iteration_2/` and point Section K there | Isolates Section K permanently and preserves Iteration 2 verbatim | **Do this** |
> | Hard-code Iteration 2 numbers directly in `phase2_report.tex` | Breaks the Stage 6 traceability rule against hand-typed numbers | Skip |
>
> Freeze the full Iteration 2 evidence set (`data/`, `figures/`, `report/`, `tables/`) under `docs/crisp_dm/iteration_2/` with a SHA-256 manifest (`frozen.sha256`), point `phase2_report.tex` Section K to those frozen files, remove `write_iteration2` from `src/stage6_report/run.py`, and add a test verifying every frozen hash.

## Why this reading fits

Commit `d12a48e` implements the entire freeze: 33 Iteration 2 files (CSVs, JSONs, confusion PNGs, generated `.tex` macros, and `.tex` tables) were committed under `docs/crisp_dm/iteration_2/` with `frozen.sha256`, `phase2_report.tex` was switched from `artifacts/stage6/generated/` to `docs/crisp_dm/iteration_2/report/`, `write_iteration2` was dropped from `src/stage6_report/run.py`, and `tests/stage6/test_frozen_iteration2.py` was added. This matches `iteration_log.json` (`F28`) and the frozen `ShapeSense_Deployed/web/iteration2.html` view.

## Validation

- Added `tests/stage6/test_frozen_iteration2.py` (`test_every_frozen_file_matches_its_recorded_hash`), checking all 33 file SHA-256 digests listed in `docs/crisp_dm/iteration_2/frozen.sha256`.
- Updated `tests/stage6/test_snippets.py` and verified `phase2_report.tex` compiles and passes `check_report` traceability without fallback `--` values in Section K.

## Our decision

Froze all 33 Iteration 2 inputs, generated macros, tables, and figures under `docs/crisp_dm/iteration_2/`, repointed Section K in `phase2_report.tex` to `docs/crisp_dm/iteration_2/report/` and `docs/crisp_dm/iteration_2/tables/`, and stopped `src/stage6_report/run.py` from regenerating Iteration 2 outputs.

## Measured effect

All 33 frozen Iteration 2 files pass SHA-256 verification (`frozen.sha256`), leaving Section K and `iteration2.html` completely unchanged after Iteration 3 overwrote `artifacts/stage5/` (retaining Iteration 2's `+0.06` reused-test and `+0.08` fresh-holdout results intact).

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`F28`)

### The provenance theorem: Closed-Iteration Immutability

**Claim:** once an iteration closes, every number displayed under its heading must be a function only of that iteration's frozen snapshot, not of live mutable state.

**Proof sketch (by contradiction):** Section K reads `artifacts/stage5/status.json` live via `write_iteration2`. Iteration 3 overwrites `artifacts/stage5/`. Therefore Section K's macros (`\ItwoDelta`, etc.) change while their heading still says Iteration 2. A reader sees Iteration 3 numbers under an Iteration 2 label — a **provenance violation** and a correctness bug.

**The fix (freeze + repoint):** commit 33 Iteration 2 files under `docs/crisp_dm/iteration_2/` with `frozen.sha256`; repoint `phase2_report.tex` Section K to the frozen paths; remove `write_iteration2` from `stage6_report/run.py`. Now Section K is a function of immutable committed bytes.

| Alternative | Fails | Constraint violated |
|---|---|---|
| Keep regenerating from `artifacts/stage5/` | Provenance theorem | Immutability |
| Hard-code numbers in `.tex` | Traceability rule | No hand-typed numbers (see `F26`) |
| Freeze + repoint + hash manifest | — | **Satisfies all** |

The **hash manifest** is the verification leg: `test_every_frozen_file_matches_its_recorded_hash` checks all 33 SHA-256 digests — applying the same bit-identity discipline as `C36` to *report artifacts*: **freeze bytes, verify hashes, never regenerate closed evidence.**

