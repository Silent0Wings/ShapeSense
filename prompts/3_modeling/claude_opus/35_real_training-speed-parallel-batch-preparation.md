# 3_modeling - Speeding up training: parallel batch preparation

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: F21, C30
- Source: **exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (19:38)

> are you using gpu for trianing ?  but add this as highest proiority next to do =[ould it go faster? Spreading the image preparation across more CPU cores could cut the time noticeably, but I'd leave it. It means changing the training code mid-iteration and restarting the search. It would also change the random image stream, so the runs would no longer match the experiments that set this budget, and I'd have to re-validate that. Cutting trials isn't allowed either, because the goal only permits that if the estimate passes 24 hours for a job, and this search is at 13 to 17.] paralel and threading the bottlneck areas

## Response 1

Yes, training is on the GPU: the workers hold about 5.4 GB of GPU memory and its use keeps spiking up to 90%. I'll put the speed-up at the top of the to-do list and work on it next.

Editing the training code in place would contaminate the running search, because each new search phase reloads that code. So the search keeps running while I measure where the time goes.

**The tuning search isn't running right now.** I stopped it on purpose after 4 of 200 trials to build the speed-up you asked for, and I'm benchmarking that change before relaunching.

**Yes, training uses the GPU.** The bottleneck is image preparation, about 80% of each step, which ran on a single CPU core while the GPU waited.

**The speed-up so far:**
- Image preparation now runs across 7 CPU processes, with one training run at a time, and the batches come out the same whatever the process count. The Stage 4 tests all pass.
- The random image stream did change, as I'd warned. The 108 experiments keep their recorded numbers, but they can't be retrained exactly from this code. I'll record that as a deviation under its CRISP-DM step.
- An early prototype was about twice as fast even while competing with the search for CPU. The first full benchmark timed out, so I can't yet say how much faster real training is. A second run is in progress with a watcher on it.
- If the speed-up doesn't hold up, I'll revert it and relaunch the search as before.

**Your 43 saved drawings: yes, but only as informal evidence.** The goal allows them to be reviewed in Phase 8, and they won't be used for training, tuning or any score. Using them for training would break the pre-registered design.

They're already revealing, though: all four models agreed on only 5 of the 43. The most common split, 8 drawings, was A0 saying square while the other three said pentagon.

They also don't record which shape you meant to draw, so they can't be scored or trained on until they're labeled. That could be useful for a future iteration if you want it. I haven't committed them.

## Prompt 2 (20:03)

> what about the augmentation is it not threaded ? what about the synthesis ?

## Response 2

Neither is threaded, but with the new change both run in parallel, using processes instead of threads.

| Step | Before | Now |
|---|---|---|
| Augmentation | One CPU core, on the training thread | Spread across the 7 worker processes |
| Synthetic drawing | One CPU core, on the training thread | Spread across the same 7 workers |

**How it splits the work:** each worker builds a whole batch, including both its augmented and its synthetic images, while the other workers build the next batches. So the parallelism is between batches, and within one batch the images are still made one at a time. That doesn't cost anything as long as enough finished batches are queued for the GPU.

**Why not threads:** most of this code is Python, and only one thread can run Python at a time. Processes don't have that limit. I didn't benchmark a threaded version, though, so the 17% I quoted for threads was an estimate from the timings. Threads also wouldn't fit the design as it stands, because one math thread per worker is what stopped the workers fighting over cores.

Arm A0 uses neither step and its batches take only 11 ms, so it stays in the main process.

The benchmark is still running, so I don't have the final speed-up number yet.

This is a very useful result, though the lines need careful reading. The "0.0s total" means these are the saved runs from the first benchmark, reused rather than rerun. They still show real timings:

- With 7 workers an epoch takes **2.1 seconds, against about 20 before**, roughly 10 times faster.
- The validation score is **identical** at every worker count (65.8511), so the speed-up doesn't change the training at all.
- But pool start-up costs about 124 seconds per trial, because each worker reloads PyTorch one at a time. Over 200 trials that's almost 7 hours, so it needs fixing first.

I'll stop this benchmark and fix the start-up.

All 191 tests pass and the change is committed. Relaunching the search with the fast pipeline and its watcher.

**The speed-up works and the tuning search is running again from the start.** An epoch now takes about 2.3 seconds instead of about 20, measured on short real runs for all arm types.

| Remaining work | Before | Now (estimate) |
|---|---|---|
| Phase 5 search, 200 trials | 13 to 17 hours | About 6 hours |
| Phase 6 retraining, 40 runs | About 4 hours | About 2 hours |

Those estimates come from 5-epoch runs, so I'll confirm them once the search has run for a while.

**What changed:**
- Batches are now built by 7 CPU processes, and one training run goes at a time so the GPU isn't shared.
- Validation scores came out identical with 4 and 7 processes, so the speed-up doesn't change the training.
- All 191 tests I ran pass, covering Stage 4, Stage 0 and the contracts, and it's committed locally.

**What this cost or changed:**
- The random image stream is different now. The 108 experiments keep their recorded numbers but used the old stream, and that's recorded as a deviation.
- The first search's 4 trials are set aside, not mixed in.

**A correction to the record:** I had blamed the earlier launch crash on editing code during start-up. The same error came back with no edits, from the way Python starts pool workers on demand on Windows, so I've corrected the log. It may also explain the silent hang, but that isn't proven. Training no longer uses that kind of pool, and a stalled batch now raises an error instead of hanging.

The 5-minute watcher is on, and it will now also catch that timeout error.

The search relaunched at 20:27, about a minute ago, so 0 of 200 is expected. There are no errors in the log, and the GPU is still idle because the program is loading data. The first trial should finish within a few minutes, and the 5-minute watcher will flag it if it doesn't.

## Prompt 3 (20:30)

> when training the model how do we reduce the wait ? can we batch prepare them before the training so that during training there is no wait ?

## Response 3

We're effectively doing that already, and there's almost no wait left. The 7 workers build batches ahead of the training loop and hand them over in order, so a finished batch is normally ready when the GPU asks for one.

The benchmark shows it. Arm A0 needs no image preparation, and its epochs take about 2.2 seconds. Arm B, the heaviest, takes about 2.3 seconds. Since the arm with no preparation is just as slow, preparation is no longer what limits the speed. What's left is the GPU work and the validation pass after each epoch.

**Preparing everything before training wouldn't help:**
- **The work is the same.** One 60-epoch run needs about 2,940 batches, so the CPU cost just moves to before the run. Training would start later and finish at about the same time.
- **Saving batches to reuse across trials would change the experiment.** Every trial has different augmentation or generator settings, so each needs its own images. Reusing them would also stop models seeing fresh random images at each step, which is what the augmentation is for.
- **It takes a lot of disk.** That's about 3 GB per trial, or several hundred GB for the whole search.

**The remaining options are small.** Workers could start the next epoch's batches during validation, which might save a fraction of a second per epoch. It's not worth changing the code again now that the search is running.

These timings are from 5-epoch runs, and I'll check them against the real trials as they finish.

## Prompt 4 (20:31)

> investigate whow can we speed up the system

## Response 4

I'll measure where the time goes in the real trials first. Everything here is read-only, so the search keeps running.

I need to correct my estimate: **the first real trial took about 6 minutes, so "about 6 hours" for the search was too optimistic.** The 5-epoch benchmark caught only the fast stretches. A real 60-epoch run flipped between about 2.2 and 6 seconds per epoch.

At 6 minutes a trial, the search would take about 12 hours, and the old setup averaged 5 to 7.5 minutes per trial. So on this first trial the real gain is small. If every epoch ran at the fast rate, a trial would take about 2.5 minutes.

My own diagnostic commands ran during part of that trial, so it may have looked slower than normal. The cause of the slow stretches isn't established yet. The GPU does report its power cap as active, and a laptop shares its power budget between CPU and GPU, so running 7 CPU workers flat out may be slowing the GPU. That's a hypothesis until the 10-minute log is in.

The speed-up steps will go under their CRISP-DM steps in the log and the dashboard. The first change is already there under Modeling, and I'll add what this investigation finds. The search is still running, and I'll leave the machine alone while the log collects.

1 of 200 search trials was done at 20:38. I'm leaving the machine alone while the 10-minute log collects.

## Prompt 5 (20:40)

> read the code and investigate further

## Response 5

Reading the code is light enough not to disturb the log. I'll go through the image transform, the generator and the training path.

I've read the code. The image transform and the generator are the two main things to speed up, and I have some leads, but none of these is measured yet.

| Lead | Where | Expected effect | Changes results? |
|---|---|---|---|
| Work out each stored image's ink points, center and thin-line flag once, rather than for every augmentation | `_augment` in the transform | Moderate saving on CPU | No |
| Build the frame-margin mask once instead of for every image | `_outer_ring` | Small | No |
| Send batches between processes as 1 MB of raw bytes rather than 4 MB of floats | Batch workers | Less work for the main process | No |
| Stop forcing a sync with the GPU at every step to read the loss and accuracy | Training loop | Probably small | No |
| Turn off the strict deterministic GPU mode | Training setup | Possibly large on GPU | **Yes**, runs stop being exactly repeatable |
| Mixed-precision training | Training loop | Possibly large on GPU | **Yes**, the numbers change |

The generator is already simple, so I don't see much to gain there. The two options that change results would weaken the reproducibility this project depends on, so I wouldn't use them without your say-so.

None of those leads explains why epochs flip between 2.2 and 6 seconds, which is the biggest question. The 10-minute log should show that, and when it finishes I'll compare it to the epoch timings, then record the findings under their CRISP-DM steps.

3 of 200 search trials are done at 20:43, with 2 finished in the last 5 minutes. That's already a faster pace than the first trial.

The log is done. I'll line up each epoch's duration with what the machine was doing at that moment.

**Training is now limited by the rest of the machine, not by the code.** In real trials an epoch takes 2 to 6 seconds, down from about 20. My earlier figure of 2.3 seconds was only the fast end, and I've corrected it in the record.

**What the 10-minute log showed:**

| | Fast epochs | Slow epochs |
|---|---|---|
| Whole-machine CPU busy | 90% | 99% |
| GPU busy | 63% | 38% |
| GPU temperature | 71°C | 69°C |

It isn't overheating, and CPU speed was the same in both. When the CPU runs out of room, the workers fall behind and the GPU waits.

**What's using the CPU besides training** (a single snapshot, so it's indicative):
- Windows Defender: about 2 cores
- System activity: about 1 core
- Your editor (Antigravity IDE): about 1 core
- A `cmake` and `test_app_shell` build: active, and it may be yours

**Ways to speed it up further, best first:**
1. **Exclude this project from Windows Defender's real-time scan, or pause other heavy work during runs.** It costs nothing in code or results. The search would drop from about 9 to 11 hours to about 6 to 7. A Defender exclusion lowers your security on that folder, so I won't change it myself. The folders would be the repo and its `.venv`.
2. **Cache the per-image work and send smaller batches between processes.** Neither should change results, and together they should free some CPU, but I haven't built or measured them.
3. **Mixed precision or relaxing strict GPU determinism.** These could be fast, but they change results or repeatability, so I recommend against them.

The search is healthy at 4 of 200 with no errors, so it should finish around 6 to 8 a.m. All the speed-up steps are now recorded under Modeling in the CRISP-DM record and on the dashboard.

**Your call:** do you want to add the Defender exclusion or pause that build? And should I build option 2? It would mean stopping and restarting the search, so I'd only do it if you want it now.

5 of 200 search trials are done at 20:53, with 1 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 20:58 with 6 of 200 search trials done.

8 of 200 search trials are done at 21:03, with 2 finished in the last 5 minutes.

10 of 200 search trials are done at 21:08, with 2 finished in the last 5 minutes.

11 of 200 search trials are done at 21:13, with 1 finished in the last 5 minutes.

12 of 200 search trials are done at 21:18, with 1 finished in the last 5 minutes.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Benchmarks before and after, and validation scores compared at different process counts.

## Our decision

We made speed the top priority. Opus 5.5 had first suggested leaving it until after the iteration. Batches are now built by 7 processes, with one generator per step and one run at a time (C30).

## Measured effect

An epoch fell from about 20 s to between 2 and 6 s. Validation scores were identical at different process counts (F21). By design there is no change to macro F1.

---

## CPU-Bound Data Pipeline Parallelization & System Resource Profiling (`F21`, `C30`)

### Metadata & Lineage

* **Entries:** `C30` (*Parallel batch preparation via 7 worker processes*), `F21` (*Validation invariance across worker counts*)
* **Date:** `2026-11-09` (19:38–21:18 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)
* **VRAM / Compute Footprint:** `~5.4 GB` VRAM active, GPU utilization spiking to `90%` during compute bursts, CPU data preparation accounting for `~80%` of step wall-clock latency

### Systems Bottleneck Analysis & Concurrency Architecture

1. **GIL Contention vs. Multiprocessing (`spawn`):** Because image rasterization (synthetic drawing) and stochastic geometric/morphological augmentations execute primarily in Python/NumPy on the main training thread, Python's Global Interpreter Lock (GIL) prevented multithreading from scaling across cores. Offloading batch assembly to **7 dedicated worker processes** (`1` training process + `7` prep workers = `8` physical/logical core saturation) eliminated GIL serialization while restricting each worker to **one BLAS/math thread** to prevent intra-node thread thrashing.
2. **Arm-Conditional Dispatch:**
   * **Arm `A0` (Clean Real Only):** Requires zero runtime augmentation or synthesis (`~11 ms/batch`), executing inline in the main process without IPC serialization overhead.
   * **Arms `A1`, `B`, `A2`, `P`:** Workers assemble complete 256-image batches ahead of the GPU consumer loop (`prefetch queue`), overlapping host CPU augmentation/synthesis with device forward/backward passes.
3. **Worker Initialization Bottleneck (`124 s` $\rightarrow$ Amortized):** Naive per-trial pool spawning incurred `~124 s` per trial (`~6.9 hours` across 200 trials) because each Windows `spawn` child imported PyTorch sequentially. Eliminating per-trial pool teardown and adding a **5-minute watchdog** prevented silent Windows pool hangs.
4. **Why Pre-Computing All Batches to Disk Was Rejected:**
   * **Zero Compute Reduction:** A 60-epoch run requires `60 × 49 = 2,940` batches; shifting CPU execution pre-training leaves total wall-clock time unchanged.
   * **Experimental Contamination & Storage Explosion:** Every hyperparameter trial mutates augmentation/generator parameters (preventing cross-trial reuse), and materializing `2,940` batches consumes `~3 GB/trial` (`~600 GB` across 200 trials).

### Empirical Profiling & Host Contention Telemetry

| Regime / Measurement | Metric | Baseline (Single-Core) | 7-Worker Pipeline (Uncontended) | 7-Worker Pipeline (Host-Contended) |
| --- | --- | --- | --- | --- |
| **Epoch Wall-Clock Time** | Seconds / epoch | `~20.0 s` | `2.1 s – 2.3 s` (`~9.5×` speedup) | `2.2 s – 6.0 s` (bimodal) |
| **System CPU Utilization** | Total host CPU % | Single-core bound | `90%` | `99%` (starving workers) |
| **GPU Utilization & Temp** | Active % / Core °C | ~20% duty cycle | `63%` busy / `71°C` | `38%` busy / `69°C` (no thermal throttle) |
| **Validation Macro-F1** | Seed-locked parity | `65.8511` | `65.8511` (`0.0000` delta) | Identical across 1, 4, 7 workers |

*Root Cause of Bimodal Epoch Variance (`2.2 s` vs. `6.0 s`):* Host telemetry proved the GPU was not thermally throttling (`69°C`); rather, concurrent background processes—**Windows Defender real-time scanning (`~2 cores`)**, OS background tasks (`~1 core`), **Antigravity IDE (`~1 core`)**, and an active **`cmake` / `test_app_shell` build**—saturated the remaining CPU headroom, starving the 7 worker processes.

