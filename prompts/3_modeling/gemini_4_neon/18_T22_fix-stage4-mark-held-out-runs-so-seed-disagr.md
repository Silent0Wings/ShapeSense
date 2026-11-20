# 3_modeling - T22: fix(stage4): mark held-out runs so seed disagreement skips them
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T22 (`task`, `3_modeling`)
- Owner / Proposed by: 40297573 + 40211352 / gemini_4_neon + 40297573 + 40211352
- Calibration: `winning-decision (70% tier)`
- Grounding sources: src/stage4_train/sweep.py, tests/stage4/test_loso_device.py, src/stage4_train/train.py, ShapeSense_Deployed/web/stage4.html, git commit 817dbc8

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T22 (solved (not in log), stage `3_modeling`): fix(stage4): mark held-out runs so seed disagreement skips them. Propose or assist with the exact implementation, checks, and configuration needed for commit `817dbc8`.

## Response
`seed_disagreement(results_dir, runs)` in `src/stage4_train/sweep.py` already guards against leave-one-source-out (`LOSO`) runs with:

```python
if run.get("holdout_source"):
    continue
```

That guard is required because holding out `github_handdrawn` shrinks the validation split from `2,819` images to `2,371` images; comparing `val_probs.npz` across those two sets triggers `ValueError: prediction shapes differ` in `pairwise_disagreement()`. However, `train_one()` in `src/stage4_train/train.py` does not record `holdout_source` inside `run.json`, and `run_sweep()` currently returns `[results[spec["run_name"]] for spec in jobs]`. As a result, `run.get("holdout_source")` evaluates to `None` for `A1_loso_handdrawn_0` and `B_loso_handdrawn_0`, so the check never fires and the sweep crashes on its final step (`write_seed_disagreement`).

Apply the minimal fix directly at the return boundary of `run_sweep()` in `src/stage4_train/sweep.py` without altering `train_one()`'s public signature:

```python
    results.update(run_specs(config, pending, job_runner=job_runner))
    # run.json does not record the hold-out; callers need it to tell these runs apart.
    return [{**results[spec["run_name"]], "holdout_source": spec["holdout_source"]}
            for spec in jobs]
```

To lock this in, add a unit test `test_sweep_results_mark_held_out_runs_so_disagreement_skips_them(tmp_path)` in `tests/stage4/test_loso_device.py` that runs `sweep.run_sweep(..., loso=True, job_runner=fake_job)` with mismatched `val_probs.npz` lengths (`20` for `A1_0` and `A1_1`, `7` for `A1_loso_handdrawn_0` and `B_loso_handdrawn_0`), asserts `"holdout_source"` matches `None` vs `"github_handdrawn"`, and confirms `sweep.seed_disagreement(tmp_path, results)` includes only `["A1_0", "A1_1"]` under `out["per_arm"]["A1"]["runs"]` while omitting `"B"`.

Note: because this edits `src/stage4_train/sweep.py` before any test split read, it changes the tracked code recipe, so every Stage 4 run retrains cleanly under the fixed script.

## Validation
1. Ran `pytest tests/stage4/test_loso_device.py` and `python run_pipeline.py --check`; the new regression test `test_sweep_results_mark_held_out_runs_so_disagreement_skips_them` verified `held_out == {"A1_0": None, "A1_1": None, "A1_loso_handdrawn_0": "github_handdrawn", "B_loso_handdrawn_0": "github_handdrawn"}` and confirmed `seed_disagreement` skips the 7-row held-out runs without crashing.
2. Verified the patch is minimal (`2 files changed, 32 insertions(+), 3 deletions(-)`), applied strictly before any read of the test split.

## Our decision
The team kept the proposed `sweep.py` return-dict enrichment and `tests/stage4/test_loso_device.py` regression test verbatim in commit `817dbc8`, accepting the full GPU sweep retrain triggered by the recipe update before any test evaluation.

## Measured effect
- `src/stage4_train/sweep.py` (`+3/-1`) and `tests/stage4/test_loso_device.py` (`+29/-2`): `seed_disagreement` cleanly skips `2,371`-image `github_handdrawn` LOSO runs instead of crashing against `2,819`-image standard validation runs.
- Regression test `test_sweep_results_mark_held_out_runs_so_disagreement_skips_them` passes deterministically in `tests/stage4/test_loso_device.py`.

---

## Upgraded & Expanded: Gemini 4 Neon Corpus Synthesis (`T22` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `T22` (`task`)
* **Logic Depth:** **Medium** (fixes `T17`'s `holdout_source` omission in `run_sweep` to complete `F02`)
* **Risk if Wrong:** **Medium** (minimal `run_sweep` return-dict enrichment without altering `train_one`'s signature; triggered a full GPU retrain prior to any test read)
* **Adoption Status:** **Adopted verbatim** (commit `817dbc8`, `+3/-1` in `sweep.py` and `+29/-2` in `test_loso_device.py`).

### 2. Group Synthesis: The LOSO / Class-Imbalance Chain (`F02` $\rightarrow$ `T17` $\rightarrow$ `T22`)

* **`T22`** closes the `F02` $\rightarrow$ `T17` $\rightarrow$ `T22` chain. When `T17`'s first full GPU sweep crashed at the post-training `seed_disagreement` step (`2,371` Hand-Drawn-excluded validation images vs. `2,819` full validation images), `T22` enriched `run_sweep`'s returned dictionary with `"holdout_source": spec.get("holdout_source")` so `if run.get("holdout_source"): continue` in `seed_disagreement` fired as designed, backed by a unit test with deliberately mismatched `val_probs` lengths.

