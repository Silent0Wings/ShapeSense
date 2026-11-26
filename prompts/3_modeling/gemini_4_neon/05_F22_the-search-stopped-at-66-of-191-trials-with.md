# 3_modeling - F22: The search stopped at 66 of 191 trials with a GPU error.
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: F22 (`failure`, `3_modeling`)
- Owner / Proposed by: 40256377 + 40211352 / gemini_4_neon + 40256377 + 40211352
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/search.py`, `src/stage4_train/train.py`, `results/phase2_snapshot/iteration_log.json`, `results/phase2_snapshot/winners.json`, `docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/failures.html`, commits `b81b67f`, `69dcb02`


## Prompt
The search stopped at trial 66 of 191 with a cuDNN execution failure. Is the GPU damaged, and how do we resume without losing the finished trials?

Literature/search framing: What causes a cuDNN execution failure (CUDNN_STATUS_EXECUTION_FAILED) part way through a long PyTorch training search on a Windows desktop GPU, when the system log shows no driver error? Search for known causes (driver timeout detection and recovery, other programs releasing or claiming the GPU, memory pressure, overheating) and for how long searches checkpoint and resume safely. Our case: it happened at 66 of 191 trials, while other programs were being closed.

## Response
No - a single `CUDNN_STATUS_EXECUTION_FAILED` with **no driver reset or TDR entry in the Windows Event Log** does not indicate permanent GPU hardware damage. On a Windows desktop/laptop GPU (here, an 8 GB RTX 3080), `CUDNN_STATUS_EXECUTION_FAILED` most commonly stems from a transient CUDA/cuDNN context disruption when other GPU-accelerated applications (browsers, desktop compositors, IDE windows) close and release DXGI/VRAM resources mid-kernel, or from transient memory/scheduling contention under WDDM (`train.parallel_runs: 1`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `cudnn.benchmark = False`).

### 1. Verify GPU health and clear stale processes
Before relaunching:
- Check `nvidia-smi` for orphaned `python.exe` processes still holding VRAM from the crashed search (or its `prep.py` worker pool) and terminate any leftover process.
- Run a quick PyTorch CUDA/cuDNN smoke test (`Conv2d` forward + backward on `(256, 1, 64, 64)` float32 tensor with `torch.backends.cudnn.benchmark = False`) and inspect `nvidia-smi` temperature and memory.

### 2. Resume safely without losing the 66 completed trials
`src/stage4_train/search.py` already caches every completed trial atomically at the end of `run_trial`:
- Each finished trial writes `artifacts/stage4/tuning_iter3/<phase>/<trial>/result.json` containing `{"name", "settings", "val_macro_f1", "best_epoch", "epochs_run", "per_class"}`.
- On relaunch, `run_trial` checks `if done_path.is_file()` and `if done.get("settings") == settings: return done` (where `_settings(spec)` hashes `arm`, `seed`, `overrides`, `hparams`, and `fold`).
- Additionally, `execute()` builds `known = {_settings_key(r["settings"]): r for r in finished}` and skips any spec whose serialized settings already completed, so all **66 completed trials** carry over untouched and only the remaining `125` trials execute (assuming no config or code changes were made in between).
- Add a written long-job recovery rule: inspect the log and GPU health, record the failure in `docs/crisp_dm/iteration_log.json`, kill any leftover process, relaunch a single copy, and halt for investigation if the failure repeats.

## Validation
- Checked Windows system logs (no GPU driver error) and ran `nvidia-smi` plus a CUDA/cuDNN test pass confirming the RTX 3080 operated normally (`40256377` and `40211352`).
- Terminated the leftover process and relaunched `python -m src.stage4_train.search`.
- Verified via `artifacts/stage4/tuning_iter3/` logs that `run_trial` matched `done.get("settings") == settings` for all `66` already-finished trials and resumed directly from trial `67` through `191` (`191` trained + `9` duplicate-settings reused = `200` total search specs), producing identical `winners.json` inputs (`results/phase2_snapshot/winners.json`).

## Our decision
Confirmed GPU health, stopped the leftover process, relaunched the search once so all 66 finished trials carried over, and formalized the long-job recovery rule in `docs/crisp_dm/iteration_log.json` (`Long-job recovery`). Because the root cause of the transient cuDNN error during desktop app closure could not be pinned down with certainty, F22 remains recorded as `Partly` (`docs/crisp_dm/README.md`, `iteration_log.json`).

## Measured effect
- **Trials preserved:** **66 of 191** completed trials reused verbatim (`0` lost compute), and all remaining **125** trials finished without further GPU errors.
- **Total search outcome:** `191` trained runs (`9` repeated settings reused via `execute`) completed in ~3 hours 50 minutes (`175` main/CV/confirm trials after the initial resume, median **92-184 s** per trial), yielding the frozen Iteration 3 winners (`A0 94.19`, `A1 95.20`, `B 95.06`, `A2 95.80`, `P 95.17` 3-seed validation macro-F1).

---

## : Gemini 4 Neon Corpus Synthesis (`F22` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F22` (`failure`)
* **Logic Depth:** **Medium** (depends on `C30`'s atomic `result.json` resume and settings-hash verification)
* **Risk if Wrong:** **Medium** (`66/191` trials preserved; root cause never pinned $\rightarrow$ marked `Partly`)
* **Adoption Status:** **Adopted recovery protocol; rejected "GPU damaged" hypothesis** (no Windows TDR Event 4101 entry; device passed health checks and completed all remaining 125 search trials + 40 final runs).

### 2. Group Synthesis: Speed, Crashes, and the Optimization Stage (`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`, `F22`, `F25`)

* **`F22` (cuDNN halt at `66/191`)** confirms no hardware damage (no TDR entry), preserves all 66 finished trials via atomic `result.json` + settings-hash resume, and finishes the remaining 125. Because the transient cuDNN fault coincided with desktop app closures and could not be attributed to a single confirmed driver event, its state remains `Partly` and motivated the formal 7-step Long-Job Recovery SOP (`C37`).
* **`F19` $\rightarrow$ `C30` $\rightarrow$ `C31` $\rightarrow$ `C39`** forms the surrounding systems pipeline: replacing lazy `ProcessPoolExecutor` with an eager 7-worker `spawn` pool (`F19`, `C30`), auditing and registering bit-exact optimizations including the 256-entry `uint8` LUT (`C31`), and measuring the `175`-run search completion in `~3 h 50 m` with the quieter-machine caveat (`C39`).

