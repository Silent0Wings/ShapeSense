# 3_modeling - F19: The first launch of the validation experiments crashed. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F19 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f19) · Record: [F19](../inferred_prompts.md#f19)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> What causes 'invalid handle' errors in Python's concurrent.futures.ProcessPoolExecutor on Windows, where processes start with the spawn method and workers are started on demand as jobs arrive? Search the CPython bug tracker and forum threads for known causes and fixes, and for whether multiprocessing.Pool, which starts every worker at once, avoids the problem. Our case: the error came back with no code edits during start-up.

## Response

### Well established

- **On Windows, workers are spawned and get their pipe handles through inheritance.** Spawn "starts a fresh Python interpreter process" and does not inherit unneeded handles. It is the default on Windows ([Python docs, multiprocessing](https://docs.python.org/3/library/multiprocessing.html)). In a CPython bug report, the mechanism is described as setting up an inheritable pipe handle and passing it on the command line. Anything that breaks that handover produces "invalid handle" or "access denied" in the child ([bpo-35797](https://bugs.python.org/issue35797)).
- **ProcessPoolExecutor spawns workers on demand since the bpo-39207 change.** The fix "Spawn workers on demand in ProcessPoolExecutor" (GH-19453, April 2020, targeted at 3.9) makes `submit()` start a new process only when no idle worker exists and the count is below `max_workers`. Idle workers are reused ([bpo-39207](https://bugs.python.org/issue39207), [commit message](https://www.python.org/pipermail/python-checkins/2020-April/165541.html)). So on Windows, worker processes are created **while** the executor's management thread is running and jobs are flowing, not once at start-up.
- **On-demand spawning has already caused one confirmed regression.** With the fork method it deadlocked because "os.fork() is unsafe to use in any process with threads", and the fix reverted on-demand spawning for fork only, in 3.9 to 3.11 ([gh-90622](https://github.com/python/cpython/issues/90622)). Spawn and forkserver keep on-demand behaviour, which a maintainer described as avoiding that particular deadlock.
- **A worker dying abruptly breaks the whole pool.** Since 3.3, `BrokenProcessPool` is raised for every pending job when any worker ends uncleanly ([Python docs, concurrent.futures](https://docs.python.org/3.13/library/concurrent.futures.html)).

### Single reports (known Windows causes of WinError 6 near pools)

- **venv launcher (fixed):** in a venv, `python.exe` is a redirector that forwards the command line but not the handle table, so children got invalid handles. This was a regression in 3.7.2, fixed by PR 11676 ([bpo-35797](https://bugs.python.org/issue35797)).
- **Pipe inheritance regression in 3.13 (open):** passing an inheritable pipe descriptor to a child fails with "[WinError 6] the handle is invalid" on 3.13, while the same code works on 3.12. A core developer blames the C runtime's emulation of POSIX file descriptors on Windows ([gh-133506](https://github.com/python/cpython/issues/133506)). That report uses `os.spawnl`, not multiprocessing.
- **Handles closed by another thread:** a third-party pull request traces a worker's WinError 6 at `self._sem.release()` in `multiprocessing/queues.py`, followed by `BrokenProcessPool`, to the `platform` module's WMI queries timing out under CPU load and closing an unrelated handle ([chunkhound PR 526](https://github.com/chunkhound/chunkhound/pull/526)). The related CPython issue confirms a race in `_wmi` under load, fixed by gh-134313 for 3.13 and 3.14. I could not confirm a 3.12 backport, and the CPython issue itself does not describe closing arbitrary handles ([gh-130727](https://github.com/python/cpython/issues/130727)).
- **joblib/loky** reported a WinError 6 in a queue `get` that led to `BrokenProcessPool` on Python 3.7, fixed in joblib 0.14.0 ([lightrun summary of the joblib issue](https://lightrun.com/answers/joblib-joblib-python-37-windows-parallelisation-does-not-work)). This is a secondary page.

### What I could not find

No CPython issue says that **on-demand spawning with the spawn method** causes invalid-handle errors on Windows. Nor did I find evidence that `multiprocessing.Pool` is immune. Pool also passes handles to spawned children, and it re-spawns workers when `maxtasksperchild` is set. The evidence on this point is thin.

### Reasoning

The pattern "comes back with no code edits, during start-up" points to a race in the handle handover rather than a code-change problem. On-demand spawning moves process creation into the window where other threads are busy: the executor's management and queue-feeder threads, plus any threads in the training code, such as CUDA or WMI-backed `platform` calls under heavy CPU load. Any handle closed or recycled during that window breaks the new child's handover. Starting every worker up front (Pool, or a pool that pre-spawns all workers before submitting work) shrinks that window to a single quiet moment. This explains why the replacement looks stable, but it is a mitigation, not a proven fix. Turning a stalled batch into an error, as the new pool does, is the right complement, because `BrokenProcessPool` otherwise surfaces only when results are collected.

## How it applies to ShapeSense

To narrow it down: record the exact Python version (3.13 has the open pipe-inheritance regression), check whether the interpreter is a venv redirector, and grep the worker code path for `platform.*` calls (some versions run WMI queries) during start-up under load. Keep the pre-spawned pool and the stall-to-error guard. If the error recurs, the minimal reproducer is a submit storm of no-op tasks under CPU load, with and without on-demand spawning. Results are unaffected either way, because each trial is deterministic from its config. A crash costs wall time, not correctness.

## Validation

The search partly supports the documented cause. On-demand spawning on Windows is real (bpo-39207), it has already caused one confirmed regression (gh-90622, for fork), and several Windows handle races near pools are documented. But no tracker entry ties spawn-mode on-demand creation to WinError 6, so the record's attribution remains a well-motivated hypothesis. The search adds alternative causes worth ruling out: the Python version, the venv launcher and `platform`/WMI calls. It does not contradict the record. The "Partly" state fits, because the root cause is not pinned down.

## Our decision

The project relaunched at first, then replaced the on-demand pool with one that starts every worker at once and raises an error on a stalled batch. The findings suggest optionally recording the Python version and venv status with each run and checking for `platform` calls in workers, to narrow the cause if the error returns. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Windows `spawn` Handle Inheritance & `WinError 6` Races (`F19`)

### Metadata & Lineage

* **Entry ID / Type:** `F19` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/prep.py`

### Windows Process Creation & Handle Handover Internals

* **Inheritable Pipe Handover (`bpo-35797`):** On Windows (`spawn` start method), parent processes pass serialized pipe handles via command-line arguments during child interpreter bootstrap; any handle invalidated or closed concurrently raises `[WinError 6] The handle is invalid` followed by `BrokenProcessPool`.
* **On-Demand Spawning Race (`bpo-39207` / `GH-19453`):** Since Python 3.9, `concurrent.futures.ProcessPoolExecutor` spawns workers lazily inside `submit()` while queue-feeder threads, CUDA drivers, and WMI-backed `platform` queries (`gh-130727` / `gh-134313`) contend for handles under high CPU load. Additionally, Python 3.13 introduced an open POSIX-FD pipe inheritance regression (`gh-133506`).
* **Architectural Mitigation:** Pre-spawning all 7 workers up front in a persistent pool isolates handle handover to a single quiescent initialization window, while wrapping batch waits in explicit timeouts prevents silent hangs.

