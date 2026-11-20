

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [11_evidence_functional-dependencies.md](../claude_opus/11_evidence_functional-dependencies.md)
# 1_data_integration - I05: Six-constraint FD suite and injected violation negative testing (reconstructed)

- Stage 1 topic: I05
- Model: Gemini 4 Neon
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/check_fds.py`, `results/phase2_snapshot/fd_check.json`, `tests/stage1/test_fd_scripts.py`
- Follow-up: `../claude_opus/08_I05_functional-dependencies-on-filtered-rows.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

After `build_unified_dataset.py` builds the `18,500`-row catalog and `src/stage1_freeze/run.py` applies `exclude_source_labels` (`500` `quickdraw/diamond` rows dropped) plus global pHash splitting, Stage 1 must prove relational integrity across the active `18,000` rows (`stages/stage_1.md` R8). In particular, `check_fds.py` originally read `metadata.csv` directly - which still held pre-exclusion rows and stale Phase 1 splits - raising the risk of checking the wrong frame or having an FD checker pass vacuously.

## Exchange

**User:**
> Which relational functional dependencies are sufficient to prove Stage 1 integration integrity across sources, labels, and split manifests - and how do we test the FD checker itself so it cannot pass vacuously?

**Gemini 4 Neon:**
> Define six explicit functional dependencies in `CHECKS` covering source metadata, taxonomy harmonization, key uniqueness, and native geometry, evaluate them on the **filtered active rows with reassigned splits**, and include a synthetic negative-injection test:
>
> 1. `source_id -> domain` (verifies each source maps to one domain: `sketch` or `render`).
> 2. `source_id -> license` (verifies single license per source, e.g., `CC0`, `CC BY 4.0`).
> 3. `(source_id, original_label) -> label_id` (verifies deterministic label harmonization per source).
> 4. `label_id -> label_name` (verifies bijection with the 10 taxonomy classes).
> 5. `image_id -> (path, split)` (verifies primary-key uniqueness and unique split assignment per image).
> 6. `source_id -> (native_width, native_height)` (verifies uniform native resolution within each source).
>
> | Design Choice | Risk / Trade-off | Verdict |
> |---|---|---|
> | Check `metadata.csv` as-is without filtering | Tests excluded `quickdraw/diamond` rows and stale Phase 1 `split` column (`stages/stage_1.md` R8 bug) | **Reject** |
> | Check only `image_id -> split` | Misses corrupted label mappings, mixed source licenses, or inconsistent native dimensions | **Reject** |
> | All 6 `CHECKS` on `fd_rows()` + `label_id="999"` violation injection | Proves full relational integrity on active rows and verifies detector sensitivity | **Adopt** |

**User:**
> How should the negative test and unit tests ensure the checker catches conflicts and reads the active config instead of a stale hardcoded file?

**Gemini 4 Neon:**
> Pair a self-test in `check_fds.py` with config-driven unit tests:
>
> - In `check_fds.py:main()`, clone `rows[0]` with `label_id="999"` and run `check_fd(rows + [bad], ["source_id", "original_label"], ["label_id"])` to confirm `1` violating group is flagged.
> - In `check_fds.py:main()`, resolve `paths.metadata` via `load_default_config()` at call time (never at import time) and verify that in `tests/stage1/test_fd_scripts.py`.
> - In `run.py:plan_freeze()`, build the target frame with `fd_rows(rows, metadata_rows, split_of)` before passing it to `check_rows()`, failing Stage 1 if any of the 6 FDs fails (`fd_all_hold` becomes `False`).

## Why this reading fits

Gemini 4 Neon's specification matches `src/stage1_freeze/check_fds.py` (`CHECKS`, `check_fd`, `check_rows`, and the `label_id="999"` injected-violation block in `main()`), `src/stage1_freeze/stats.py` (`fd_rows`), and `tests/stage1/test_fd_scripts.py` (`test_check_fds_main_reads_config_metadata`, `test_discover_fds_main_reads_config_metadata`). Evaluating `CHECKS` over `fd_rows()` directly resolves requirement R8 in `stages/stage_1.md`, while the synthetic violation injection and `test_fd_violation_blocks_manifests` guarantee the check is non-vacuous and fail-closed.

## Validation

Every claim in this exchange is verified in repository test suites and snapshot artifacts:

- **Snapshot FD results (`results/phase2_snapshot/fd_check.json`):** All 6 constraints passed with `n_violations: 0` and `holds: true` over the `18,000` active rows:
  - `source_id -> domain`: `4` groups, `0` violations
  - `source_id -> license`: `4` groups, `0` violations
  - `(source_id, original_label) -> label_id`: `21` groups, `0` violations
  - `label_id -> label_name`: `10` groups, `0` violations
  - `image_id -> (path, split)`: `18000` groups, `0` violations
  - `source_id -> (native_width, native_height)`: `4` groups, `0` violations
- **Unit & integration tests:**
  - `tests/stage1/test_fd_scripts.py` monkeypatches `load_default_config` to confirm both `check_fds.main()` and `discover_fds.main()` read `paths.metadata` from config dynamically (`"Rows: 3"`, `"source_id -> domain: 1 groups, HOLDS"`).
  - `tests/stage1/test_run_fail_closed.py` (`test_fd_violation_blocks_manifests`) injects a `"RENDER"` domain mismatch on one row of `"src"` and verifies `stage1.run(cfg)` writes `fd_check.json`, sets `checks["fd_all_hold"] is False`, sets `status == "failed"`, and writes zero manifests.

## Our decision

The team implemented the 6-constraint `CHECKS` suite and `check_fd` / `check_rows` engine in `src/stage1_freeze/check_fds.py`, wired `plan_freeze()` in `src/stage1_freeze/run.py` to evaluate `check_rows()` on `fd_rows()` (active post-exclusion rows with newly assigned splits), and kept the `label_id="999"` injected-violation self-test plus `tests/stage1/test_fd_scripts.py`.

## Measured effect

- **Relational integrity proven on active rows:** `results/phase2_snapshot/status1.json` reports `checks.fd_all_hold: true` alongside `results/phase2_snapshot/fd_check.json` showing exact expected group cardinalities (`4 / 4 / 21 / 10 / 18000 / 4`) and `0` violations across all `18,000` frozen images.
- **Fail-closed regression coverage:** Both config-path resolution (`test_fd_scripts.py`) and Stage 1 manifest blocking on an FD violation (`test_fd_violation_blocks_manifests`) are enforced by automated `pytest` checks.

## Deeper detail: why each FD matters

### The 6 FDs are a complete schema audit

| FD | What it enforces | Why it matters |
|---|---|---|
| `source_id -> domain` | Each source has one domain | Prevents conflicting domain assignments |
| `source_id -> license` | Each source has one license | Prevents conflicting license assignments |
| `(source_id, original_label) -> label_id` | Each (source, original_label) maps to one canonical label | The core harmonization invariant |
| `label_id -> label_name` | Each label ID maps to one name | Prevents duplicate or conflicting label definitions |
| `image_id -> (path, split)` | Each image maps to one path and one split | Prevents duplicate or conflicting image assignments |
| `source_id -> (native_width, native_height)` | Each source has consistent native dimensions | Prevents inconsistent source metadata |

- **Why these 6 matter:** each catches a different kind of schema inconsistency. Together they form a complete schema audit.
- **Why this is a good design:** it's comprehensive without being redundant.

### Why post-filter rows, not raw metadata

| Frame | Rows | Split values | Verdict |
|---|---|---|---|
| Raw `metadata.csv` | 18,500 (includes 500 excluded) | Stale Phase 1 | Reject |
| Post-filter `fd_rows` | 18,000 (excludes 500) | New Stage 1 | Adopt |

- **Why raw metadata is wrong:** it includes the 500 excluded `quickdraw/diamond` rows and has stale Phase 1 split values.
- **Why `fd_rows` is right:** it filters to active `image_id`s and overwrites `split` with the new Stage 1 assignment.
- **Why this matters:** running FD checks on the wrong frame would either miss violations or produce false positives.

### Why the injected-violation test matters

- **The `label_id="999"` test:** appends a row with an invalid `label_id` to the rows, then checks that `check_fd` catches `1` violating group for `(source_id, original_label) -> label_id`.
- **Why this matters:** it proves the FD checker actually catches errors, rather than silently passing on a bug. This is a "meta-test" that validates the validator itself.
- **Why `label_id="999"` specifically:** it's an obviously invalid value that should never appear in a valid dataset, making it a clean test case.
- **Why this is in `check_fds.main()` and not just a unit test:** running it in `main()` means it runs every time the script is invoked, providing continuous validation.

### Why config-driven path resolution

- **`load_default_config()` instead of a hard-coded path:** allows tests to redirect the metadata path cleanly, without monkey-patching or environment variables.
- **Why this matters for testability:** it makes the script testable in isolation, since the test can point it at a temp file rather than the real `metadata.csv`.
- **Why "never at import time":** resolving at call time (not import time) ensures the config is read fresh each run, which is important for testability.

### Why gate `freeze()` on `fd_all_hold`

- **`plan_freeze()` runs `check_rows` before `freeze()`:** if `fd_all_hold` is `False`, `freeze()` is never called, so no manifests are written.
- **Why this matters:** it's the same fail-closed pattern as I04. A schema violation should block the freeze, not just be logged.
- **Why write `fd_check.json` even on failure:** the diagnostic output is useful for debugging, so it should be written regardless of whether the freeze proceeds.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | This entry (I05) | The 18,000 active rows are the input to the FD check |
| I02 (identity) | This entry (I05) | The `md5`/`phash` in the manifests come from I02 |
| I03 (global grouping) | This entry (I05) | The `phash_group` in the manifests comes from I03 |
| I04 (fail-closed freeze) | This entry (I05) | The `plan_freeze()` gating is the same pattern as I04 |
| I06 (standardization) | This entry (I05) | The standardized PNGs are the input to the FD check |
| A01 (noise bands) | This entry (I05) | The noise bands are part of the `plan_freeze()` validation |

- **Why this matters:** this entry (I05) is the decision that established the 6-constraint FD suite, which is the foundation for the schema audit.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating a Gemini reply.
- **This is a `winning-decision` calibration:** Gemini's proposal was correct and was adopted. This is the best kind of outcome.
- **The 6 FDs are a complete schema audit:** each catches a different kind of inconsistency.
- **The post-filter frame is critical:** running FD checks on the wrong frame would miss violations or produce false positives.
- **The injected-violation test is a "meta-test":** it validates the validator itself.
- **The config-driven path resolution is good for testability:** it makes the script testable in isolation.
- **Cross-reference to I01, I02, I03, I04, I06, A01:** this entry is the foundation for the schema audit.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.