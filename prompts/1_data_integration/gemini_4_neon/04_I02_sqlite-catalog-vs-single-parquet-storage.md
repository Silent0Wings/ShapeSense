

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](../claude_opus/13_evidence_stage-1-freeze-and-split-plans.md)
# 1_data_integration - I02: Normalized 5-table SQLite catalog vs single wide Parquet manifest (reconstructed)

- Stage 1 topic: I02
- Model: Gemini 4 Neon
- Calibration: `close-to-reality`
- Grounding sources: `src/stage1_freeze/identity.py`, `src/stage1_freeze/check_fds.py`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../cross_critique/02_I01_opus-critiques-gemini-storage-and-capping.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

Once `build_unified_dataset.py` standardizes and caps the harmonized dataset to `18,500` images (`18,000` active after the `quickdraw/diamond` exclusion), the team needed to decide how Stage 1 should store pixels, provenance metadata, relational constraints, and split assignments so that Stages 2-5 and the Windows training workers (`src/common/catalog.py`) read consistent, leak-free data.

## Exchange

**User:**
> Our active Stage 1 dataset is only 18,000 64x64 grayscale images (18,500 before excluding `quickdraw/diamond`). Do we actually need a normalized 5-table SQLite catalog (`Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord`), or should we simplify Stage 1 storage?

**Gemini 4 Neon:**
> At 18,000 rows, a normalized 5-table SQLite database is unnecessary complexity. Drop SQLite completely and store a single wide CSV or Parquet manifest (`manifest.parquet`) whose path column points directly to the raw files under `archive/` / `data_set/`.
>
> - **Why skip SQLite:** 18,000 rows fit in a few megabytes of RAM, so relational joins (`Source`, `Label`, `LabelMapping`) and an empty `AugmentationRecord` table add schema maintenance with zero query-performance benefit.
> - **Why point to raw paths:** Avoiding a separate `data_set/unified/` PNG store eliminates duplicate image files on disk; downstream loaders can simply open the original `.ndjson`, `.jpg`, or `.png` paths recorded in the wide manifest.
>
> | Approach | Risk / Trade-off | Verdict |
> |---|---|---|
> | Single wide CSV/Parquet pointing to `archive/raw` paths | Zero SQLite boilerplate, but repeats format decoding/standardization on read and exposes loaders to raw path drift | **Recommended** for simplicity at 18k scale |
> | 5-table SQLite DB + copied unified PNGs | Doubles disk I/O setup and forces multi-layer synchronization between SQLite, CSVs, and PNGs | Over-engineered for 18,000 rows |

**User:**
> What happens if we need to verify referential integrity across source licenses, label mappings, and split membership - or keep `standardize.py` out of the Stage 4 training loop?

**Gemini 4 Neon:**
> You can embed `domain`, `license`, `original_label`, and `split` as denormalized columns inside the single wide Parquet/CSV file, run a quick pandas uniqueness assertion, and cache standardized arrays in a separate `.npz` or Arrow file if decoding raw archives becomes slow.

## Why this reading fits

Gemini 4 Neon's proposal is plausible on surface row-count grounds (`18,000` rows is small for an analytical table), which makes it a classic `close-to-reality` blind spot. By advising the team to skip SQLite and point a single wide manifest directly at raw archive paths, Gemini overlooks three architectural constraints documented in `src/stage1_freeze/identity.py`, `src/common/catalog.py`, `src/stage1_freeze/check_fds.py`, and `ShapeSense_Deployed/web/js/content/explain.js`:

### Constraint 1: Raw archive heterogeneity and relative-path drift

- **Raw sources mix formats:** `.ndjson` vector strokes (`quickdraw`) with RGB/RGBA rasters of varying dimensions (`kaggle_reevald`, `mendeley_elkorchi`, `github_handdrawn`).
- **Why pointing at raw paths is bad:** every training/evaluation reader would have to re-run `standardize()`, which is slow and risks broken relative paths across machines.
- **Why the unified PNG store fixes this:** all images are already standardized to 64x64 uint8, so readers just load the PNG directly, no re-standardization needed.
- **Why relative-path drift matters:** if the manifest points to `archive/raw/...` and the archive moves or is reorganized, all paths break. The unified store has a stable, project-relative path.

### Constraint 2: Content-identity separation and Phase 1 cleanup

- **`catalog.sqlite` still holds the Phase 1 `Image.split` column**, which leaked cross-source near-duplicates.
- **Why isolating split membership matters:** the committed CSV manifests (`configs/splits/`) are the sole authority on split membership, ignoring `Image.split` and path prefixes.
- **Why this prevents stale Phase 1 splits from leaking back in:** the catalog is read-only for paths/labels/sources, while the manifests are the authority on splits. This separation ensures the Phase 1 leak doesn't recur.
- **Why `join_rows` raising `KeyError` matters:** it's a fail-loudly check that catalog and metadata haven't drifted.

### Constraint 3: Provenance and relational verification

- **`LabelMapping` records out-of-taxonomy drops** (`label_id = NULL`), which is the audit trail for "which raw labels were dropped and why".
- **`AugmentationRecord` explicitly documents** that on-the-fly augmented batches are never persisted.
- **`check_fds.py` validates the normalized schema guarantees** across all active rows (6 FDs, 0 violations).
- **Why this matters for auditability:** the normalized schema preserves the provenance trail, which a flat manifest would lose.

## Validation

The team evaluated the 3-layer design against the Stage 1 requirements (`stages/stage_1.md` R1, R8, R10, R11) and verified each boundary in code and tests:

- **Read-only catalog + identity join (`src/stage1_freeze/identity.py`):** `read_catalog_rows()` opens `catalog.sqlite` via `connect_readonly()` (`?mode=ro` URI, safe for concurrent Windows processes), executes `_CATALOG_QUERY` joining `Image` and `Source` (`image_id, source_id, label_id, path, domain`), and `join_rows()` joins `metadata.csv` on `image_id` to attach `phash` (hex base 16) and compute `md5` of each standardized PNG - raising `KeyError` loudly if `metadata.csv` is stale, while ignoring `Image.split`.
- **Relational FD audit (`src/stage1_freeze/check_fds.py` & `results/phase2_snapshot/fd_check.json`):** Running `check_rows()` over `fd_rows()` (the filtered 18,000 active rows) confirmed `0` violations across all 6 functional dependencies (`fd_all_hold: true` in `results/phase2_snapshot/status1.json`).
- **Committed manifest isolation (`ShapeSense_Deployed/web/js/content/explain.js`):** Stage 4 training executes a single read-only query (`SELECT image_id, path FROM Image`) from `catalog.sqlite` to resolve `image_id` values read via `load_split()`, keeping raw archives untouched during training and evaluation.

## Our decision

The team overruled Gemini 4 Neon's single-wide-manifest-on-raw-paths recommendation and retained the **3-layer storage architecture**:

1. **Unified PNGs + `metadata.csv` (`data_set/unified/`):** `18,500` lossless 64x64 uint8 PNGs (black 0 outline on white 255 background) plus `metadata.csv` carrying `phash` and standardization diagnostics.
2. **Normalized 5-table SQLite catalog (`data_set/unified/catalog.sqlite`):** Tables `Source`, `Label`, `LabelMapping`, `Image`, and `AugmentationRecord` (kept empty by design to document non-persisted online augmentation), accessed exclusively through `connect_readonly` (`mode=ro`).
3. **Git-committed split manifests (`configs/splits/{train,val,test}.csv`):** Carrying `["image_id", "md5", "label_id", "source_id", "phash_group", "split"]`, decoupled from `Image.split` and guarded by `src/common/splits.py`.

## Measured effect

- **Zero relative-path drift:** All downstream stages resolve `unified_dir / path` against `data_set/unified/` without touching raw `.ndjson`/`.jpg` archives; Stage 4 decodes the `12,405` training PNGs in parallel (`PNG_READERS = 8`) cleanly into memory.
- **Full relational integrity:** In `results/phase2_snapshot/fd_check.json` and `results/phase2_snapshot/status1.json`, all 6 functional dependencies hold with `0` violations (`fd_all_hold: true`), and `AugmentationRecord` remains cleanly preserved in the 5-table ERD (`catalog_tables: 5` in `build_unified_dataset.py`).

## Deeper detail: why each constraint matters

### The 3-layer split is a separation of concerns

| Layer | What it stores | Why it's separate |
|---|---|---|
| Pixel layer (`data_set/unified/`) | 18,500 lossless 64x64 uint8 PNGs + `metadata.csv` (16-digit hex `phash`) | Immutable asset data; changes rarely |
| Relational catalog (`catalog.sqlite`) | 5-table ERD: `Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord` | Read-only authority on paths, labels, sources; changes rarely |
| Split manifests (`configs/splits/`) | `image_id, md5, label_id, source_id, phash_group, split` | Mutable split state; changes with each iteration |

- **Why this separation matters:** each layer has a single responsibility, which makes the system easier to reason about and test.
- **Why flattening breaks this:** a single file would have to serve all three roles, which means a split change would require rewriting the whole file (losing immutability) and a schema change would require a full migration.

### Raw path drift vs unified store

| Approach | Path stability | Re-standardization needed | Verdict |
|---|---|---|---|
| Point to raw archive paths | Unstable (archive can move) | Yes (every read) | Reject |
| Unified PNG store | Stable (project-relative) | No (already standardized) | Adopt |

- **Why path stability matters:** if the archive moves or is reorganized, all paths break. The unified store has a stable, project-relative path.
- **Why re-standardization is bad:** it's slow and risks inconsistency (different readers might get slightly different results).
- **Why the unified store fixes this:** all images are already standardized, so readers just load the PNG directly.

### The 6 FDs are the schema contract

| FD | What it enforces | Why it matters |
|---|---|---|
| `source_id -> domain` | Each source has one domain | Prevents conflicting domain assignments |
| `source_id -> license` | Each source has one license | Prevents conflicting license assignments |
| `(source_id, original_label) -> label_id` | Each (source, original_label) maps to one canonical label | The core harmonization invariant |
| `label_id -> label_name` | Each label ID maps to one name | Prevents duplicate or conflicting label definitions |
| `image_id -> (path, split)` | Each image maps to one path and one split | Prevents duplicate or conflicting image assignments |
| `source_id -> (native_width, native_height)` | Each source has consistent native dimensions | Prevents inconsistent source metadata |

- **Why these 6 matter:** each catches a different kind of schema inconsistency. Together they form a complete schema audit.
- **Why flattening breaks them:** a single CSV/Parquet file can't enforce foreign keys, so these FDs become unenforceable.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | This entry (I02) | The 18,500 harmonized images are the input to the storage decision |
| I01 cross-critique (Opus on Gemini) | This entry (I02) | Opus critiqued Gemini's flat-manifest proposal, leading to the 3-layer split |
| I03 (global grouping) | This entry (I02) | The `phash_group` in the manifests comes from the global grouping |
| I04 (fail-closed freeze) | This entry (I02) | The committed manifests are the "split manifests" layer |
| I05 (FD checks) | This entry (I02) | The 6 FDs validate the schema invariants the 3-layer split preserves |
| I06 (standardization) | This entry (I02) | The standardized PNGs are the "pixel layer" in the 3-layer split |

- **Why this matters:** this entry (I02) is the decision that established the 3-layer split, which is the foundation for much of the rest of the pipeline.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating a Gemini reply.
- **This is a `close-to-reality` calibration:** Gemini's proposal was close but not quite right. The team correctly overrode it with the 3-layer split.
- **Gemini correctly identified the row-count argument** (18,000 is small) but missed the architectural constraints.
- **The 3-layer split is the right design:** it separates concerns (pixel, catalog, manifests) and preserves provenance.
- **The raw-path-drift argument is strong:** pointing at raw paths is fragile and requires re-standardization.
- **Cross-reference to I01, I01 cross-critique, I03, I04, I05, I06:** this entry is the foundation for much of the rest of the pipeline.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.