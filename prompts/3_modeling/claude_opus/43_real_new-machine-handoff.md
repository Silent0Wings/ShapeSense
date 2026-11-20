# 3_modeling - Picking up the work on the new GPU machine

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: D04, F02
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (15:46)

> the work moved to a new machine due to better cpu gpu and ram , pickup where the work stoped and produce a clear long horizon goal prompt for me to give you

## Response 1

I'll reconstruct where the work stopped from the tracker, the uncommitted diff, memory and this machine's hardware, then write the prompt from that.

The tracker stops at the P-61 blocker: the Stage 4 rerun is meant for this machine. Next I'm checking whether this machine is ready for that, plus the handoff notes and the uncommitted fix.

The pinned `torch 2.14.1` has a CUDA 13.0 build for Windows and Python 3.12, so the original versions can stay. Now I'm writing the goal prompt into `.agents/`, next to your earlier ones.

Written for: a future Claude session running unattended on this machine.

The goal prompt is ready and your commit rule is added. I didn't run tests or training, because `.venv` still points at the old machine, so the last handoff's "338 tests pass" is unconfirmed here.

**To start it, paste this:**

```
Read .agents/goal_new_machine.md and carry out that goal.
```

**Where the work stopped:** Stage 4 failed on the two leave-one-source-out runs, because ellipse exists only in the Hand-Drawn source. You already chose the 9-class fix, and it sits uncommitted in the working tree. Stages 5 and 6 have never run, and the test split is still sealed.

**What the prompt does, in order:**
1. Rebuilds the environment with the same pinned `torch 2.14.1`, using its CUDA build, which I confirmed exists.
2. Commits the fix through the guard.
3. Proves the GPU path with short test runs, then reruns all 17 trainings on the GPU.
4. Runs the one-time test evaluation, then the report, export, demo and clean-copy rehearsal.

It also makes a few small crash fixes before the rerun, because any change to the training code after that would invalidate the runs.

**Commit rule:** it's now in a new `CLAUDE.md` (not committed yet), in my memory for this project, and in the goal prompt. The existing `.commit_guard/safe_commit.py` already does the checking, so I didn't write a new script. No commits were made this session.

**Worth knowing:**
- **Tracker is wrong in two places:** it lists `tests/stage4/test_loso_device.py` and a `train.device` config setting, and neither exists in this copy. The prompt has them recreated before any training.
- **Fewer CPU cores:** the GPU is a real gain, but this CPU has 8 cores, while the old settings were tuned for 14. The prompt sets parallel runs from a measurement here instead of keeping the old value.
- **Old results get replaced:** the rerun overwrites the 15 CPU trainings, so the prompt copies them to a separate folder first.

**Your call:** the rule is only an instruction for now, so a plain `git commit` would still go through. Do you want me to add a Claude Code hook that blocks anything except the guard?

## Prompt 2 (15:52)

> Read .agents/goal_new_machine.md and carry out that goal.

## Response 2

I'll work through the goal's phases in order, starting with Phase 0: rebuilding the environment on Python 3.12 with CUDA torch, then getting a baseline from the tests.

All pass, including a real run on the GPU. I'm removing one assertion I wrote that can't fail, then proving the tests can fail by mutating each protected behaviour.

The tree is clean and content is unchanged. Now the Phase 2 recipe-window fixes, each with its test.

The Stage 4 sweep is running on the GPU in the background, with an estimated 70 minutes for 17 trainings plus the Stage 0 to 3 re-checks. I'll pick up when it finishes. Commits so far are `ea816df`, `f5405b2` and `78cded9`, all through the guard with no attribution.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The handoff's claim that 338 tests pass was flagged as unconfirmed on the new machine until the environment was rebuilt.

## Our decision

Training moved to the RTX 3080, with every arm of one experiment on the same hardware (D04).

## Measured effect

Speed only. See C39 for measured trial times.

---

## Cross-Machine Migration, CUDA Environment & LOSO Schema Fix (`D04`, `F02`)

### Metadata & Lineage

* **Entries:** `D04` (*Standardizing all arms of an experiment on the RTX 3080 workstation*), `F02` (*LOSO Hand-Drawn 9-class fix for single-source `ellipse`*)
* **Date:** `2026-11-08` (15:46–15:52 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)
* **Commits:** `ea816df`, `f5405b2`, `78cded9` (all committed via `.commit_guard/safe_commit.py`)

### Hardware Migration & Blocker Resolution Runbook

1. **Resolving the `P-61` Leave-One-Source-Out (LOSO) Crash (`F02`):** Stage 4 had previously aborted on Hand-Drawn LOSO runs because `ellipse` exists exclusively in the Hand-Drawn source—leaving zero training examples when Hand-Drawn is held out. Committed the 9-class LOSO masking fix and recreated missing config/test artifacts (`train.device`, `tests/stage4/test_loso_device.py`) that the handoff tracker erroneously listed as present.
2. **Environment & Concurrency Recalibration (`D04`):**
   * Rebuilt Python `3.12` `.venv` with pinned `torch 2.14.1+cu130` for Windows and re-verified the full test suite from scratch rather than trusting the prior machine's `"338 tests pass"` claim.
   * Archived the 15 prior CPU-trained artifacts to an isolated directory before relaunching all 17 GPU runs (`~70 min` estimated) on the RTX 3080 so every arm in the comparison trained on identical hardware.
   * Re-measured worker concurrency for the new machine's **8-core CPU** (down from 14 cores on the previous host) and codified the zero-AI-attribution commit rule in `CLAUDE.md` and `.agents/goal_new_machine.md`.

