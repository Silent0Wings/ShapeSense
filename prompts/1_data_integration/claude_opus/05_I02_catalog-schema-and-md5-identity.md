

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](13_evidence_stage-1-freeze-and-split-plans.md)

# 1_data_integration - I02: Relational SQLite catalog schema and content-addressed MD5 identity (reconstructed)

- Stage 1 topic: I02
- Model: Opus 5.5
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/identity.py`, `stages/stage_1.md`, `ShapeSense_Deployed/web/js/content/explain.js`, `results/phase2_snapshot/fd_check.json`
- Follow-up: `../gemini_4_neon/04_I02_sqlite-catalog-vs-single-parquet-storage.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

In Phase 1, `build_unified_dataset.py` assigned positional identifiers (`f"{r['source_id']}_{r['label']}_{i:06d}"`) and wrote `Image.split` plus `train/val/test/` directory prefixes into `data_set/unified/catalog.sqlite`. However, `catalog.sqlite`'s `Image` table stored neither `phash` (which lived only in `metadata.csv`) nor `md5` (which existed only as an unpersisted function). Whenever a rebuild removed or reordered an image, every subsequent positional `image_id` shifted, breaking exclusion lists and split tracking (`stages/stage_1.md`). Stage 1 needed a clean relational catalog and content-addressed identity model that stayed Windows-safe across concurrent readers.

## Exchange

**User:**
> Phase 1 left us with two split files - `catalog.sqlite` and `metadata.csv` - plus positional `image_id` values and legacy `Image.split` prefixes that leaked near-duplicates. How should we structure the Stage 1 storage layers, relational schema, and content identity without rewriting all 18,500 PNG files?

**Opus 5.5:**
> Separate storage into three focused layers and promote `md5` and `phash` to first-class manifest fields in `src/stage1_freeze/identity.py`:
>
> - **Keep the 3-layer storage layout:**
>   1. **Pixel layer (`data_set/unified/`):** `18,500` lossless `64x64` single-channel `uint8` PNGs (black `0` outline on white `255`) alongside `metadata.csv` (16-digit hex `phash`, `PHASH_HEX_BASE = 16`).
>   2. **Relational SQLite catalog (`catalog.sqlite`):** Retain the 5-table ERD (`Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord`) as the authority on paths, labels, and sources - never split membership. Keep `AugmentationRecord` empty since augmented images are generated on the fly.
>   3. **Committed manifests (`configs/splits/{train,val,test}.csv`):** Store `MANIFEST_COLUMNS` (`image_id, md5, label_id, source_id, phash_group, split`) as the sole authority on split membership, ignoring `Image.split` and path prefixes.
> - **Enforce read-only Windows-safe catalog access:** Open `catalog.sqlite` via `connect_readonly` (`Path(catalog_path).resolve().as_uri() + "?mode=ro"`, `uri=True`), one connection per process, executing `_CATALOG_QUERY` (`SELECT i.image_id, i.source_id, i.label_id, i.path, s.domain FROM Image AS i JOIN Source AS s ON s.source_id = i.source_id`) in `read_catalog_rows`.
> - **Verify content identity from decoded pixels:** In `load_unified(config)`, read `catalog_rows` via `read_catalog_rows` and `metadata_rows` via `read_metadata`, then call `join_rows(catalog_rows, metadata_rows, md5_of)` to project `ROW_FIELDS = ("image_id", "label_id", "source_id", "domain", "phash", "path", "md5")`. Compute `md5(read_png(unified_dir / rel_path))` directly from the decoded grayscale `uint8` array bytes so identity depends strictly on pixel content, and raise `KeyError` if any catalog row is missing from `metadata.csv`.

**User:**
> Why compute `md5` from `read_png(...)` in `load_unified` instead of hashing the PNG file bytes on disk or trusting `image_id`?

**Opus 5.5:**
> Hashing `arr.tobytes()` via `src/common/imaging.py` (`md5`) makes identity invariant to PNG zlib headers or compression metadata while matching `build_unified_dataset.py` and `standardize.py`. Here is the trade-off:

| Approach | Risk / Trade-off | Verdict |
|---|---|---|
| Trust positional `image_id` and `Image.split` | Rebuilds renumber `image_id`s after any removal; `Image.split` reflects leaky Phase 1 grouping | Reject |
| Hash raw PNG bytes on disk | Sensitive to encoder/zlib metadata changes; still misses `phash` join validation | Reject |
| 5-table read-only SQLite + `join_rows` + `md5(read_png(...))` | Reads every PNG once in `load_unified`, fails loudly on stale `metadata.csv`, locks manifests to `md5` + `phash` | Adopt |

## Why this reading fits

Opus 5.5's design matches `src/stage1_freeze/identity.py`, `src/common/catalog.py`, and `ShapeSense_Deployed/web/js/content/explain.js` line for line: `ROW_FIELDS`, `_CATALOG_QUERY`, `PHASH_HEX_BASE = 16`, `connect_readonly` with `?mode=ro`, `read_catalog_rows`, `read_metadata`, `join_rows` (raising `KeyError` on missing metadata and sorting by `image_id`), and `load_unified` computing `md5(read_png(unified_dir / rel_path))` are all present verbatim in the codebase.

## Validation

- `results/phase2_snapshot/fd_check.json` verifies relational integrity across the `18,000` active rows: `image_id -> (path, split)` (`18000` groups, `0` violations), `source_id -> domain` (`4` groups, `0` violations), `source_id -> license` (`4` groups, `0` violations), and `label_id -> label_name` (`10` groups, `0` violations).
- `results/phase2_snapshot/status1.json` confirms `no_id_in_two_splits: true` and `no_md5_in_two_splits: true` across the frozen splits.
- `stages/stage_1.md` (`R1`, `R2`, `R11`) and `explain.js` document that `Image.split` and `train/val/test/` path prefixes are ignored while `connect_readonly` keeps multi-process Windows reads safe.

## Our decision

The team kept the 5-table SQLite ERD (`Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord`) in `catalog.sqlite` as the read-only authority for paths, sources, and labels via `connect_readonly`, and adopted `src/stage1_freeze/identity.py` (`read_catalog_rows`, `read_metadata`, `join_rows`, `load_unified`) to materialize `ROW_FIELDS` with pixel-array `md5` and 64-bit `phash` into the Stage 1 manifests.

## Measured effect

- Every unified image carries both an immutable `md5` computed from decoded `64x64` `uint8` pixels and a 64-bit DCT `phash` (`PHASH_SIZE = 32`, `PHASH_LOW = 8`), eliminating positional `image_id` fragility.
- All `18,000` active catalog rows join cleanly against `metadata.csv` with `0` relational FD violations (`results/phase2_snapshot/fd_check.json`) and zero cross-split `image_id` or `md5` duplicates (`results/phase2_snapshot/status1.json`).

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor, C02, C34 and I01 entries, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The reconstruction is honest about its source:** the entry explicitly says it is "reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved". This is good practice: it's transparent about what is and isn't a primary source.
- **The 3-layer storage layout is a clean separation of concerns:** pixel data, relational metadata, and split manifests are three separate concerns, each with its own storage layer. This is good software architecture.
- **Content-addressed identity (md5 from decoded pixels) is a strong design choice:** it makes identity invariant to PNG encoding details, which is important for a dataset that might be re-encoded or re-compressed.
- **The `join_rows` with `KeyError` on missing metadata is a good fail-loudly pattern:** it catches stale or incomplete metadata early rather than silently producing wrong results.
- **The `connect_readonly` with `?mode=ro` is Windows-safe:** this is a practical detail that matters for a Windows-first development environment.
- **The 5-table ERD is retained, not rewritten:** this is a good example of incremental improvement rather than a full rewrite. The existing schema is kept, just with better identity handling.
- **Cross-reference to S06/F18/C02/C24/C34:** the MD5-manifest pattern is used throughout the project. This entry extends it to content-addressed identity (md5 from decoded pixels), which is a natural evolution.
- **Cross-reference to I01:** the `label_id` and `source_id` in `ROW_FIELDS` come directly from the I01 schema harmonization. This is a good example of the two entries building on each other.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.