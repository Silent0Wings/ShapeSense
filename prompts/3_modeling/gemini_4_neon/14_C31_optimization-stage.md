# 3_modeling - C31: Optimization stage
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C31 (`change`, `3_modeling`)
- Owner / Proposed by: 40297573 + 40211352 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/docs/crisp_dm/README.md, ShapeSense/src/stage4_train/prep.py, ShapeSense/src/stage4_train/train.py, ShapeSense/src/stage2_augment/transform.py, ShapeSense/src/common/hashing.py, ShapeSense/src/stage5_eval/stats.py, ShapeSense/tests/stage4/test_prep.py, ShapeSense/docs/crisp_dm/iteration_log.json

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
A 60-epoch trial takes 5 to 7.5 minutes and image preparation runs on one core. Plan an optimization stage inside Modeling: which changes to try, how to measure each, and how to prove the results do not change.

## Response
Because CRISP-DM defines six standard phases, create a named **Optimization stage inside Modeling** (`docs/crisp_dm/README.md`) rather than a seventh step. Enforce one strict rule: **an optimization is registered only after measurement shows it helps, and anything that alters numerical results or repeatability (e.g., mixed precision / AMP or relaxed `torch.use_deterministic_algorithms`) is excluded.**

### 1. Ranked optimization targets (from step-level profiling)
1. **Parallel batch preparation (`prep.py` + `sampling.step_rng`):** Profiling shows batch prep takes `226` - `376 ms` vs `~70 ms` GPU step (~80% of runtime). Move to 7 CPU worker processes (`prep_workers: 7`), `parallel_runs: 1` (preventing nested pools and VRAM stalls), `_light_children()` (eliminating PyTorch re-imports in workers), and `multiprocessing.Pool` (avoiding Windows `ProcessPoolExecutor` invalid-handle crashes).
2. **Process-wide shared worker pool (`prep.py#_shared_pool`):** Keep one worker pool alive across trials in `search.py` and `sweep.py` instead of respawning per trial (`~16 s` of `~220 s` per trial was pool setup/teardown outside epochs).
3. **Cache per-image ink geometry (`src/stage2_augment/transform.py#_ink_facts`):** Real training images are augmented repeatedly; cache each stored image's ink point coordinates and thin-line flag (`~18%` of `transform` CPU time in profile).
4. **Exact GPU pixel conversion via `uint8` LUT (`train.py`):** Send `uint8` batches (`1 MB` vs `4 MB` float32) and index a 256-entry `pixel_values` lookup table built on the CPU (`to_float(np.arange(256))`). *Never* divide by `255.0` directly on GPU without checking parity first, because float division rounding differs between CPU and GPU.
5. **Remove per-step GPU synchronization & cache validation (`train.py`):** Accumulate `loss_total` and `correct_total` as device tensors and read once per epoch; pre-upload `val_images` to GPU once (`~43 ms` saved per `~3.4 s` epoch); skip writing `val_curve.png` during search trials (`save_curve=False`, `~0.57 s`/trial).
6. **Downstream shared bottlenecks & machine contention:** Speed up `common/hashing.py` (directory scans + NumPy bit count), `stage5_eval/stats.py` (blocked bootstrap matrix multiply), and audit background CPU usage (e.g., Defender / competing processes) if slow epochs still hit 99% CPU.

### 2. Measurement & equivalence proof protocol
- **Measure each change:** Record per-trial wall time, per-epoch seconds, and component timing (`loader_benchmark.json`, `train_log.csv`) before registering in `README.md`.
- **Prove zero numerical drift:**
  1. Unit equivalence tests in `tests/stage4/test_prep.py` asserting bit-identical batches across worker counts, cached `_ink_facts` invariance, and shared pool isolation across successive runs.
  2. Two full 60-epoch end-to-end reruns comparing **every logged number across all 60 epochs** (`train_loss`, `train_acc_trainmode`, `val_loss`, `val_acc`, `val_macro_f1`, `lr`, `synthetic_share`) against the baseline trials.

## Validation
Executed across commits `b3bb15d` and `534643d` by `40297573` and `40211352`, with every change audited and tested:
- **GPU `/ 255.0` catch (`F24`):** Measurement proved direct GPU division by `255` rounded **126 of 256** uint8 pixel values differently from CPU `to_float`, which would have altered results; the CPU-generated 256-entry `pixel_values` LUT in `train.py#L399` achieved 0/256 mismatches (`F24` overcome).
- **Pool audit (`F23`):** Code audit of `_shared_pool` and `BatchPool` fixed five edge-case bugs (orphan temp files, masked exceptions in `close()`, reused temp paths via `_STREAM_NUMBERS`, and half-updated `_SHARED` state on spawn failure).
- **Unit & rerun equivalence:** `tests/stage4/test_prep.py` passed (`test_batches_match_the_single_process_stream`, `test_one_pool_serves_successive_runs`, `test_cached_shape_facts_do_not_change_the_augmented_image`). Two full 60-epoch reruns with the latest code finished in **163 s** and **176 s**, matching the earlier trials identically on every logged number across all 60 epochs.

## Our decision
Registered the Optimization stage inside Modeling in `docs/crisp_dm/README.md`, applying every speed change that preserved exact numerical equivalence (`b3bb15d`, `534643d`) and explicitly excluding mixed precision and relaxed determinism.

## Measured effect
- **Per-trial runtime:** Dropped from `5` - `7.5` minutes effective (single-core prep, 2 runs at once) -> `~3.7` minutes average (`2.6` - `5` min) in the first parallel version -> `163` s and `176` s on two verified 60-epoch reruns with the latest code.
- **Measured component savings (`README.md`):** `_ink_facts` cache (~`18%` of `transform` time), shared worker pool (`~16 s` of `~220 s`/trial), GPU-cached validation (`43 ms`/`3.4 s` epoch), `uint8` LUT transfer (up to `~3 ms`/`~69 ms` step), skipped search plots (`0.57 s`/trial).
- **Zero drift:** Both verification reruns matched earlier trials identically on every logged metric across all 60 epochs.

---

## Upgraded & Expanded: Gemini 4 Neon Corpus Synthesis (`C31` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C31` (`change`)
* **Logic Depth:** **High** (registers the Optimization sub-stage inside Phase 3 Modeling; enforces zero-drift verification across `C30`, `F23`, `F24`, and feeds `C39`)
* **Risk if Wrong:** **High** (unverified GPU `/255` scalar division rounds **126 of 256** `uint8` values differently from CPU `float32`, altering every downstream weight and score)
* **Adoption Status:** **Adopted verbatim** (registered Optimization stage inside Modeling; adopted only measured, bit-exact optimizations including the 256-entry CPU-computed `uint8` $\rightarrow$ `float32` lookup table; rejected AMP and relaxed determinism).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`C31`** codifies the project's **measure-then-register** rule inside CRISP-DM Modeling: no candidate speedup is registered until empirical benchmarks prove both wall-clock gain and bit-exact metric invariance.
* Its sharpest technical catch (`F24`) proved that `"looks mathematically equivalent"` and `"is floating-point equivalent"` differ: because CUDA scalar `/ 255.0` multiplies by `reciprocal(255.0)` and diverges by 1 ULP on `126 / 256` pixel intensities, `C31` replaced GPU division with a 256-entry lookup table (`0 / 256` mismatches) and proved bit-identical convergence across all 60 epochs on two full verification reruns (`t13` at `163 s`, `t10` at `176 s`).

