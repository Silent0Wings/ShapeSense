# 3_modeling - T17: feat: implement stage 4 training and stage 5 evaluation pipelines with tests
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T17 (`task`, `3_modeling`)
- Owner / Proposed by: 40211352 + 40304911 / gemini_4_neon
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: src/stage4_train/run.py, src/stage4_train/sampling.py, src/stage4_train/sweep.py, src/stage4_train/train.py, src/stage5_eval/evaluate.py, src/stage5_eval/run.py, tests/stage5/test_evaluate.py, tests/stage5/test_run.py, configs/pipeline.yaml, ShapeSense_Deployed/web/stage4.html, git commit 69b9265


## Prompt
Task T17 (built, stage `3_modeling`): feat: implement stage 4 training and stage 5 evaluation pipelines with tests. Propose or assist with the exact implementation, checks, and configuration needed for commit `69b9265`.

## Response
To support CUDA GPU sweeps alongside leave-one-source-out (`LOSO`) runs across both Stage 4 training and Stage 5 evaluation, update the pipeline in two coordinated parts:

1. **Stage 4 CUDA device resolution and LOSO class exclusion (`src/stage4_train/`)**:
   - In `src/stage4_train/train.py`, add `resolve_device(config)` (`DEVICE_CHOICES = ("auto", "cpu", "cuda")`), raising loudly when `train.device: cuda` is configured without a visible GPU so runs never silently fall back to CPU. Add `runtime_id(config)` recording `device`, `device_name`, and PyTorch build in `recipe_fingerprint` and `run.json`. Update `macro_f1_points(labels, preds, n_classes, excluded=())` to skip `excluded` classes, move `model` and batch tensors `(x, y)` onto `device` inside `train_one`, call `model.cpu()` before `_save_torchscript(model, out_dir / MODEL_FILE)` so saved models stay device-neutral for Stages 5 and 6, and persist `"device"`, `"device_name"`, and `"excluded_classes"` in `run.json`.
   - In `src/stage4_train/run.py`, wire `sgd_step_fn` and the benchmark metadata to `resolve_device(config)`.
   - In `src/stage4_train/sampling.py`, add `_labels_for_batch(n, n_classes, excluded, rng)` and `excluded_classes: tuple[int, ...] = ()` on `make_batch` / `BatchStream` so `A1_loso_handdrawn_*` and `B_loso_handdrawn_*` never sample `ellipse` (since `github_handdrawn` is the sole source of `ellipse`).
   - In `src/stage4_train/sweep.py`, add `classes_lost_to_holdout(train_store)` (`tuple(int(c) for c in np.flatnonzero(train_store.class_counts() == 0))`) and pass `excluded_classes=excluded` into `train_one` when `holdout_source` is set, returning `[results[spec["run_name"]] for spec in jobs]` from `run_sweep` so `write_seed_disagreement` can compute per-arm pairwise disagreement.

2. **Stage 5 LOSO evaluation filtering and unit tests (`src/stage5_eval/`, `tests/stage5/`)**:
   - In `src/stage5_eval/evaluate.py`, add `excluded_labels: tuple[int, ...] = ()` to `ModelSpec` and apply `mask = ~np.isin(labels, spec.excluded_labels)` right after `source_filter`.
   - In `src/stage5_eval/run.py`, add `loso_excluded_classes(stage4_dir, name)` reading `excluded_classes` from `run.json` and `scored_macro_f1(y_true, y_pred, k)` averaging `per_class_f1` only over `present = np.unique(y_true)`.
   - Add unit tests in `tests/stage5/test_evaluate.py` (`test_excluded_labels_drop_rows_after_the_source_filter`) and `tests/stage5/test_run.py` (`test_loso_macro_f1_averages_only_the_scored_classes`, `test_loso_excluded_classes_read_from_run_json`).

## Validation
1. Ran `pytest tests/stage5/test_evaluate.py tests/stage5/test_run.py` and `python run_pipeline.py --check`; the Stage 5 LOSO filtering, `scored_macro_f1` (100.0 on partial-class arrays), and `run.json` `excluded_classes` tests all passed.
2. Ran the first full Stage 4 GPU sweep end-to-end; all training runs completed and saved CPU-neutral `model.pt` TorchScript files, **but the sweep crashed in the final `seed_disagreement` step** (`pairwise_disagreement` `ValueError: prediction shapes differ`).
3. Root-cause inspection showed `run_sweep` returned `results[spec["run_name"]]` from `run.json` without propagating `holdout_source`. Because `train_one` did not write `holdout_source` to `run.json`, `if run.get("holdout_source"): continue` in `seed_disagreement` never fired, causing the `2,371`-image `github_handdrawn`-held-out runs (`A1_loso_handdrawn_0`, `B_loso_handdrawn_0`) to be compared against the `2,819`-image normal runs.

## Our decision
The team committed the Stage 4 CUDA/LOSO and Stage 5 evaluation implementation and tests in `69b9265` (`8 files changed, 836 insertions(+), 700 deletions(-)` including line-ending normalization in `sweep.py` and `train.py`). Because validation on the first complete GPU sweep caught the omitted `holdout_source` propagation in `run_sweep` (causing `seed_disagreement` to crash on 2,371 vs 2,819 validation shapes), the team immediately opened a follow-up crash fix in T22 (`817dbc8`) before any test-split read.

## Measured effect
- `69b9265` landed across 8 files (`src/stage4_train/{run,sampling,sweep,train}.py`, `src/stage5_eval/{evaluate,run}.py`, `tests/stage5/test_{evaluate,run}.py`), passing all Stage 5 unit tests (`3` new LOSO test functions) and `run_pipeline.py --check`.
- First full GPU sweep trained all runs to completion with CPU-neutral TorchScript exports (`model.cpu()`), exposing the `seed_disagreement` 2,371-vs-2,819 shape mismatch resolved in T22 (`817dbc8`).

---

## : Gemini 4 Neon Corpus Synthesis (`T17` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `T17` (`task`)
* **Logic Depth:** **High** (implements `F02`'s 9-class LOSO masking + `D04` CUDA device support across Stages 4 and 5; directly opens `T22`)
* **Risk if Wrong:** **High** (first full GPU sweep **crashed in `seed_disagreement`** on `2,371` vs. `2,819` validation shapes because `run_sweep` did not propagate `holdout_source` $\rightarrow$ fixed in `T22`)
* **Adoption Status:** **Adopted with immediate follow-up fix (`T22`)** (commit `69b9265` followed by `817dbc8` prior to any sealed test-split read).

### 2. Group Synthesis: The LOSO / Class-Imbalance Chain (`F02` $\rightarrow$ `T17` $\rightarrow$ `T22`)

* **`F02` $\rightarrow$ `T17` $\rightarrow$ `T22`** is the corpus's clearest **implementation-caught-a-real-bug** sequence:
  1. **`F02`** established the three-part 9-class Hand-Drawn LOSO design (`ellipse` exists only in `github_handdrawn`).
  2. **`T17`** (`69b9265`) wired `excluded_classes` in `sampling.py`, `classes_lost_to_holdout` in `sweep.py`, `ModelSpec.excluded_labels` in Stage 5, and CUDA execution (`model.cpu()` TorchScript saves).
  3. On the first complete GPU sweep, every model trained cleanly, but `seed_disagreement` crashed comparing `2,371`-image held-out validation predictions against `2,819`-image full validation predictions because `train_one` did not persist `holdout_source` into `run.json`. **`T22`** (`817dbc8`) enriched `run_sweep`'s return dictionary with `holdout_source` and added a regression test before any test read occurred.

