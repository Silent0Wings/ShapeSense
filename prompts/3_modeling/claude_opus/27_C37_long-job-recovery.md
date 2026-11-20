# 3_modeling - C37: Long-job recovery
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C37 (`change`, `3_modeling`)
- Owner / Proposed by: 40211352 / opus_medium_5.5 + 40211352
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, prompts/3_modeling/claude_opus/10_t67-record-the-gpu-error-during-the.md, src/stage4_train/search.py, docs/crisp_dm/README.md, stages/stage_4.md, commits b81b67f, 6b310f8

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
The iteration 3 search stopped at 66 of 191 trials. The log ends with a cuDNN execution failure during a training step; it happened around the time some other programs were being closed on the machine. We relaunched by hand and it is running again, but we realised we have no written rule for this: what to check, what to write down, how to relaunch, and when to give up and investigate instead. Can you write one we can follow for every long job?

## Response
The relaunch you did was right, and the reason it was safe belongs in the rule: the search reuses any finished trial whose saved settings match exactly, so a relaunch costs only the trial that was interrupted. The danger in a crash is not lost work; it is a second copy, a half-alive process or an unrecorded failure. The rule should target those.

**Recovery procedure for a long job**

1. **Check the log.** Read the last lines and the error. Note the trial name and how many trials had finished. Leave the interrupted trial's folder alone; a trial without `result.json` is retrained anyway.
2. **Check the GPU.** Run `nvidia-smi`. Confirm the card is visible, and look for leftover Python processes still holding memory. A leftover process is the most likely cause of a second crash.
3. **Stop leftovers.** Kill every process from the crashed job, including its workers, before relaunching.
4. **Record it.** Add an entry to the iteration log: time, trial count, the error text, what else was running on the machine, and "cause not established" unless you actually established it. A guess is written as a guess.
5. **Relaunch one copy.** Exactly one, from the same config and code. Two copies would train the same pending trials twice and write to the same trial folders. Do not edit training code while it runs, because workers reload it for every trial.
6. **Watch it.** Keep the stall watcher running at its 5-minute check.
7. **Stop after repeated failures.** If the same job fails again after a clean relaunch, stop relaunching. Keep the logs and investigate: a repeated failure is a bug or a hardware problem, not bad luck, and the results are not trustworthy until it is understood.

**What the rule must not do.** It must not change any setting, seed or trial limit to get past a crash, and it must never read test data. A relaunch is valid only because it reproduces the same trials.

**For this crash.** No GPU driver error is in the system log and the card works, so record the cause as not established, with the note about programs being closed at the time.

## Validation
- `src/stage4_train/search.py` reuses a finished trial only when its settings match, "so a stopped search resumes".
- The relaunch carried the 66 finished trials over (F22 in `iteration_log.json`), and the search finished with 191 trainings plus 9 reused results.
- `docs/crisp_dm/README.md` records the stall watcher and the rule against editing code while a search runs.

## Our decision
Long-job recovery: no written rule for a job that crashed -> check the log and GPU, record it, relaunch one copy, and stop after repeated failures. A crash at 66 of 191 trials showed the gap. The exact number of failures that counts as "repeated" is not recorded.

## Measured effect
No separate measurement recorded. The crash cost only the interrupted trial: 66 finished trials carried over after the relaunch (`iteration_log.json`, F22).

---

## Crash Forensics & Idempotent Job Recovery Protocol (`C37`)

### Metadata & Lineage

* **Entry ID / Type:** `C37` (`change`, `3_modeling`)
* **Date:** `2026-11-10`
* **Owner / Proposed By:** `40211352` / `opus_medium_5.5 + 40211352` (`proposed`)
* **Linked Failure Mode:** `F22` (cuDNN execution failure at trial `66 / 191`)
* **Primary Artifacts:** `src/stage4_train/search.py`, `docs/crisp_dm/README.md`, `stages/stage_4.md`, commits `b81b67f`, `6b310f8`

### Incident Forensics & Idempotent Resume Semantics

At trial `66 / 191` of the Iteration 3 search, training aborted with a `cuDNN execution failure` coincident with desktop application closures (likely WDDM/GPU context reset). Because `run_trial` writes `result.json` atomically only upon full trial completion and `search.py` skips any trial whose canonical settings match a valid `result.json`, **66 completed trials were preserved intact** and only the in-flight trial `66` required re-execution.

### Standardized 7-Step Long-Job Recovery SOP

| Step | Action | Systems / Scientific Rationale |
| --- | --- | --- |
| **1. Log & Artifact Triage** | Inspect tail of stderr/stdout; record trial index and exception signature. | Do not delete the interrupted trial directory; absence of `result.json` triggers automatic clean overwrite. |
| **2. Device & Driver Audit** | Run `nvidia-smi` to verify GPU visibility and inspect resident allocations. | Zombie CUDA contexts from orphaned workers are the primary cause of secondary OOM/cuDNN crashes on relaunch. |
| **3. Process Tree Purge** | Terminate all residual parent and `spawn` worker PIDs. | Prevents concurrent file writes and VRAM contention. |
| **4. Epistemic Logging** | Append timestamp, trial count, verbatim error, and concurrent host activity to `iteration_log.json`. | Explicitly label root cause `"cause not established"` unless proven via system/driver logs—never record hypotheses as facts. |
| **5. Single-Instance Relaunch** | Launch **exactly one** orchestrator process from unmodified code/config. | Dual instances cause write races on identical trial paths; live code edits corrupt worker module reloads. |
| **6. Watchdog Continuity** | Re-arm the 5-minute stall watcher. | Detects silent driver/IPC deadlocks within one polling interval. |
| **7. Circuit Breaker** | Halt relaunches upon repeated failure of the same trial. | Distinguishes transient OS/GPU glitches from deterministic code bugs or hardware degradation. |

*Strict Prohibition:* Never alter hyperparameters, random seeds, or trial caps to bypass a crash, and never inspect test splits during recovery.

