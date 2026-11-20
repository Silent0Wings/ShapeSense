# 4_testing - A18: Prediction cache keys miss preprocessing code.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A18 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/evaluate.py, src/common/features.py, src/stage5_eval/robust.py, tests/stage5/test_iteration3_repairs.py, tests/stage5/test_evaluate.py, results/phase2_snapshot/status5.json, ShapeSense_Deployed/web/changes.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Prediction cache keys miss preprocessing code.

## Response
In `src/stage5_eval/evaluate.py`, `model_fingerprint(path)` currently returns only `sha256_path(path)` - the SHA-256 digest of the serialized model artifact (`model.pt` for TorchScript CNNs or `<kind>.joblib` for scikit-learn baselines). When `evaluate_models` (and `robust.predict_levels`) checks `cached_for(path, spec.fingerprint, manifest_hash)`, a cached `.npz` file in `artifacts/stage5/predictions/` (or `predictions_fresh/`, `predictions_fresh2/`, `predictions_robust/`) is reused whenever `rec["model_hash"] == spec.fingerprint` and `rec["manifest_hash"] == manifest_hash`.

### Silent staleness flaw
Stage 5 does **not** store raw inference preprocessing inside the `.pt` or `.joblib` weights alone; both predictors transform `uint8` images through `src/common/features.py`:
- `predict_torchscript` divides `images_u8` by `np.float32(PIXEL_SCALE)` (`255.0` from `src/common/features.py`) before building `(N, 1, S, S)` tensors.
- `predict_baseline` calls `pixel_features(images_u8)` or `hog_features(images_u8, hog_pixels_per_cell)` (`ORIENTATIONS = 9`, `CELLS_PER_BLOCK = 2`, `/ PIXEL_SCALE`) from `src/common/features.py`.

Although `src/stage5_eval/run.py::inputs(config)` tracks `sha256_path(resolve("src/common"))` in `status.json`, `evaluate.cached_for` does not include the preprocessing code hash in `ModelSpec.fingerprint`. Consequently, any edit to `src/common/features.py` (such as changing `PIXEL_SCALE`, dtype casting, or HOG parameters) leaves `model_hash` unchanged and causes `cached_for` to silently serve stale predictions from disk without re-running inference.

### Recommended fix
Define `PREPROCESSING_CODE = "src/common/features.py"` in `src/stage5_eval/evaluate.py` and include its content hash in `model_fingerprint`:

```python
PREPROCESSING_CODE = "src/common/features.py"

def model_fingerprint(path: str | Path) -> str:
    """The model file and the code that prepares its inputs, so a change to either is seen."""
    return f"{sha256_path(path)}+{sha256_path(resolve(PREPROCESSING_CODE))}"
```

Because `build_specs` uses `evaluate.model_fingerprint` for every CNN, baseline, and LOSO `ModelSpec`, and both `evaluate_models`, `robust.predict_levels`, and `error_stamp` in `run.py` key off `spec.fingerprint`, this single change invalidates every prediction cache and error cache automatically whenever `src/common/features.py` changes.

## Validation
- Inspected `src/stage5_eval/evaluate.py` (`PREPROCESSING_CODE`, `model_fingerprint`, `cached_for`, `predict_torchscript`, `predict_baseline`), `src/common/features.py`, and `src/stage5_eval/robust.py` (`predict_levels`).
- Verified `test_preprocessing_code_is_part_of_the_prediction_key` in `tests/stage5/test_iteration3_repairs.py`, which creates a dummy `m.pt` and asserts `"+" in evaluate.model_fingerprint(model)` (confirming both model hash and `src/common/features.py` hash are embedded).
- Checked `results/phase2_snapshot/status5.json` (`inputs["common"]` hash recorded and `models_from_cache: []` during the final Iteration 3 evaluation).

## Our decision
Verdict: **Stands**. Fixed in iteration 3 (commit `4c7cb90`). `evaluate.model_fingerprint` in `src/stage5_eval/evaluate.py` now concatenates `sha256_path(path)` and `sha256_path(resolve("src/common/features.py"))` with `"+"`, covering all clean, fresh-holdout, LOSO, baseline, and robustness prediction caches.

## Measured effect
- All prediction caches (`predictions/`, `predictions_fresh/`, `predictions_fresh2/`, `predictions_robust/`) and `error_stamp` now invalidate automatically upon any change to `src/common/features.py`, eliminating silent stale-cache hits after preprocessing edits.
- Iteration 3 ran cleanly with `models_from_cache: []` and `92` of `92` expected test/holdout reads (`results/phase2_snapshot/status5.json`); `ShapeSense_Deployed/web/changes.html` records A18 as `Stands` / `Fixed in iteration 3`.

---

## Upgraded Audit Entry (A18)

### Part I — Audit-Gap & Cache-Integrity Cluster Context (`A15`, `A16`, `A18`, `A26`)
Entries `A15`, `A16`, `A18`, and `A26` share one root pathology: **an assertion that looks like a measurement but is actually a constant, or a cache key that is narrower than the thing it claims to fingerprint.**

### A18 — Prediction cache keys miss preprocessing code

**Expanded failure-mode trace.** `model_fingerprint(path) = sha256_path(path)` fingerprints *weights only*. But inference is `weights ∘ preprocessing`, and preprocessing lives in `src/common/features.py` (`PIXEL_SCALE = 255.0`, HOG `ORIENTATIONS=9`, `CELLS_PER_BLOCK=2`). The composed function's behavior changes when *either* factor changes, yet the key hashes only one. This is a **partial-function fingerprint** — a classic cache-key-under-specification bug:

- Edit `PIXEL_SCALE` 255→1.0: `model_hash` unchanged → `cached_for` returns the old `.npz` → predictions are the *old* preprocessing's outputs silently relabeled as the new code's.
- Edit HOG params: same, and the baseline `predict_baseline` path is affected while CNN is not — so the bug is **arm-selective**, making it harder to spot by aggregate metrics.

**Why "run.py already hashes `src/common`" is insufficient.** `inputs(config)` records `sha256_path(resolve("src/common"))` in `status.json` for *provenance*, but `cached_for` never consults it. Provenance ≠ cache key. The fix must put the code hash *inside* `spec.fingerprint`, which `build_specs` uses for every CNN/baseline/LOSO spec, and which `evaluate_models`, `robust.predict_levels`, and `error_stamp` all key off. This single-point change gives **transitive invalidation**: edit `features.py` → every prediction cache, every error cache, every robustness cache invalidates automatically. The test asserting `"+" in model_fingerprint(model)` is a structural pin that the hash is *composed*, not merely *present*.

**Complexity note.** Concatenating hashes with `"+"` is not cryptographic composition — it's a namespace separator, which is fine here because both operands are fixed-length hex; a reviewer should confirm no collision-by-concatenation ambiguity (there is none for two 64-hex digests joined by a non-hex separator).

### Cross-Cutting Failure Signature: The Composed-Function Key
If `f = g ∘ h`, the cache key must hash *both* `g` and `h`. Hashing weights (`g`) but not preprocessing (`h`) is the canonical instance.

