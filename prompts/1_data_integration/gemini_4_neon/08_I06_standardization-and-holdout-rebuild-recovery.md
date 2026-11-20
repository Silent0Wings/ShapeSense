

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_standardize-and-merge-sources.md](../claude_opus/10_evidence_standardize-and-merge-sources.md), [04_evidence_opus-grounds-gemini-integration-plan.md](../cross_critique/04_evidence_opus-grounds-gemini-integration-plan.md)
# 1_data_integration - I06: Non-destructive raster standardization and disjoint holdout rebuild recovery (reconstructed)

- Stage 1 topic: I06
- Model: Gemini 4 Neon
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/standardize.py`, `src/stage1_freeze/fresh_holdout_2.py`, `src/stage1_freeze/source_check.py`, `results/phase2_snapshot/shortcut_notice.md`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../cross_critique/03_I03_gemini-critiques-opus-splitting-and-standardization.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

ShapeSense integrates four visually distinct shape sources - `quickdraw` sketches, `kaggle_reevald` renders, `mendeley_elkorchi` filled/colored polygons, and `github_handdrawn` transparent RGBA strokes. Stage 1 needed a standardization pipeline that removes trivial visual giveaways (fill polarity, random background colors, thick vs thin rings, alpha channels) without distorting shape geometry (e.g., never stretching a rectangle into a square), an honest measurement of any remaining source shortcut, and a clean way to build a second disjoint fresh holdout (`fresh_holdout_2`) for CRISP-DM iteration 3 after earlier holdout/test evaluations.

## Exchange

**User:**
> How should we pair Stage 1 image normalization with an honest check for residual source leakage - and if we need a second fresh holdout (`fresh_holdout_2`) after iteration 2, how do we recover and extend the sampling walk without overlapping `catalog`, `test`, or `fresh_holdout`?

**Gemini 4 Neon:**
> Treat standardization, shortcut detection, and holdout recovery as three tightly coupled invariants:
>
> 1. **Geometry-preserving 5-step `standardize.py`:** Convert every image to a lossless `64x64` single-channel `uint8` PNG (black `0` ink on white `255` background), deferring `[0, 1]` float normalization to Stage 4 load time:
>    - Alpha flattening (`_flatten_alpha`) onto white.
>    - Background-distance foreground mask (`_foreground_mask`, `BG_DISTANCE_T = 60.0`, `MIN_CONTRAST = 8.0`).
>    - Outlier gate (`MIN_FG_FRACTION = 0.0015`, `MIN_SHAPE_PX = 12`, `MIN_INK_64 = 20`).
>    - Aspect-preserving square crop + letterbox (`_to_square` with `MARGIN = 0.08`, `_resize_mask` using `BOX`/`BILINEAR` to `TARGET = 64`).
>    - Closed-shape 2-px outline redraw when `core.sum() / region.sum() > FILLED_CORE` (`0.30`).
> 2. **Honest source-shortcut diagnosis (`source_check.py`):** Fit `LogisticRegression(max_iter=1000)` on `16x16` mean-pooled pixels (`POOL_SIDE_PX = 16`) over `train` and score on `val` for all classes with `>= 2` sources (`MIN_SOURCES = 2`). If pooled accuracy beats the majority-source baseline by more than `10` points, emit `shortcut_notice.md` / `NOTICE_shortcut.md` mandating per-source reporting and leave-one-source-out runs in Stages 4-6.
> 3. **Deterministic replay + disjoint extension (`fresh_holdout_2.py`):** Replay the exact `SEED = 20261109` (`PER_GROUP = 300`, `SKIP_SOURCES = ("quickdraw",)`) walk of `fresh_holdout.py`, assert `_csv_hash(first_rows) == sha256_path(splits_dir / "fresh_holdout.csv")` so the first holdout is proven excluded, and then advance from `positions[key]` for `SECOND_PER_GROUP = 300`, dropping any candidate within `phash_hamming_max = 2` of `metadata.csv` (`known`) or prior holdout hashes (`kept`).
>
> | Component | Risk / Trade-off | Verdict |
> |---|---|---|
> | Non-aspect-preserving resize to 64x64 | Stretches rectangles into squares and ellipses into circles | **Reject** |
> | Hiding source-classifier shortcut or skipping `fresh_holdout.csv` hash check | Masks domain confounding or risks reusing iteration 2 holdout images | **Reject** |
> | 5-step aspect-padded `standardize.py` + `source_check.py` notice + verified-replay `fresh_holdout_2.py` | Preserves geometry, forces honest LOSO checks, and guarantees strictly disjoint holdout images | **Adopt** |

**User:**
> Why not normalize directly to `float32` on disk, and what if `fresh_holdout_2.py` encounters an image whose standardized pixels match a catalog image even if its raw path wasn't sampled?

**Gemini 4 Neon:**
> Keep disk files as `uint8` PNGs so images remain lossless, human-inspectable, and compact (Stage 4 uses a 256-entry lookup table at training time). For near-duplicates, `fresh_holdout_2.py` checks `near(known, value, max_hamming) or near(np.array(kept, dtype=np.uint64), value, max_hamming)` *after* `standardize(image)` and computes `md5(arr)` for `fresh2_{digest[:16]}`, so any standardized duplicate or Hamming-2 near-copy from another raw file is still caught and dropped.

## Why this reading fits

Gemini 4 Neon's recommendations align with the verified implementation across `src/stage1_freeze/standardize.py`, `src/stage1_freeze/source_check.py`, `src/stage1_freeze/fresh_holdout_2.py`, and `ShapeSense_Deployed/web/js/content/explain.js`. Geometry-preserving padding protects `circle`/`ellipse` and `square`/`rectangle` boundaries, `source_check.py` cleanly quantifies the remaining pixel-level domain signal without peeking at `test`, and `fresh_holdout_2.py` verifies exact hash reproduction of `fresh_holdout.csv` (`_csv_hash`) before advancing the deterministic cursor.

## Validation

- **Standardization & lossless persistence:** `standardize.py` converts all accepted images to `64x64` `uint8` (`0`/`255`) PNGs and logs rejected outliers (`no_contrast`, `blank_or_near_blank`, `shape_too_small`, `degenerate_after_resize`) to `rejects.csv`.
- **Source-shortcut measurement (`results/phase2_snapshot/source_classifier.json` & `shortcut_notice.md`):** Evaluating `2,356` validation images across the 7 multi-source classes (`ellipse`, `pentagon`, and `diamond` skipped as single-source) measured `pooled_accuracy: 0.917` (`0.91723259762309`) vs `pooled_majority_rate: 0.467` (`0.466893039049236`), a `45.0`-point gain above the `10`-point trigger (`shortcut_detected: true` in `status1.json`).
- **Disjoint holdout verification (`src/stage1_freeze/fresh_holdout_2.py` & `ShapeSense_Deployed/web/js/content/explain.js`):** Replaying `SEED = 20261109` checks `_csv_hash(first_rows) == sha256_path(splits_dir / "fresh_holdout.csv")` (failing loudly with `RuntimeError` on mismatch) before drawing `SECOND_PER_GROUP = 300` images per `(source, label)` group across the 3 non-QuickDraw sources (`4,500` total holdout images across all 10 classes), deduplicated against `known` and `kept` at `phash_hamming_max = 2`.

## Our decision

The team implemented and locked all three components:

1. Kept `src/stage1_freeze/standardize.py` unaltered as the shared 5-step `64x64` `uint8` outline normalizer for real catalog builds, fresh holdouts, and Stage 5 robustness checks.
2. Wired `shortcut_check()` into `src/stage1_freeze/run.py:plan_freeze()`, emitting `NOTICE_shortcut.md` (`results/phase2_snapshot/shortcut_notice.md`) whenever `gain_points > trigger_points`.
3. Implemented `src/stage1_freeze/fresh_holdout_2.py` with `SEED = 20261109`, `_csv_hash` replay verification of `fresh_holdout.csv`, and `SEALED_SPLITS` registration in `src/common/splits.py`.

## Measured effect

- **Mandatory shortcut mitigation triggered:** The `0.917` vs `0.467` (`+45.0` points) source-classifier result formally triggered Decision 12 / `stage_1.md` R14, requiring per-source accuracy tables in Stage 5, `github_handdrawn` leave-one-source-out runs for arms A1 and B, and single-source asterisks for `ellipse`, `pentagon`, and `diamond`.
- **Clean iteration 3 evaluation set:** `fresh_holdout_2.csv` provides `4,500` sealed, standardized `64x64` images across all 10 classes (`300` per `(source, label)` group, skipping `quickdraw`), strictly disjoint by `md5` and Hamming-2 `phash` from the `18,000`-image frozen catalog and `fresh_holdout.csv`.

## Deeper detail: why each design choice matters

### The 5-step standardization is geometry-preserving

| Step | What it does | Why it matters |
|---|---|---|
| 1. Alpha flattening | Composites RGBA onto white | Handles transparent backgrounds |
| 2. Foreground mask | Adaptive background distance | Separates shape from background |
| 3. Outlier gate | Rejects blank/tiny/degenerate | Ensures only valid shapes survive |
| 4. Aspect-preserving crop + letterbox | Crops to square, pads to 64x64 | Preserves geometry (no stretching) |
| 5. Closed-shape outline redraw | Redraws closed shapes to 2-px outline | Normalizes fill without destroying open strokes |

- **Why aspect-preserving matters:** a non-aspect-preserving resize would stretch rectangles into squares and ellipses into circles, which breaks the geometric definitions from S07.
- **Why closed-shape-only redraw matters:** it normalizes fill for closed shapes (which have a clear interior) without destroying open/dashed strokes (which are the interesting part of sketches).
- **Why `uint8` on disk:** lossless, human-inspectable, and compact. Float normalization is deferred to Stage 4 load time.

### The shortcut check is honest

| Metric | Value | Why it matters |
|---|---|---|
| Pooled accuracy | 0.917 | High, meaning the shortcut is real |
| Majority baseline | 0.467 | The "do nothing" baseline |
| Gain | 45.0 points | Far above the 10-point trigger |
| Trigger | 10 points | The threshold for `shortcut_detected: true` |

- **Why 0.917 vs 0.467 matters:** it means a simple classifier can tell which source an image came from with high confidence, which is a real shortcut.
- **Why the 10-point trigger:** it's a reasonable threshold for "this is a real problem, not noise".
- **Why `shortcut_notice.md`:** it formally documents the shortcut and triggers mandatory Stage 4/5 per-source reporting and LOSO runs.

### The fresh holdout replay is deterministic

| Step | What it does | Why it matters |
|---|---|---|
| 1. Replay `SEED = 20261109` | Replays the exact walk of `fresh_holdout.py` | Ensures the first holdout is reproducible |
| 2. Assert `_csv_hash(first_rows) == sha256_path(...)` | Verifies the first holdout hash | Proves the first holdout is excluded |
| 3. Advance from `positions[key]` | Continues from where the first holdout stopped | Ensures no overlap |
| 4. Drop near-duplicates (`phash_hamming_max = 2`) | Checks against `known` (catalog) and `kept` (prior holdouts) | Ensures the holdout is disjoint |

- **Why the hash check matters:** it proves the first holdout is exactly what was intended, which is critical for reproducibility.
- **Why the near-duplicate check matters:** it ensures the holdout is truly disjoint from the catalog and prior holdouts.
- **Why `md5(arr)` for `fresh2_{digest[:16]}`:** it catches standardized duplicates even if the raw path wasn't sampled.

### Why `uint8` not `float32` on disk

| Format | Pros | Cons | Verdict |
|---|---|---|---|
| `uint8` PNG | Lossless, human-inspectable, compact | Needs conversion at load time | Adopt |
| `float32` on disk | No conversion needed | Larger, not human-inspectable | Reject |

- **Why `uint8` is better:** it's lossless, human-inspectable, and compact. Stage 4 uses a 256-entry lookup table at training time, which is fast.
- **Why `float32` is worse:** it's larger and not human-inspectable, and the conversion at load time is cheap.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | This entry (I06) | The 18,000 active rows are the input to standardization |
| I02 (identity) | This entry (I06) | The `md5`/`phash` come from the standardized PNGs |
| I03 (global grouping) | This entry (I06) | The `phash` from standardization is the input to the grouping |
| I04 (fail-closed freeze) | This entry (I06) | The standardized PNGs are the input to the freeze |
| I05 (FD checks) | This entry (I06) | The 6 FDs validate the schema invariants standardization preserves |
| F05 (source attribution) | This entry (I06) | The shortcut is measured by `source_check.py` |
| C02 (fresh holdout) | This entry (I06) | The first holdout is replayed and extended by `fresh_holdout_2` |
| C24 (second fresh holdout) | This entry (I06) | The second holdout is built by `fresh_holdout_2` |

- **Why this matters:** this entry (I06) is the decision that established the 5-step standardization, the shortcut check, and the fresh holdout replay, which are the foundation for much of the rest of the pipeline.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating a Gemini reply.
- **This is a `winning-decision` calibration:** Gemini's proposal was correct and was adopted. This is the best kind of outcome.
- **The 5-step standardization is geometry-preserving:** it doesn't stretch rectangles into squares or ellipses into circles.
- **The shortcut check is honest:** it measures the shortcut rather than hiding it.
- **The fresh holdout replay is deterministic:** it ensures the holdout is reproducible and disjoint.
- **Cross-reference to I01, I02, I03, I04, I05, F05, C02, C24:** this entry is the foundation for much of the rest of the pipeline.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.