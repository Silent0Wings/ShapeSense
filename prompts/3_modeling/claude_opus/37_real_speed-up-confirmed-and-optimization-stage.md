# 3_modeling - Did the speed-up work? Record it as a CRISP-DM stage

> **Edited for publication (2026-11-20):** one word for a shared commit-author trailer is written as "shared-author" throughout, because the repository's commit guard rejects the original word. Nothing else was changed.

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C31, C39
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (22:17)

> so we have improved the speed of training ?

## Response 1

Yes compared with where we started, but the latest round of optimizations isn't proven to add much yet.

| Version | Time per 60-epoch trial |
|---|---|
| Original, image preparation on one core | About 5 to 7.5 minutes effective |
| First parallel version | About 3.7 minutes on average, between 2.6 and 5 |
| Latest optimized code, one trial | 163 seconds (about 2.7 minutes), including start-up |

That one trial is a rerun of `t13`, which was among the fastest under the first parallel version. Its median epoch went from 2.46 to 2.26 seconds, about 8% faster, and the numbers came out identical. It's a single trial, and this machine's speed swings a lot with whatever else is running, so that figure isn't reliable yet.

Once the second trial finishes and the search has run for a while, I'll compare real averages. Only what's measured to help gets registered as an optimization step.

## Prompt 2 (22:18)

> add this as a stage in crsip dm

## Response 2

It's added: there's now an **Optimization stage** in the CRISP-DM record, with the before-and-after times and every change's state. It also appears on the dashboard's Changes page under Modeling.

I made it a named stage inside Modeling rather than a seventh step, because CRISP-DM has six standard steps and the dashboard is built around them. If you'd rather have it as its own step in the cycle diagram, tell me and I'll add it.

The figure for the latest code is marked as one trial only, so it isn't yet a reliable average. I'll commit this along with the code once the second exactness trial finishes.

Paused: training hasn't been relaunched and nothing is running. The work is committed as `454f23e`, through the guard, with you as the only author and no shared-author line. Nothing has been pushed.

**The speed-up is confirmed, and it's modest.** I reran two finished trials on the new code:

| Trial | Score, old and new | Median epoch, before | Median epoch, now | Time for the rerun |
|---|---|---|---|---|
| `t13` | 93.181471, identical | 2.46 s | 2.26 s | 163 s |
| `t10` | 75.642602, identical | 2.46 s | 2.27 s | 176 s |

- **Results are unchanged.** Every logged number matched across all 60 epochs, so the 16 finished trials stay.
- **The gain is about 8% per epoch** on these two trials. Against the original one-core setup, a trial is now roughly two to three times faster.
- **What I can't say yet** is how much the latest round helps under a busy machine, because these were two short reruns. A longer stretch of the search would show that.

Also done and committed: all tests pass, the two Stage 6 bugs are fixed, and the 9 repeated search runs now reuse finished results, so 191 trainings remain to count rather than 200.

I've updated [.agents/restart_iteration3.md](.agents/restart_iteration3.md) with this. Tell me when you want the search started.

Paused at your instruction. The goal isn't finished, and the search will start when you tell me to.

Still paused. Nothing is running.

Paused until you say to start.

Still paused, waiting for you.

Paused, waiting for you.

Still paused.

Still paused until you tell me to start.

Paused. Nothing is running.

No response requested.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Two finished trials were rerun on the new code and compared on every logged number.

## Our decision

We added an Optimization stage inside Modeling, where each optimization is registered once it is measured.

## Measured effect

The reruns took 163 s and 176 s, against about 5 to 7.5 min before, and matched on every logged number (C31). Later measurement: 175 trainings in about 3 h 50 min (C39).

---

## Empirical Speedup Verification & CRISP-DM Optimization Registry (`C31`, `C39`)

### Metadata & Lineage

* **Entries:** `C31` (*First parallel batch pipeline ~3.7 min/trial*), `C39` (*Post-audit optimization completing 175 trainings in ~3 h 50 min*)
* **Date:** `2026-11-09` (22:17–22:18 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)
* **Commit:** `454f23e` (passed `.commit_guard/safe_commit.py` with zero attribution lines)

### Bit-Exactness & Latency Benchmarks Across Pipeline Generations

| Trial ID | Validated Score (Old vs. New) | Median Epoch (First Parallel) | Median Epoch (Post-Audit) | Total Wall-Clock (Incl. Startup) |
| --- | --- | --- | --- | --- |
| **`t13`** | `93.181471` (bit-identical across 60 epochs) | `2.46 s` | `2.26 s` (`-8.1%`) | **`163 s`** (`2.72 min`) |
| **`t10`** | `75.642602` (bit-identical across 60 epochs) | `2.46 s` | `2.27 s` (`-7.7%`) | **`176 s`** (`2.93 min`) |

#### Architectural Progression & Process Governance

* **Three-Stage Throughput Evolution:** Single-core baseline (`5.0–7.5 min/trial`) $\rightarrow$ First parallel pool (`~3.7 min/trial`, range `2.6–5.0 min`) $\rightarrow$ Post-audit persistent pool (`163–176 s/trial`, completing **175 new trainings in `~3 h 50 min`** during Iteration 3).
* **CRISP-DM Taxonomy Integration:** Rather than altering the canonical 6-phase CRISP-DM cycle diagram, optimization experiments were registered as a formal **Optimization sub-stage inside Phase 3 (Modeling)**, enforcing a strict rule that candidate speedups enter the registry **only after empirical verification of both wall-clock gain and metric invariance**.

