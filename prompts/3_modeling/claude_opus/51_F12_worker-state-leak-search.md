# 3_modeling - F12: The first polarity experiment gave invalid results. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F12 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f12) · Record: [F12](../inferred_prompts.md#f12)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> How can state leak between reused worker processes in Python multiprocessing (patched modules, global variables, maxtasksperchild), and what are the reproducibility best practices for experiments run through process pools?

## Response

### Well established (official documentation)

- **Pool workers are long-lived by default.** "Worker processes within a Pool typically live for the complete duration of the Pool's work queue". With the default `maxtasksperchild=None`, "worker processes will live as long as the pool" ([Python docs, multiprocessing](https://docs.python.org/3/library/multiprocessing.html)). Anything a task changes at module level in a worker (a monkey-patched function, a module global, a cached object, an RNG state) is therefore still there for the next task that lands on the same worker.
- **`maxtasksperchild` / `max_tasks_per_child` is the official way to get fresh workers.** It is "the number of tasks a worker process can complete before it will exit and be replaced with a fresh worker process" ([Python docs, multiprocessing](https://docs.python.org/3/library/multiprocessing.html)). `concurrent.futures.ProcessPoolExecutor` gained `max_tasks_per_child` in 3.11. Setting it switches the default start method to spawn, and it is incompatible with fork ([Python docs, concurrent.futures](https://docs.python.org/3.13/library/concurrent.futures.html)).
- **Under spawn, children re-import modules and do not inherit the parent's runtime state.** Spawn "starts a fresh Python interpreter process", is the default on Windows and macOS, and does not inherit unnecessary handles ([Python docs](https://docs.python.org/3/library/multiprocessing.html)). The docs warn that a global seen in a child "may not be the same as the value in the parent". Only module-level constants are safe, so resources should be passed explicitly as arguments ([Programming guidelines](https://docs.python.org/3/library/multiprocessing.html)). A patch applied in the parent after import therefore never reaches spawned workers, while a patch applied inside a worker persists in that worker.
- **The initializer runs once per worker, not once per task** ([Python docs](https://docs.python.org/3/library/multiprocessing.html)). Per-task setup belongs in the task function.
- **RNG state needs explicit seeding in every process.** PyTorch's reproducibility notes say to seed `torch`, `random` and NumPy, and to give DataLoader workers a `worker_init_fn` and a seeded `generator`. They also state that full reproducibility is not guaranteed across releases or platforms, or between CPU and GPU ([PyTorch randomness notes](https://docs.pytorch.org/docs/2.15/notes/randomness.html)).

### Single reports and bug-tracker items

- The meaning of "task" is ambiguous. For `Pool.map`, the count applies to chunks, not to individual calls ([bpo-24475 thread](https://www.python.org/pipermail/python-bugs-list/2015-June/274926.html)). So `maxtasksperchild=1` with `map` and a chunksize above 1 still runs several calls in one worker.
- `max_tasks_per_child` itself had a deadlock in which the executor could hang after a worker hit its limit with tasks still queued. The docs list it as fixed (gh-115634) ([Python docs, concurrent.futures](https://docs.python.org/3.13/library/concurrent.futures.html)).
- Test frameworks show the same failure mode: long-lived pytest-xdist workers carry module-level changes from one test to the next, and pytest-forked exists to box tests that apply leaky monkeypatches ([pytest-xdist docs](https://pytest-xdist.readthedocs.io/), [pytest-forked mirror](https://gitee.com/mirrors_pytest-dev/pytest-forked)).

### Reasoning: best practices for experiments through pools

1. Make every task self-contained: take a complete config as arguments, apply any patch or override inside the task, and undo it in a `finally`, or better, pass behaviour as a parameter rather than patching.
2. Use `maxtasksperchild=1` (with `chunksize=1` for map) for experiments where a leak would invalidate results. Spawn cost is small next to a training run.
3. Seed every RNG inside the task from (arm, seed), never from worker identity or order.
4. Add a canary: each task records its process id, the identity of the patched function, and a hash of its effective config in the result, so a leak shows up in the output.
5. Run a control: the same experiment with the patch disabled must reproduce the baseline bit for bit.

## How it applies to ShapeSense

The polarity experiment patched the image path (inverted vs standard) inside reused workers. Because workers lived for the whole pool, an inversion patch from one task could apply to a later "standard" task, mixing conditions. That is exactly the long-lived-worker behaviour the docs describe. Rerunning with one task per worker is the documented fix. The rerun's result (standard vs inverted within seed noise: A0 91.69 vs 91.93, A1 93.62 vs 93.57) is believable because each condition now starts from a fresh interpreter. For future ablations, passing the condition as a parameter and logging a config hash per result would make such a leak visible in the output rather than in odd numbers.

## Validation

The documentation agrees with the documented cause: by default a pool worker keeps module state across tasks, so a patch leaks. It agrees with the fix too: one task per worker gives a fresh process each time. It adds two cautions: with `map`, "task" means chunk, so `chunksize` must be 1 for the guarantee to hold; and `max_tasks_per_child` in `ProcessPoolExecutor` had its own deadlock bug in some versions. Nothing contradicts the record.

**Code check, 2026-11-20:** the chunk caution does not apply to the current code. Training runs go through `ProcessPoolExecutor.map` in `src/stage4_train/sweep.py`, whose `chunksize` defaults to 1, so each call is its own task. No file in `src/` sets `max_tasks_per_child` now. With `train.parallel_runs: 1` in `configs/pipeline.yaml`, runs execute one at a time in the parent process anyway.

## Our decision

The project discarded the invalid run and reran with one task per worker. The valid rerun found no effect of polarity. The findings suggest optionally passing ablation switches as task parameters instead of patches, and adding a per-result config hash as a canary. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Multiprocessing Worker State Isolation & Process-Pool Reproducibility (`F12`)

### Metadata & Lineage

* **Entry ID / Type:** `F12` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis + codebase verification)
* **Primary Artifacts:** `src/stage4_train/sweep.py`, `configs/pipeline.yaml` (`train.parallel_runs: 1`)

### Systems Mechanics of Worker State Contamination

In Python's `multiprocessing` subsystem (`Pool` and `concurrent.futures.ProcessPoolExecutor`), worker processes are persistent by default (`maxtasksperchild=None`) and survive across the entire task queue.

1. **Asymmetric State Persistence Under `spawn`:** Under Windows' mandatory `spawn` start method, child processes boot a fresh Python interpreter and re-import top-level modules rather than inheriting parent heap state. Consequently, monkey-patches applied inside the parent process *after* module import never propagate to children, whereas a monkey-patch, global variable mutation, or cached object mutated *inside* a worker task persists across all subsequent tasks routed to that worker PID.
2. **Task-Boundary Granularity & Pool Lifecycle Edge Cases:**
   * **Chunking Ambiguity (`bpo-24475`):** In `Pool.map`, `maxtasksperchild=1` governs **chunks** rather than individual items; a `chunksize > 1` still executes multiple calls inside a single worker interpreter before recycling.
   * **Executor Recycling Deadlocks (`gh-115634`):** `ProcessPoolExecutor(..., max_tasks_per_child=1)` (introduced in Python 3.11) suffered a confirmed deadlock when workers exited upon hitting their task cap while queued work remained.
   * **Initializer Scope:** Pool `initializer` hooks execute once per worker spawn rather than once per task, making per-task state isolation inside the task entrypoint mandatory.

### Application to ShapeSense Polarity Ablation & Codebase Verification

| Verification Layer | Failure Mode / Finding | ShapeSense Resolution & Grounding |
| --- | --- | --- |
| **Polarity Experiment Contamination** | Monkey-patching the image-inversion transform inside reused workers leaked inverted polarity into subsequent `"standard"` tasks within the same worker PID. | Discarded the contaminated run and re-executed with strict process isolation (one task per fresh worker); clean rerun proved polarity invariance within seed variance (`A0: 91.69` vs. `91.93`; `A1: 93.62` vs. `93.57`). |
| **Static Audit of `sweep.py`** | Evaluated whether `ProcessPoolExecutor.map` chunking or `max_tasks_per_child` bugs affect production runs. | Confirmed `sweep.py` uses default `chunksize=1` and zero `max_tasks_per_child` overrides, while `train.parallel_runs: 1` executes trials sequentially in-process. |
| **Hardening Blueprint** | Prevent future ablation leaks via architectural parameterization. | Pass experimental toggles (e.g., polarity) as explicit serializable task arguments rather than monkey-patches, and log `(os.getpid(), fn.__qualname__, effective_config_sha256)` as a canary inside every `result.json`. |

