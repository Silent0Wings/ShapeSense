# 4_testing - T05: feat(stage0): add pipeline runner, hash cache and migration check
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T05 (`task`, `infrastructure (supports testing)`)
- Owner / Proposed by: 40297573 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: run_pipeline.py, src/stage0_infra/__init__.py, src/stage0_infra/data_archive.py, src/stage0_infra/migration.py, src/stage0_infra/run.py, tests/stage0/test_data_archive.py, tests/stage0/test_guards_block_violations.py, tests/stage0/test_migration_compare.py, tests/stage0/test_runner.py, tests/stage0/test_stage0_inputs.py, README.md, docs/crisp_dm/iteration_log.json, ShapeSense_Deployed/web/index.html, ShapeSense_Deployed/web/stage0.html, git commit 6af8b0b

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T05 (built, stage `infrastructure (supports testing)`): feat(stage0): add pipeline runner, hash cache and migration check. Propose or assist with the exact implementation, checks, and configuration needed for commit `6af8b0b`.

## Response
Commit `6af8b0b` implements the Stage 0 infrastructure (`src/stage0_infra/`) and upgrades the root orchestrator (`run_pipeline.py`) so every run is guarded, idempotent via content hashing, and provably equivalent to the pre-refactor Phase 1 dataset scripts:

1. **Root orchestrator (`run_pipeline.py`)**
   - Always execute guards first (`lint-imports` + `pytest tests/contracts`). Any guard failure aborts before a single stage runs; `--check` runs guards only.
   - Mint one `run_id` per invocation and pass it to every stage's `artifacts/stageN/status.json`.
   - Resolve `dependency_closure(requested, depends)` using `stage_depends()` (inspecting each module's `DEPENDS` attribute dynamically without executing stage code).
   - For each stage in topological order, compute `stage.inputs(config)`. If the recorded `inputs` dictionary in `artifacts/stageN/status.json` matches and the prior `status` is `"passed"`, skip the stage as `"cached"` unless `--force` is given; if any stage fails, stop immediately before downstream stages execute.
   - Expose `--stages`, `--check`, `--force`, `--dashboard`, and `--demo`, plus `restore_frozen_winners()` when frozen iteration search outputs are needed downstream.

2. **Stage 0 runner (`src/stage0_infra/run.py`)**
   - Set `STAGE = "stage0"`, `DEPENDS = []`, `BUILD_MODULE = "src.stage1_freeze.build_unified_dataset"`, and `CODE_DIRS = {"code": "src/stage0_infra", "common": "src/common", "build_code": "src/stage1_freeze"}`.
   - In `inputs(config)`, hash `CODE_DIRS`, `requirements.txt`, `.python-version`, and `paths["catalog"]` via `sha256_path()`, and use `raw_fingerprint(paths["raw_dir"], exclude=[Path(paths["unified_dir"]).name])` returning `"files=<n>;bytes=<total>"`. Using a file-count/byte-total fingerprint in `inputs()` avoids hashing ~187k+ raw files on every cache check while never referencing files that `run()` itself writes (preventing cache churn).
   - In `migration_check()`, invoke `BUILD_MODULE` via `subprocess.run([sys.executable, "-m", BUILD_MODULE, "--out", str(rebuild), "--data", str(raw)], ...)` into `artifacts/stage0/rebuild/` rather than importing `src.stage1_freeze`, preserving the `.importlinter` `stages-independent` contract and never writing to `data_set/`.
   - In `run(config)`, run `migration_check()` to produce `artifacts/stage0/migration_check.json`, then compute the full content digest via `archive_sha256()` into `artifacts/stage0/data_archive_sha256.txt`.

3. **Deterministic raw archive digest (`src/stage0_infra/data_archive.py`)**
   - Implement `archive_sha256(root, exclude=None)` using `scan_files(root)`, filtering out top-level `exclude` (such as `"unified"`), sorting `(rel, entry.path)` lexicographically, and feeding `hash_named_files(files)` so identical archives yield identical `"sha256:<hex>"` digests across filesystems and OSes regardless of timestamps or directory order.

4. **Migration equivalence check (`src/stage0_infra/migration.py`)**
   - Compare `data_set/unified/` (`before`) against `artifacts/stage0/rebuild/` (`after`) across five fields (`COMPARED = ["catalog_content", "rows", "class_counts", "phash_groups", "metadata_content"]`):
     - Read `catalog.sqlite` read-only (`?mode=ro`) across `TABLES = ["Source", "Label", "LabelMapping", "Image", "AugmentationRecord"]`, sorting rows deterministically with `key=repr` and hashing with `sha256_obj()`.
     - Recompute per-`(source_id, label_name)` pHash clusters via `near_dup_groups(..., max_hamming)` from `metadata.csv` (matching Phase 1 scope prior to Stage 1's Decision 15 global regrouping) and compare `metadata_content` sorted by `(key, value)`.
     - Return `{"equal": not diffs, "compared": COMPARED, "differences": diffs, ...}` and write formatted JSON via `write_check()`.

5. **Unit tests (`tests/stage0/`)**
   - Add `test_data_archive.py` (order/timestamp invariance and exclude filtering), `test_guards_block_violations.py` (live probe tests against `.importlinter` and `TestSplitAccessError`), `test_migration_compare.py` (diff detection across every `COMPARED` key), `test_runner.py` (dependency closure, hash-cache hit/miss, `--force`, fail-fast stopping), and `test_stage0_inputs.py` (fingerprint stability and zero self-write cache churn).

## Validation
- Executed `python -m pytest tests/stage0 -q`, verifying all five test modules (`test_data_archive.py`, `test_guards_block_violations.py`, `test_migration_compare.py`, `test_runner.py`, `test_stage0_inputs.py`).
- Executed `python run_pipeline.py --check` to confirm `lint-imports` and `pytest tests/contracts` run as pre-flight guards and pass before stage execution.
- Verified `python run_pipeline.py --stages 0` writes `artifacts/stage0/migration_check.json` (`equal: true`) and `artifacts/stage0/data_archive_sha256.txt`, and a second invocation skips Stage 0 as `cached` without re-running the 5-minute rebuild.

## Our decision
The team accepted Gemini 4 Neon's implementation verbatim in commit `6af8b0b`. In particular, invoking `src.stage1_freeze.build_unified_dataset` as a subprocess in `migration_check()` kept Stage 0 decoupled under `.importlinter`, and splitting `raw_fingerprint()` (`inputs`) from `archive_sha256()` (`run`) kept cached invocations fast while guaranteeing full byte-level archive verification whenever raw data or code changes.

## Measured effect
- **Commit `6af8b0b`:** 11 files changed (`731 insertions(+), 32 deletions(-)`), adding the complete `src/stage0_infra/` package, updated `run_pipeline.py`, and 5 Stage 0 test suites (`328` lines of Stage 0 tests).
- **Operational guarantees:** Unchanged stages skip deterministically via `status.json` input hashes; raw archive hashing scales across `196,353` archive files (`explain.js` `FACTS.archive_files`); migration equivalence between the pre-move scripts and moved Stage 1 build is verified automatically before Stage 1 runs.

---

## Upgraded & Expanded Technical Analysis (`T05`)

### 1. Pure-Function Input Fingerprinting & Cache Fixed-Point Invariant
In `run_pipeline.py`, the topological stage loop decides whether to skip stage $s$ via:
$$\text{Skip}(s) \iff \neg\texttt{force} \;\wedge\; \texttt{status.status} = \texttt{"passed"} \;\wedge\; \texttt{status.inputs} = s.\texttt{inputs}(\texttt{config})$$
- **Self-Write Disjointness Invariant:** Let $R(s)$ be the set of filesystem paths read by $s.\texttt{inputs}(\texttt{config})$ and $W(s)$ be the set of paths written by $s.\texttt{run}(\texttt{config})$. Cache idempotence requires $R(s) \cap W(s) = \emptyset$; if `inputs()` hashes any file modified by `run()`, the stage invalidates its own cache on every execution (`test_stage0_inputs.py`).
- **Two-Speed Archive Verification (`raw_fingerprint` vs. `archive_sha256`):**
  - `raw_fingerprint(raw_dir)` (called on every cache check in `inputs()`) performs an $\mathcal{O}(N_{\text{files}})$ metadata scan returning `"files=<n>;bytes=<total>"` without reading file payloads across `196,353` raw files.
  - `archive_sha256(root)` (called inside `run()` only on a cache miss) sorts `(rel_path, full_path)` lexicographically and streams full byte digests through `hash_named_files(files)`, guaranteeing OS- and filesystem-order-independent cryptographic verification.

### 2. Subprocess Isolation for Migration Equivalence (`migration_check`)
- **Respecting `stages-independent`:** Because `.importlinter` forbids `src.stage0_infra` from importing `src.stage1_freeze`, `migration_check()` invokes `sys.executable -m src.stage1_freeze.build_unified_dataset --out artifacts/stage0/rebuild --data data_set` in an isolated child process.
- **Five-Axis Relational & Perceptual Equivalence (`COMPARED`):** `src/stage0_infra/migration.py` opens both `data_set/unified/catalog.sqlite` and `artifacts/stage0/rebuild/catalog.sqlite` in read-only URI mode (`?mode=ro`), sorts table rows deterministically by `key=repr`, hashes `catalog_content`, `rows`, `class_counts`, recomputed per-`(source_id, label_name)` `phash_groups`, and sorted `metadata_content`, proving (`equal: true`) that refactoring the Phase 1 scripts into Stage 1 produced zero dataset drift.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** `raw_fingerprint()` (in `inputs()`) and `archive_sha256()` (in `run()`) are a deliberate performance-vs-correctness split. A cache hit is cheap and a cache miss is fully verified. The unified dir is excluded from the fingerprint because `run()` writes it; including the stage's own output would mean the fingerprint never matches twice.

**Changelog:** [1] two-hash split as a stated trade; [2] self-write exclusion; [3] the subprocess call means Stage 0 and Stage 1 share no interpreter state; [4] sort-then-hash keeps the digest portable across OSes.

**Open questions:** Is the pHash scope ("Phase 1, prior to Decision 15") documented anywhere besides this entry? Does `--force` skip the 5-minute rebuild?
