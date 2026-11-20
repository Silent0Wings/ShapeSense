# 3_modeling - F23: The first shared worker pool had five bugs. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F23 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f23) · Record: [F23](../inferred_prompts.md#f23)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> What are the common pitfalls when building a persistent shared worker pool for batch preparation? Search for known issues with random seeds across workers (for example the duplicated NumPy seed in PyTorch DataLoader workers), shared memory, error propagation and clean shutdown.

## Response

### Well established

**Random seeds.**
- PyTorch seeds its own generator per worker, but not other libraries. The [DataLoader docs](https://docs.pytorch.org/docs/2.15/data.html) say "each worker will have its PyTorch seed set to `base_seed + worker_id`". Other libraries can repeat across workers, and `worker_init_fn` is the hook for seeding them.
- The well-known version of this bug: with `fork`, every worker inherits the same NumPy global state, so the augmentations come out identical ([PyTorch forum](https://discuss.pytorch.org/t/dataloader-workers-generate-the-same-random-augmentations/28830), [blog survey of affected projects](https://hn.jakechampion.name/reader/https://tanelp.github.io/posts/a-bug-that-plagues-thousands-of-open-source-ml-projects)).
- NumPy's documented fix for parallel streams is `SeedSequence.spawn`, which gives independent child streams with a negligible chance of collision. The docs warn that hand-built `[worker_id, root_seed]` seeds can collide with spawned ones if the two schemes are mixed ([NumPy parallel RNG](https://numpy.org/devdocs/reference/random/parallel.html)).

**Shared memory.**
- On Windows, a `SharedMemory` block is freed only when every handle is closed, and `unlink()` has no effect. The resource tracker that cleans up leaks is POSIX-only ([bpo-38119](https://www.python.org/pipermail/python-bugs-list/2019-September/418582.html), [bpo-41447](https://mail.python.org/pipermail/python-bugs-list/2020-July/451190.html), [shm_win_patch notes](https://github.com/amsikking/shm_win_patch)). The tracker's leak warnings also go off when cleanup was correct ([bpo-45209 fix](https://mail.python.org/pipermail/python-checkins/2021-September/172468.html)). If buffers are named, a crash can leave stale segments or files behind, and a reused name can hand a reader old data.

**Error propagation.**
- A worker that dies hangs `multiprocessing.Pool` ([bpo-22393](https://bugs.python.org/issue22393)). `ProcessPoolExecutor` raises `BrokenProcessPool` instead ([docs](https://docs.python.org/3/library/concurrent.futures.html)). Exceptions that can't be pickled can also hang a pool or hide the real error ([bpo-13751](https://mail.python.org/pipermail/python-bugs-list/2012-January/157030.html), [bpo-24900](https://mail.python.org/pipermail/python-bugs-list/2015-August/279055.html)).
- PyTorch's C++ DataLoader comment notes that when a worker crashes, "Details are lost due to multiprocessing", and suggests `num_workers=0` for a readable trace ([source](https://android.googlesource.com/platform/external/pytorch/+/39520ffec1/torch/csrc/DataLoader.cpp)). The DataLoader `timeout` argument bounds each batch wait ([docs](https://docs.pytorch.org/docs/2.15/data.html)).
- **Cleanup that hides the error.** In Python 3, an exception raised during cleanup carries the original as `__context__` ([PEP 3134](https://peps.python.org/pep-3134/)). But the new exception is the one that propagates and shows first, so a failing second cleanup can bury the real cause unless the code re-raises the original.

**Clean shutdown.**
- A child with unflushed queue items won't exit, and joining it can deadlock ([multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html)). On Windows, `spawn` re-imports the main module, so the entry point needs an `if __name__ == '__main__':` guard ([DataLoader docs](https://docs.pytorch.org/docs/2.15/data.html)). `persistent_workers=True` keeps workers alive across epochs. That is the "persistent pool" design.

### Single reports

The advice to reseed NumPy every epoch applies only to workers that are rebuilt each epoch. With persistent workers, seeding once at start-up is enough ([kiwix SO answer](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/a/67182158)). Albumentations derives its worker seeds from `torch.initial_seed()` ([docs](https://albumentations.ai/docs/4-advanced-guides/reproducibility/)).

### Reasoning (mine, not sourced)

For a pool that must give the **same** batches as a single-process stream, the seed rule is stricter than "different per worker". Each batch's random stream has to be a function of the batch index, not of which worker happens to build it. Otherwise results change with the worker count or the scheduling. On Windows with `spawn`, the forked-duplicate bug can't happen, but unseeded NumPy state is fresh in every child, which breaks reproducibility instead.

### How it applies to ShapeSense

`BatchPool` runs on Windows, with persistent workers and file-backed transfer. The literature's pitfall list covers every kind of bug the audit found: crash leftovers (temporary files and shared memory not freed), cleanup hiding the real error (exception masking), a reused file path giving stale data (stale named buffers), and a failed restart leaving a dead entry (pool liveness and `BrokenProcessPool`-style handling). The project's equivalence test against the single-process stream is the right guard for the seed pitfall.

## Validation

The record's five bugs are all well-known categories: leftover temporary files after a crash, cleanup that hides the real error, a reused file path giving a worker the wrong data, and a failed restart leaving a dead entry. They were caught in an audit before they caused harm. The literature agrees and adds nothing that contradicts it. It does flag a sixth category that the record doesn't list, seed and stream assignment. The project's bit-exact equivalence tests cover it, so it was evidently handled by design rather than found as a bug.

## Our decision

The project audited the pool, fixed all five bugs, and confirmed that the tests passed and the reruns matched exactly. The findings suggest keeping three properties under test: batch seed tied to batch index (not to worker), the original exception kept when cleanup fails, and unique file names per batch and generation. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Persistent Worker Pool Invariants & Windows Resource Semantics (`F23`)

### Metadata & Lineage

* **Entry ID / Type:** `F23` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/prep.py`, `src/stage4_train/sampling.py`, `tests/stage4/test_prep.py`

### Literature Cross-Audit of the Five `BatchPool` Bugs

| Failure Domain | Literature & CPython / PyTorch Grounding | ShapeSense Resolution & Verification |
| --- | --- | --- |
| **1. Cross-Worker RNG Determinism** | `SeedSequence.spawn` (NumPy parallel RNG docs) avoids both `fork` state duplication and ad-hoc `[worker_id, seed]` collisions. | `sampling.step_rng(seed, epoch, step)` binds PRNG state strictly to `(seed, epoch, step)`—making batch contents invariant to worker scheduling order or pool size. |
| **2. Windows File/SHM Lifecycle** | Windows lacks POSIX unlink-while-open semantics (`bpo-38119`, `bpo-41447`); active worker handles raise `PermissionError` on `os.unlink()` and recycled names serve stale segments. | Monotonic `itertools.count()` stream IDs (`shapesense_stream_<n>_`) prevent cache-key reuse; `contextlib.suppress(OSError)` makes `close()` idempotent. |
| **3. PEP 3134 Exception Masking** | Raising an exception inside `finally` chains the original error as `__context__` (PEP 3134) but propagates the cleanup error to the top, hiding the true root cause. | Guarded `os.unlink()` and atomic `_SHARED.clear()` prevent cleanup failures from shadowing training exceptions. |

