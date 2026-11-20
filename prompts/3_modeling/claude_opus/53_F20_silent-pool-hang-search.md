# 3_modeling - F20: The 108-trial experiment run hung silently after 6 trials. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F20 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f20) · Record: [F20](../inferred_prompts.md#f20)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why can a Python multiprocessing pool hang silently, with workers waiting for work and the parent waiting for results? Search for known causes (a worker dying, a pickling failure, deadlocks after fork or spawn) and for how long jobs detect stalls (timeouts, watchdogs, faulthandler).

## Response

### Well established

- **A dead worker hangs `multiprocessing.Pool`.** The CPython tracker has had this open for years: [bpo-22393](https://bugs.python.org/issue22393), "multiprocessing.Pool shouldn't hang forever if a worker process dies unexpectedly", and the earlier [bpo-9205](https://bugs.python.org/issue9205), "Parent process hanging in multiprocessing if children terminate unexpectedly". The pool quietly replaces the dead worker, but the task it held is lost, so `map`/`apply` waits forever.
- **`concurrent.futures.ProcessPoolExecutor` is meant to fail loudly instead.** The [official docs](https://docs.python.org/3/library/concurrent.futures.html) define `BrokenProcessPool` as raised "when one of the workers of a ProcessPoolExecutor has terminated in a non-clean fashion". The 3.3 changelog quoted there says that before this, operations "would often freeze or deadlock".
- **Pickling failures on the way back are a known hang path.** Tracker reports cover a worker result that cannot be encoded ([bpo-9244](https://www.python.org/pipermail/python-bugs-list/2010-July/105702.html)), an exception whose constructor needs arguments and so cannot be unpickled ([bpo-13751](https://mail.python.org/pipermail/python-bugs-list/2012-January/157030.html)), the same thing in `ProcessPoolExecutor` ([bpo-24900](https://mail.python.org/pipermail/python-bugs-list/2015-August/279055.html)), and an argument that fails to pickle ([bpo-19425](https://www.python.org/pipermail/python-bugs-list/2013-October/220102.html)). Several were fixed, but the class of bug keeps coming back.
- **Queues can deadlock on join.** The [multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html) warn that a child that has put items on a queue "will not terminate until all buffered items have been flushed to the pipe", so joining it "may get a deadlock".
- **Fork after threads can deadlock the child.** From Python 3.12, `os.fork()` in a multi-threaded process raises a `DeprecationWarning` saying the child may deadlock, and the docs point to `spawn` or `forkserver` ([CPython docs change](https://ghproxy-9d2.pages.dev/python/cpython/pull/109773/files), [discussion](https://discuss.python.org/t/concerns-regarding-deprecation-of-fork-with-alive-threads/33555/14)). **This does not apply on Windows**, where `spawn` is the only start method.
- **Detection tools.** [`faulthandler.dump_traceback_later`](https://docs.python.org/3/library/faulthandler.html) dumps every thread's stack after a timeout using a watchdog thread, and can exit too. `faulthandler.register` is "Not available on Windows". `Future.result(timeout=)` and `as_completed(timeout=)` raise `TimeoutError` instead of waiting forever ([docs](https://docs.python.org/3/library/concurrent.futures.html)). From outside, `py-spy dump --pid` prints the live stack of every thread, and `--subprocesses` covers the workers too ([py-spy README](https://docs.rs/crate/py-spy/0.4.2/source/README.md)).

### Single reports

- PyTorch's own C++ DataLoader source says that if a worker "dies due to bus error/segfault or just hang, the main process will hang waiting for data", and that the cause is often outside PyTorch's control ([source mirror](https://android.googlesource.com/platform/external/pytorch/+/39520ffec1/torch/csrc/DataLoader.cpp)). PyTorch's answer was a `timeout` argument on the DataLoader ([docs](https://docs.pytorch.org/docs/2.15/data.html)).
- On Windows, `[WinError 6] The handle is invalid` shows up in pool pipe and semaphore code ([bpo msg336650](https://bugs.python.org/msg336650), [WebKit 226702](https://bugs.webkit.org/show_bug.cgi?id=226702)), and spawned children don't inherit the parent's handle table ([bpo-35797](https://www.python.org/pipermail/python-bugs-list/2019-January/392446.html)). I found **no** tracker report that ties WinError 6 to a later silent hang.

### Reasoning (mine, not sourced)

"Workers waiting for work, parent waiting for results" fits a task (or its result) that was lost between the processes: the worker died or failed while serializing, and the pool carried on. Seen from outside, that looks exactly like a deadlock. Without a stack dump taken during the hang, nobody can tell it apart from a CUDA or driver wait inside a worker.

### How it applies to ShapeSense

ShapeSense ran on Windows, so the fork hazards are ruled out. That leaves a dead or failed worker, a lost pickle, or a blocked IPC handle. The only one with nearby evidence is the WinError 6 handle error from F19 in the same on-demand pool, and the literature doesn't connect the two. The right defences, all documented, are: bound every wait (timeouts on results), turn a dead worker into an exception (`BrokenProcessPool` or an equivalent liveness check), and be able to read stacks during a hang (`faulthandler.dump_traceback_later` in each process, or `py-spy dump` from outside). Results don't depend on any of these, because ShapeSense already reuses the per-trial result files.

## Validation

The record says the cause was "not established". The literature agrees that this symptom has several well-documented causes and that nothing in the log tells them apart. It adds that `multiprocessing.Pool` in particular hangs by design when a worker dies (bpo-22393), which is worth knowing because the later `BatchPool` is built on `multiprocessing.Pool`. Its 600 s batch timeout is the documented mitigation for exactly that hole. Nothing found contradicts the record. The link to F19 stays a plausible guess, unproven.

## Our decision

The project stopped the job, relaunched it with the finished trials reused, added a stall watcher checked every 5 minutes for every long job, set `train.parallel_runs: 1`, and moved batch preparation to a pool that starts all its workers together and has a per-batch timeout. The findings support that set. One addition is worth considering: arm `faulthandler.dump_traceback_later` (or keep `py-spy` ready) so that the next hang is diagnosed from its stacks rather than just restarted. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Multiprocessing Deadlock Pathologies & Watchdog Forensics (`F20`)

### Metadata & Lineage

* **Entry ID / Type:** `F20` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/prep.py` (`600 s` batch timeout), 5-minute stall watcher

### Taxonomy of Silent Multiprocessing Hangs on Windows

* **Unmonitored Worker Termination (`bpo-22393`, `bpo-9205`):** Unlike `ProcessPoolExecutor` (which raises `BrokenProcessPool`), `multiprocessing.Pool` replaces dead workers silently without failing the lost in-flight task—causing `get()` / `map()` to block indefinitely.
* **Result/Exception Pickling Failures (`bpo-9244`, `bpo-13751`, `bpo-24900`):** Unpicklable exceptions (e.g., custom C-extension/CUDA errors requiring multi-argument constructors) fail inside the worker's result-serialization loop, dropping the response while the parent blocks forever.
* **Unflushed Pipe Buffer Join Deadlocks:** Child processes holding unconsumed items in OS pipe buffers cannot exit cleanly on `join()`.

### Defense-in-Depth Instrumentation

* **Implemented Controls:** Bounded `600 s` batch retrieval timeout inside `BatchPool`, persistent pre-spawned pool, `train.parallel_runs: 1`, and external 5-minute progress watchdogs.
* **Recommended Diagnostic Upgrade:** Arm `faulthandler.dump_traceback_later(timeout, repeat=True)` inside parent and worker processes (Windows-compatible, unlike `faulthandler.register`) or attach `py-spy dump --subprocesses --pid <PID>` on stall detection to capture live C/Python call stacks before restarting.

