# 4_testing - A17: The gallery refresh forces an extra test read.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A17 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/run.py, src/stage5_eval/evaluate.py, tests/stage5/test_run.py, results/phase2_snapshot/status5.json, results/phase2_snapshot/iter2_status.json, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/changes.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The gallery refresh forces an extra test read.

## Response
In `src/stage5_eval/run.py`, `evaluate_fn` starts by calling `gallery_refresh_name(specs, err_path, candidate, ...)` and deleting a cached prediction file before running `evaluate.evaluate_models`:

```python
refresh = gallery_refresh_name(specs, err_path, candidate, error_stamp)
if refresh is not None:
    evaluate.cache_path(d["predictions"], refresh).unlink(missing_ok=True)
ev = evaluate.evaluate_models(config, specs, evaluate.default_test_reader(config),
                              d["predictions"], manifest_hash=manifest_hash)
```

Because `gallery_refresh_name` picks the first candidate arm member (`_arm_of(spec) == candidate`, e.g., `B_0` or `A2_0`) and unlinks its `.npz` prediction cache, this forces an extra call to `default_test_reader(config)` - and therefore an extra logged read of `configs/splits/test.csv` in `artifacts/test_access.log` - solely to populate `ev["images"]` for rendering the error gallery PNGs (`errors_square_diamond.png`, `errors_square_rectangle.png`, `errors_circle_ellipse.png`).

### Why this looks problematic
1. **Cache-invalidation side effect:** Unlinking an already-valid prediction cache violates the spirit of "one read per model" whenever Stage 5 is re-run, because a visualization step (`figures.error_gallery`) is causing an additional sealed test read even though all model predictions are already cached.
2. **Tight coupling:** Visual gallery generation should ideally be decoupled from test-split reads - either by skipping galleries cleanly (`GALLERIES_SKIPPED = "skipped (cache)"`) when no fresh read occurred in the current run instead of deleting a prediction cache, or by treating gallery refresh as an opt-in diagnostic flag so `evaluate_models` never invalidates its own cache for plotting.

## Validation
- Inspected `src/stage5_eval/run.py` (`gallery_refresh_name`, `gallery_errors`, `evaluate_fn`, `expected` read calculation) and `tests/stage5/test_run.py::test_no_unaccounted_gallery_read`.
- Checked the two key conditions that Gemini's critique overstated:
  1. `gallery_refresh_name` returns `None` whenever `_error_cache_current(err_path, error_stamp)` is `True`, so it does **not** force a read on normal cached reruns - it only fires if the error file is missing (or stale after A16's stamp check) when all candidate caches already exist.
  2. When it does fire, unlinking `refresh` causes `evaluate.evaluate_models` to evaluate that one model through `default_test_reader` (`src.stage5_eval.evaluate`), which increments `ev["n_reads"]` and `expected`, appends one line to `artifacts/test_access.log`, and keeps `extra_reads == 0`.
- Verified in `results/phase2_snapshot/status5.json` (`run_id`: `2026-11-10T05:27:17-05:00/933815`) that `models_from_cache` is `[]` and `test_reads == 92 == test_reads_expected` (`extra_reads == 0`); in Iteration 2 (`iter2_status.json`), `test_reads == 52 == test_reads_expected` (`extra_reads == 0`).

## Our decision
Verdict: **Partly**. State: **No action**. The team concluded that Gemini's claim only partially holds: the refresh only occurs when the error cache is missing (or stale under A16), never on a normal cached rerun, and when it occurs it goes through the audited model reader and is fully counted in `test_reads` and `expected` (`extra_reads == 0`). No change to `gallery_refresh_name` was needed.

## Measured effect
- On normal Stage 5 runs with all models freshly evaluated (`status5.json`), `ev["images"]` is already returned by `evaluate_models` with `0` additional reads (`92` of `92` expected reads; `extra_reads: 0`).
- On cached reruns where `ensemble_<candidate>_errors.npz` already exists and matches `error_stamp`, `gallery_refresh_name` returns `None` and `0` test reads occur; only if `errors.npz` is missing does one counted model read occur (`test_no_unaccounted_gallery_read` in `tests/stage5/test_run.py`). `ShapeSense_Deployed/web/changes.html` records A17 as `Partly` / `No action`.

---

## Upgraded Audit Entry (A17)

### Part II — Sealed-Read Accounting Cluster (`A17`)

### A17 — Gallery refresh forces an extra test read

**Steelman of the critique.** Unlinking a valid prediction cache to force `ev["images"]` for a *visualization* violates the "one read per model" invariant in spirit. On a cached rerun, a plotting concern should not increment `n_reads`.

**Expanded rebuttal logic.** The claim overstates on three counts, each checkable:

1. **Gating on error-cache currency.** `gallery_refresh_name` returns `None` whenever `_error_cache_current(err_path, error_stamp)` is `True`. So on *any* normal cached rerun with a current error cache, zero reads occur. The refresh fires only when the error file is missing or (post-A16) stamp-stale — i.e., when a read is *already* necessary to regenerate a legitimately invalid artifact.
2. **Accounting closure.** When it does fire, the unlinked model re-evaluates through `default_test_reader = src.stage5_eval.evaluate`, which *increments both* `ev["n_reads"]` and `expected`. So `test_reads == expected` and `extra_reads == 0` — the read is not "extra," it is *counted*, and the audit (A15, post-fix) confirms it.
3. **Idempotency evidence.** `status5.json` shows `models_from_cache: []` and `92 == 92`; `iter2_status.json` shows `52 == 52`. `test_no_unaccounted_gallery_read` pins the cached-rerun case at zero extra reads.

**Deeper verdict.** "Partly" is the honest calibration: the *mechanism* (unlink-to-refresh) is real, but the *harm* (uncounted extra read) does not occur because the read is funneled through the audited reader and counted. The residual design smell — viz coupled to cache invalidation — is real but has no measured correctness cost. A stronger future design would decouple via an opt-in `--refresh-galleries` flag, which the entry fairly notes as the "ideal" alternative.

**Ordering dependency (`A16` ↔ `A17`).** `A16` (error-cache stamp) is a *prerequisite* for `A17`'s refresh behavior to be correct rather than accidental: because `A16` ensures the error cache is invalidated on genuine model/preprocessing/manifest staleness and preserved otherwise, `A17`'s single counted read fires if and only if an error-gallery rebuild is legitimately required.

