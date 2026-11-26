

>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](../claude_opus/13_evidence_stage-1-freeze-and-split-plans.md)
# 1_data_integration - I04: Sealed holdout split guards, test access logging, and atomic swaps 

- Stage 1 topic: I04
- Model: Gemini 4 Neon
- Calibration: `winning-decision`
- Grounding sources: `src/common/splits.py`, `src/stage1_freeze/leakage.py`, `src/stage1_freeze/run.py`, `tests/stage1/test_run_fail_closed.py`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../claude_opus/07_I04_fail-closed-leakage-checks-and-atomic-freeze.md`

## Context

In a multi-stage experimental pipeline (`stage0_infra` through `stage6_report`), splitting the data cleanly in Stage 1 is insufficient if Stage 2 (augmentation), Stage 3 (synthetic generation), or Stage 4 (CNN training and hyperparameter search) can silently read `configs/splits/test.csv` or the later iteration holdouts (`fresh_holdout`, `fresh_holdout_2`). At the same time, Stage 1 itself must never leave partial or corrupted manifest CSVs in `configs/splits/` if a leakage check, FD check, or noise-band check fails mid-run (`stages/stage_1.md` R9).

## Exchange

**User:**
> Once Stage 1 writes `configs/splits/{train,val,test}.csv`, how do we enforce the sealed-split contract across Stages 2-5 so tuning code never silently touches test images - and how do we prevent Stage 1 from leaving broken manifests behind if a check fails?

**Gemini 4 Neon:**
> Combine two enforcement boundaries - one at **read time** (`src/common/splits.py`) and one at **freeze time** (`src/stage1_freeze/leakage.py` + `src/stage1_freeze/run.py`):
>
> - **Read-time gate (`load_split`):** Register `"test"`, `"fresh_holdout"`, and `"fresh_holdout_2"` in `SEALED_SPLITS`. Inspect the Python call stack (`_caller()`) and raise `TestSplitAccessError(PermissionError)` unless the caller lives under `src.stage5_eval` (or `__main__` inside `stage5_eval`).
> - **Append-only audit log:** Every permitted read of a sealed split appends one CSV line (`iso_timestamp, run_id, caller_module, split, n_rows`) to `artifacts/test_access.log`, never truncating prior entries, with `count_test_reads` and `reads_outside` scoped by `run_id`.
> - **Fail-closed atomic freeze:** Run all validation (`plan_freeze`: leakage checks, noise bands, FD checks, source-shortcut check) *before* touching `configs/splits/`. In `freeze()` / `write_manifests()`, write all three CSVs into a temporary `.splits_tmp_*` folder first, then atomically replace each destination via `os.replace(p, dest)`.
>
> | Mechanism | Risk / Trade-off | Verdict |
> |---|---|---|
> | File permissions or naming conventions only | Easily bypassed by scripts or stale relative reads; no audit trail per `run_id` | **Reject** |
> | `load_split()` caller gate + append-only log + direct `open()` writes in Stage 1 | Protects reads, but a Stage 1 crash mid-write leaves mismatched `train.csv` / `test.csv` | **Reject** |
> | `load_split()` guard + `test_access.log` + `plan_freeze()` + `.splits_tmp_` `os.replace` | Blocks unauthorized reads, audits all Stage 5 reads, and makes manifest writes all-or-nothing | **Adopt** |

**User:**
> What if `python -m src.stage5_eval.run` runs directly as `__main__`, or a Stage 1 failure happens right after diagnostic artifacts (`fd_check.json`) are generated?

**Gemini 4 Neon:**
> Handle both explicitly:
>
> - In `_allowed_test_reader()`, when `module == "__main__"`, check whether `Path(module_file).resolve().relative_to(STAGE5_DIR)` succeeds so CLI entrypoints inside `src/stage5_eval/` still pass the guard.
> - In `run.py`, write diagnostic artifacts (`split_stats.csv`, `noise_bands.csv`, `fd_check.json`, `source_classifier.json`) from `plan_freeze()` first so failures are debuggable, then return `status: "failed"` *before* calling `freeze()` if any check is false.

## Why this reading fits

Gemini 4 Neon's design matches the production enforcement architecture in `src/common/splits.py`, `src/stage1_freeze/leakage.py`, and `src/stage1_freeze/run.py` (`stages/stage_1.md` R9 and `ShapeSense_Deployed/web/js/content/explain.js`). Separating `plan_freeze()` from `freeze()` guarantees that diagnostic outputs remain inspectable on failure while `configs/splits/` stays untouched, and gating `SEALED_SPLITS` inside `load_split()` makes unauthorized reads fail loudly at runtime while preserving an immutable `test_access.log` trail.

## Validation

The contract and fail-closed test suites directly verify every branch of this design:

- **Fail-closed Stage 1 suite (`tests/stage1/test_run_fail_closed.py`):**
  - `test_clean_run_passes_and_writes_three_manifests`: verifies a clean run passes all 4 checks (`no_id_in_two_splits`, `no_md5_in_two_splits`, `no_phash_group_spans`, `fd_all_hold`) and leaves no `.splits_tmp_*` directory.
  - `test_noise_band_failure_blocks_manifests`: confirms raising on missing class test rows leaves `_manifests(cfg) == []`.
  - `test_fd_violation_blocks_manifests`: confirms an FD failure writes `fd_check.json` for diagnosis, sets `status == "failed"`, and writes zero manifests.
  - `test_leak_blocks_manifests`: confirms an injected `md5` collision across splits fails `no_md5_in_two_splits` and writes zero manifests.
  - `test_plan_freeze_writes_nothing`: confirms `plan_freeze()` is completely side-effect-free.
- **Sealed-split guard suite (`tests/contracts/test_load_split_guard.py`):** verifies `load_split("train")` succeeds without logging (`test_train_read_allowed_anywhere`), non-Stage-5 callers raise `TestSplitAccessError` without touching the log (`test_test_read_blocked_outside_stage5`), `src.stage5_eval` reads succeed and append one line per call without truncation (`test_test_read_allowed_from_stage5_module`, `test_each_test_read_appends_one_line`, `test_log_never_truncated`), and `count_test_reads` scopes counts by `SHAPESENSE_RUN_ID` (`test_count_scoped_to_run_id`).

## Our decision

The team implemented the full read-time and freeze-time guard stack:

1. **`src/common/splits.py`:** Enforces `SEALED_SPLITS = ("test", "fresh_holdout", "fresh_holdout_2")`, allowing only `src.stage5_eval` (or `__main__` inside `STAGE5_DIR`) via `_allowed_test_reader` and logging each permitted read to `artifacts/test_access.log` (`DEFAULT_LOG`).
2. **`src/stage1_freeze/leakage.py`:** Implements `leakage_checks()`, `write_manifests()` using `.splits_tmp_` + `os.replace()` + `finally: shutil.rmtree(tmp, ignore_errors=True)`, and `freeze()`.
3. **`src/stage1_freeze/run.py`:** Runs `plan_freeze()` before `freeze()`, returning `status: "failed"` with zero manifests written whenever any leakage or FD check fails.

## Measured effect

- **Snapshot verification (`results/phase2_snapshot/status1.json`):** `stage1` completed with `status: "passed"`, `checks: {"no_id_in_two_splits": true, "no_md5_in_two_splits": true, "no_phash_group_spans": true, "fd_all_hold": true}`, and committed byte-deterministic `configs/splits/{train,val,test}.csv` manifests.
- **Zero unlogged or premature test reads:** All pipeline stages outside `src.stage5_eval` are programmatically blocked by `TestSplitAccessError`, while Stage 5 sealed reads remain permanently audited per `run_id` in `artifacts/test_access.log`.

## Deeper detail: why each design choice matters

### The two enforcement boundaries

| Boundary | Where | What it enforces | Why |
|---|---|---|---|
| Read-time | `src/common/splits.py` | Only Stage 5 can read sealed splits | Prevents accidental reads during tuning |
| Freeze-time | `src/stage1_freeze/leakage.py` + `run.py` | Manifests are all-or-nothing | Prevents partial/corrupted manifests |

- **Why two boundaries:** read-time prevents unauthorized reads; freeze-time prevents partial writes. Together they form a complete guard.
- **Why this is defence in depth:** a bug in one boundary is caught by the other.

### The read-time gate: `load_split`

| Mechanism | What it does | Why |
|---|---|---|
| `SEALED_SPLITS` | Registers `test`, `fresh_holdout`, `fresh_holdout_2` | Defines which splits are sealed |
| `_caller()` | Inspects the Python call stack | Determines who is calling |
| `TestSplitAccessError` | Raises unless caller is Stage 5 | Fails loudly on unauthorized reads |
| `test_access.log` | Appends one line per permitted read | Creates an audit trail |

- **Why the call-stack inspection:** it's the only way to know who is calling at runtime.
- **Why `TestSplitAccessError` (a `PermissionError` subclass):** it's a specific exception type that makes the failure mode clear and testable.
- **Why the audit log is append-only:** it preserves the full history, which is useful for auditing.
- **Why `run_id` scoping:** it lets you count reads per run, which is useful for debugging.

### The freeze-time guard: atomic swap

| Mechanism | What it does | Why |
|---|---|---|
| `plan_freeze()` | Runs all validation before touching `configs/splits/` | Fail-closed at the check layer |
| `.splits_tmp_*` | Temporary directory for staging | Keeps temp on the same volume |
| `os.replace()` | Atomic rename | All-or-nothing write |
| `finally: shutil.rmtree(tmp)` | Cleanup on failure | No orphaned temp dirs |

- **Why `plan_freeze()` before `freeze()`:** if validation fails, `freeze()` is never called, so no manifests are written.
- **Why `.splits_tmp_*` in `splits_dir.parent`:** on Windows, `os.replace` across volumes can fail; keeping temp on the same volume ensures atomicity.
- **Why `os.replace` and not `shutil.move`:** `os.replace` is atomic on the same filesystem.
- **Why `finally` cleanup:** ensures no orphaned temp dirs even if `os.replace` fails.

### The `__main__` edge case

- **Why `_allowed_test_reader()` checks `Path(module_file).resolve().relative_to(STAGE5_DIR)`:** when run as `python -m src.stage5_eval.run`, the module is `__main__`, so the call-stack check would fail. The path check handles this.
- **Why this matters:** it ensures CLI entrypoints inside `src/stage5_eval/` still pass the guard.

### The diagnostic-first pattern

- **Why write diagnostics (`fd_check.json`, etc.) from `plan_freeze()` first:** so failures are debuggable even if `freeze()` is never called.
- **Why return `status: "failed"` before `freeze()`:** ensures no manifests are written on failure.
- **Why this is the same pattern as I05:** the FD check writes diagnostics then gates `freeze()`. This is a consistent pattern.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | This entry (I04) | The 18,000 active rows are the input to the freeze |
| I02 (identity) | This entry (I04) | The `md5`/`phash` in the manifests come from I02 |
| I03 (global grouping) | This entry (I04) | The `phash_group` in the manifests comes from I03 |
| I05 (FD checks) | This entry (I04) | The FD check is part of the `plan_freeze()` validation |
| C02 (fresh holdout) | This entry (I04) | The `fresh_holdout` is one of the sealed splits |
| C24 (second fresh holdout) | This entry (I04) | The `fresh_holdout_2` is one of the sealed splits |
| A01 (noise bands) | This entry (I04) | The noise bands are part of the `plan_freeze()` validation |

- **Why this matters:** this entry (I04) is the decision that established the read-time and freeze-time guard stack, which is the foundation for the sealed-split contract.

## Notes on the log

- **This is a `winning-decision` calibration:** Gemini's proposal was correct and was adopted. This is the best kind of outcome.
- **The two-boundary design is defence in depth:** read-time + freeze-time.
- **The `__main__` edge case is a practical detail:** it ensures CLI entrypoints work.
- **The diagnostic-first pattern is consistent with I05:** write diagnostics, then gate `freeze()`.
- **Cross-reference to I01, I02, I03, I05, C02, C24, A01:** this entry is the foundation for the sealed-split contract.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.