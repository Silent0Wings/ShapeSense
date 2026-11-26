# 3_modeling - F19: The first launch of the validation experiments crashed.
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: F19 (`failure`, `3_modeling`)
- Owner / Proposed by: 40297573 / 40297573
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `src/stage4_train/prep.py`, `src/stage4_train/sweep.py`, `src/stage4_train/experiments.py`, `results/phase2_snapshot/iteration_log.json`, `docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/failures.html`, commit `6b310f8`


## Prompt
The validation experiments crash at launch with an invalid-handle error from the worker pool on Windows. What is the cause, and how do we make the pool reliable?

Literature/search framing: What causes 'invalid handle' errors in Python's concurrent.futures.ProcessPoolExecutor on Windows, where processes start with the spawn method and workers are started on demand as jobs arrive? Search the CPython bug tracker and forum threads for known causes and fixes, and for whether multiprocessing.Pool, which starts every worker at once, avoids the problem. Our case: the error came back with no code edits during start-up.

## Response
On Windows, `concurrent.futures.ProcessPoolExecutor` uses the `spawn` start method and initializes worker processes **lazily on demand** as tasks are submitted (`_adjust_process_count` / `ProcessPoolExecutor` call queue), rather than spawning all workers eagerly during `__init__`. Each newly spawned interpreter communicates over inherited OS pipe/event handles (`_winapi` / `CreateProcess` handle duplication). When multiple workers spawn concurrently while the parent process is rapidly submitting jobs or tearing down handles, Windows handle duplication can fail with `OSError: [WinError 6] The handle is invalid` (or `BrokenProcessPool`).

A common contributing trigger on Windows is modifying or saving Python modules while `spawn` workers are still starting up: because each lazily spawned worker re-imports `__main__` and the target module from disk, any mid-startup edit can desynchronize pickled callables or interrupt worker initialization and leave invalid pipe handles.

To get the validation experiments running immediately and stabilize `ProcessPoolExecutor`:
1. **Eliminate concurrent edits and relaunch:** Freeze all edits to `src/stage4_train/` before launch, clear any stale Python processes, and relaunch the experiment runner cleanly.
2. **Stagger or cap `ProcessPoolExecutor` concurrency:** Keep `train.parallel_runs` low (e.g. `1` or `2`) and submit an initial warm-up task before fanning out the rest of the 108-trial experiment queue so worker processes do not contend on handle inheritance at `t = 0`.
3. **Note on `multiprocessing.Pool`:** `multiprocessing.get_context("spawn").Pool(workers)` spawns all worker processes upfront during pool construction rather than on demand, which avoids lazy-spawn handle races at job submission time, though switching pool implementations is unnecessary if clean relaunches without code edits resolve the crash.

## Validation
- `40297573` froze code edits and relaunched the validation experiments; the immediate relaunch completed without crashing on startup, confirming the short-term workaround.
- **Gap caught later:** Exactly as recorded in `results/phase2_snapshot/iteration_log.json` (`F19`), the identical `invalid handle` crash **returned on a subsequent launch with zero code edits during start-up**. That disproved the hypothesis that mid-startup edits were the primary cause and showed that keeping `ProcessPoolExecutor` with lazy on-demand Windows spawning was insufficient for long-run reliability.
- In the subsequent batch-preparation refactor (`src/stage4_train/prep.py`, commit `b3bb15d` / `6b310f8`), the team inspected `_shared_pool` and verified via unit/integration tests that eager `multiprocessing.get_context("spawn").Pool(workers, _init_child)` plus `results.next(timeout=BATCH_TIMEOUT_S)` (`600` s) eliminates both the lazy-spawn invalid-handle race and silent hangs.

## Our decision
Relaunched cleanly at first to unblock the 108 Iteration 3 validation experiments, while flagging Gemini 4 Neon's initial blame on code edits / keeping `ProcessPoolExecutor` as incomplete once the error recurred without edits. The team subsequently replaced the on-demand batch worker pool in `src/stage4_train/prep.py` with an eager `multiprocessing.get_context("spawn").Pool` (`_shared_pool`), paired with `_light_children()` (skipping `__main__`/PyTorch re-import in workers) and `BATCH_TIMEOUT_S = 600` to turn stalled batches into explicit errors (`F19` marked `Partly` in `iteration_log.json`).

## Measured effect
- **Initial relaunch:** Unblocked and ran the **108 validation experiment trials** (`docs/crisp_dm/iteration_3/experiments/`), though the invalid-handle crash recurred once more before the pool architecture changed.
- **After `prep.py` eager `Pool` + `_light_children`:** Pool startup dropped from **~2 minutes per trial** (`~15 s` PyTorch re-import per worker) to **a few seconds**, epoch time fell from **~20 s to 2-6 s** with `prep_workers: 7`, and **191 search trials + 40 final/LOSO trainings** completed with zero invalid-handle crashes.

---

## : Gemini 4 Neon Corpus Synthesis (`F19` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F19` (`failure`)
* **Logic Depth:** **Medium** (leads directly into `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`)
* **Risk if Wrong:** **Medium** (first workaround worked, then **recurred with zero edits** $\rightarrow$ initial hypothesis disproved)
* **Adoption Status:** **Adopted with correction** (`Partly`: initial blame on mid-startup code edits disproved by recurrence; eager `multiprocessing.get_context("spawn").Pool` + `_light_children` + `BATCH_TIMEOUT_S = 600` adopted).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`F19` (invalid handle)** is a diagnostic that was *wrong twice*: the first clean relaunch worked, so mid-startup edits were blamed; then the crash **recurred with zero edits**, disproving that hypothesis. The real fix was eager `multiprocessing.get_context("spawn").Pool` + `_light_children` + `BATCH_TIMEOUT_S = 600`. Measured: pool startup `~2 min` $\rightarrow$ a few seconds; epoch `~20 s` $\rightarrow$ `2–6 s`.
* **`C30`** is the parallel-prep design: `step_rng(seed, epoch, step)` so batch $k$ is bit-identical at any worker count; `_light_children` to avoid PyTorch re-import; `uint8` IPC ($1/4$ the `float32` payload); `pool.imap` with a 600 s timeout; `A0` kept in-process; `parallel_runs: 1`.
* **`C31`** registers the **Optimization stage inside Modeling** with a strict rule: register only measured wins; exclude anything that changes results (AMP, relaxed determinism). Its sharpest catch is the **GPU `/255` parity failure** (`126/256` uint8 mismatches $\rightarrow$ CPU-built 256-entry LUT).
* **`F22` (cuDNN halt at `66/191`)** confirms no hardware damage (no TDR entry), preserves all 66 finished trials via atomic `result.json` + settings-hash resume, and finishes the remaining 125 (`Partly`).
* **`F25`** explains why Task Manager shows `~0%`: it graphs `3D`/`Copy`, not `Compute`; `nvidia-smi` confirms CUDA, pulsing `0–96%` because CPU prep (`115.4 ms`) dominates the `18.5 ms` GPU step.
* **`C39`** closes the loop with before/after and the honest caveat: **not all** of the `3.7 min` $\rightarrow$ `92–184 s` gain is code — Defender exclusion and closing programs removed real CPU contention.

**Depth note:** `F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39` is the corpus's **longest causal chain**, demonstrating scientific discipline in admitting `F19`'s first hypothesis was wrong, rejecting AMP in `C31`, and splitting code gain from quieter-machine gain in `C39`.

