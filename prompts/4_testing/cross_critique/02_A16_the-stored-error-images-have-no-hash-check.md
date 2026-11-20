# 4_testing - A16: The stored error images have no hash check.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A16 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/run.py, src/stage5_eval/evaluate.py, tests/stage5/test_iteration3_repairs.py, results/phase2_snapshot/status5.json, results/phase2_snapshot/iteration_log.json, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/changes.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: The stored error images have no hash check.

## Response
In `src/stage5_eval/run.py`, Stage 5 caches misclassified test images for the candidate ensemble in `artifacts/stage5/predictions/ensemble_<candidate>_errors.npz` (e.g., `ensemble_B_errors.npz` or `ensemble_A2_errors.npz`) so that subsequent runs can render the confusion-pair error galleries (`errors_square_diamond.png`, `errors_square_rectangle.png`, `errors_circle_ellipse.png`) without re-reading the test split when all per-seed predictions are served from cache.

Currently, both `gallery_refresh_name(specs, err_path, candidate)` and `gallery_errors(images, err_path, y, pred_b, image_ids)` only check whether the file exists on disk:
- `gallery_refresh_name` returns `None` if `Path(err_path).is_file()`.
- `gallery_errors` loads `z["images"]`, `z["labels"]`, and `z["preds"]` whenever `images is None` and `err_path.is_file()`.

Neither function stores or verifies a cryptographic stamp tying the cached error images to the current candidate models or the current test manifest.

### Failure mode
1. **Model or preprocessing updates:** If the candidate models are retrained (changing `model.pt`), `src/common/features.py` changes, or the `candidate` role in `configs/pipeline.yaml` changes while an older `ensemble_<candidate>_errors.npz` remains on disk, and `ev["images"]` is `None` (because predictions were already cached or only some models refreshed), `gallery_errors` silently loads stale images, labels, and predictions from the previous run and plots outdated error galleries.
2. **Manifest updates:** If `configs/splits/test.csv` is re-frozen, `evaluate.evaluate_models` rejects stale per-seed prediction caches via `manifest_hash`, unless a stale `errors.npz` check prevents refresh or a legacy `errors.npz` is read when `images` is `None`.

### Recommended fix
1. Construct an `error_stamp` in `src/stage5_eval/run.py` combining the fingerprints of every full-split candidate arm member and the SHA-256 of `test.csv`:
   ```python
   error_stamp = "+".join(
       s.fingerprint for s in specs
       if s.extra.get("arm") == candidate and is_full_split_spec(s)
   ) + "@" + manifest_hash
   ```
2. Write `stamp=np.asarray(stamp)` inside `np.savez_compressed(err_path, ...)` in `gallery_errors`.
3. Add `_error_cache_current(err_path, stamp)` to verify `err_path.is_file()` and `str(z["stamp"]) == stamp` (returning `False` on `OSError`, `KeyError`, or `ValueError` so legacy un-stamped files are rejected), and call `_error_cache_current` in both `gallery_refresh_name` and `gallery_errors`.

## Validation
- Inspected `src/stage5_eval/run.py` (`_error_cache_current`, `gallery_refresh_name`, `gallery_errors`, and `error_stamp` in `run()`).
- Verified the unit test `test_stale_error_images_are_not_reused` in `tests/stage5/test_iteration3_repairs.py`, which writes `errors.npz` under stamp `"models-1"`, confirms `gallery_errors(None, path, y, pred, ids, "models-1")` returns the cached arrays, and confirms `gallery_errors(None, path, y, pred, ids, "models-2")` returns `None`.
- Verified in `results/phase2_snapshot/status5.json` that Iteration 3 generated `artifacts/stage5/predictions/ensemble_A2_errors.npz` (`sha256:ef476d1c...`), `errors_square_diamond.png`, `errors_square_rectangle.png`, and `errors_circle_ellipse.png` with `metrics.galleries == "rendered"`.

## Our decision
Verdict: **Stands**. Fixed in iteration 3 (commit `4c7cb90`). `gallery_errors` now persists `stamp` (candidate full-split model fingerprints plus `test_manifest` SHA-256), and `_error_cache_current` ignores any missing, un-stamped, or mismatched error cache in both `gallery_refresh_name` and `gallery_errors`.

## Measured effect
- Stale or un-stamped `ensemble_<candidate>_errors.npz` files are deterministically ignored (`None` returned or one candidate prediction cache invalidated for refresh), preventing silent mismatch between rendered `errors_*.png` figures and the evaluated ensemble.
- In Iteration 3 (`status5.json`), `metrics.galleries` is `"rendered"` across all three configured confusion pairs (`[square, diamond]`, `[square, rectangle]`, `[circle, ellipse]`) while keeping `checks.test_reads == 92` of `92` expected (`checks.extra_reads == 0`). On the public site (`ShapeSense_Deployed/web/stage5.html`), the error gallery PNGs are intentionally omitted because they contain sealed test images.

---

## Upgraded Audit Entry (A16)

### Part I — Audit-Gap & Cache-Integrity Cluster Context (`A15`, `A16`, `A18`, `A26`)
Entries `A15`, `A16`, `A18`, and `A26` share one root pathology: **an assertion that looks like a measurement but is actually a constant, or a cache key that is narrower than the thing it claims to fingerprint.** They are the most dangerous class of flaw in a sealed-evaluation pipeline because they produce *green checks that cannot go red*.

### A16 — Stored error images have no hash check

**Expanded failure-mode trace.** `gallery_errors` previously gated on `err_path.is_file()` alone. The silent path is: predictions cached → `ev["images"] is None` → `gallery_errors` loads `z["images"]/["labels"]/["preds"]` from a *stale* `ensemble_<candidate>_errors.npz`. Three independent staleness axes are conflated into one existence check:

- **Model axis:** `model.pt` retrained for one arm member → predictions invalid, but error gallery still "exists."
- **Code axis:** `src/common/features.py` preprocessing changed (see A18) → same.
- **Manifest axis:** `test.csv` re-frozen → `manifest_hash` rejects per-seed caches, but the *error* cache is checked before that rejection can propagate.

Crucially, the failure is **conditional on `images is None`** — so it only manifests on *cached reruns*, which is exactly when nobody is watching the rendered PNGs. A full fresh run masks the bug entirely; it appears only in the reproducibility/idempotency path, which is the path least likely to be manually inspected.

**Deepened fix rationale.** The `error_stamp = fingerprints_of_full_split_arm_members + "@" + manifest_hash` composes the *same* two staleness sources that govern prediction caches, plus the manifest. `_error_cache_current` must return `False` (not raise) on `OSError`/`KeyError`/`ValueError` so that **legacy un-stamped files are treated as stale, not as fatal** — this is a deliberate fail-closed-to-refresh policy that preserves backward compatibility while eliminating the silent-hit path. The `test_stale_error_images_are_not_reused` test pins the exact contract: same stamp → cache hit; different stamp → `None` → forced refresh.

**Second-order insight.** Note the interaction with A17: a stamp mismatch here *invalidates* the error cache, which then triggers `gallery_refresh_name` to unlink a prediction cache. So A16's fix and A17's "no action" verdict are coupled — A16 makes the refresh *correct* (only fires on genuine staleness), which is precisely why A17's extra read is acceptable.

