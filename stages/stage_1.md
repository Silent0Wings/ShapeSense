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
