# 3_modeling - F20: The 108-trial experiment run hung silently after 6 trials. 

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Worksheet entry: F20 (`failure`, `3_modeling`)
- Owner / Proposed by: `40256377` / `opus_medium_5.5 + 40256377`
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `ShapeSense/src/stage4_train/experiments.py`, `ShapeSense/src/stage4_train/sweep.py`, `ShapeSense/src/stage4_train/prep.py`, `ShapeSense/configs/pipeline.yaml`, `ShapeSense/docs/crisp_dm/iteration_log.json`, `ShapeSense/docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/failures.html`, `ShapeSense_Deployed/web/stage4.html`, commits `52e79e1`, `6b310f8`


## Prompt ()

> **User:** Our 108-trial validation experiment run hung silently after 6 trials with no error in the log-workers looked idle while the parent waited for results. Why can a Python multiprocessing pool stall like this, and how should we diagnose and catch hangs in long runs?

## Response ()

> **Opus 5.5:** On Windows (`spawn`), a silent hang where workers sit idle and the parent blocks forever happens whenever the IPC pipe between parent and child stops progressing without raising an exception-typically a **CUDA context / driver deadlock** when spawned workers share or contend on the GPU, or a silent C-level abort in a worker that never writes to the result queue while `pool.map` waits indefinitely.
>
> To diagnose it and keep long sweeps from sitting stuck for hours, add timeouts and stack-dump diagnostics inside `ProcessPoolExecutor` and monitor progress from outside:
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Leave `ProcessPoolExecutor.map` unmonitored | Parent blocks forever on a dead or wedged worker; zero log output | Reject |
> | Add `faulthandler.dump_traceback_later` + per-future `timeout` inside `ProcessPoolExecutor` | Surfaces the stalled stack frame and raises `TimeoutError` instead of hanging indefinitely | Adopt for pool diagnostics |
> | Pair resumable per-trial caches with an external periodic progress check | Lets us kill and relaunch a hung job without losing completed trials | Adopt for all long runs |
>
> Immediate steps:
> - **Enable `faulthandler`** (and `register(SIGBREAK)` / `dump_traceback_later`) in the parent and workers so a stuck pipe or CUDA wait prints the exact blocking line.
> - **Replace bare `pool.map` with `submit` + `as_completed(..., timeout=...)`** in `run_specs`, assuming `ProcessPoolExecutor` stays as the job runner once timeouts guard the futures.
> - **Rely on the existing per-trial `result.json` resume check** so stopping and relaunching reuses the 6 completed trials cleanly.

## Why this reading fits

Opus 5.5 gave a credible diagnosis centered on a GPU/CUDA deadlock and recommended adding `faulthandler` and future timeouts while keeping `ProcessPoolExecutor`. In practice, the exact cause of the `F20` hang was never established-it used the same on-demand `ProcessPoolExecutor` that threw Windows invalid-handle errors in `F19`, so `train.parallel_runs` was set to `1` (`configs/pipeline.yaml`), batch preparation moved to `multiprocessing.Pool` (`BatchPool` in `src/stage4_train/prep.py`, which starts all workers together and enforces `BATCH_TIMEOUT_S = 600`), and operational monitoring used an external 5-minute stall watcher rather than keeping `ProcessPoolExecutor` pools active for parallel runs.

## Validation

The hang happened after 6 trials finished at `12:11` and was discovered on a status check at `14:28` (`2 hours 17 minutes` lost). After stopping the wedged job and relaunching at `14:31` with finished-trial reuse, all `108` validation experiment trials ran to completion and were scored twice with identical numbers (`docs/crisp_dm/iteration_log.json`, commit `52e79e1`). `tests/stage4/test_prep.py` verifies `BatchPool` equivalence against the single-process stream (`docs/crisp_dm/README.md`).

## Our decision

We stopped the hung job, relaunched reusing finished trials, instituted a mandatory **5-minute stall watcher** for all long jobs (`docs/crisp_dm/README.md`), set `train.parallel_runs: 1` in `configs/pipeline.yaml`, and later replaced the on-demand `ProcessPoolExecutor` batch/run pattern with `multiprocessing.Pool` in `src/stage4_train/prep.py` (`BATCH_TIMEOUT_S = 600`) so a stalled batch raises an error immediately.

## Measured effect

The 6 completed trials were preserved, all `108` validation trials finished cleanly after relaunch (`52e79e1`), and the 5-minute stall watcher prevented any subsequent silent multi-hour stalls across the `191`-trial Iteration 3 search and final 5-seed retraining (`6b310f8`).

## Deeper detail: why the hang happened

| Cause | What it does | Why it hangs |
|---|---|---|
| CUDA context/driver deadlock | Workers contend on GPU | IPC pipe stops |
| Silent C-level abort | Worker never writes to queue | `pool.map` waits forever |

- **Why the hang happened:** the IPC pipe stopped without an exception.
- **Why this is a real problem:** it's silent and indefinite.
- **Why this is a good diagnosis:** it's plausible.

### The three options

| Option | Effect | Recommendation |
|---|---|---|
| Unmonitored | Blocks forever | Reject |
| Faulthandler + timeout | Surfaces the stall | Adopt for diagnostics |
| Resumable cache + external check | Kill and relaunch | Adopt for all long runs |

- **Why these options:** they're the standard approaches.
- **Why this is a good design:** it's robust.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F19 (invalid-handle errors) | F20 | F19 is related (pool issues) |
| F23 (five bugs) | F20 | F23 is related (pool audit) |
| T58 (record validation) | F20 | T58 is the record |
| T68 (record session bugs) | F20 | T68 is the record |

- **Why this matters:** F20 is the finding, and the fixes build on F19, F23, T58, and T68.

## Notes on the log

- **The hang happened because the IPC pipe stopped.** It's silent and indefinite.
- **The three options are standard.** They're robust.
- **Cross-reference to F19, F23, T58, T68:** F20 builds on all four.

