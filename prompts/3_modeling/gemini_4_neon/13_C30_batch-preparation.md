# 3_modeling - C30: Batch preparation
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C30 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 + 40248536 + 40297573 / gemini_4_neon + 40248536 + 40297573
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/src/stage4_train/prep.py, ShapeSense/src/stage4_train/sampling.py, ShapeSense/src/stage4_train/train.py, ShapeSense/configs/pipeline.yaml, ShapeSense/tests/stage4/test_prep.py, ShapeSense/docs/crisp_dm/README.md, ShapeSense/docs/crisp_dm/iteration_log.json, ShapeSense_Deployed/web/stage4.html


## Prompt
Image preparation takes about 80% of each training step. Propose a faster batch preparation (random generator per step, several processes building batches ahead of the GPU) that gives identical batches at any process count.

## Response
Profiling shows `226` - `376 ms` spent preparing each batch in Python versus `~70 ms` on the GPU - meaning CPU image preparation is ~80% of each training step, limiting augmented/synthetic epochs to ~20 seconds. Because `transform` (Stage 2) and `generate` (Stage 3) are CPU-bound Python/NumPy/OpenCV work, threads hit the GIL. Moving batch construction to parallel worker processes solves the bottleneck - provided randomness is decoupled from execution order.

### 1. Per-step independent RNG (`sampling.step_rng`)
Replace sequential per-epoch RNG state with a deterministic per-step generator in `src/stage4_train/sampling.py`:
```python
def step_rng(seed: int, epoch: int, step: int) -> np.random.Generator:
    return np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([int(seed), int(epoch), int(step)]))
    )
```
Because `(seed, epoch, step)` uniquely determines every draw in `BatchStream.raw_batch`, batch `k` is bit-identical whether computed in-process (`workers=1`) or across `4` or `7` processes.

### 2. Multi-process `BatchPool` (`src/stage4_train/prep.py`)
- **Pre-spawned `multiprocessing.Pool` (`workers = 7`):** Use `multiprocessing.get_context("spawn").Pool(workers, _init_child)` (pre-starting all 7 workers at once rather than `ProcessPoolExecutor`'s on-demand spawning, which raises invalid-handle errors on Windows), with `threadpool_limits(1)` in `_init_child` so workers do not oversubscribe BLAS/OpenMP threads.
- **`_light_children()`:** Temporarily clear `__main__.__spec__` and `__file__` around `Pool(...)` creation so spawned Windows workers do not re-import PyTorch (`~15 s` per worker).
- **Closure-free recipe handoff & `uint8` IPC:** Strip unpicklable `transform`/`generate` closures from a shallow copy of `BatchStream`, write `(bare, config)` to a uniquely numbered temp file (`shapesense_stream_<n>_*.pkl`), and let each worker lazily rebuild `build_transform(config)` / `build_generator(config)` once per stream path. Return `raw_batch` as `uint8` (`(N, 1, 64, 64)`, `1/4` the IPC payload of `float32`), streaming in order via `pool.imap` with `BATCH_TIMEOUT_S = 600` so a dead worker raises instead of hanging silently.
- **Skip `A0` & avoid nested pools:** `prepared(stream, config, workers)` keeps `A0` (`not augment and not synthetic`) and `workers <= 1` in-process, and sets `train.parallel_runs: 1` in `configs/pipeline.yaml` so one GPU run trains at a time without nested pools or 8 GB VRAM contention.

### 3. Record the RNG stream deviation
Changing from per-epoch RNG to `step_rng` changes which random sequence is drawn even though batches stay deterministic. Document this in `docs/crisp_dm/iteration_log.json` and `README.md` rather than retraining the already-completed 108 validation experiments.

## Validation
Implemented in commit `b3bb15d` by `40256377`, `40248536`, and `40297573`, and verified with `tests/stage4/test_prep.py` and multi-worker runs:
- `test_each_step_has_its_own_repeatable_generator` and `test_a_step_does_not_depend_on_the_steps_before_it` confirmed step-level RNG independence.
- `test_batches_match_the_single_process_stream` confirmed `BatchPool(..., workers=2)` produces identical `uint8` images, labels, and `is_synthetic` masks to single-process `BatchStream.epoch`.
- `test_real_images_alone_stay_in_process` confirmed `A0` bypasses the pool (`prepared(...) is stream`).
- Validation scores on 4 vs. 7 preparation workers matched identically, and epoch times dropped from ~20 s to 2-6 s (first parallel version averaged ~3.7 min per 60-epoch trial).

## Our decision
Adopted the entire architecture verbatim in `src/stage4_train/prep.py`, `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, and `configs/pipeline.yaml` (`prep_workers: 7`, `parallel_runs: 1`), and recorded the non-retraining of the 108 validation experiments as an explicit CRISP-DM deviation.

## Measured effect
- **Epoch time:** Dropped from ~20 s (1 core) to `2` - `6` s (`2.2` s in fast stretches, `3.6` s typical, `5.4` s on a busy machine), cutting 60-epoch trial runtime from `5` - `7.5` minutes effective (two runs at once) to ~`3.7` minutes average (`2.6` - `5` min) in the first parallel version.
- **Pool startup overhead:** `_light_children()` cut child worker startup from ~2 minutes/trial to a few seconds.
- **Bitwise worker invariance:** Validation scores are identical across 1, 4, and 7 preparation processes.

---

## : Gemini 4 Neon Corpus Synthesis (`C30` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C30` (`change`)
* **Logic Depth:** **High** (`step_rng` per-step PRNG + `uint8` IPC + eager `spawn` Pool + `_light_children`; resolves `F19`/`F21` and feeds `C31`/`C39`/`F22`)
* **Risk if Wrong:** **High** (cross-worker RNG drift or stale worker caches would break bitwise reproducibility across worker counts)
* **Adoption Status:** **Adopted verbatim** (`prep_workers: 7`, `parallel_runs: 1`, `step_rng(seed, epoch, step)`, `_light_children()`, `BATCH_TIMEOUT_S = 600`, with bitwise worker-count invariance verified by unit tests and empirical benchmarks).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`C30`** is the parallel batch-preparation architecture built after `F19` exposed lazy `ProcessPoolExecutor` handle races on Windows:
  1. `step_rng(seed, epoch, step)` derives an isolated `PCG64` generator via `SeedSequence` so batch $k$ is bit-identical regardless of worker count (`1`, `4`, or `7` workers).
  2. `_light_children()` prevents spawned Windows worker processes from re-importing `__main__` and PyTorch (`~2 min` startup $\rightarrow$ a few seconds).
  3. `uint8` batch IPC cuts pipe payload size by $75\%$ (`4 MB` $\rightarrow$ `1 MB` per batch), while `A0` (clean real only, `11 ms`/batch) stays in-process.
  4. Setting `train.parallel_runs: 1` avoids nested worker pools (`2 * 7` CPU core oversubscription) and provides the deterministic atomic-trial foundation that allowed `F22` (`66/191` cuDNN halt) to resume with zero lost work.

