# 3_modeling - F25: The GPU looked idle in Windows Task Manager during training. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F25 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f25) · Record: [F25](../inferred_prompts.md#f25)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why does Windows Task Manager show the GPU as almost idle during CUDA training? Search for which engines Task Manager graphs by default (3D, copy, video vs CUDA or compute) and for the right tools to measure GPU use (nvidia-smi).

## Response

### Well established

- **Task Manager graphs engines, and it picks four.** Microsoft's DirectX team post [GPUs in the Task Manager](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/) (Steve Pronovost, July 2017) explains that a GPU exposes several independently scheduled engines. "By default, the Task Manager will pick 4 engines to be displayed", and you change one by "clicking on the engine name and choosing another one from the list". The same post says the data is collected "no matter what API is being used", with CUDA as an example. So CUDA work *is* measured, just on its own engine, which may not be among the four shown.
- **The headline percentage is the busiest engine.** The same post says Task Manager uses "the percentage utilization of the busiest engine as a representative of the overall GPU usage". It needs a WDDM 2.0 or later driver.
- **nvidia-smi measures kernel occupancy over time.** NVML, which nvidia-smi is built on, defines GPU utilization as the "percent of time over the past sample period during which one or more kernels was executing". The sample period is between 1 s and 1/6 s depending on the product. PyTorch's `torch.cuda.utilization` repeats that definition ([docs](https://docs.pytorch.org/docs/2.8/generated/torch.cuda.utilization.html)). It is a time share, not a measure of how many cores are busy.

### Single reports

- Many users see near 0% in Task Manager while nvidia-smi shows real load. The usual fix is switching a graph's dropdown to "Cuda" or "Compute_0" ([PyTorch forum 172232](https://discuss.pytorch.org/t/python-says-cuda-is-enabled-and-being-used-but-my-system-monitor-shows-otherwise/172232), [PyTorch forum 194331](https://discuss.pytorch.org/t/how-to-check-gpu-usage-when-running-pytorch/194331), [Esri thread](https://community.esri.com/t5/arcgis-pro-questions/train-deep-learning-data-100-cpu-usage-0-gpu/m-p/1036868), [MathWorks answer](https://www.mathworks.com/matlabcentral/answers/719290-gpu-usage-not-showing-in-the-task-manager)).
- A PyTorch maintainer's reply says "the Windows task manager does not show the `Compute` tab by default and you might need to enable it" ([thread 172232](https://discuss.pytorch.org/t/python-says-cuda-is-enabled-and-being-used-but-my-system-monitor-shows-otherwise/172232)). A search summary also mentioned a Windows setting that hides the CUDA entry altogether, but I couldn't find that claim on any page I opened, so I treat it as unconfirmed.
- Systems with an integrated GPU can lead people to watch the wrong GPU in Task Manager (same forum threads).

### Reasoning (mine, not sourced)

The Microsoft post doesn't say exactly which four engines are chosen by default. The forum reports suggest that on GeForce cards they are usually 3D, Copy, Video Encode and Video Decode. On that reading, the headline should still show the compute engine if it is the busiest. A low headline next to a busy CUDA engine may therefore depend on driver or scheduling settings. I couldn't settle this from sources. The practical rule is unaffected: check nvidia-smi or the CUDA/Compute engine graph, not the default 3D graph.

### Right way to measure

`nvidia-smi` (or `nvidia-smi -l 1`, or `nvidia-smi dmon`) for a time view, the process list in nvidia-smi to confirm *which* process holds the GPU, and the training run's own record of `torch.cuda.get_device_name()`. A profiler (Nsight Systems or the PyTorch profiler) is the way to see gaps between kernels. An NVIDIA engineer on the developer forum notes that "the compute pipe can be 100% active if even a single thread is running on 1 SM", so a high reading doesn't mean the GPU is saturated. SM-level metrics (DCGM `PROF_SM_ACTIVE`, Nsight Systems `SM_ACTIVE`) show how much of the GPU is actually in use ([forum 368787](https://forums.developer.nvidia.com/t/gpu-utilization/368787)).

### How it applies to ShapeSense

The ShapeSense CNN runs short kernels on 64x64 inputs. When batches arrive late (F21), the GPU sits idle between steps, and the NVML time share swings sharply. That fits the record's 0 to 96% swing exactly. The 0% Task Manager reading was a display artifact. The real swings point back to input-pipeline stalls, not to a problem with the device.

## Validation

The record says Task Manager's default GPU graphs don't include CUDA compute work, and that nvidia-smi and the run records confirmed the RTX 3080 was in use. The literature agrees on the mechanism (engines are graphed separately, the CUDA engine is often not among the four shown) and on the remedy (nvidia-smi). One nuance: Microsoft says CUDA work *is* collected and the headline uses the busiest engine, so "doesn't include CUDA" is best read as "the default graphs don't show the CUDA engine". It doesn't mean the data is missing.

## Our decision

The project confirmed with nvidia-smi and the run records that training was on the RTX 3080, and explained the 0 to 96% swing as waiting for the next batch. The findings back this. A small wording refinement for the docs is to say the CUDA engine is not among the default graphs. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## WDDM Engine Telemetry vs. NVML Kernel Occupancy (`F25`)

### Metadata & Lineage

* **Entry ID / Type:** `F25` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `nvidia-smi` telemetry logs, `configs/pipeline.yaml` (`device: cuda`)

### Telemetry Architecture & Diagnostic Interpretation

* **Windows Task Manager Engine Selection (Microsoft DirectX Blog, WDDM 2.0+):** Task Manager polls per-engine hardware counters across independent GPU command queues (`3D`, `Copy`, `Video Encode`, `Video Decode`, `Cuda` / `Compute_0`) and displays four default graphs. Because `Cuda` is omitted from the default 4-panel view on GeForce drivers, active CUDA workloads read `0%` in the default `3D` graph while dedicated VRAM (`2.7 / 8.0 GB`) confirms active residency on the RTX 3080.
* **NVML Temporal Duty Cycle vs. SM Occupancy:** `nvidia-smi` reports the percentage of the sampling window (`1/6 s` to `1 s`) during which at least one CUDA kernel was active—not Streaming Multiprocessor (SM) saturation. On ShapeSense's lightweight `64 × 64` `SmallCNN`, the `0%–96%` oscillation (`~44%` mean) directly reflects sub-millisecond GPU kernel bursts interleaved with host CPU batch-preparation latency (`F21`), confirming healthy GPU execution without hardware fault.

