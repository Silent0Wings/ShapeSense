# 3_modeling - F23: The first shared worker pool had five bugs. 

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [36_real_complexity-diagram-and-code-only-audit.md](36_real_complexity-diagram-and-code-only-audit.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Worksheet entry: F23 (`failure`, `3_modeling`)
- Owner / Proposed by: `40211352` / `opus_medium_5.5`
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `ShapeSense/src/stage4_train/prep.py`, `ShapeSense/src/stage4_train/train.py`, `ShapeSense/src/stage4_train/sampling.py`, `ShapeSense/tests/stage4/test_prep.py`, `ShapeSense/docs/crisp_dm/iteration_log.json`, `ShapeSense/docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/failures.html`, `ShapeSense_Deployed/web/stage4.html`, commits `534643d`, `6b310f8`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Before we run the search on the new persistent shared worker pool (`BatchPool` in `src/stage4_train/prep.py` from `534643d`), audit it for lifecycle and concurrency bugs: temp-file leaks on crashes, cleanup masking errors, stale worker caches from reused paths, failed pool restarts, and cross-worker RNG duplication.

## Response ()

> **Opus 5.5:** Your per-step RNG design in `sampling.step_rng(seed, epoch, step)` is safe against the classic duplicated-NumPy-seed bug because every `(seed, epoch, step)` builds an independent `PCG64` generator via `SeedSequence`. However, the shared `BatchPool` and its `train_one` caller have **five concrete lifecycle and caching bugs** that will bite on Windows or during crashes:
>
> | Bug | Failure mode | Fix |
> |---|---|---|
> | 1. Unprotected epoch loop in `train_one` | An exception mid-training skips `batches.close()`, leaking temp stream `.pkl` files | Wrap the training loop in `try...finally` closing `pretrain_batches` and `batches` |
> | 2. `os.unlink(self.path)` unguarded in `close()` | On Windows a worker may still hold the `.pkl` open after a crash, raising `PermissionError` in `finally` and hiding the real training error (and breaking repeat `close()`) | Wrap `os.unlink(self.path)` in `with suppress(OSError):` so `close()` is idempotent |
> | 3. Cache key on temp path without unique sequence | `_load_stream(path)` caches `_CHILD["path"]`; if `mkstemp` reuses a unlinked path, persistent workers run the old stream/transform | Add a monotonic `itertools.count()` counter (`_STREAM_NUMBERS`) to the temp prefix (`shapesense_stream_<n>_`) |
> | 4. Partial state on failed `_shared_pool` restart | If terminating `old` or spawning the new `Pool` raises, `_SHARED` still holds a dead pool entry | Pop `old` and call `_SHARED.clear()` before terminating/spawning; call `_SHARED.update(...)` only after success |
> | 5. Leak in `BatchPool.__init__` on `pickle.dump` failure | If pickling `(bare, config)` fails after `mkstemp`, `self.path` is never unlinked | Wrap `os.fdopen` / `pickle.dump` in `try...except BaseException: self.close(); raise` |
>
> Fix all five in `src/stage4_train/prep.py` and `src/stage4_train/train.py` before launching the search, and add a test proving one shared pool serves successive runs (`B` then `A1`) with byte-identical batches to the single-process `BatchStream`.

## Why this reading fits

Commit `534643d` explicitly noted *"Written and reviewed by reading only: not yet run or tested"* when introducing the process-wide `_SHARED` pool and temp-file stream handoff in `src/stage4_train/prep.py`. Auditing that code before the live search exposed the exact five Windows/crash edge cases documented in `docs/crisp_dm/iteration_log.json` (`F23`) and fixed directly in `prep.py` and `train.py`.

## Validation

`tests/stage4/test_prep.py` covers `BatchPool` parity and reuse (`test_batches_match_the_single_process_stream`, `test_one_pool_serves_successive_runs`, `test_each_step_has_its_own_repeatable_generator`, `test_a_step_does_not_depend_on_the_steps_before_it`). As recorded in `docs/crisp_dm/iteration_log.json` and `docs/crisp_dm/README.md`, tests passed and two reruns on the updated pool matched earlier trials identically on every logged metric across all 60 epochs.

## Our decision

All five bugs were fixed in `src/stage4_train/prep.py` and `src/stage4_train/train.py` before launching the search (`F23` marked `Overcome` in `docs/crisp_dm/iteration_log.json`), keeping one persistent 7-worker `spawn` pool per process with monotonic stream IDs and safe cleanup.

## Measured effect

Zero temp-file corruption or masked errors occurred across the `191`-trial Iteration 3 search (`175` new trainings in about `3 hours 50 minutes`), per-trial duration dropped from `~3.7 minutes` (`220 s`) to `163 s` and `176 s` on the two exact-match verification reruns (saving the `16 s` per-trial pool startup overhead), and every validation number reproduced identically.

## Deeper detail: why the five bugs matter

| Bug | Why it matters | Why the fix works |
|---|---|---|
| 1. Unprotected epoch loop | Temp file leak | `try...finally` guarantees cleanup |
| 2. Unguarded `os.unlink` | Masks real error | `suppress(OSError)` makes it idempotent |
| 3. Cache key on temp path | Stale worker cache | Monotonic counter prevents reuse |
| 4. Partial state on restart | Dead pool entry | Clear before, update after |
| 5. Leak on `pickle.dump` failure | Temp file leak | `try...except` closes on failure |

- **Why these bugs matter:** they're real lifecycle/concurrency bugs that bite on Windows or during crashes.
- **Why the fixes work:** they're standard patterns for each failure mode.
- **Why this is a good audit:** it's thorough and actionable.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| T62 (optimize pipeline) | F23 | F23 is the audit, T62 is the optimization |
| F20 (108-trial hang) | F23 | F20 is related (pool issues) |
| C35 (augmentation speed) | F23 | C35 is related (pool caching) |

- **Why this matters:** F23 is the audit that found the five bugs, building on T62, F20, and C35.

## Notes on the log

- **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repo records.
- **The five bugs are real.** They're lifecycle/concurrency bugs.
- **The fixes are standard patterns.** They work.
- **Cross-reference to T62, F20, C35:** F23 builds on all three.

---

## Multiprocessing Lifecycle, IPC & Windows `spawn` Audit (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `F23` (`failure`, `3_modeling` — marked `Overcome`)
* **Date:** `2026-11-10`
* **Owner / Proposed By:** `40211352` / `opus_medium_5.5` (`winning-decision`, 70% calibration tier)
* **Primary Artifacts:** `src/stage4_train/prep.py`, `src/stage4_train/train.py`, `src/stage4_train/sampling.py`, `tests/stage4/test_prep.py`, commits `534643d`, `6b310f8`

### Architectural Context

To eliminate the `~16 s` per-trial overhead of tearing down and respawning multiprocessing workers across a 191-trial hyperparameter search, commit `534643d` introduced a process-wide persistent `BatchPool` (`_SHARED`) in `src/stage4_train/prep.py`. Stream metadata (`bare` dataset references and arm transform configurations) was serialized to a temporary `.pkl` file via `tempfile.mkstemp` so persistent `spawn` workers could lazily load and cache stream state across batches.

Because commit `534643d` was written via static inspection without live execution, a pre-flight concurrency and failure-mode audit identified **five critical lifecycle defects** on Windows (`spawn` start method + mandatory file locks) and crash recovery paths.

### Deep-Dive Failure Mode Matrix & Remediations

| # | Component & Defect | Concurrency / OS Failure Mechanism | Deterministic Remediation |
| --- | --- | --- | --- |
| **1** | **Unprotected Training Loop (`train.py`)** | Exceptions raised mid-epoch bypass `batches.close()` and `pretrain_batches.close()`, leaking temporary `.pkl` artifacts on disk. | Wrapped training execution inside a strict `try ... finally` block guaranteeing deterministic teardown of both stream handles. |
| **2** | **Unguarded `os.unlink(self.path)` (`prep.py`)** | Under Windows file-locking semantics, if a worker crashes or lags while reading `self.path`, `os.unlink()` raises `PermissionError` inside `finally`, **masking the root training exception** and breaking idempotency on subsequent `close()` calls. | Wrapped `os.unlink(self.path)` in `contextlib.suppress(OSError)`, ensuring `close()` is strictly idempotent and never shadows upstream tracebacks. |
| **3** | **Non-Monotonic Cache Key Collision (`prep.py`)** | Persistent workers memoized stream state keyed solely on `_CHILD["path"]`. If the OS recycled a previously unlinked `mkstemp` filename, workers silently served **stale stream/augmentation state** from a prior arm. | Introduced a module-level monotonic `itertools.count()` sequence (`_STREAM_NUMBERS`) embedded into the file prefix (`shapesense_stream_<n>_`), guaranteeing globally unique cache keys per process lifetime. |
| **4** | **Non-Atomic `_SHARED` Pool Restart (`prep.py`)** | During `_shared_pool` reconfiguration, if `old.terminate()` or `Pool(...)` raised an exception, `_SHARED` retained stale/dead pool references, poisoning all subsequent trials in the sweep. | Implemented atomic state transition: pop `old` and invoke `_SHARED.clear()` *prior* to termination/spawning; call `_SHARED.update(...)` only after the new pool initializes cleanly. |
| **5** | **Constructor Leak on Serialization Failure (`prep.py`)** | In `BatchPool.__init__`, if `os.fdopen` or `pickle.dump((bare, config))` failed after `mkstemp` allocated the file descriptor/path, `self.path` leaked permanently. | Guarded descriptor wrapping and pickling in `try ... except BaseException: self.close(); raise`. |

#### Verification of Step-Level RNG Independence (`sampling.py`)

The audit confirmed that cross-worker RNG duplication was already prevented: `sampling.step_rng(seed, epoch, step)` derives an independent `numpy.random.PCG64` bit generator per `(seed, epoch, step)` tuple via `np.random.SeedSequence`. Consequently, batch composition and stochastic augmentations are invariant to worker scheduling order or pool reuse.

### Empirical Verification & Throughput Impact

* **Regression Suite (`tests/stage4/test_prep.py`):** Added `test_batches_match_the_single_process_stream`, `test_one_pool_serves_successive_runs` (verifying `B` $\rightarrow$ `A1` transition parity), `test_each_step_has_its_own_repeatable_generator`, and `test_a_step_does_not_depend_on_the_steps_before_it`.
* **Production Search Performance:** Across **191 total trials** (`175` new trainings completed in `~3 h 50 m`), zero file-locking exceptions or cache collisions occurred. Per-trial wall-clock time dropped from `~220 s` (`3.7 min`) to `163 s–176 s` (`~25%` latency reduction), with two verification reruns reproducing **bit-identical metrics across all 60 epochs**.

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |


