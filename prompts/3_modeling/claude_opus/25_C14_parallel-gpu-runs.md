# 3_modeling - C14: Parallel GPU runs 
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: C14 (`change`, `3_modeling`)
- Owner / Proposed by: 40248536 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, prompts/3_modeling/claude_opus/03_t20-run-three-trainings-at-once-then.md, configs/pipeline.yaml, src/stage4_train/sweep.py, src/stage4_train/run.py, src/stage4_train/train.py, commits a77ebe7, 45f7fe0

> ** from repo, not a saved chat:** No export of the original Claude Opus chat exists. The user prompt and the response below are written from the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
We moved Stage 4 to the RTX 3080 laptop and set three trainings to run at once to get through the sweep faster. After the loader benchmark the sweep started and then just sat there: the GPU memory is full (8 GB) and no run is making progress. How many parallel runs actually fit, and can we make that a setting in `configs/pipeline.yaml` instead of a number in the code? We cannot let it change any result.

## Response
**Why three did not fit.** Count GPU processes, not workers. Stage 4 runs the loader benchmark in the parent process first, and the parent keeps its GPU memory afterwards. With three run workers that is four processes holding CUDA memory on an 8 GB card, each with its own CUDA context, model, optimiser state and batches. Once the card is full, the runs do not fail cleanly; they stall waiting for memory. So "three workers" was really four GPU tenants.

**How many fit.** I would set two. That gives three GPU processes counting the parent, which is one fewer than the setup that stalled. I would not try to squeeze the number from a memory estimate: the safe value is the largest one you have watched run through a full epoch without a stall, and two is the obvious step down from the value that failed.

**Make it a setting.**
- Add `train.parallel_runs` to `configs/pipeline.yaml`, with a comment that records why: the 8 GB card, the parent holding memory after the benchmark, and the date of the stall.
- `run_specs` in `src/stage4_train/sweep.py` reads it: one at a time when it is 1 or there is only one job, otherwise a pool of `min(parallel_runs, len(specs))` workers.
- Write the value into the Stage 4 status file, so every run records how it was scheduled.

**Why it cannot change results.** Each job carries its own arm and seed, and every source of randomness is derived from them inside the job. Running two at a time or one at a time therefore produces the same model for the same (arm, seed). Keep `parallel_runs` out of the recipe fingerprint, so changing it does not force a retrain of finished runs, and keep the step budget fixed at 49 per epoch for every arm.

| Setting | GPU processes | Risk |
|---|---|---|
| 3 workers | 4 | Stalled on 8 GB |
| 2 workers | 3 | Recommended |
| 1 worker | 2 | Safe, slowest |

## Validation
- `configs/pipeline.yaml` documents the cause: "the parent keeps GPU memory after the benchmark, so 3 workers (4 GPU processes) filled the VRAM and stalled (2026-11-08); each run stays deterministic from (arm, seed)".
- `src/stage4_train/sweep.py` `run_specs` uses `train.parallel_runs`, and `src/stage4_train/run.py` records it in the stage status.
- `src/stage4_train/train.py` lists `parallel_runs` in `RECIPE_TRAIN_KEYS_IGNORED`, so the setting does not invalidate finished runs.

## Our decision
Parallel GPU runs: more workers than the GPU could hold -> at most two (`train.parallel_runs: 2`), because Stage 4 stalled on 8 GB of GPU memory. In iteration 3 the value moved to 1, so the batch-preparation pools are not nested (`configs/pipeline.yaml`).

## Measured effect
No separate measurement recorded. F03 (Stage 4 stalled on the GPU) is recorded as Overcome (`iteration_log.json`).

---

## Execution Concurrency & CUDA Memory Governance (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `C14` (`change`, `3_modeling`)
* **Date:** `2026-11-08`
* **Owner / Proposed By:** `40248536` / `opus_medium_5.5` (`proposed`)
* **Linked Failure Mode:** `F03` (*Stage 4 stalled on the GPU* — marked `Overcome` in `iteration_log.json`)
* **Primary Artifacts:** `configs/pipeline.yaml`, `src/stage4_train/sweep.py`, `src/stage4_train/run.py`, `src/stage4_train/train.py`, commits `a77ebe7`, `45f7fe0`

### Problem Statement & Systems Failure Analysis

During the migration of Stage 4 execution to an NVIDIA RTX 3080 Laptop GPU (8 GB GDDR6 VRAM), setting worker concurrency to 3 caused an immediate post-benchmark deadlock.

#### Root Cause: Unaccounted Parent CUDA Context & WDDM/Linux Driver Contention

1. **The `N + 1` Tenant Fallacy:** Stage 4 executes a dataloader throughput benchmark directly inside the **parent orchestrator process** prior to spawning training jobs. Upon benchmark completion, PyTorch's caching allocator retains its primary CUDA context, cuDNN workspace handles, and pinned host-to-device buffers rather than releasing them back to the OS driver.
2. **VRAM Footprint Multiplication:** Launching `N = 3` training workers instantiated **4 concurrent CUDA contexts** (`1 parent + 3 workers`), each maintaining independent model parameters, Adam/optimizer momentum states, activation graphs, and 256-image batch tensors on an 8 GB physical boundary.
3. **Silent Thrashing Over Hard OOM:** Rather than raising a deterministic `torch.cuda.OutOfMemoryError`, unified memory paging / driver-level context switching stalled kernel scheduling entirely, halting forward/backward progression across all workers.

### Architectural Resolution & Determinism Guarantees

#### 1. Concurrency Cap & Configuration Externalization

* **`configs/pipeline.yaml`:** Introduced `train.parallel_runs: 2` (capping total GPU tenants at `1 parent + 2 workers = 3`), accompanied by inline documentation recording the 8 GB hardware ceiling, parent context retention, and the `2026-11-08` incident.
* **Pool Dispatch Logic (`src/stage4_train/sweep.py`):** Updated `run_specs` to evaluate `train.parallel_runs` dynamically:
  * Executes sequentially in-process when `parallel_runs == 1` or `len(specs) == 1` (eliminating IPC/spawn overhead).
  * Instantiates a bounded worker pool of size `min(parallel_runs, len(specs))` otherwise.
* **Observability (`src/stage4_train/run.py`):** Serialized the active `parallel_runs` value into Stage 4's runtime status JSON (`stage4_status.json`) for auditability.

#### 2. Fingerprint Isolation & Numerical Invariance

To guarantee that execution topology cannot perturb model weights or trigger redundant retraining:

* **Deterministic Isolation:** Every `(arm, seed)` job initializes its own PRNG state (`SeedSequence`) and executes a fixed **49-step epoch budget**, ensuring zero cross-worker state leakage.
* **Cache Invalidation Immunity:** Added `parallel_runs` to `RECIPE_TRAIN_KEYS_IGNORED` in `src/stage4_train/train.py`, decoupling scheduling concurrency from the cryptographic recipe fingerprint.

| `train.parallel_runs` | Active CUDA Contexts (`N + 1`) | VRAM & Scheduling Behavior | Execution Profile |
| --- | --- | --- | --- |
| **`3`** | `4` (`1 parent + 3 workers`) | **❌ Stalled:** Exceeds 8 GB VRAM; silent driver/paging deadlock | Non-terminating |
| **`2`** | `3` (`1 parent + 2 workers`) | **✅ Stable:** Fits within 8 GB envelope with headroom | Optimal for Iteration 2 |
| **`1`** | `2` (`1 parent + 1 worker`) | **✅ Conservative:** Lowest VRAM pressure; avoids nested pools | Adopted in Iteration 3 (`F23` synergy) |

### Cross-Iteration Evolution

While `train.parallel_runs: 2` resolved `F03` in Iteration 2, Iteration 3 reduced `train.parallel_runs` to `1` so that Stage 4 could dedicate a single persistent **7-worker `spawn` batch-preparation pool** (`BatchPool`) without process-nesting contention (`2 * 7` workers oversubscribing CPU cores).

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |

