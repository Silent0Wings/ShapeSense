# 1_data_integration - Stage 1 plan: data freeze and splits

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-07
- Owner: 40256377
- Worksheet entries: I02, I03, I04
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.
-  [I02](05_I02_catalog-schema-and-md5-identity.md), [I02](../gemini_4_neon/04_I02_sqlite-catalog-vs-single-parquet-storage.md), [I03](06_I03_global-phash-grouping-and-group-split.md), [I03](../gemini_4_neon/05_I03_global-phash-hamming-and-giant-groups.md), [I04](07_I04_fail-closed-leakage-checks-and-atomic-freeze.md), [I04](../gemini_4_neon/06_I04_sealed-split-guard-and-access-logging.md)

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner brief for Stage 1 (data freeze and splits) and one implementation plan per task, each tracked in ignore/todo.md.

## Response (saved output, verbatim)

### `stages/stage_1.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 1 — Data freeze and splits

> Owner brief. Everything here is about Stage 1 only. The full project
> plan is `../implementation.md`; shared rules (configs, `status.json`,
> guards) live there under *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 1` · **Code folder:** `src/stage1_freeze/`
- **Depends on:** nothing — starts day 1 · **Blocks:** Stages 2, 3, 4, 5
- **Effort:** ~1 day (the md5 pass and the global pHash regrouping are
  new in v4)

## Focus

Turn the 18,500-image SQLite catalog into **three locked, leak-free
splits** (train / validation / test) that every later stage trusts
without checking. Stage 1 is the only stage allowed to decide which
image goes where. After it finishes, the test split is frozen until
Stage 5.

## Goals

1. Give every image a **stable content identity** (`md5`), because
   `image_id` is positional and shifts whenever the build is rerun.
2. Apply the gemstone-diamond filter (Decision 1), matched on `md5`, and
   record how many images it removed.
3. Recompute pHash near-duplicate groups **across all sources**
   (Decision 15), not within each source as Phase 1 did.
4. Split 70 / 15 / 15 by group, stratified by class (and source where
   possible), and publish the new counts.
5. Prove there is no leakage with assertions that fail the stage.
6. Find out whether the image source is guessable from pixels alone
   (source-classifier check), so later stages know about the shortcut.
7. Record everything needed to rebuild the exact same splits.

## Out of scope

- Augmentation, synthetic data, training, evaluation.
- Changing `standardize.py` behaviour (Phase 1 already fixed it).
- Reading or looking at test-set *results* — there are none yet.

## Inputs

| Input | Where |
|---|---|
| SQLite catalog (18,500 rows: identity, label, source) | `data_set/unified/catalog.sqlite` |
| pHash and standardization fields | `data_set/unified/metadata.csv` |
| Standardized PNGs (for the md5 pass) | `data_set/unified/{train,val,test}/` |
| `standardize.py`, `check_fds.py`, `taxonomy.py` | `src/stage1_freeze/` (moved from `scripts/`) |
| `seed`, `split`, `filter_gemstones` | `configs/pipeline.yaml` |
| Reviewed gemstone exclusions (`image_id, md5`) | `configs/gemstone_ids.csv` |

**Two input files, not one.** The catalog's `Image` table is
`(image_id, source_id, label_id, path, size, split)` — it stores neither
pHash nor any content hash. pHash lives only in `metadata.csv`, and md5
exists only as a function (`standardize.md5`), never persisted. Stage 1
is where both become first-class columns.

## Requirements

**Must**
- R1. Compute `md5` of the standardized array for every image and carry
  it into the manifests as a column.
- R2. Match `configs/gemstone_ids.csv` on `md5`, not on `image_id`. Fail
  the stage if any listed row matches zero images or more than one.
  Count goes in `status.json → metrics.gemstones_removed`.
- R3. Recompute pHash groups over **all** images at once (Hamming ≤ 2),
  not per (source, label). Do not reuse the Phase 1 `phash_group`
  values.
- R4. Every pHash near-duplicate group lands in exactly one split.
- R5. No `image_id` and no `md5` appears in two splits.
- R6. Split ratios come from `configs/pipeline.yaml`, never hard-coded.
- R7. The same seed and catalog produce byte-identical manifests.
- R8. Run the FD check against the **filtered** rows. `check_fds.py`
  reads `data_set/unified/metadata.csv` (`check_fds.py:15`), not the
  catalog, so either regenerate that file after filtering or point the
  check at the filtered frame. Doing neither checks the wrong rows and
  passes for the wrong reason.
- R9. If R4 or R5 fails, the stage writes `status: failed`, stops, and
  writes **no** manifests.
- R10. Manifests follow the shared schema:
  `image_id, md5, label_id, source_id, phash_group, split`.
- R11. Write the manifests to `configs/splits/` and **commit them**
  (Decision 16). They are the only authority on split membership;
  `Image.split` and the `train/val/test/` path prefixes are Phase 1
  leftovers and are ignored from here on.
- R12. Recompute the per-class test counts and noise bands
  (`100 × sqrt(0.9 × 0.1 / n)`) into `split_stats.csv`. Stage 5 reads
  its class-drop thresholds from this file.
- R13. Train the source classifier only on classes with two or more
  sources, using train/validation data. Set `shortcut_detected` when
  accuracy beats the majority-source rate by more than 10 points.
- R14. If the trigger fires, notify Stages 4–6: per-source reporting and
  the Hand-Drawn leave-one-source-out experiment become mandatory.

**Should**
- Stratify by class and source; report each source's share of the test
  set (pentagon is El Korchi-only, ellipse is Hand-Drawn-only).
- **Do not expect 12,761 / 2,890 / 2,849.** Those are Phase 1 numbers
  from before the gemstone filter and before global pHash grouping.
  Both changes move them. Publish what you get and hand Stage 6 the
  note; forcing the old numbers would mean breaking a group or skipping
  the filter.

## Deliverables (`artifacts/stage1/`)

- `split_stats.csv` — per class × source × split counts, plus the
  per-class test `n` and noise band Stage 5 needs
- `source_classifier.json` — accuracy, majority-source baseline,
  `shortcut_detected` and the classes/sources evaluated
- `status.json` — counts, `gemstones_removed`, check results

Plus, outside `artifacts/` because they are committed:

- `configs/splits/{train,val,test}.csv` — the frozen manifests

## Done when

- [ ] Leakage assertions pass (R4, R5).
- [ ] Every row of `configs/gemstone_ids.csv` matched exactly one image
      by md5, and the removed count is recorded.
- [ ] The new counts are published and handed to Stage 6 for the
      report's **Split** paragraph (`phase1_report.tex:466–467`) — that
      is where split sizes live, not in `tab:stats`, which holds
      per-source file counts.
- [ ] Seed and catalog hash are recorded in `status.json → inputs`.
- [ ] The manifests are committed to `configs/splits/` in a PR.
- [ ] Manifest contract tests pass (`tests/contracts/`).
- [ ] Source-classifier result and `shortcut_detected` are written down,
      and downstream owners have been notified if the trigger fired.

## Interfaces you provide

- The three manifests above, read by others **only** through
  `common.load_split(name)`. You never hand the test manifest to anyone
  directly; Stage 5 is the only allowed reader.

## Pitfalls

- **Splitting by image instead of by group** — near-duplicates end up in
  train *and* test, and test accuracy becomes a memory test.
- **Grouping within a source only** — this is the Phase 1 bug
  (`build_unified_dataset.py:162`). Four sources drawing the same ten
  shapes produce cross-source near-duplicates, and grouping per source
  lets them straddle train and test.
- **Keying the exclusion list on `image_id`** — the id is positional
  (`f"{source}_{label}_{i:06d}"`), so one rebuild renumbers everything
  after the first removed image and the list silently drops the wrong
  drawings. Match on md5.
- **Filtering after the split** — changes the test set and breaks the
  freeze.
- **Unseeded randomness** — a rerun produces a different test set.
- **The 175-pentagon group** — one group that large can push the
  pentagon split ratio far from 70/15/15; report it, don't break the group.

## Glossary

- **Data freeze**: the moment the splits become read-only for the rest
  of the project. Example: after Stage 1 passes, changing
  `filter_gemstones` would rerun every stage.
- **Manifest**: a CSV listing which images belong to a split.
  Example: `img_00042, 3, 2, g0117, train`.
- **Perceptual hash (pHash)**: a short fingerprint that stays the same
  when an image barely changes. Example: two El Korchi pentagons that
  differ only in colour get the same pHash after standardisation.
- **Near-duplicate group**: all images whose pHashes are close enough to
  count as "the same picture". Example: group `g0117` holds 175 pentagons.
- **Group split**: a split where a whole group goes to one side.
  Example: all 175 pentagons of `g0117` go to train, none to test.
- **Stratification**: keeping class proportions roughly equal across
  splits. Example: if 10% of all images are stars, ~10% of test is stars.
- **Leakage**: information from the test set reaching training.
  Example: a near-duplicate of a test image sitting in train.
- **Shortcut (source leakage)**: a feature that reveals the source and,
  through it, the class. Example: if El Korchi images are recognisable,
  "El Korchi-looking" means "pentagon" for free.

## Missions

### M1 Spot the leak (recognition)
Prompt: which rows break a Stage 1 requirement, and which requirement?

```
image_id,md5,label_id,source_id,phash_group,split
img_001,a1b2,5,2,g010,train
img_002,c3d4,5,2,g010,test
img_003,e5f6,0,4,g011,val
img_003,e5f6,0,4,g011,train
img_004,a1b2,9,1,g012,test
img_005,0a9f,3,3,g013,val
```
Expected outcome: `img_001`/`img_002` share group `g010` across train and
test (R4). `img_003` is in val and train (R5). `img_004` carries the same
md5 as `img_001` — the same picture under two ids, which R5 also catches
and which exact-duplicate removal should have caught earlier. `img_005`
is fine.

### M2 Group-aware stratified split (application)
Prompt: produce a 70/15/15 split where groups never cross splits and
classes stay balanced.

```python
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

df = pd.read_csv("catalog_rows.csv")   # image_id, md5, label_id, source_id, phash_group
sgkf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=SEED)
folds = [test_idx for _, test_idx in sgkf.split(df, df.label_id, df.phash_group)]
# TODO: folds 0-2 -> test (15%), folds 3-5 -> val (15%), rest -> train (70%)
```
Expected outcome: three DataFrames with roughly 70/15/15 of the rows,
`df.groupby("phash_group").split.nunique().max() == 1`, and the same
output on a second run with the same `SEED`.

### M3 Fail-closed freeze (synthesis)
Prompt: combine the filter, the split, the assertions and the status
file into one `run()` that fails the stage on leakage.

```python
def run(cfg):
    df = load_catalog_with_metadata()     # catalog + metadata.csv + md5 pass
    df, removed = filter_gemstones(df) if cfg["filter_gemstones"] else (df, 0)
    df["phash_group"] = group_globally(df.phash)   # Decision 15, all sources
    splits = group_split(df, cfg["split"], cfg["seed"])
    checks = {
        "no_id_in_two_splits": ...,     # TODO
        "no_md5_in_two_splits": ...,    # TODO
        "no_phash_group_spans": ...,    # TODO
    }
    write_status("stage1", status="passed" if all(checks.values()) else "failed",
                 metrics={**counts(splits), "gemstones_removed": removed},
                 checks=checks)
```
Expected outcome: on clean data `artifacts/stage1/status.json` says
`passed` with the three counts and `split_stats.csv` carries the
per-class noise bands. Copy one test image into train by hand and
rerun — it must say `failed` and write no manifests at all.

When you finish M3, run `quiz-topic` on "Stage 1 data freeze" to check
the concepts stuck.
````

### `20_s1_md5_gemstones.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E20 evidence line

# Plan 20: S1 md5 pass, gemstone filter, contact sheet

**Stage:** `stages/stage_1.md` R1, R2, Done-when D2 · **Plan refs:** `implementation.md` Decision 1; § Shared conventions (md5 column)
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E20) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`image_id` is positional; exclusions must key on `md5`. Gemstone diamonds must be filtered before the split, from a human-reviewed list.

## 2. Root Cause & Investigation
Catalog `Image` has no content hash; no `configs/gemstone_ids.csv`.

## 3. Architecture & Modular Design Strategy
Pure: `apply_gemstone_filter(rows, exclusions) -> (rows, removed)` raising `GemstoneMatchError` when any listed md5 matches 0 or >1 images. I/O: `load_unified(config)` reads catalog (read-only) + metadata.csv + PNGs and computes md5 of the standardized array. `contact_sheet.py` renders all Quick, Draw! diamonds with `image_id` + md5 prefix (paginated) and writes an empty `configs/gemstone_ids.csv` template only if absent. The agent never classifies gemstones.

## 4. Proposed Changes by File
- `src/stage1_freeze/identity.py`, `gemstones.py`, `contact_sheet.py`.
- `tests/stage1/test_gemstones.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_removes_exact_md5_matches`, `::test_zero_match_fails`, `::test_duplicate_match_fails`, `::test_empty_list_removes_nothing`.
- **Figure review**: open each contact-sheet page with `Read`.
- **Break verification**: drop the `> 1` check → `test_duplicate_match_fails` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Until the human list exists `filter_gemstones: false` (dry run); status records `gemstone_filter: dry_run`.
````

### `21_s1_group_split.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E21 evidence line

# Plan 21: S1 global pHash groups, group split, leakage asserts, manifests

**Stage:** `stages/stage_1.md` R3–R7, R9–R11, Should 1, Done-when D1, D4–D6, Missions M1–M3 · **Plan refs:** `implementation.md` Decisions 15, 16
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E21) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Phase 1 grouped near-duplicates per (source, label) (`build_unified_dataset.py:162`), so cross-source near-duplicates could straddle splits.

## 2. Root Cause & Investigation
Stage 1 must recompute globally and write `configs/splits/*.csv`.

## 3. Architecture & Modular Design Strategy
Pure: `global_groups(phashes, max_hamming)`, `group_split(rows, ratios, seed)` — greedy largest-group-first assignment, per class, to the split furthest below its target, ties broken by source share (Should 1), deterministic for a seed; `leakage_checks(manifests)`. `run(config)` composes E20 → groups → split → checks; on any failed check returns `status: failed` and writes **no** manifests; otherwise writes the three CSVs (schema R10).

## 4. Proposed Changes by File
- `src/stage1_freeze/splitting.py`, `leakage.py`, `run.py`.
- `tests/stage1/test_splitting.py`, `tests/stage1/test_leakage.py`, `tests/contracts/test_manifests.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_leakage.py::test_mission_m1_rows_flagged`, `::test_injected_leak_writes_no_manifests` (M3); `test_splitting.py::test_groups_never_span`, `::test_ratios_close_to_target`, `::test_deterministic_for_seed`, `::test_large_group_kept_whole`; `test_manifests.py::test_schema_and_no_overlap_train_val`.
- **Pipeline**: `python run_pipeline.py --stages 1` → three manifests + `status: passed`.
- **Break verification**: assign rows by image instead of by group → `test_groups_never_span` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- The manifest contract test never reads the test split; test-manifest overlap is asserted inside Stage 1 and recorded in its status checks.
- Commit of `configs/splits/` is the user's step (no git).
````

### `22_s1_split_stats_fd.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E22 evidence line

# Plan 22: S1 split stats, noise bands, FD check on filtered rows

**Stage:** `stages/stage_1.md` R8, R12, Should 2, Done-when D3 · **Plan refs:** `implementation.md` Decision 10 (noise band); § Stage 1
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E22) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Stage 5 reads class-drop thresholds from `split_stats.csv`; the FD check must run on the post-filter rows.

## 2. Root Cause & Investigation
`check_fds.py:15` reads `metadata.csv` directly.

## 3. Architecture & Modular Design Strategy
Pure: `split_stats(rows)` (class × source × split counts) and `noise_band(n) = 100*sqrt(0.9*0.1/n)`; `check_fds.check_fd` called on the filtered rows. Writes `artifacts/stage1/split_stats.csv`, `noise_bands.csv`, `fd_check.json`, `stage6_note.md`.

## 4. Proposed Changes by File
- `src/stage1_freeze/stats.py`; `check_fds.py` gains `check_rows(rows)`.
- `tests/stage1/test_stats.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_noise_band_matches_decision_10_table`, `::test_counts_sum_to_rows`, `::test_fd_check_uses_filtered_rows`.
- **Break verification**: compute the band from total n → table test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Store full precision, round only in display.
````

### `23_s1_source_classifier.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E23 evidence line

# Plan 23: S1 source-classifier shortcut check

**Stage:** `stages/stage_1.md` R13, R14, Done-when D7 · **Plan refs:** `implementation.md` Decision 12
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E23) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
If source is predictable from standardized pixels, per-source reporting and a Hand-Drawn LOSO run become mandatory.

## 2. Root Cause & Investigation
No check exists.

## 3. Architecture & Modular Design Strategy
Pure: `shortcut_check(X_train, y_train, s_train, X_val, y_val, s_val, trigger_points)` → per class with ≥ 2 sources, logistic regression on downsampled pixels fit on train, scored on val; overall accuracy vs majority-source rate; `shortcut_detected` if it beats majority by > trigger. Writes `source_classifier.json` and, if fired, `NOTICE_shortcut.md` for Stages 4–6.

## 4. Proposed Changes by File
- `src/stage1_freeze/source_check.py`.
- `tests/stage1/test_source_check.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_detects_planted_source_signal`, `::test_no_signal_not_detected`, `::test_single_source_classes_skipped`.
- **Break verification**: compare against 0 instead of the majority rate → `test_no_signal_not_detected` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Majority-source rate is the baseline, not 50 %.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each plan's status line records 'verified in tree', with an evidence line in ignore/todo.md (E20 to E23).

## Our decision

MD5 identity with a committed gemstone ID list, the global pHash group split, split stats with FD checks, and a source classifier to measure the source shortcut.

## Measured effect

No model yet. The source classifier later fed F05 (the images reveal their source).
