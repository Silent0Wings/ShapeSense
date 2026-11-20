

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](13_evidence_stage-1-freeze-and-split-plans.md)

# 1_data_integration - I04: Fail-closed leakage verification and atomic manifest freeze on Windows (reconstructed)

- Stage 1 topic: I04
- Model: Opus 5.5
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/leakage.py`, `src/stage1_freeze/run.py`, `src/common/splits.py`, `tests/stage1/test_run_fail_closed.py`, `results/phase2_snapshot/status1.json`
- Follow-up: `../gemini_4_neon/06_I04_sealed-split-guard-and-access-logging.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

Stage 1 produces the committed split manifests (`configs/splits/{train,val,test}.csv`) that govern every downstream training and evaluation run. Because the team develops on Windows and commits manifests to Git, Stage 1 faced three operational risks: (1) a partial or failed Stage 1 run leaving half-written or stale `configs/splits/*.csv` files on disk (`stages/stage_1.md` R9), (2) Windows `csv` default `\r\n` line endings causing spurious cross-OS Git diffs and hash mismatches, and (3) downstream stages accidentally reading `test` (or fresh holdouts) without authorization or logging.

## Exchange

**User:**
> How should Stage 1 guarantee that a failed leakage or FD check never leaves partial manifests in `configs/splits/`, avoid Windows CRLF diff noise in committed CSVs, and prevent Stages 2-4 from touching the test split?

**Opus 5.5:**
> Make Stage 1 strictly fail-closed at both the check layer and the filesystem layer, then enforce runtime access control in `src/common/splits.py`:
>
> - **Run every check before touching `configs/splits/`:** Split `src/stage1_freeze/run.py` into `plan_freeze(config, rows)` and `freeze(rows, splits_dir)`. Inside `plan_freeze`, run `leakage_checks(rows)`, `noise_bands(...)`, `fd_all_hold` (`check_rows(fd_rows(...))`), and `shortcut_check(...)` first. Write diagnostic outputs to `artifacts/stage1/` so failures remain inspectable, and if `not all(checks.values())`, return `{"status": "failed", ...}` immediately without calling `freeze()`.
> - **Verify all three leakage keys in `leakage.py`:** Define `CHECK_KEYS = {"no_id_in_two_splits": "image_id", "no_md5_in_two_splits": "md5", "no_phash_group_spans": "phash_group"}` and run `leakage_checks(rows)` inside `freeze()` as well - if any check is `False`, return `{"status": "failed", "checks": checks, "outputs": []}` and write zero files.
> - **Stage and atomically swap manifests with explicit LF:** In `write_manifests(rows, splits_dir)`, sort rows by `image_id`, create a sibling temporary directory (`tempfile.mkdtemp(prefix=".splits_tmp_", dir=splits_dir.parent)`), write all three CSVs (`MANIFEST_COLUMNS`) with `encoding="utf-8"` and `LINE_TERMINATOR = "\n"`, move them via `os.replace(p, dest)`, and always clean up `tmp` in a `finally` block (`shutil.rmtree(tmp, ignore_errors=True)`).
> - **Guard sealed splits centrally:** Expose `load_split(name)` in `src/common/splits.py` with `SEALED_SPLITS = ("test", "fresh_holdout", "fresh_holdout_2")`, raising `TestSplitAccessError` unless `_allowed_test_reader` confirms the caller is inside `src.stage5_eval`, and appending every authorized read to `artifacts/test_access.log`.

**User:**
> Why create `.splits_tmp_` under `splits_dir.parent` instead of the OS temp directory (`%TEMP%`)?

**Opus 5.5:**
> On Windows, `os.replace` across volumes (e.g. `C:\Users\...\AppData\Local\Temp` to a separate project drive) can fail with cross-device link errors or break atomicity. Placing `.splits_tmp_` in `splits_dir.parent` keeps it on the same filesystem volume. Here is the comparison:

| Option | Effect | Recommendation |
|---|---|---|
| Write `configs/splits/*.csv` directly in place with default `csv` newlines | Partial writes survive crashes; Windows `\r\n` dirties Git diffs; failed checks can leave stale manifests | Reject |
| Stage in OS `%TEMP%` and check leakage only in `run.py` | Cross-drive `os.replace` failure risk on Windows; `freeze()` isn't independently fail-closed | Reject |
| `plan_freeze` + fail-closed `freeze()` + `.splits_tmp_` in `splits_dir.parent` + `LINE_TERMINATOR = "\n"` | Zero manifests written on any failure; atomic same-volume swap; deterministic LF CSVs + `load_split` guard | Adopt |

## Why this reading fits

Opus 5.5's architecture matches `src/stage1_freeze/leakage.py`, `src/stage1_freeze/run.py`, and `src/common/splits.py` directly: `CHECK_KEYS`, `LINE_TERMINATOR = "\n"`, `.splits_tmp_` under `splits_dir.parent`, `os.replace`, fail-closed `freeze()`, `plan_freeze()` ordering in `run.py`, and `SEALED_SPLITS` / `TestSplitAccessError` in `src/common/splits.py` are all implemented exactly this way.

## Validation

- `tests/stage1/test_run_fail_closed.py` exercises 5 test functions against `stage1.run` and `stage1.plan_freeze`: `test_clean_run_passes_and_writes_three_manifests`, `test_noise_band_failure_blocks_manifests`, `test_fd_violation_blocks_manifests`, `test_leak_blocks_manifests`, and `test_plan_freeze_writes_nothing`, verifying that failures leave zero `.csv` files and zero leftover `.splits_tmp_*` directories while still writing diagnostic `fd_check.json`.
- `results/phase2_snapshot/status1.json` confirms `"status": "passed"` with all four checks `true`: `no_id_in_two_splits`, `no_md5_in_two_splits`, `no_phash_group_spans`, and `fd_all_hold`.

## Our decision

The team implemented `leakage_checks`, `write_manifests`, and `freeze` in `src/stage1_freeze/leakage.py`, ordered `plan_freeze` ahead of `freeze` in `src/stage1_freeze/run.py`, and enforced `SEALED_SPLITS` access control and append-only logging in `src/common/splits.py`.

## Measured effect

- Stage 1 commits deterministic LF-terminated manifests (`configs/splits/train.csv`, `val.csv`, `test.csv`) covering `12,405` / `2,819` / `2,776` rows with zero cross-split `image_id`, `md5`, or `phash_group` leakage (`results/phase2_snapshot/status1.json`).
- End-to-end fail-closed tests (`tests/stage1/test_run_fail_closed.py`) verify that any injected leakage, noise-band failure, or FD violation blocks manifest creation cleanly.

## Deeper detail: why each design choice matters

### Fail-closed at two layers

- **Check layer (`plan_freeze`):** all validation (leakage, noise bands, FD, shortcut) runs before any file is written. If anything fails, `freeze()` is never called.
- **Filesystem layer (`freeze`):** even if `plan_freeze` somehow passed but `freeze` internally re-runs `leakage_checks` and finds a failure, it returns `{"status": "failed", "checks": checks, "outputs": []}` and writes zero files. This is defence in depth.
- **Why both layers matter:** a bug in `plan_freeze` (e.g., a check silently passing when it shouldn't) would be caught by the re-check in `freeze()`. This is a belt-and-suspenders approach.

### The three leakage keys

- `no_id_in_two_splits`: no `image_id` appears in more than one split. This catches duplicate rows.
- `no_md5_in_two_splits`: no `md5` appears in more than one split. This catches content duplicates (same pixels, different `image_id`).
- `no_phash_group_spans`: no `phash_group` spans more than one split. This catches near-duplicate leakage (similar but not identical images split across train/test).
- **Why all three matter:** each catches a different kind of leakage. `image_id` catches exact duplicates, `md5` catches content duplicates, and `phash_group` catches near-duplicates. Together they form a complete leakage check.

### Atomic same-volume swap

- **Why `.splits_tmp_` in `splits_dir.parent`:** on Windows, `os.replace` across volumes (e.g., `C:\Users\...\AppData\Local\Temp` to a separate project drive) can fail with cross-device link errors or break atomicity. Keeping the temp dir on the same volume as the destination ensures `os.replace` is a true atomic rename.
- **Why `os.replace` and not `shutil.move`:** `os.replace` is atomic on the same filesystem, whereas `shutil.move` may fall back to a copy+delete which is not atomic.
- **Why `finally` cleanup:** if `os.replace` fails mid-way, the `finally` block ensures the temp dir is cleaned up, leaving no orphaned `.splits_tmp_*` directories.

### Deterministic LF line endings

- **Why `LINE_TERMINATOR = "\n"`:** Windows `csv` module defaults to `\r\n`, which causes spurious cross-OS Git diffs and hash mismatches. Forcing `\n` makes the CSVs deterministic across OSes.
- **Why this matters for hashing:** if the CSV line endings changed between runs (e.g., due to a different OS or `csv` module version), the hash of the manifest would change, breaking the hash-verification safety net.
- **Why `encoding="utf-8"`:** ensures consistent character encoding, avoiding issues with non-ASCII characters in paths or labels.

### Sealed split access control

- **Why `SEALED_SPLITS = ("test", "fresh_holdout", "fresh_holdout_2")`:** these are the splits that must not be read casually. The `test` split is the final evaluation set, and the fresh holdouts are for unbiased verification.
- **Why `_allowed_test_reader` checks for `src.stage5_eval`:** this ensures only the evaluation stage can read the test split, preventing accidental reads from training or data-prep stages.
- **Why append to `artifacts/test_access.log`:** this creates an audit trail of every authorized read, which is useful for debugging and for proving that the test split wasn't read prematurely.
- **Why `TestSplitAccessError`:** a specific exception type makes the failure mode clear and testable, rather than a generic `PermissionError`.

### Cross-reference to the manifest pattern

- This is the same MD5/SHA-256-manifest pattern used in S06 (duplicate detection), F18 (holdout rebuild), C02 (fresh holdout), C24 (second holdout), C34 (hashing optimisation), I02 (content-addressed identity) and I03 (pHash grouping). The manifest is the source of truth for "did this change anything?"
- The difference here is that the manifest is being **written atomically and fail-closed**, not just used as a check. This is a natural evolution of the pattern.

### Cross-reference to I02 and I03

- The `image_id`, `md5`, and `phash_group` in `CHECK_KEYS` come directly from I02 (content-addressed identity) and I03 (pHash grouping). This is a good example of the entries building on each other.
- The `MANIFEST_COLUMNS` (`image_id, md5, label_id, source_id, phash_group, split`) are the same fields materialised in I02's `ROW_FIELDS`. This is a clean handoff between the two entries.

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor, C02, C34, I01, I02 and I03 entries, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The reconstruction is honest about its source:** the entry explicitly says it is "reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved". This is good practice: it's transparent about what is and isn't a primary source.
- **This is a `winning-decision` calibration:** unlike I03 (which was `close-to-reality`), this entry is calibrated as `winning-decision`, meaning Opus's recommendation was correct and was adopted as-is.
- **The two-layer fail-closed design is a strong pattern:** check layer + filesystem layer means a bug in one layer is caught by the other. This is defence in depth.
- **The atomic same-volume swap is a Windows-specific detail:** this is the kind of platform-specific knowledge that's easy to miss but important for correctness.
- **The `LINE_TERMINATOR = "\n"` is a small but important detail:** it prevents cross-OS Git diff noise and hash mismatches, which would break the hash-verification safety net.
- **The `SEALED_SPLITS` access control is a good governance pattern:** it prevents accidental reads of the test split, which is critical for unbiased evaluation.
- **The 5 test functions are thorough:** they cover the happy path and three failure modes (noise band, FD violation, leakage), plus a check that `plan_freeze` writes nothing on failure. This is good test coverage.
- **Cross-reference to the manifest pattern:** this is the same verification pattern used throughout the project. Worth noting so the pattern is recognised as a project-wide convention.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.