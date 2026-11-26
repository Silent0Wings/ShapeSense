
# 1_data_integration - I01: Opus critiques Gemini on flat manifest storage and naive source capping 

- Stage 1 topic: I01
- Model: Opus 5.5 + Gemini 4 Neon
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/build_unified_dataset.py`, `src/stage1_freeze/identity.py`, `src/stage1_freeze/check_fds.py`, `results/phase2_snapshot/status1.json`, `results/phase2_snapshot/fd_check.json`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../gemini_4_neon/03_I01_source-capping-and-label-harmonization.md`, `../gemini_4_neon/04_I02_sqlite-catalog-vs-single-parquet-storage.md`


## Context

When the team designed Stage 1 data integration for ShapeSense, two foundational questions came up back-to-back: how to harmonize and cap four heterogeneous shape sources without letting high-volume datasets overwhelm smaller ones, and how to store the unified dataset cleanly for downstream stages. Earlier Gemini 4 Neon proposals - documented in `03_I01_source-capping-and-label-harmonization.md` and `04_I02_sqlite-catalog-vs-single-parquet-storage.md` - recommended replacing the relational catalog with a flat CSV/Parquet file alongside either uncapped sampling or an aggressive 500-image cap per group. Before locking Stage 1, team members asked Opus 5.5 to perform a line-by-line cross-critique of both Gemini recommendations against our schema, functional-dependency checks, and training I/O requirements.

## Exchange

**User:**
> Gemini 4 Neon proposed two shortcuts for Stage 1 integration: (1) either leave `(source, label)` groups uncapped or cap them tightly at 500 images, and (2) replace the 5-table SQLite catalog with a single flat CSV/Parquet manifest containing paths, labels, and split assignments. Before all members sign off on that design, we want a cross-critique of where those proposals break under our data model and Stage 4 training constraints.

**Gemini 4 Neon:**
> My rationale in `03_I01_source-capping-and-label-harmonization.md` and `04_I02_sqlite-catalog-vs-single-parquet-storage.md` was simplicity and class balance:
> - Uncapped sampling preserves every raw sample, while a flat 500-per-group cap trims large datasets like Quick, Draw! down to match smaller sketch groups.
> - A single flat Parquet/CSV manifest eliminates `sqlite3` connection management, joins, and schema boilerplate, keeping paths, metadata, and split assignments in one self-contained table.

**Opus 5.5:**
> Both proposals introduce subtle correctness and lineage failures when evaluated against `src/stage1_freeze/build_unified_dataset.py`, `src/stage1_freeze/identity.py`, and `src/stage1_freeze/check_fds.py`.
>
> First, on **flat manifest storage without the 5-table SQLite catalog + `md5`/`phash` identity**:
> - **Broken foreign-key lineage:** `catalog.sqlite` encodes five normalized entities (`Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord`) with explicit foreign keys (`source_id -> Source`, `label_id -> Label`, `(source_id, original_label) -> LabelMapping`). Flattening everything into one CSV/Parquet file drops normalized `LabelMapping` provenance (including out-of-taxonomy drops such as `kite`, `trapezoid`, `parallelogram`, `Heptagon`, `Nonagon`, and `other`) and weakens enforcement of functional dependencies like `source_id -> domain`, `source_id -> license`, and `(source_id, original_label) -> label_id`.
> - **Positional ID and path fragility:** In `build_unified_dataset.py`, `image_id` is generated positionally as `f"{r['source_id']}_{r['label']}_{i:06d}"`, and `Image.split` / `{train,val,test}/...` path prefixes are Phase 1 artifacts. If you rely on a single flat manifest without separating the read-only catalog (`catalog.sqlite`, opened with `?mode=ro` in `src/common/catalog.py`) from content identity (`identity.py` joining `Image` + `Source` with `metadata.csv` and computing pixel `md5` + 16-hex `phash`) and committed split manifests (`configs/splits/{train,val,test}.csv`), any rebuild or filter renumbers `image_id` and silently shifts paths or stale split labels.
> - **Stale-metadata silent failure:** `identity.join_rows()` intentionally raises `KeyError` if any catalog `image_id` is missing from `metadata.csv`, ensuring `catalog.sqlite` and `metadata.csv` never drift silently. A monolithic flat file merges mutable split state with immutable source metadata, breaking Git-committed split freezes (`configs/splits/`) and forcing full-dataset rewrites whenever splits change.
>
> Second, on **uncapped vs. 500-cap sampling**:
> - **Uncapped sampling** lets massive sources like `quickdraw` or `mendeley_elkorchi` dominate shared classes (`circle`, `square`, `triangle`), skewing both validation metrics and source-balance ratios.
> - **A naive 500-per-group cap** starves `(source, label)` groups too early - before `standardize.py` outlier filtering and cross-source `md5` exact deduplication run - and cuts total dataset scale roughly in half, reducing per-class test `n` and widening Stage 5 noise bands (`100 * sqrt(0.9 * 0.1 / n)`).
> - **Two-stage deterministic capping** in `build_unified_dataset.py` solves both: draw up to `CANDIDATES_PER_GROUP = 1500` with `SEED = 42`, run `standardize()` (`Rejected` outliers logged to `rejects.csv`) and cross-source `seen_md5` deduplication first, and only then stop at `MAX_PER_GROUP = 1000`. That produces 18,500 harmonized images across the 4 licensed sources (`kaggle_dinesh` excluded due to `Unknown` license), yielding 18,000 active images after the rule-based exclusion of 500 `quickdraw/diamond` drawings.

**User:**
> Can you summarize the trade-offs between Gemini's initial positions and the three-layer + two-stage capping design in one table?

**Opus 5.5:**
> Here is the direct engineering comparison:

| Option | Effect | Recommendation |
|---|---|---|
| Flat CSV/Parquet only (no SQLite catalog) | Drops normalized `Source`/`Label`/`LabelMapping` FKs, conflates immutable asset paths with mutable split state, and risks silent `image_id` / `phash` drift across rebuilds | Reject; keep the 3-layer split: `64x64` PNGs + `metadata.csv`, read-only 5-table `catalog.sqlite`, and committed `configs/splits/*.csv` joined via `identity.py` |
| Uncapped `(source, label)` sampling | Lets high-volume sources (`quickdraw`, `mendeley_elkorchi`) dominate shared classes and distorts class/source priors | Reject; cap per `(source, label)` group |
| Naive `500`-per-group cap | Applied blindly, shrinks post-dedup yield and widens Stage 5 test noise bands (`split_stats.csv` / `noise_bands.csv`) | Reject; insufficient headroom after outlier rejection and deduplication |
| Two-stage cap (`CANDIDATES_PER_GROUP = 1500` -> `standardize` + `md5` dedup -> `MAX_PER_GROUP = 1000`) | Filters `Rejected` and exact duplicates before enforcing the 1,000-image ceiling, yielding 18,500 harmonized rows and 18,000 active rows after `quickdraw/diamond` exclusion | Adopt; matches `build_unified_dataset.py` and `ShapeSense_Deployed/web/js/content/explain.js` (`FACTS.build`) |

## Why this reading fits

Opus 5.5's cross-critique aligns directly with the final Stage 1 architecture recorded across `src/stage1_freeze/build_unified_dataset.py`, `src/stage1_freeze/identity.py`, and `ShapeSense_Deployed/web/js/content/explain.js`. Rather than treating storage as an all-or-nothing choice between Parquet and SQL, the winning implementation separates concerns into three clean layers: lossless `64x64` `uint8` PNGs plus `metadata.csv` (carrying 16-digit hex `phash`) on disk, a read-only (`?mode=ro`) 5-table `catalog.sqlite` as the authority on sources, labels, mappings, and paths, and Git-committed CSV manifests (`configs/splits/{train,val,test}.csv`) carrying `image_id, md5, label_id, source_id, phash_group, split`. Likewise, two-stage capping (`1500` candidates -> standardization + `md5` dedup -> `1000` max per group) guarantees clean headroom without source dominance.

## Validation

- **Functional dependency verification (`src/stage1_freeze/check_fds.py`, `results/phase2_snapshot/fd_check.json`):** All six schema FDs hold with `n_violations: 0` and `holds: true` across the 18,000 active images:
  - `source_id -> domain` (4 groups)
  - `source_id -> license` (4 groups)
  - `(source_id, original_label) -> label_id` (21 groups)
  - `label_id -> label_name` (10 groups)
  - `image_id -> (path, split)` (18,000 groups)
  - `source_id -> (native_width, native_height)` (4 groups)
- **Stage 1 freeze checks (`results/phase2_snapshot/status1.json`):** `no_id_in_two_splits: true`, `no_md5_in_two_splits: true`, `no_phash_group_spans: true`, `fd_all_hold: true`, `status: "passed"`.
- **Deployment fact audit (`ShapeSense_Deployed/web/js/content/explain.js`):** `FACTS.build` verifies `candidates_per_group: 1500`, `max_per_group: 1000`, `rows: 18500`, and `EXPLAIN.stage1` documents the three-layer storage and 5-table ERD (`Source`, `Label`, `LabelMapping`, `Image`, `AugmentationRecord`).

## Our decision

The team rejected Gemini 4 Neon's flat-manifest-only and uncapped/500-cap proposals from `03_I01_source-capping-and-label-harmonization.md` and `04_I02_sqlite-catalog-vs-single-parquet-storage.md`, adopting Opus 5.5's recommended architecture:
1. Keep the two-stage deterministic cap (`SEED = 42`, `CANDIDATES_PER_GROUP = 1500`, `MAX_PER_GROUP = 1000`) after `standardize()` and cross-source `md5` deduplication in `src/stage1_freeze/build_unified_dataset.py`, excluding `kaggle_dinesh` (`Unknown` license).
2. Retain the 5-table `catalog.sqlite` (opened read-only via `connect_readonly` in `src/common/catalog.py`) paired with `metadata.csv` and `src/stage1_freeze/identity.py` (`load_unified` / `join_rows`) so every row carries both `phash` and content `md5` while ignoring Phase 1 `Image.split` leftovers.

## Measured effect

- Harmonized catalog size stabilized at `18,500` standardized `64x64` PNGs (`FACTS.build.rows = 18500`).
- After applying the `quickdraw/diamond` rule exclusion (`excluded_by_rule: {"quickdraw/diamond": 500}`), Stage 1 froze `18,000` active images into `12,405` train / `2,819` val / `2,776` test (`results/phase2_snapshot/status1.json`).
- All 6 functional dependencies in `results/phase2_snapshot/fd_check.json` and all 4 integrity/leakage gates in `status1.json` passed with zero violations.

## Deeper detail: why each critique lands

### Flat manifest: broken foreign-key lineage

- **The 5-table ERD encodes provenance:** `Source` (domain, license), `Label` (name), `LabelMapping` (the `(source_id, original_label) -> label_id` mapping), `Image` (path, split), `AugmentationRecord` (empty, since augmentation is on-the-fly).
- **Why flattening breaks this:** a single CSV/Parquet file can't enforce foreign keys, so the `LabelMapping` provenance (which out-of-taxonomy labels were dropped and why) is lost.
- **Why this matters for auditability:** the `LabelMapping` table is the record of "which raw labels were dropped and why", which is critical for reproducibility and auditability.
- **Why the 6 FDs depend on this:** `source_id -> domain`, `source_id -> license`, and `(source_id, original_label) -> label_id` all rely on the normalized schema. Flattening would make these FDs unenforceable.

### Flat manifest: positional ID and path fragility

- **`image_id` is positional:** `f"{r['source_id']}_{r['label']}_{i:06d}"` means the ID depends on the order rows were processed. Any rebuild that changes the order (e.g., due to a filter) renumbers all subsequent IDs.
- **Why this is fragile:** if `image_id` shifts, all downstream references (exclusion lists, split assignments, `phash_group`) break silently.
- **Why the 3-layer split fixes this:** the read-only catalog (`catalog.sqlite`) is the authority on paths and IDs, the identity layer (`identity.py`) joins catalog + metadata to get `md5`/`phash`, and the committed manifests (`configs/splits/`) are the authority on split membership. Each layer has a single responsibility.
- **Why `join_rows` raising `KeyError` matters:** it's a fail-loudly check that catalog and metadata haven't drifted. A monolithic flat file would merge these, losing the check.

### Flat manifest: stale-metadata silent failure

- **`identity.join_rows()` raises `KeyError` on missing metadata:** this ensures catalog and metadata never drift silently.
- **Why a monolithic flat file breaks this:** it merges mutable split state with immutable source metadata, so a split change would require rewriting the whole file, losing the immutability guarantee.
- **Why Git-committed split manifests matter:** they're the audit trail for "which images are in which split", which is critical for reproducibility.

### Uncapped sampling: source dominance

- **`quickdraw` and `mendeley_elkorchi` are high-volume:** 3,500 and 90,000 images respectively, vs 20,000 for reevald and 27,292 for frobertpixto.
- **Why uncapped is a problem:** the high-volume sources would dominate shared classes (`circle`, `square`, `triangle`), skewing both validation metrics and source-balance ratios.
- **Why this matters for the shortcut:** if one source dominates, the model learns "which source" rather than "which shape", which is the F05 shortcut problem.

### Naive 500-cap: starved groups

- **500-per-group is too aggressive:** it doesn't leave headroom for outlier rejection (via `standardize()`) and cross-source `md5` deduplication.
- **Why this matters:** after filtering, you might have far fewer than 500 clean images per group, which shrinks the dataset and widens the Stage 5 noise bands.
- **Why the noise band matters:** `100 * sqrt(0.9 * 0.1 / n)` means smaller `n` means wider bands, which means less statistical power to detect harm.

### Two-stage cap: the right design

- **`CANDIDATES_PER_GROUP = 1500`:** draw up to 1500 candidates per group, giving headroom for filtering.
- **`standardize()` + `md5` dedup:** filter out `Rejected` outliers and exact duplicates.
- **`MAX_PER_GROUP = 1000`:** only then enforce the 1000-image ceiling.
- **Why this works:** it guarantees clean headroom (1500 - 1000 = 500 spare per group) without source dominance.
- **Why `SEED = 42`:** makes the sampling reproducible.

### Cross-reference to I02, I04, I05

- **I02** is the content-addressed identity (`md5` from decoded pixels), which is the "identity" layer in the 3-layer split.
- **I04** is the fail-closed manifest freeze, which is the "committed manifests" layer in the 3-layer split.
- **I05** is the FD check, which validates the schema invariants that the 3-layer split preserves.
- **Why this matters:** the 3-layer split is the architectural foundation that I02, I04, and I05 all build on. This entry (I01 cross-critique) is the decision that established that foundation.

### Cross-reference to F05 and I06

- **F05** is the source-attribution shortcut (`0.917` accuracy). Uncapped sampling would make this worse by letting one source dominate.
- **I06** is the standardization shortcut discussion. The two-stage cap is part of the response to the shortcut problem: by capping per group, you prevent any one source from dominating.
- **Why this matters:** the two-stage cap is a direct mitigation for the shortcut problem, complementing the I06 decision to keep standardization frozen.

## Notes on the log


- **This is a `winning-decision` calibration:** Opus's cross-critique was correct and was adopted. This is the best kind of two-LLM comparison outcome.
- **The 3-layer split is the architectural foundation:** pixel data, relational metadata, and split manifests are three separate concerns, each with its own storage layer.
- **The two-stage cap is a direct mitigation for the shortcut problem:** by capping per group, you prevent any one source from dominating.
- **The 6 FDs depend on the normalized schema:** flattening would make them unenforceable.
- **The `join_rows` KeyError is a fail-loudly check:** it ensures catalog and metadata haven't drifted.
- **Cross-reference to I02, I04, I05:** the 3-layer split is the foundation they build on.
- **Cross-reference to F05 and I06:** the two-stage cap is a direct mitigation for the shortcut problem.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.