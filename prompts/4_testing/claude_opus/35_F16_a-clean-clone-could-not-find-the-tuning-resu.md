# 4_testing - F16: A clean clone could not find the tuning result. ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/35_F16_a-clean-clone-could-not-find.md](../gemini_4_neon/35_F16_a-clean-clone-could-not-find.md)
- Date: 2026-11-09
- Worksheet entry: F16 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40304911 / opus_medium_5.5 + 40304911
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `run_pipeline.py`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_log.json`, `tests/stage0/test_runner.py`, `README.md`, commit `3a5a3b3`, `ShapeSense_Deployed/web/failures.html`, `ShapeSense_Deployed/web/changes.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** On a clean clone, the pipeline fails because `artifacts/` is gitignored and Stages 4 and 6 expect `artifacts/stage4/tuning_iter2/winners.json`. How do we make a fresh clone reproduce the full pipeline without rewriting the frozen Stage 4 code?

## Response ()

> **Opus 5.5:** Keep `artifacts/` untracked as a build directory and treat the frozen Iteration 2 search output as a committed source input that the runner stages into place when missing:
>
> - **Committed source of truth:** Keep the frozen tuning winners in Git at `docs/crisp_dm/iteration_2/search/winners.json`.
> - **Restore-if-absent in the runner:** In `run_pipeline.py`, add a small helper (`restore_frozen_winners`) that copies `FROZEN_WINNERS` to `artifacts/stage4/tuning_iter2/winners.json` only when the target file does not already exist. Because it runs in `run_pipeline.py` before dependency resolution, Stage 4 and Stage 6 code stay completely untouched.
> - **Do not overwrite local runs:** Guarding with `if target.is_file(): return False` ensures a re-run or local search never gets clobbered by the committed copy.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Track `artifacts/` in Git | Bloats history with checkpoints, predictions, and cached plots | Skip |
> | Point Stage 4 and Stage 6 directly at `docs/crisp_dm/` | Modifies recorded Stage 4 code after Iteration 2 closed | Skip |
> | Restore `winners.json` in `run_pipeline.py` when absent | Clean clones succeed while local runs and frozen Stage 4 code stay intact | **Do this** |
>
> Verify the mechanism with both a unit test in `tests/stage0/test_runner.py` (covering restore-when-missing and no-overwrite-when-present) and a full clean-clone rehearsal from scratch.

## Why this reading fits

Commit `3a5a3b3` implements `FROZEN_WINNERS` and `restore_frozen_winners` in `run_pipeline.py` specifically so Stage 4 code stays untouched while a fresh clone succeeds. Both `iteration_log.json` (`F16`) and the clean-clone rehearsal entry confirm this resolved the missing-artifact failure and reproduced every score on a fresh checkout.

## Validation

- Added `test_frozen_winners_restored_only_when_absent` in `tests/stage0/test_runner.py`, verifying `restore_frozen_winners` returns `True` and copies the committed file when absent, and returns `False` without overwriting an existing `winners.json`.
- Executed an end-to-end clean-clone rehearsal (`docs/crisp_dm/iteration_log.json`) running all seven stages from a fresh checkout.

## Our decision

Committed `docs/crisp_dm/iteration_2/search/winners.json` as the frozen tuning record and wired `restore_frozen_winners` into `run_pipeline.py` ahead of stage execution, leaving Stage 4 code unchanged.

## Measured effect

The clean-clone rehearsal passed all seven pipeline stages and reproduced the verdict, every robustness figure, all 40 validation scores (matching all 32 Iteration 2 GPU validation scores as well), and every results table apart from run IDs and folder paths.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`F16`)

### The boundary problem: Build Artifacts vs. Source Artifacts

`artifacts/` is gitignored (build output). But the Iteration 2 tuning winners are **frozen evidence** — they are inputs to Stages 4 and 6, and they must be identical on every clone. Committing `artifacts/` would bloat history with checkpoints and predictions. Pointing Stages 4/6 at `docs/` would modify closed-iteration code. The resolution: **a frozen artifact is committed at its canonical source path, and the runner materializes it into the build directory on demand.**

### The four required properties of `restore_frozen_winners`

1. **Idempotent** — running twice is a no-op (second call returns `False`).
2. **Non-destructive** — never overwrites an existing `winners.json` (a local search must not be clobbered by the committed copy).
3. **Positioned correctly** — runs in `run_pipeline.py` *before* dependency resolution, so Stages 4/6 never see a missing file.
4. **Code-preserving** — Stage 4 source is untouched.

The guard `if target.is_file(): return False` satisfies (1) and (2) simultaneously: presence short-circuits both restore and overwrite.

### Verification

The unit test covers restore-when-missing (`True`) and no-overwrite-when-present (`False`). The **clean-clone rehearsal** is the integration proof: all seven stages pass from a fresh checkout and reproduce all 40 Iteration 3 validation scores (plus all 32 Iteration 2 scores).

