# C28 — Upgraded & Expanded: Robustness Check Location

Below is a substantially expanded reconstruction of C28, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C28: Robustness check location

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-09
- **Entry:** C28 (`change`, `4_testing`)
- **Owner / Proposed by:** team / team
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `src/stage5_eval/robust.py`, `src/stage5_eval/run.py`, `src/common/perturb.py`, `src/common/hashing.py`, `tests/stage5/test_iteration3_repairs.py`, `results/phase2_snapshot/status5.json`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/robustness.html`, commits `ff1f269`, `4c7cb90`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> Our robustness check is a separate script that only reads validation. Should it move into Stage 5, and how do we build the perturbed sets once, hash them and make sure sealed sets are read in only one place?

**Implicit constraints (made explicit):**
1. The sealed-read contract (`test_access.log` / `reads_outside(run_id, READER)`) must be **enforced**, not merely documented.
2. Perturbed sets must be **built exactly once** and **verified on every reuse** — not silently regenerated.
3. The perturbation primitives must be **shared** so validation and holdout robustness use identical transforms.
4. The solution must **fail loudly** on drift, tampering, or accidental direct CSV reads — not degrade silently.
5. Cached predictions must be **keyed** so a model change or manifest change invalidates them automatically.

---

## Response

Yes — move the robustness evaluator into Stage 5 as `src/stage5_eval/robust.py` (invoked from `src/stage5_eval/run.py`), and move the shared perturbation primitives into `src/common/perturb.py` so every sealed split read stays confined to `READER = "src.stage5_eval.evaluate"`.

### 1. Why it must live inside Stage 5

A standalone `robustness/run.py` cannot read sealed splits (`fresh_holdout_2.csv`) without violating the `test_access.log` contract enforced by `reads_outside(run_id, READER)`. Any read outside `src.stage5_eval.evaluate` fails `test_reads_ok` and breaks `run_pipeline.py`'s single-place sealing guarantee.

**Why "move it in" rather than "widen the reader" (complex logic):**
- Widening `READER` to include a second module would make the single-reader guarantee *auditable only by convention* — a future contributor could add a third reader and no test would catch it without a hardcoded list.
- Keeping `READER` as a single string means `reads_outside` is a **structural** check: any read from any other module fails, regardless of who added it.
- The robustness evaluator legitimately needs the sealed images; the correct fix is to move the *evaluator* into the trusted reader's call graph, not to move the *trust boundary* outward.

### 2. Building once, hashing, and verifying on every reuse

Implement `robust.sets_for(images, levels, seed, out_dir, manifest_hash)` in `src/stage5_eval/robust.py`, wired into `evaluate_fn` in `src/stage5_eval/run.py`:

**2.1 Single sealed read per model.**
`evaluate_fn` calls:

```python
evaluate.evaluate_models(
    config, arm_specs,
    evaluate.fresh_holdout_reader(config, robust_cfg["split"]),
    d["predictions_fresh2"],
    manifest_hash=fresh2_hash,
)
```

which returns `ev["fresh2"]["images"]` from that single counted read (`n_reads = 25` arm models in Iteration 3). The perturbed sets are derived **from that in-memory image array**, not from a second CSV read.

**2.2 Build once + SHA-256 manifest.**
`sets_for` writes `artifacts/stage5/perturbed_fresh2/manifest.json` storing:
- `manifest_hash` — SHA-256 of `fresh_holdout_2.csv` bytes, verified via `sha256_path` **without logging a split read** (hashing bytes is not a read of the split's contents in the access-log sense; this distinction must be documented in `src/common/hashing.py`).
- `"sets"` — a map `{level_name: sha256_path(path)}`.

For each level not yet recorded, it calls `build_set(name, images, seed)` **once** with `seed = 20261109` and writes `artifacts/stage5/perturbed_fresh2/<name>.npz` via `np.savez_compressed`.

**Why "build once" is load-bearing (depth):** perturbation is stochastic (Gaussian noise, salt-and-pepper, etc.). If the sets were rebuilt per run, two runs with the same seed but different library versions, BLAS backends, or float paths could produce *slightly* different arrays — silently breaking reproducibility across machines. Freezing the `.npz` and hashing it converts "same seed" into "byte-identical artifact," which is a stronger and machine-independent guarantee.

**2.3 Tamper & drift checks.**
On any subsequent call:
- If `stored["manifest_hash"] != manifest_hash` → `RuntimeError` (the split changed under us).
- If `sha256_path(path) != stored["sets"][name]` → `RuntimeError` (a `.npz` was modified or corrupted).
- If a set is missing **and** `images is None` (e.g., all clean predictions came from cache) → `RuntimeError`, instead of silently regenerating or reading the CSV directly.

**Why the `images is None` branch is the subtle one (edge case):** the cache-hit path is exactly where a naive implementation would "helpfully" fall back to re-reading the CSV to rebuild a missing set. That fallback would (a) log an unexpected sealed read, and (b) produce a set that may not match the frozen hash. Raising instead forces the operator to fix the missing artifact through the sanctioned path.

**2.4 Cached per-(model, level) predictions.**
`robust.predict_levels(...)` writes predictions to `artifacts/stage5/predictions_robust/<model>/<level>.npz`, keyed by `(spec.fingerprint, manifest_hash)`, and never touches `fresh_holdout_2.csv`.

**Why key on both (depth):** `spec.fingerprint` alone would serve stale predictions after a split change; `manifest_hash` alone would serve stale predictions after a model/checkpoint change. The pair invalidates on either.

**2.5 Single-reader accounting.**
`analyse_fn` sums `expected = ev["n_reads"] + fresh_reads + fresh2_reads` and asserts `test_reads_ok(test_reads, expected, extra_reads)` where `extra_reads == 0`.

**Why sum-then-assert rather than assert-per-source:** a single total catches the case where one source under-reads and another over-reads by the same amount (a plausible bug when refactoring readers). Per-source assertions would miss that.

---

## Validation

The team implemented `src/stage5_eval/robust.py` and wired it into `src/stage5_eval/run.py` (commits `ff1f269`, `4c7cb90`), verified by `tests/stage5/test_iteration3_repairs.py` and `tests/stage5/test_run.py`, covering:

| Test | What it proves |
|---|---|
| Hash-mismatch failure | A modified `fresh_holdout_2.csv` raises before any set is used. |
| Manifest-drift detection | A modified `.npz` raises rather than being silently consumed. |
| Cache hits | Repeated runs reuse `.npz` and predictions without re-reading the CSV. |
| `reads_outside == 0` | No module outside `src.stage5_eval.evaluate` read a sealed split. |

During Iteration 3 Stage 5 execution and the clean-clone rehearsal (`status5.json`):
- All `23` `.npz` files in `artifacts/stage5/perturbed_fresh2/` matched their `manifest.json` SHA-256 digests.
- `extra_reads` remained `0`.

---

## Our decision

Adopted Gemini 4 Neon's Stage 5 integration **verbatim**:

- Moved robustness evaluation into `src/stage5_eval/robust.py` (`evaluate_fn` → `robust.sets_for` → `robust.predict_levels` → `robust.analyse`).
- Kept `src/stage5_eval/evaluate.py` as the **sole reader** of `test.csv`, `fresh_holdout.csv`, and `fresh_holdout_2.csv`.
- Froze the `23` hashed `.npz` perturbation sets for `fresh_holdout_2`.

**Rationale for verbatim adoption (depth):** every alternative considered violates at least one implicit constraint:
- *Standalone script with widened reader* → breaks constraint 1 (structural, not conventional, enforcement).
- *Rebuild sets per run* → breaks constraint 2 (reproducibility across machines).
- *Fallback-to-CSV on missing set* → breaks constraint 4 (silent degradation).
- *Cache keyed on model only* → breaks constraint 5 (stale predictions after split change).

Verbatim adoption is the only option that satisfies all five simultaneously.

---

## Measured effect

**Zero unaccounted sealed reads** (`results/phase2_snapshot/status5.json`):

| Component | Reads |
|---|---|
| `test.csv` | 27 |
| `fresh_holdout.csv` | 20 |
| `fresh_holdout_2.csv` (arm models) | 25 |
| LOSO | 15 |
| Additional reads accounted by `evaluate` | 5 |
| **Total expected** | **92** |
| **Total actual** | **92** |
| **`extra_reads`** | **0** |
| **`test_reads_ok`** | **True** |

**Reproducible hashed artifacts:**
- All `23` perturbed copies of `fresh_holdout_2` (`4,500` images each) built once under `seed = 20261109` and verified by SHA-256.
- Clean-clone rehearsal reproduced `robust_results.json` and `robust_comparisons.csv` identically (`+9.20`, CI `[8.89, 9.53]`).

**Interpretation (depth):** the clean-clone rehearsal is the load-bearing evidence here — it demonstrates that the frozen `.npz` artifacts, not the seed alone, are what reproduce the result. `extra_reads = 0` across a full rehearsal is the audit proof that the single-reader contract held through a complete pipeline run, not just in unit tests.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added the **"why move it in, not widen the reader"** argument (structural vs conventional enforcement) | Logical rigor |
| 3 | Explained **why "build once" is load-bearing** (machine-independent reproducibility vs seed-only) | Depth |
| 4 | Added the **`images is None` edge case** analysis (the cache-hit path where naive fallback would occur) | Edge-case logic |
| 5 | Explained **why cache keys on both `spec.fingerprint` and `manifest_hash`** | Depth |
| 6 | Explained **why sum-then-assert** catches offsetting read errors that per-source assertions miss | Logical rigor |
| 7 | Converted validation into a **table** mapping each test to the constraint it proves | Auditability |
| 8 | Added **alternative-rejection rationale** for verbatim adoption (each alternative violates a named constraint) | Decision depth |
| 9 | Converted read accounting into a **table** and added an **interpretation** paragraph tying rehearsal to audit proof | Clarity |
| 10 | Flagged `sha256_path` vs "logging a split read" as a **distinction requiring documentation** in `src/common/hashing.py` | Failure-mode anticipation |

**Open questions / assumptions (for the team to confirm):**
- Is the `sha256_path`-is-not-a-read distinction **documented in `src/common/hashing.py`**, or only implicit? A future contributor could reasonably assume hashing a file counts as reading it and either skip the hash check or add a spurious access-log entry.
- Does `manifest.json` record the **library versions** (numpy, scipy, PIL) used to build the `.npz`? If a future environment upgrade changes perturbation behavior, the frozen `.npz` remains valid, but a *rebuild* would silently differ. Recording versions makes the rebuild-vs-reuse decision explicit.
- Is the `n_reads = 25` arm-model count **derived from `arm_specs`** or hardcoded? If hardcoded, adding an arm would break the accounting silently.
- Does `test_run.py` cover the **offsetting under/over-read** case (one source under, another over, total matches)? The sum-then-assert design handles it, but the test should prove it does.
- Is `robust_comparisons.csv` covered by the same SHA-256 manifest pattern as the `.npz` sets, or is it a derived artifact that can legitimately vary (e.g., bootstrap seed)? The rehearsal reproduced it identically, but the guarantee should be stated explicitly.

---

### Additional Depth Notes (`C28`): Orthogonal Guards & Worked Tamper-Detection Paths
1. **Orthogonality of Access Control (`reads_outside`) vs. Integrity Control (`manifest.json`):**
   - `READER = "src.stage5_eval.evaluate"` + `reads_outside(run_id, READER) == 0` enforces **who** may touch a sealed split and **how many times** (`test_reads == expected`).
   - `perturbed_fresh2/manifest.json` (`manifest_hash` + per-level SHA-256 digests) enforces **what** bytes are consumed on cache hits when no split read occurs. Both guards are required: access logs without hashes miss on-disk `.npz` corruption during cached reruns, while hashes without access logs miss unauthorized scripts reading the raw CSV.
2. **Exact `RuntimeError` Paths Verified in `tests/stage5/test_iteration3_repairs.py`:**
   - **Path A (Split Manifest Drift):** `sets_for()` compares `stored["manifest_hash"]` against `manifest_hash` (`sha256_path(fresh_holdout_2.csv)`); any mismatch immediately raises `RuntimeError` (`test_perturbed_sets_refuse_a_different_manifest_or_a_changed_file`).
   - **Path B (Perturbed `.npz` Tampering):** Before loading `perturbed_fresh2/<level>.npz`, `sets_for()` recomputes `sha256_path(path)` and raises `RuntimeError` if it differs from `stored["sets"][level]`.
   - **Path C (Missing `.npz` When `images is None`):** On a cached prediction run where `ev["fresh2"]["images"]` is `None`, if any `<level>.npz` is missing from disk, `sets_for()` raises `RuntimeError` rather than falling back to reading `fresh_holdout_2.csv`.
