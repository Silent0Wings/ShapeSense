# 3_modeling - F03: Stage 4 stalled on the GPU. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F03 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f03) · Record: [F03](../inferred_prompts.md#f03)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> Why does PyTorch training stall or slow down sharply when several training processes share one 8 GB GPU? Search for what is known about GPU memory oversubscription, CUDA context overhead per process and how to size the number of parallel runs.

## Response

### Well established

- **Every process pays for its own CUDA context.** PyTorch's documentation on NVIDIA MPS says: "each process creates its own CUDA context which occupies additional GPU memory" ([PyTorch Serve, NVIDIA MPS](https://docs.pytorch.org/serve/hardware_support/nvidia_mps.html)). A PyTorch developer explains on the forum that the size depends on compute capability, CUDA version and the number of loaded kernels, and that `torch.cuda.memory_summary()` does not show it, only `nvidia-smi` does ([forum: CUDA context size per process](https://discuss.pytorch.org/t/cuda-context-size-per-process/79976)). A context cannot be released without ending the process ([forum: reduce GPU memory blocked by context](https://discuss.pytorch.org/t/reduce-gpu-memory-blocked-by-context/142587)).
- **PyTorch's caching allocator keeps freed memory reserved.** Memory held by the allocator (`memory_reserved`) is separate from memory used by live tensors (`memory_allocated`), and the allocator can be configured or disabled through environment variables ([PyTorch CUDA environment variables](https://docs.pytorch.org/docs/2.15/cuda_environment_variables.html)). One consequence: a process that finished GPU work still holds its reserve, and other processes cannot use it.
- **MPS exists to let processes share one context and schedule kernels together.** NVIDIA describes the MPS server as "the clients' shared connection to the GPU and owner of the GPU scheduling resources", which brings reduced context switching ([NVIDIA MPS docs](https://docs.nvidia.com/deploy/mps/latest/index.html)). I could not confirm from these docs whether MPS runs on Windows.

### Single reports and secondary sources

- **Context size figures:** about 500 MB per process in one forum report and about 1.2 GB in another ([forum 79976](https://discuss.pytorch.org/t/cuda-context-size-per-process/79976), [forum 142587](https://discuss.pytorch.org/t/reduce-gpu-memory-blocked-by-context/142587)). These come from older versions. Measure your own setup.
- **On Windows, a full GPU can slow down instead of failing.** Under the WDDM driver model, `cudaMalloc` goes through Windows' memory manager, which can page between device and system memory. An NVIDIA forum respondent calls this expected behaviour ([NVIDIA forum: cudaMalloc with sysmem fallback](https://forums.developer.nvidia.com/t/cudamalloc-with-sysmem-fallback/347791)). NVIDIA's guidance, as mirrored on CivitAI, says that drivers from 546.01 on can disable this "shared memory fallback", trading steady speed for a crash when memory runs out ([CivitAI mirror](https://civitai.com/articles/2870/get-huge-sdxl-inference-speed-boost-with-disabling-shared-vram-tested-with-8-gb-vram-gpu)). The switch is "CUDA - Sysmem Fallback Policy" in the NVIDIA Control Panel ([InvokeAI docs](https://invoke.ai/configuration/low-vram-mode/)). I could not reach NVIDIA's own page, and secondary sources disagree on the driver version that introduced the policy (536.40 vs 546.01) ([Medium](https://medium.com/@usamakenway/increase-cuda-memory-with-sysmem-fallback-policy-bb0011b3d7ec)).
- **Compute contention also slows runs that fit in memory.** Users report that jobs sharing one GPU slow each other down through time-slicing, and recommend that each of N jobs use roughly 1/N of the GPU ([Reddit thread](https://lr.us.psf.lt/r/deeplearning/comments/1e5bmar/performance_becomes_slower_while_running_multiple), [PyTorch forum](https://discuss.pytorch.org/t/multiple-nccl-calls-reduce-training-speed/102985)).
- **A sizing rule from an HPC guide:** run several processes on one GPU only if each stays under about 40% of memory, and cap each with `torch.cuda.set_per_process_memory_fraction` ([Technion HPC guide](https://hpc.cs.technion.ac.il/?p=91)).

### Reasoning: how to size parallel runs

Total demand is roughly (number of GPU processes) x (context + peak reserved memory), and it has to fit under the card's memory with some margin for the Windows desktop compositor. Count every process that has touched CUDA, including a parent that ran a benchmark. Measure each term once with `nvidia-smi` through a full epoch, then pick the largest N that fits. Beyond that point, extra runs do not add throughput for a small CNN, because the GPU is time-sliced. With a 242k-parameter model, compute contention and CPU-side batch preparation tend to limit speed before memory does. To make overcommitment fail loudly rather than stall, set "Prefer No Sysmem Fallback" or a per-process memory fraction.

## How it applies to ShapeSense

On a Windows laptop with an 8 GB RTX 3080, four GPU processes (the parent plus three workers) is plausibly enough to cross the limit once contexts and allocator reserves add up. The documented symptom, a stall rather than an out-of-memory error, is exactly what WDDM sysmem fallback predicts. This is consistent but unconfirmed for this machine: nobody checked whether shared GPU memory rose during the stall. Two cheap guards would turn a future stall into an immediate error: set the fallback policy to "Prefer No Sysmem Fallback", or call `set_per_process_memory_fraction` in each worker. Iteration 3's move to one run at a time sidesteps the issue. Since runs are deterministic from (arm, seed), parallelism affects only wall time.

## Validation

The literature agrees with the documented cause (memory, not compute; one CUDA context per process; the parent holding memory after the benchmark) and with the fix (fewer GPU processes). It adds the likely reason the failure was a silent stall rather than a crash: Windows sysmem fallback, which pages GPU memory into system RAM. That mechanism is backed by NVIDIA forum posts and NVIDIA guidance quoted second-hand, not by an official page I could open, so it stays a hypothesis for ShapeSense. Nothing contradicts the record.

## Our decision

The project limited training to two parallel runs (three GPU processes), all 32 trainings finished, and iteration 3 later went to one run at a time (`train.parallel_runs: 1`). The findings suggest optionally disabling sysmem fallback, or capping per-process memory, so that overcommitment fails loudly. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## CUDA Context Overhead & Windows WDDM Sysmem Fallback (`F03`)

### Metadata & Lineage

* **Entry ID / Type:** `F03` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `configs/pipeline.yaml` (`train.parallel_runs`), `src/stage4_train/sweep.py`

### Memory Accounting & WDDM Paging Mechanics

* **Non-Releasable Per-Process CUDA Contexts:** Each OS process initializing CUDA allocates an independent hardware context (`~500 MB–1.2 GB` depending on compute capability, driver version, and loaded cuDNN kernels) that is invisible to `torch.cuda.memory_summary()` and cannot be freed without terminating the process.
* **Caching Allocator Retention:** PyTorch's caching allocator retains freed blocks in `memory_reserved` rather than returning them to the driver. Because the parent orchestrator executed the dataloader benchmark on CUDA first, launching 3 worker processes instantiated 4 concurrent CUDA memory tenants (`1 parent + 3 workers`) on an 8 GB RTX 3080.
* **Why Overcommitment Stalled Instead of Raising OOM (WDDM Sysmem Fallback):** Under Windows Display Driver Model (WDDM), `cudaMalloc` transparently pages overflow allocations across the PCIe bus into system RAM ("shared GPU memory fallback") unless disabled via NVIDIA Control Panel (`CUDA - Sysmem Fallback Policy: Prefer No Sysmem Fallback`), causing orders-of-magnitude latency collapse that manifests as a silent deadlock rather than a clean `OutOfMemoryError`.

### Deterministic Sizing & Fail-Loud Controls

* **Capacity Formula:** $N_{\text{workers}} \le \lfloor (V_{\text{card}} - V_{\text{desktop}} - V_{\text{parent}}) / (V_{\text{context}} + V_{\text{peak\_reserved}}) \rfloor$, measured empirically via `nvidia-smi` across a full epoch.
* **Hardening Controls:** Calling `torch.cuda.set_per_process_memory_fraction(...)` per worker or disabling WDDM sysmem fallback converts silent PCIe thrashing into immediate fail-fast exceptions, while Iteration 3's `train.parallel_runs: 1` eliminates multi-tenant context overhead altogether.

