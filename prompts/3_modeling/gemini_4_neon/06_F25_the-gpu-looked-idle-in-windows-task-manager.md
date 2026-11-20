# 3_modeling - F25: The GPU looked idle in Windows Task Manager during training.
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: F25 (`failure`, `3_modeling`)
- Owner / Proposed by: 40253714 / gemini_4_neon + 40253714
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/train.py`, `src/stage4_train/prep.py`, `results/phase2_snapshot/loader_benchmark.json`, `results/phase2_snapshot/status4.json`, `results/phase2_snapshot/iteration_log.json`, `docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/failures.html`, commit `6b310f8`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Windows Task Manager shows the GPU idle during training. Is training really running on the RTX 3080?

Literature/search framing: Why does Windows Task Manager show the GPU as almost idle during CUDA training? Search for which engines Task Manager graphs by default (3D, copy, video vs CUDA or compute) and for the right tools to measure GPU use (nvidia-smi).

## Response
Yes - training is almost certainly running on the RTX 3080, and Windows Task Manager's default GPU panel is misleading you.

### Why Task Manager reads ~0%
By default, Task Manager's Performance tab displays four WDDM engine graphs: **3D**, **Copy**, **Video Decode**, and **Video Encode**. PyTorch CUDA kernels run on the **Compute / CUDA** engine, which is *not* graphed by default (you have to click one of the engine dropdowns and explicitly select `Cuda` or `Compute_0`, and even then WDDM polling can under-report short bursts). Meanwhile, `configs/pipeline.yaml#train.device` is set to `"cuda"`, and `resolve_device(config)` in `src/stage4_train/train.py` explicitly raises `ValueError` if `torch.cuda.is_available()` is false - so Stage 4 cannot silently fall back to CPU.

### How to verify definitively
1. **Check `nvidia-smi` live during an epoch:** Run `nvidia-smi` (or `nvidia-smi -l 1` / `nvidia-smi dmon`) in PowerShell. Confirm the `python.exe` process appears under `Processes` on GPU 0 (`NVIDIA GeForce RTX 3080 Laptop GPU`), with dedicated CUDA VRAM allocated and active `gpu` SM utilization.
2. **Inspect the Stage 4 run metadata:** Check `artifacts/stage4/<run_name>/run.json` (written by `train_one` via `runtime_id(config)` in `src/stage4_train/train.py`), which records `"device": "cuda"` and `"device_name"`.
3. **Expect pulsed (0% - 96%) rather than flat 100% utilization:** Look at `loader_benchmark.json`: one 256-image batch takes `mean_batch_ms ≈ 115.4 ms` to prepare on CPU (`prep_workers: 7` in `src/stage4_train/prep.py`), whereas the GPU forward/backward/AdamW step on `SmallCNN` (`242,250` params) takes only `mean_step_ms ≈ 18.5 ms` (`~69 ms` total overhead in early benchmarks). Thus the RTX 3080 processes each batch in a brief burst (spiking toward ~96% utilization) and then drops back toward 0% while waiting on CPU augmentation/synthetic generation for the next batch.

## Validation
- `40253714` polled `nvidia-smi` during active Iteration 3 training (`status4.json` / `run.json`), observing the training `python.exe` process attached to the RTX 3080 with matching dedicated VRAM allocation and GPU utilization swinging between `0%` and `96%` across batch arrivals.
- Cross-checked `results/phase2_snapshot/loader_benchmark.json` (`"device": "cuda"`, `mean_batch_ms: 115.41`, `mean_step_ms: 18.51`, `images_per_s: 2218.1`) and `run.json` fields (`"device": "cuda"`), confirming no CPU fallback occurred.

## Our decision
Confirmed CUDA execution on the RTX 3080 via `nvidia-smi` and run records (`F25` marked `Overcome` in `results/phase2_snapshot/iteration_log.json`), and used `nvidia-smi` rather than Task Manager's default 3D/Copy graphs for all subsequent GPU monitoring and optimization checks.

## Measured effect
- **Verified hardware execution:** `100%` of Stage 4 search and final sweep runs executed on the RTX 3080 (`device: "cuda"`), with observed SM utilization pulsing **0% - 96%** between CPU-prepared batches (`115.4 ms` batch prep vs `18.5 ms` GPU step in `loader_benchmark.json`).
- **Diagnostic impact:** Prevented wasted debugging of a non-existent CPU fallback and confirmed that CPU batch preparation (handled via `prep_workers: 7` and ink-point caching) - not GPU compute - was the pacing bottleneck.

---

## Upgraded & Expanded: Gemini 4 Neon Corpus Synthesis (`F25` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F25` (`failure`)
* **Logic Depth:** **Low** (diagnostic verification explaining `C30`/`C31`'s CPU-bound pacing)
* **Risk if Wrong:** **Low** (Task Manager graphs `3D`/`Copy`, not `Compute`; `nvidia-smi` confirms `cuda`)
* **Adoption Status:** **Adopted verbatim** (`Overcome`: confirmed RTX 3080 execution via `nvidia-smi` and run records; attributed `0%–96%` duty-cycle swings to CPU batch-preparation pacing).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`F25`** explains why Windows Task Manager shows `~0%` on the RTX 3080: its default 4-engine view graphs `3D`, `Copy`, and `Video`, omitting `Cuda`/`Compute_0`. `nvidia-smi` confirms active residency (`2,733 MiB / 8,192 MiB`), with utilization pulsing `0–96%` because CPU prep (`115.4 ms` on one core) dominates the `18.5 ms` GPU step.
* Together with **`F19`**, **`C30`**, **`C31`**, **`F22`**, and **`C39`**, this diagnosis directed optimization effort away from a phantom GPU-device bug and onto the real bottleneck: parallelizing and caching CPU batch preparation across 7 persistent `spawn` workers while preserving bit-exact reproducibility.

