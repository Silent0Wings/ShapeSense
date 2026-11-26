# 3_modeling - A08: Deterministic mode is overstated.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A08 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/train.py, src/stage4_train/sampling.py, docs/crisp_dm/iteration_2/data/stage4_status.json, results/phase2_snapshot/iteration_log.json, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/failures.html


## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Deterministic mode is overstated.

## Response
The docstrings and design notes in `src/stage4_train/train.py` claim deterministic execution (`R9: each run stays deterministic from (arm, seed)`), but `_seed_everything(seed, num_threads)` (lines 258-264) only provides best-effort determinism:

1. **`warn_only=True` silently permits non-deterministic CUDA kernels.** Line 264 calls `torch.use_deterministic_algorithms(True, warn_only=True)`. Any layer without a deterministic GPU backward pass - such as `AdaptiveAvgPool2d` (`self.pool` in `SmallCNN`) or certain `BatchNorm2d`/reduction kernels - will log a warning and execute non-deterministically instead of raising an error.
2. **Late `CUBLAS_WORKSPACE_CONFIG` and missing cuDNN deterministic flag.** `_seed_everything` calls `os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")` inside `train_one`, which only takes effect if CUDA/cuBLAS has not already been initialized in the worker process (note that `run.py` initializes CUDA during `sgd_step_fn` and `benchmark` before spawning or running training). It also sets `torch.backends.cudnn.benchmark = False` without setting `torch.backends.cudnn.deterministic = True`, and never seeds Python's global `random` or legacy `np.random` (though `sampling.py` isolates batch RNG via `step_rng(seed, epoch, step)`).

Consequently, Stage 4 runs cannot be assumed to produce bit-identical weights or validation scores across reruns on GPU; you should switch to `warn_only=False` (replacing `AdaptiveAvgPool2d` with a deterministic fixed mean over the `4x4` spatial map) to guarantee exact reproducibility.

## Validation
The team inspected `_seed_everything` and `runtime_id` in `src/stage4_train/train.py` and tested end-to-end reproducibility via a full clean-clone rehearsal (`F16` in `iteration_log.json`):
- **Code check:** Confirmed Gemini 4 Neon's reading of `torch.use_deterministic_algorithms(True, warn_only=True)` in `src/stage4_train/train.py`: determinism is technically best-effort rather than strictly enforced (`warn_only=False`), and `recipe_fingerprint` / `runtime_id` explicitly scopes model reuse to the same `(device, device_name, torch.__version__)` because CPU and GPU floating-point arithmetic differ (and `pixel_values` is precomputed on CPU to avoid GPU division rounding differences across 126 of 256 levels).
- **Clean-clone rehearsal:** The team cloned the repository into a separate directory on the same GPU (8 GB RTX 3080 Laptop) and re-ran the full pipeline end-to-end. Every single one of the **32 validation scores** in Iteration 2 (`20` main runs across `A0`/`A1`/`B`/`A2` x `5` seeds + `12` leave-one-source-out runs) reproduced identically.

## Our decision
- **Team verdict: `Partly` (`Disclosed`).** Gemini 4 Neon is right that `warn_only=True` makes PyTorch's deterministic mode best-effort rather than strict - warnings do not abort non-deterministic ops - so cross-hardware bit-identity is not guaranteed. However, Gemini's concern that GPU runs drift between reruns on the project machine was refuted by the clean-clone rehearsal.
- The team kept `_seed_everything` as-is (avoiding risky architecture changes to `SmallCNN`'s `AdaptiveAvgPool2d` between iterations) and disclosed the best-effort scope alongside the rehearsal verification.

## Measured effect
- **Iteration 2 clean-clone rehearsal:** **32 of 32** validation macro-F1 scores (`A0`/`A1`/`B`/`A2` x 5 seeds + 12 LOSO runs) matched identically on the project GPU.
- **Iteration 3 clean-clone rehearsal (`iteration_log.json`):** **40 of 40** validation scores (`A0`/`A1`/`B`/`A2`/`P` x 5 seeds + 15 LOSO runs), every robustness figure, and every results table reproduced identically on a fresh clone (differing only in run IDs and folder paths).

---

## Scope of Determinism Under `warn_only=True` and CUDA Initialization Order (`A08`)

### Claim Metadata

* **Entry ID:** `A08` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `close-to-reality (30% tier)`
* **Grounding Artifacts:** `src/stage4_train/train.py`, `src/stage4_train/sampling.py`, `results/phase2_snapshot/iteration_log.json`, `docs/crisp_dm/iteration_2/data/stage4_status.json`

### Mechanistic & Systems Analysis

While `src/stage4_train/train.py` asserts per-`(arm, seed)` determinism under requirement R9, `_seed_everything(seed, num_threads)` enforces best-effort rather than strict determinism:

1. **Non-Blocking Determinism Flag:** `torch.use_deterministic_algorithms(True, warn_only=True)` logs warnings rather than throwing runtime exceptions when encountering non-deterministic CUDA backward kernels (such as `AdaptiveAvgPool2d` in `SmallCNN.pool` or atomic reduction kernels in `BatchNorm2d`).
2. **CUDA Context Initialization Race:** `os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")` is executed inside `train_one` after `run.py` has already initialized CUDA contexts during benchmarking (`sgd_step_fn`), meaning cuBLAS workspace allocation is already locked. Furthermore, `torch.backends.cudnn.deterministic = True` is omitted alongside `cudnn.benchmark = False`, and global Python `random` / legacy `np.random` states are unseeded (mitigated in data loading by isolated per-step `np.random.Generator` instances via `step_rng(seed, epoch, step)`).

### Empirical Reproducibility Verification

To distinguish theoretical non-determinism across hardware from practical bit-exactness on the target compute environment (8 GB NVIDIA RTX 3080 Laptop GPU), the team executed full clean-clone rehearsals (`F16` in `iteration_log.json`) in isolated directories:

* **Iteration 2 Rehearsal:** **$32 / 32$** validation macro-F1 scores ($20$ main runs + $12$ leave-one-source-out runs) reproduced bit-identically.
* **Iteration 3 Rehearsal:** **$40 / 40$** validation macro-F1 scores ($25$ main runs across 5 arms + $15$ LOSO runs), every robustness curve, and every summary table reproduced identically.
* Additionally, `recipe_fingerprint` / `runtime_id` explicitly scopes cache reuse to `(device, device_name, torch.__version__)` and precomputes `pixel_values` on CPU to eliminate cross-device IEEE-754 rounding drift across 126 of 256 uint8 intensity levels.

### Resolution

* **Verdict:** **Partly** (strict cross-hardware determinism is not enforced due to `warn_only=True`, but intra-machine reproducibility is 100% deterministic).
* **Action:** Preserved `SmallCNN` architecture (`AdaptiveAvgPool2d`) to maintain cross-iteration comparability and documented the hardware-scoped determinism guarantee.

