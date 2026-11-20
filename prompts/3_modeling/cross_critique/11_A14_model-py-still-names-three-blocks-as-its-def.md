# 3_modeling - A14: model.py still names three blocks as its default.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A14 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/model.py, configs/pipeline.yaml, docs/crisp_dm/iteration_2/investigation/report.md, results/phase2_snapshot/iteration_log.json, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/failures.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: model.py still names three blocks as its default.

## Response
There is a code/documentation mismatch between `configs/pipeline.yaml` and `src/stage4_train/model.py`:

- In `configs/pipeline.yaml#train.channels`, the active network uses **four** convolutional blocks: `[32, 64, 128, 128]` (chosen before Iteration 1 per `F17` to expand the receptive field from `22 px` to `46 px` on `64x64` inputs, yielding `242,250` trainable parameters at `10` classes).
- In `src/stage4_train/model.py`, `build_model(config, n_classes, dropout)` passes `config["train"]["channels"]` dynamically, so pipeline runs do use four blocks. However, `SmallCNN.__init__` still defines a **three-block** default (`channels: Sequence[int] = (32, 64, 128)`) and its docstring describes `3 x [Conv-BN-ReLU-MaxPool]`.

While `run.py` and `train_one` always invoke `build_model(config, ...)`, any unit test, standalone script, or external caller instantiating `SmallCNN()` directly without passing `channels` silently gets the obsolete 3-block (`22 px` receptive field) network rather than the production 4-block architecture. Both the `channels` parameter default in `SmallCNN.__init__` and the docstring in `src/stage4_train/model.py` should be updated to four blocks: `(32, 64, 128, 128)`.

## Validation
The team inspected `src/stage4_train/model.py`, `configs/pipeline.yaml`, and `configs/models/*.yaml`:
- Confirmed `configs/pipeline.yaml#train.channels: [32, 64, 128, 128]` and `configs/models/*.yaml` (`block_channels: [32, 64, 128, 128]`, `learned_parameters: 242250`) already ran the 4-block CNN in every trained arm (`A0`, `A1`, `B`, `A2`), as verified by `status4.json` (`n_params: 242250` via `loader_benchmark.json`).
- Confirmed Gemini 4 Neon's finding that `SmallCNN.__init__` and the module/class docstrings in `src/stage4_train/model.py` still carried the legacy 3-block default from before `F17`.
- Updated `src/stage4_train/model.py` for Iteration 3 (`channels: Sequence[int] = (32, 64, 128, 128)` at line 43 and module docstring lines 4-6: `four: 32 / 64 / 128 / 128`, `About 242k parameters at 10 classes`), and verified `SmallCNN()` with default arguments matches `build_model(config, ...)` (`242,250` parameters).

## Our decision
- **Team verdict: `Stands` (`Fixed in iteration 3`).** The team agreed with Gemini 4 Neon's finding. Because Iteration 2 runs had used `build_model(config, ...)` with `[32, 64, 128, 128]`, no trained weights were affected; the team updated `SmallCNN.__init__`'s default `channels` to `(32, 64, 128, 128)` and updated the docstring to four blocks in Iteration 3.

## Measured effect
- **Trained architecture invariant:** All Iteration 2 and Iteration 3 CNN runs (`SmallCNN`) share identical `4`-block `[32, 64, 128, 128]` geometry (`46-px` receptive field, `242,250` trainable parameters).
- **Code alignment:** Updating `SmallCNN.__init__` default `channels` to `(32, 64, 128, 128)` in `src/stage4_train/model.py` eliminated the divergence between direct `SmallCNN()` instantiation and `build_model(config, ...)`, passing Iteration 3's Stage 4 test suite and clean-clone rehearsal.

---

## Upgraded & Expanded Comparison: Opus 5.5 Audits of Gemini 4 Neon (`A14` & Cross-File Synthesis)

### 1. What these files are

All four cross-critique files (`11_A14` through `14_real`) record the same pattern: **Claude Opus 5.5 (medium effort, in Claude Code) critiquing Gemini 4 Neon's reports** in a real, saved session. Files `12`–`14` are verbatim exchanges; this file (`11_A14`) is a simulated Gemini response grounded in the committed repo.

| File | Gemini report under review | Opus verdict | Worksheet entries |
|---|---|---|---|
| `12_…checks…gemini-review-of-the-training-document` | Review of the training document (4 precision errors, claims to verify, design points) | Mostly right; 3 of 27 points don't stand | C23–C27 |
| `13_…checks…speed-and-voting-audit` | Speed audit + equal-weight voting design | Direction right, several fixes overstated, some facts wrong | C40, C30, C31, F24 |
| `14_…sub-agents-check…speed-report` | Two-part speed/budget report (search + per-run) | Mostly out of date for iteration-3 code; one reuse point kept | C31, C32, C39 |
| `11_A14_…model-py-still-names-three-blocks` | `model.py` still defaults to three blocks | Stands; fixed in iteration 3 | A14 |

The through-line: **Gemini's findings were checked against code and measurements, not accepted or dismissed wholesale.** Valid points became iteration-3 work; invalid or out-of-date ones were dropped or disclosed.

### 2. File 11 — A14: `model.py` three-block default

Simulated Gemini response, grounded in the repo, finding a code/documentation mismatch:

- `configs/pipeline.yaml#train.channels` uses **four** blocks `[32, 64, 128, 128]` (chosen pre-Iteration 1 per F17; receptive field 22 px → 46 px on 64×64; 242,250 params at 10 classes).
- `build_model(config, n_classes, dropout)` passes channels dynamically, so pipeline runs use four blocks — **but** `SmallCNN.__init__` still defaults to `channels=(32, 64, 128)` (three blocks, 22 px) and its docstring says `3 x [Conv-BN-ReLU-MaxPool]`. Any caller instantiating `SmallCNN()` directly silently gets the obsolete network.

**Validation:** team confirmed the config and all trained arms (A0, A1, B, A2) ran the 4-block CNN (`n_params: 242250`, verified via `status4.json` / `loader_benchmark.json`); confirmed the stale default and docstrings; **updated `model.py` for Iteration 3** (`channels` default at line 43, module docstring lines 4–6), and verified `SmallCNN()` now matches `build_model(config, …)` at 242,250 parameters.

**Verdict:** `Stands` (fixed in iteration 3). No trained weights affected. Measured effect: trained architecture invariant (all iter-2/iter-3 runs share 4-block geometry, 46-px receptive field, 242,250 params); code alignment eliminated the divergence and passed the Stage 4 test suite and clean-clone rehearsal.

### 3. Consolidated verdict ledger

**Gemini claims that stood and became work:** second never-read holdout; arm P; grouped 3-fold CV selection; equal-real/scarcity/budget experiments; damaged-image primary test; all four precision corrections; determinism wording; stale-text extension; all seven design disclosures; equal-weight soft voting; 9-run reuse (~35 min); `SmallCNN` default fix.

**Gemini claims that did not stand or were out of date:** browser-side ONNX; validation-caching magnitude; Matplotlib magnitude; fit-loop culprit; 1 MB batch as big win; hardware power cap; `non_blocking` without pinned memory; "FP32 bypasses Tensor Cores"; A0 clean-data precision; "all fixes preserve reproducibility"; iteration-2 search counts applied to iteration 3; most "zero-risk" training-loop list; GPU augmentation now; pruning/Optuna/smaller top-K (pre-registered rules).

**Deferred or disclosed rather than fixed:** 13 of 27 training-document points; Stage 6 traceability and cache bugs (owner's call); `val_curve.png` removed.

**Measured effects:** no change to macro F1 from the speed work; ~35 min search saving from reuse; iteration-3 headline: A2 beat A0 by **+9.20 macro F1, 95% CI [8.89, 9.53]**, on 4,500 never-read damaged images (C23).

### 4. What ties them together

Three principles recur across all four files:

1. **Check, don't accept.** Every Gemini claim was tested against code, a profile, or a measurement — never accepted on authority. Where Opus couldn't verify (e.g., `configs/pipeline.yaml`, Stages 2–3 in the first review), it said so.
2. **Pre-registration constrains the fixes.** Valid points were folded into iteration 3 *before* any run. Cuts that would violate the pre-registered rules (pruning, Optuna, smaller top-K) were rejected even though they'd have been faster — and the 13 deferred fixes were deferred precisely because fixing them would force a retrain or alter a frozen analysis.
3. **Don't touch a running search.** Shared-code edits during the search would silently mix code versions; the code-only session stopped the search at 16/200 and held everything for approval rather than proceeding. Reproducibility was treated as a first-class constraint, not an afterthought.

