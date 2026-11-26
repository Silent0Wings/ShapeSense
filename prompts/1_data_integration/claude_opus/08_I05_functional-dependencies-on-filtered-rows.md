

>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [11_evidence_functional-dependencies.md](11_evidence_functional-dependencies.md)

# 1_data_integration - I05: Enforcing functional dependencies on post-filter active rows 

- Stage 1 topic: I05
- Model: Opus 5.5
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/check_fds.py`, `results/phase2_snapshot/fd_check.json`, `tests/stage1/test_fd_scripts.py`
- Follow-up: `../gemini_4_neon/07_I05_fd-check-coverage-and-injected-violation-test.md`

## Context

After excluding `500` `quickdraw/diamond` rows (and supporting optional `gemstone_ids.csv` exclusions) and recomputing global pHash splits, `data_set/unified/metadata.csv` still reflects all `18,500` pre-exclusion catalog rows and legacy Phase 1 `split` values. As warned in `stages/stage_1.md` (R8), running functional-dependency (FD) checks directly against raw `metadata.csv` validates the wrong row set and stale split assignments. The team needed a clean way to evaluate schema invariants on the exact post-filter active rows and verify that the validator itself cannot pass silently on a bug.

## Exchange

**User:**
> `check_fds.py` reads `metadata.csv`, which has all 18,500 rows and the old Phase 1 `split` column. If we drop 500 `quickdraw/diamond` rows and re-split in Stage 1, how should we run FD validation so exclusions don't mask or desync invariants, and how do we prove the FD checker actually catches errors?

**Opus 5.5:**
> Keep `check_fds.py` pure over an explicit row list (`check_rows(rows, checks=CHECKS)`), feed it the exact post-filter active rows with updated split labels during Stage 1, and pair it with an injected-violation sanity check:
>
> - **Construct the post-filter frame (`fd_rows`):** Never pass raw `metadata.csv` to `check_rows` inside `run.py`. Restrict `metadata.csv` rows to the active post-exclusion `image_id`s (`18,000` rows) and overwrite `split` with the newly assigned Stage 1 split (`split_of[iid]`) before calling `check_rows`.
> - **Audit all 6 schema invariants in `CHECKS`:**
>   1. `source_id -> domain`
>   2. `source_id -> license`
>   3. `(source_id, original_label) -> label_id`
>   4. `label_id -> label_name`
>   5. `image_id -> (path, split)`
>   6. `source_id -> (native_width, native_height)`
> - **Keep config-driven CLI resolution and an injected-violation test:** In `check_fds.main()`, load `paths.metadata` from `load_default_config()` rather than a hard-coded path so tests can redirect it cleanly, and run a negative test (`bad = dict(rows[0], label_id="999")`) appended to `rows` to confirm `check_fd` catches `1` violating group for `(source_id, original_label) -> label_id`.

**User:**
> Should we also check `fd_all_hold` before writing `configs/splits/*.csv` so an FD violation aborts the freeze?

**Opus 5.5:**
> Yes - run `check_rows` inside `plan_freeze()` before `freeze()`, write the structured diagnostics to `artifacts/stage1/fd_check.json`, and block manifest writing whenever `fd_all_hold` is `False`. Here is how the strategies compare:

| Option | Effect | Recommendation |
|---|---|---|
| Run `check_fds.py` only on raw `metadata.csv` post-hoc | Checks `18,500` stale rows including excluded `quickdraw/diamond` and Phase 1 `split` values; never blocks broken manifests | Reject |
| Check only `label_id -> label_name` and `image_id -> split` | Misses source-level `domain`, `license`, `(source_id, original_label) -> label_id`, and native dimension invariants | Reject |
| Run all 6 `CHECKS` on `fd_rows` inside `plan_freeze()` + injected-violation test | Audits exact `18,000` post-filter rows with new splits, gates `freeze()`, and verifies detector sensitivity | Adopt |

## Why this reading fits

Opus 5.5's recommendation matches `src/stage1_freeze/check_fds.py`, `src/stage1_freeze/stats.py` (`fd_rows`), `src/stage1_freeze/run.py` (`plan_freeze`), and `tests/stage1/test_fd_scripts.py`: `CHECKS` lists the exact 6 FDs, `check_rows` accepts the filtered rows from `fd_rows(rows, metadata_rows, ...)`, `check_fds.main()` runs the `label_id="999"` injected-violation check and reads `paths.metadata` via `load_default_config()`, and `plan_freeze` sets `checks["fd_all_hold"]` before `freeze()`.

## Validation

- `results/phase2_snapshot/fd_check.json` confirms all 6 FDs hold with `0` violations on the `18,000` post-filter rows: `source_id -> domain` (`4` groups), `source_id -> license` (`4` groups), `(source_id, original_label) -> label_id` (`21` groups), `label_id -> label_name` (`10` groups), `image_id -> (path, split)` (`18000` groups), and `source_id -> (native_width, native_height)` (`4` groups).
- `tests/stage1/test_fd_scripts.py` (`test_check_fds_main_reads_config_metadata`, `test_discover_fds_main_reads_config_metadata`) verifies config-driven metadata resolution.
- `tests/stage1/test_run_fail_closed.py` (`test_fd_violation_blocks_manifests`) confirms an injected `source_id -> domain` violation forces `status: "failed"`, `checks["fd_all_hold"] is False`, writes `fd_check.json`, and leaves zero manifests.

## Our decision

The team implemented `check_rows` with all 6 `CHECKS` and the `label_id="999"` injected-violation check in `src/stage1_freeze/check_fds.py`, wired `fd_rows` into `plan_freeze` in `src/stage1_freeze/run.py` to gate `freeze()` on `fd_all_hold`, and covered config path resolution and fail-closed FD blocking with unit tests.

## Measured effect

- All 6 functional dependencies pass with `n_violations: 0` across `18,000` post-filter active rows (`results/phase2_snapshot/fd_check.json`), and `fd_all_hold: true` is recorded in `results/phase2_snapshot/status1.json`.
- Both the standalone `label_id="999"` self-test in `check_fds.py` and `test_fd_violation_blocks_manifests` confirm that any schema conflict fails loudly rather than passing silently.

## Deeper detail: why each design choice matters

### Why post-filter rows, not raw metadata

- **Raw `metadata.csv` has 18,500 rows** (including the 500 excluded `quickdraw/diamond` rows) and **stale Phase 1 `split` values**.
- **Post-filter `fd_rows` has 18,000 rows** (excluding the 500) and **new Stage 1 `split` values**.
- **Why this matters:** running FD checks on the wrong row set would either miss violations (if excluded rows had violations) or produce false positives (if stale split values conflicted with new ones).
- **The `fd_rows` function is the bridge:** it takes raw `metadata.csv` rows, filters to active `image_id`s, and overwrites `split` with the new Stage 1 assignment. This ensures the FD check sees exactly the right data.

### Why all 6 FDs, not just 2

- **`source_id -> domain`:** ensures each source maps to exactly one domain (e.g., `quickdraw` -> `sketch`).
- **`source_id -> license`:** ensures each source maps to exactly one license (e.g., `quickdraw` -> `CC BY 4.0`).
- **`(source_id, original_label) -> label_id`:** ensures each `(source, original_label)` pair maps to exactly one canonical label. This is the core harmonization invariant from I01.
- **`label_id -> label_name`:** ensures each label ID maps to exactly one name. This catches duplicate or conflicting label definitions.
- **`image_id -> (path, split)`:** ensures each image maps to exactly one path and one split. This catches duplicate or conflicting image assignments.
- **`source_id -> (native_width, native_height)`:** ensures each source has consistent native dimensions. This catches inconsistent source metadata.
- **Why all 6 matter:** each catches a different kind of schema inconsistency. Together they form a complete schema audit.

### Why the injected-violation test matters

- **The `label_id="999"` test:** appends a row with an invalid `label_id` to the rows, then checks that `check_fd` catches `1` violating group for `(source_id, original_label) -> label_id`.
- **Why this matters:** it proves the FD checker actually catches errors, rather than silently passing on a bug. This is a "meta-test" that validates the validator itself.
- **Why `label_id="999"` specifically:** it's an obviously invalid value that should never appear in a valid dataset, making it a clean test case.
- **Why this is in `check_fds.main()` and not just a unit test:** running it in `main()` means it runs every time the script is invoked, providing continuous validation.

### Why config-driven path resolution

- **`load_default_config()` instead of a hard-coded path:** allows tests to redirect the metadata path cleanly, without monkey-patching or environment variables.
- **Why this matters for testability:** it makes the script testable in isolation, since the test can point it at a temp file rather than the real `metadata.csv`.

### Why gate `freeze()` on `fd_all_hold`

- **`plan_freeze()` runs `check_rows` before `freeze()`:** if `fd_all_hold` is `False`, `freeze()` is never called, so no manifests are written.
- **Why this matters:** it's the same fail-closed pattern as I04. A schema violation should block the freeze, not just be logged.
- **Why write `fd_check.json` even on failure:** the diagnostic output is useful for debugging, so it should be written regardless of whether the freeze proceeds.

### Cross-reference to I01 and I04

- The 6 FDs are a direct consequence of I01's schema harmonization (the `LABEL_MAP`, `ambiguity_margins`, etc.). This is a good example of the entries building on each other.
- The `plan_freeze` gating on `fd_all_hold` is the same fail-closed pattern as I04. This is a good example of the entries building on each other.
- The `fd_check.json` diagnostic output is the same pattern as I04's `artifacts/stage1/` outputs. This is a good example of the entries building on each other.

## Notes on the log


- **This is a `winning-decision` calibration:** like I01, I02 and I04, this entry is calibrated as `winning-decision`, meaning Opus's recommendation was correct and was adopted as-is.
- **The 6 FDs are a complete schema audit:** each catches a different kind of inconsistency, and together they form a complete check.
- **The injected-violation test is a "meta-test":** it validates the validator itself, which is a subtle but important pattern.
- **The `fd_rows` function is the key bridge:** it ensures the FD check sees exactly the right data (post-filter, new splits).
- **The config-driven path resolution is good for testability:** it makes the script testable in isolation.
- **The `plan_freeze` gating is the same fail-closed pattern as I04:** a schema violation blocks the freeze, not just gets logged.
- **Cross-reference to I01 and I04:** the 6 FDs come from I01's schema harmonization, and the `plan_freeze` gating comes from I04's fail-closed pattern. This is a good example of the entries building on each other.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.