# 3_modeling - C39: Optimization stage, measured
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C39 (`change`, `3_modeling`)
- Owner / Proposed by: 40211352 / gemini_4_neon + 40211352
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/docs/crisp_dm/README.md, ShapeSense/docs/crisp_dm/iteration_log.json, ShapeSense/docs/crisp_dm/iteration_3/search/winners.json, ShapeSense/results/phase2_snapshot/loader_benchmark.json, ShapeSense/src/stage4_train/search.py, ShapeSense_Deployed/web/stage4.html


## Prompt
Here are the measured trial times by phase after the optimizations. Summarize the optimization stage with before and after numbers, and say what part of the gain may come from a quieter machine.

## Response
The measured phase timings from the completed iteration 3 search close out the Optimization stage inside Modeling with clear before-and-after benchmarks and an explicit attribution note separating code gains from host CPU contention.

### 1. Before vs. after summary
| Stage / Version | Per-trial runtime (60 epochs) | Total search runtime | Notes |
|---|---|---|---|
| **Original (1-core prep, 2 runs at once)** | ~5 to 7.5 min effective (~20 s/epoch) | - | Image prep was ~80% of each step |
| **First parallel version (7 prep workers, per-trial pool)** | ~3.7 min avg (2.6-5 min; 3.6-5.1 s/epoch typical) | ~9 hours (projected) | `step_rng`, `_light_children`, `parallel_runs: 1` |
| **Latest optimized code + quieter machine** | **92 to 184 s median by phase** (reruns: **163 s** and **176 s**) | **~3 hours 50 min for 175 trainings** | Shared pool, `_ink_facts` cache, `uint8` LUT, no per-step GPU sync, GPU-cached val, no search plots |

All optimizations were verified to preserve exact outputs: the two `163 s` and `176 s` reruns matched the earlier trials identically on every logged number across all 60 epochs.

### 2. What part of the gain comes from a quieter machine
Not all of the drop from `~3.7` minutes (`~9` hours projected) to `92` - `184 s` median (`~3` hours `50` minutes) is from code changes alone:
- **Measured CPU contention (`F21`):** Before the final optimizations, epoch times on the 7-process loader swung between `2.2 s` (fast stretches) and `5.4 s` (busy stretches) with **zero change in GPU temperature or power cap**. In slow epochs total machine CPU hit **99% busy** versus **90% busy** in fast epochs.
- **External load removed mid-search:** Windows Defender was consuming ~2 CPU cores and background applications several more. Adding a Defender exclusion and closing other programs part way through the search removed that CPU contention.
- **Reporting rule:** Record the `92` - `184 s` median and `3 hours 50 minutes` total accurately as the combined result of the registered optimizations and a quieter machine, rather than claiming the entire speedup came purely from Python/GPU changes.

## Validation
Recorded in commit `e9fd141` (`docs/crisp_dm/README.md`, `docs/crisp_dm/iteration_log.json`, `docs/crisp_dm/iteration_3/search/winners.json`) and checked by `40211352`:
- Confirmed the two `163 s` and `176 s` verification reruns matched earlier trials identically on every logged metric across all 60 epochs.
- Confirmed the iteration 3 search completed all `191` non-duplicate trials (`9` reused from identical settings across `200` specs; `66` trials carried over after the `F22` GPU halt, `175` trainings timed in the post-optimization run totaling ~3 hours 50 minutes).
- Confirmed `loader_benchmark.json` reflects the shared-pool, single-run configuration (`parallel_runs: 1`, `num_threads: 2`, `2,218.1` img/s on `B` including one SGD step, `18.51 ms` mean step time, `est_run_s: 393.7 s`).

## Our decision
Adopted and published the before/after summary and the quieter-machine caveat verbatim in `docs/crisp_dm/README.md` (§ "Optimization stage (part of Modeling)") and `docs/crisp_dm/iteration_log.json` (`C39`), keeping the Optimization stage closed inside Modeling.

## Measured effect
- **Trial time reduction:** From `5` - `7.5` min effective (1-core) and `~3.7` min (first parallel version) down to **`92` - `184 s` median by phase** (and `163 s` / `176 s` on exact-match reruns).
- **Search wall-clock time:** `175` trainings completed in **~3 hours 50 minutes** vs. ~`9` hours projected at `~3.7` min/trial, with part of the gain explicitly attributed to closing background programs and adding the Windows Defender exclusion.
- **Correctness preserved:** 100% match across all 60 epochs on every logged number on both verification reruns.

---

## : Gemini 4 Neon Corpus Synthesis (`C39` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C39` (`change`)
* **Logic Depth:** **Medium** (measures `C30` and `C31` across the full 191-trial Iteration 3 search)
* **Risk if Wrong:** **Medium** (attributing the entire `~3.7 min` $\rightarrow$ `92–184 s` reduction purely to code changes would overclaim by ignoring host CPU contention relief)
* **Adoption Status:** **Adopted with correction / caveat** (published full before/after timings alongside the explicit caveat splitting code speedup from the quieter machine after Windows Defender exclusion and closing desktop apps).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`C39`** closes the `F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39` causal chain with production search telemetry (`175` trainings after resume completed in `~3 h 50 m`, median `92–184 s` by phase vs. `~9 h` projected) and an explicit epistemic guardrail: because Windows Defender real-time exclusions and closing concurrent desktop programs freed `~3–4` CPU cores mid-search, the record explicitly splits the measured gain between code optimizations (`C30`, `C31`) and a quieter host machine rather than claiming the entire speedup was pure Python/CUDA engineering.

