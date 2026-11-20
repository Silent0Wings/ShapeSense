# 3_modeling - F22: The search stopped at 66 of 191 trials with a GPU error. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F22 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f22) · Record: [F22](../inferred_prompts.md#f22)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> What causes a cuDNN execution failure (CUDNN_STATUS_EXECUTION_FAILED) part way through a long PyTorch training search on a Windows desktop GPU, when the system log shows no driver error? Search for known causes (driver timeout detection and recovery, other programs releasing or claiming the GPU, memory pressure, overheating) and for how long searches checkpoint and resume safely. Our case: it happened at 66 of 191 trials, while other programs were being closed.

## Response

### Well established

- **The error is generic.** `CUDNN_STATUS_EXECUTION_FAILED` means a cuDNN kernel failed to run. It doesn't say why. PyTorch forum threads show it in very different situations: suspected out-of-memory, version mismatches, only some batch sizes, batch-norm and RNN layers ([thread 4441](https://discuss.pytorch.org/t/cudnn-status-execution-failed/4441), [thread 17625](https://discuss.pytorch.org/t/cuda-error-runtimeerror-cudnn-status-execution-failed/17625), [thread after two epochs](https://discuss.pytorch.org/t/cudnn-error-cudnn-status-execution-failed-after-two-epochs/175026)). None of them names a single root cause.
- **CUDA errors are reported late.** The [PyTorch CUDA semantics notes](https://docs.pytorch.org/docs/2.8/_sources/notes/cuda.rst.txt) explain that GPU work is queued, so an error surfaces at a later call. `CUDA_LAUNCH_BLOCKING=1` makes calls synchronous to locate it. The line where cuDNN failed may not be the line that broke.
- **Windows TDR resets a GPU that stops responding.** [Microsoft's WDDM TDR article](https://learn.microsoft.com/windows-hardware/drivers/display/timeout-detection-and-recovery) states "The default timeout period in Windows is two seconds". The OS then resets the GPU and purges all allocations from video memory. On recovery it "Logs the preceding message in the Event Viewer". That is Event ID 4101, "Display driver ... stopped responding and has successfully recovered" ([TechNet wiki](https://learn.microsoft.com/en-us/archive/technet-wiki/1462.event-id-4101-display-driver-timeout-detection-and-recovery)). The timeout is set by `TdrDelay` and related keys ([TDR registry keys](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys)).
- **NVIDIA classifies driver-reported GPU faults by Xid code** (application, driver, hardware, memory, bus, thermal), and warns that one code often has several possible root causes ([Xid docs](https://docs.nvidia.com/deploy/xid-errors/working-with-xid-errors.html), [Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html)). The Xid workflow is aimed mainly at Linux logs.

### Single reports

- NVIDIA forum replies say the watchdog applies to every WDDM device, even one with no display attached. They also say WDDM batches kernel launches, so the 2 s limit applies to the whole batch ([forum 31721](https://forums.developer.nvidia.com/t/wddm-timeout-detection-and-recovery/31721), [watchdog thread](https://forums.developer.nvidia.com/t/watchdog-timer-kills-cuda-code/133603)). A TDR normally shows up in CUDA as `cudaErrorLaunchTimeout` ([forum 68651](https://forums.developer.nvidia.com/t/how-to-detect-display-driver-stopped-responding-and-has-recovered/68651)), not as a cuDNN execution failure.
- Event 4101 reports blame driver versions, overclocks and even faulty RAM ([MS Q&A](https://learn.microsoft.com/en-us/answers/questions/4155833/fixed-nvlddmkm-gaming-video-crash-error-bad-ram), [Dell KB](https://www.dell.com/support/kbdoc/en-us/000156216/troubleshooting-the-timeout-detection-and-recovery-feature-within-windows)). These are anecdotes.
- I found **no** source documenting that closing other programs makes a CUDA process fail. A source for overheating causing cuDNN failures was not found either, beyond the "thermal" category in Xid.

### Reasoning (mine, not sourced)

With no 4101 or `nvlddmkm` event in the log, a full TDR is unlikely, since Windows logs those on recovery. The remaining candidates are a one-off fault in the device or driver, a transient memory-allocation failure, or interference while other GPU apps (browsers and overlays use the same WDDM GPU) were tearing down their contexts. That last one fits the timing but has no source behind it. A single event can't separate them. Only a repeat with `CUDA_LAUNCH_BLOCKING=1` and Event Viewer open could.

### Checkpoint and resume

The documented pattern is the one ShapeSense already uses: make each trial a unit with a durable completion record, and skip completed units on relaunch. Optuna formalises the remaining piece. A trial whose heartbeat stops is marked FAIL after a grace period and can be retried automatically ([RDBStorage docs](https://optuna.readthedocs.io/zh-cn/stable/reference/generated/optuna.storages.RDBStorage.html), [fail_stale_trials](https://optuna.readthedocs.io/en/v3.1.0/reference/generated/optuna.storages.fail_stale_trials.html), [RetryHeartbeatStaleTrialCallback](https://optuna.readthedocs.io/en/latest/reference/generated/optuna.storages.RetryHeartbeatStaleTrialCallback.html)). The key properties are: a record is written only when the trial completes, an interrupted trial is never half-counted, and the unfinished trial is rerun from scratch with the same seed.

### How it applies to ShapeSense

The search reproduces each trial from its seed and config, so rerunning the interrupted trial is exact. That makes per-trial reuse sufficient, with no need for mid-trial checkpoints. Avoiding GPU-heavy desktop activity during long runs is a cheap precaution.

## Validation

The record leaves the cause "not established", and the literature supports leaving it open. The error is generic, and the strongest documented Windows cause, TDR, normally leaves an Event Viewer entry, which the record says was absent. That points somewhat against TDR. The "programs being closed" timing is not backed by any source. Checking that the GPU still worked, then relaunching and reusing the finished trials, matches the documented practice.

## Our decision

The project checked that the GPU still worked, stopped the leftover process and relaunched, and all 66 finished trials carried over. If it happens again, the findings suggest recording the Event Viewer System log (`nvlddmkm`, Event 4101) and the CUDA error type, and rerunning the failing trial with `CUDA_LAUNCH_BLOCKING=1`. Nothing was changed in this pass.

Added 2026-11-20, from an outside second opinion the user shared:
- **The recorded facts:** the exact error, from the real session export (`38_real_is-training-on-the-right-gpu.md`), was `cuDNN error: CUDNN_STATUS_EXECUTION_FAILED`. The software on the training machine on 2026-11-20 was PyTorch 2.14.1+cu130 (CUDA 13.0), cuDNN 9.24 (`torch.backends.cudnn.version()` = 92400), NVIDIA driver 610.88 and an RTX 3080 Laptop GPU with 8 GB. The versions at the time of the failure were not recorded. The error has not happened again.
- **Two more checks for a repeat:**
  - **cuDNN's own API log:** set `CUDNN_LOGLEVEL_DBG=3` and `CUDNN_LOGDEST_DBG=<file>`, then rerun the failing trial. The log shows the first cuDNN call that fails, with its parameters.
  - **`compute-sanitizer --tool memcheck`:** run it on a small reproduction to rule out an invalid memory access that cuDNN only reports later.
- **Same verdict:** the second opinion agrees with this file. An application-level cuDNN or CUDA fault is more likely than a recovered driver reset, and the cause stays not established.

## Measured effect
None. Research only, no run.

---

## `CUDNN_STATUS_EXECUTION_FAILED`, WDDM TDR & Fault-Tolerant Search Checkpointing (`F22`)

### Metadata & Lineage

* **Entry ID / Type:** `F22` (`failure`, `3_modeling` — literature audit + post-incident forensic addendum)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis + runtime stack audit)
* **Runtime Stack Recorded:** `PyTorch 2.14.1+cu130` (CUDA `13.0`), `cuDNN 9.24` (`92400`), NVIDIA Driver `610.88`, NVIDIA RTX 3080 Laptop GPU (`8 GB` GDDR6)

### Forensic Diagnosis of Mid-Sweep `CUDNN_STATUS_EXECUTION_FAILED`

1. **Asynchronous CUDA Queue Semantics:** Because CUDA kernel launches execute asynchronously on device streams, `CUDNN_STATUS_EXECUTION_FAILED` surfaces at a subsequent synchronization barrier rather than the exact offending operation unless `CUDA_LAUNCH_BLOCKING=1` is set.
2. **Ruling Out Windows WDDM TDR (`Event ID 4101`):** Under Windows Display Driver Model (WDDM), the OS watchdog resets the GPU if a batched kernel command buffer exceeds `TdrDelay` (`2.0 s` default), purging all VRAM allocations and logging `Event ID 4101` (`nvlddmkm`) in Windows Event Viewer. The absence of `Event ID 4101` in the system log argues against a full driver TDR reset and points toward an application/library-level cuDNN kernel fault, transient allocation failure, or WDDM context contention triggered when concurrent desktop GPU applications closed at trial `66 / 191`.

### Durable Checkpointing & Repeat-Failure Diagnostic Escalation

| Operational Layer | Implemented Safeguard | Escalation Protocol on Recurrence |
| --- | --- | --- |
| **Atomic Trial Persistence** | Trials emit `result.json` only upon completion; interrupted trial `66` lacked `result.json` and restarted cleanly from its deterministic `(arm, seed)` config while all `66` prior trials carried over. | Capture Windows Event Viewer System logs (`Event ID 4101` / `nvlddmkm`) and NVIDIA Xid/driver telemetry immediately. |
| **Kernel-Level Isolation** | Confirmed GPU device health and terminated orphaned worker PIDs prior to single-instance relaunch. | Re-run the isolated failing trial with `CUDA_LAUNCH_BLOCKING=1`, `CUDNN_LOGLEVEL_DBG=3` (`CUDNN_LOGDEST_DBG=<file>`), and `compute-sanitizer --tool memcheck` to pinpoint exact cuDNN descriptor parameters or out-of-bounds memory accesses. |

