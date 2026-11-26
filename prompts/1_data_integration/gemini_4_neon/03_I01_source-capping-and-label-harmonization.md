

>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_standardize-and-merge-sources.md](../claude_opus/10_evidence_standardize-and-merge-sources.md), [09_evidence_integration-cases-draft.md](09_evidence_integration-cases-draft.md)
# 1_data_integration - I01: Source capping budgets and candidate headroom across 196k raw files 

- Stage 1 topic: I01
- Model: Gemini 4 Neon
- Calibration: `close-to-reality`
- Grounding sources: `src/stage1_freeze/build_unified_dataset.py`, `configs/pipeline.yaml`, `results/phase2_snapshot/status1.json`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../cross_critique/02_I01_opus-critiques-gemini-storage-and-capping.md`

## Context

Across the installed source archives under `data_set/`, `ShapeSense_Deployed/web/js/content/explain.js` records `196,353` raw archive files spanning heterogeneous formats (`.ndjson` strokes in `quickdraw`, `.jpg` renders in `kaggle_reevald`, `.png` renders in `mendeley_elkorchi`, and RGBA sketches in `github_handdrawn`). Before Stage 1 can freeze splits, `src/stage1_freeze/build_unified_dataset.py` has to harmonize source labels into the 10-class taxonomy (`src/stage1_freeze/taxonomy.py`), reject corrupt or degenerate inputs, deduplicate exact pixel hashes, and bound each `(source_id, label)` bucket so no single source dominates a shape class.

## Exchange

**User:**
> We have 196,353 raw files across our shape datasets before standardization and deduplication. When building `data_set/unified/`, how many images per `(source, label)` group should we sample and keep in Stage 1?

**Gemini 4 Neon:**
> You should choose between two clean extremes rather than adding multi-stage sampling parameters:
>
> - **Option A (Full ingest + loss weighting):** Standardize and ingest all 196,353 raw files into the unified dataset, then balance training with inverse class-frequency weights in the cross-entropy loss.
> - **Option B (Direct hard cap at 500):** Shuffle each `(source, label)` group once and stop reading immediately at 500 raw items per group - no separate pre-filter candidate budget needed.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Full ingest (196,353 files) + inverse loss weights | Maximizes data volume, but standardization and MD5/pHash passes scale to the full archive and class-source imbalance persists in pixel space | Viable if storage/CPU budget is unconstrained |
> | Direct hard cap at 500 raw items per group | Fast, deterministic, and caps every `(source, label)` bucket to at most 500 items | **Preferred** for fast iteration and tight disk footprint |
> | Two-stage candidate pool + keep cap | Extra magic constant to tune (`candidates` vs `kept`) with little benefit if raw sources are mostly clean | Over-engineered for a 10-class dataset |

**User:**
> Wait - if we hard-cap at 500 raw items *before* standardization and exact-MD5 deduplication, won't `Rejected` outliers and exact pixel duplicates shrink some `(source, label)` buckets well below 500? And if `quickdraw` or `mendeley_elkorchi` has thousands of valid shapes, isn't 500 throwing away useful multi-source diversity?

**Gemini 4 Neon:**
> Good catch on outlier attrition, though in practice:
>
> - Standardizing all 196,353 files would still be wasteful when `kaggle_reevald` and `mendeley_elkorchi` already repeat many identical renders.
> - If you worry about attrition, keep the single-pass `500` cap and simply accept slightly smaller counts (e.g., 460-490) for noisier sketch sources, or bump the single loop cap to 600 without introducing a separate candidate ceiling.

## Why this reading fits

This is a representative `close-to-reality` engineering exchange: Gemini 4 Neon correctly identifies the tension between ingesting all `196,353` raw files and bounding per-source dominance, and it spots the CPU/storage cost of standardizing the entire archive. However, it misses the operational reality inside `src/stage1_freeze/build_unified_dataset.py`: standardization (`standardize()`) raises `Rejected` on blank, low-contrast, tiny, or degenerate shapes (`rejects.csv`), and standardized 64x64 renders can collide on `md5` (`exact_dups`). Cutting off raw iteration at 500 - or conflating the candidate pre-filter limit with the final retention cap - either under-fills noisy buckets or abandons clean headroom needed to reach a balanced `1,000`-image ceiling per `(source, label)` group.

## Validation

The team tested the Stage 1 build pipeline (`src/stage1_freeze/build_unified_dataset.py` followed by `src/stage1_freeze/run.py`) against the installed raw datasets and verified the resulting counts and integrity gates in `results/phase2_snapshot/status1.json` and `ShapeSense_Deployed/web/js/content/explain.js`:

- **Label harmonization & source exclusions:** `SOURCES` and `LABEL_MAP` in `build_unified_dataset.py` map the four licensed sources (`quickdraw`, `kaggle_reevald`, `mendeley_elkorchi`, `github_handdrawn`) into the 10 taxonomy classes (`TAXONOMY`), dropping out-of-taxonomy labels (`kite`, `trapezoid`, `parallelogram`, `Heptagon`, `Nonagon`, `other`) and excluding `kaggle_dinesh` whose license is `"Unknown"`.
- **Attrition before capping:** During `build()`, candidate items undergo `standardize(im)` (which logs failures to `rejects.csv`) and cross-source exact pixel deduplication (`seen_md5`), meaning raw file count does not equal kept count.
- **Downstream iteration 1 adjustment:** Even with clean deduplication, `configs/pipeline.yaml` later excludes `[[quickdraw, diamond]]` via `exclude_source_labels` before splitting (`500` drawings removed in `status1.json`), confirming that each `(source, label)` budget needed enough initial sample size (`1,000` kept where available) so downstream rule exclusions and per-class test noise bands (`noise_bands.csv`) remain well-powered.

## Our decision

The team rejected both full 196k ingestion and a single-pass 500 hard cap, adopting a **two-stage capping budget** in `src/stage1_freeze/build_unified_dataset.py` (`SEED = 42`):

1. **Candidate headroom (`CANDIDATES_PER_GROUP = 1500`):** Shuffle each `(source, label)` list deterministically with `random.Random(SEED)` and inspect at most `items[:CANDIDATES_PER_GROUP]`. This bounds CPU work over the `196,353` raw files while providing a 50% buffer for `Rejected` images and `seen_md5` exact duplicates.
2. **Retention cap (`MAX_PER_GROUP = 1000`):** Stop the inner loop once `n_kept >= MAX_PER_GROUP`, preventing abundant sources from overwhelming rarer ones while retaining full 1,000-image density per `(source, label)` group where clean images exist.
3. **Pre-split exclusion (`configs/pipeline.yaml`):** Apply `exclude_source_labels: [[quickdraw, diamond]]` in `src/stage1_freeze/run.py` (`apply_source_label_exclusions`) prior to near-duplicate grouping and freezing.

## Measured effect

- **Unified catalog built:** `18,500` harmonized, deduplicated 64x64 uint8 rows written to `data_set/unified/` (`metadata.csv` and `catalog.sqlite`, documented in `ShapeSense_Deployed/web/js/content/explain.js`).
- **Active frozen split:** After `excluded_by_rule: {"quickdraw/diamond": 500}`, `results/phase2_snapshot/status1.json` records `18,000` active images split into `12,405` train, `2,819` validation, and `2,776` test (`status: "passed"`), with all leakage checks (`no_id_in_two_splits`, `no_md5_in_two_splits`, `no_phash_group_spans`) and all 6 functional dependencies (`fd_all_hold: true`) verified.

## Deeper detail: why each option fails or succeeds

### Option A: Full ingest + loss weighting

| Aspect | Assessment |
|---|---|
| Data volume | Maximizes (all 196,353 files) |
| CPU/storage cost | High (standardize + MD5/pHash on everything) |
| Class-source imbalance | Persists in pixel space (loss weighting helps but doesn't fix) |
| Verdict | Viable if unconstrained, but wasteful |

- **Why it's wasteful:** `kaggle_reevald` and `mendeley_elkorchi` already repeat many identical renders, so standardizing all of them is redundant work.
- **Why loss weighting doesn't fully fix imbalance:** it helps at training time but doesn't fix the underlying pixel-space imbalance, which is what the source classifier (F05) picks up on.

### Option B: Direct hard cap at 500

| Aspect | Assessment |
|---|---|
| Data volume | Capped at 500 per group (too low) |
| CPU/storage cost | Low (only 500 per group processed) |
| Attrition risk | High (Rejected + duplicates shrink below 500) |
| Verdict | Rejected (starves groups) |

- **Why it starves groups:** after `standardize()` rejects outliers and `seen_md5` removes duplicates, you might have far fewer than 500 clean images per group.
- **Why this matters for the noise band:** smaller `n` means wider noise bands (`100 * sqrt(0.9 * 0.1 / n)`), which means less statistical power.
- **Why Gemini's "accept 460-490" suggestion is insufficient:** it doesn't account for the fact that some groups might shrink much more than others, creating new imbalance.

### Two-stage cap: the right design

| Stage | What happens | Why |
|---|---|---|
| 1. Draw candidates | Up to 1500 per `(source, label)` group, `SEED = 42` | Gives 50% headroom for filtering |
| 2. Filter | `standardize()` rejects outliers; `seen_md5` dedup removes exact duplicates | Ensures only clean, unique images survive |
| 3. Cap | Stop at 1000 per group | Prevents source dominance |

- **Why 1500 candidates:** 1500 - 1000 = 500 spare per group, which is a 50% buffer for attrition.
- **Why this is better than 500-cap:** it guarantees enough clean images to reach 1000 per group, even after filtering.
- **Why this is better than full ingest:** it bounds CPU work to 1500 per group (not 196,353 total), which is manageable.
- **Why `SEED = 42`:** makes the sampling reproducible.

### The attrition is real and measurable

- **`standardize()` rejects:** blank, low-contrast, tiny, or degenerate shapes, logged to `rejects.csv`.
- **`seen_md5` dedup:** exact pixel duplicates across sources, which is common for clean renders.
- **Why this matters:** the raw file count (196,353) is not the kept count (18,500). The difference is attrition.
- **Why the 50% buffer matters:** it accounts for this attrition, ensuring enough clean images survive to reach 1000 per group.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 cross-critique (Opus on Gemini) | This entry (I01) | Opus critiqued Gemini's 500-cap proposal, leading to the two-stage cap |
| I02 (identity) | The two-stage cap | The `md5` dedup is part of the filtering stage |
| I03 (global grouping) | The two-stage cap | The cap prevents source dominance, which mitigates the shortcut |
| I04 (fail-closed freeze) | The two-stage cap | The 18,000 active rows are the result of the cap + exclusion |
| I05 (FD checks) | The two-stage cap | The 6 FDs validate the schema invariants the cap preserves |
| I06 (standardization) | The two-stage cap | The `standardize()` rejection is part of the filtering stage |
| F05 (source attribution) | The two-stage cap | The cap mitigates the shortcut by preventing source dominance |
| A01 (noise bands) | The two-stage cap | Even per-class counts (from the cap) mean tighter noise bands |

- **Why this matters:** this entry (I01) is the decision that established the two-stage cap, which is the foundation for much of the rest of the pipeline.

## Notes on the log

- **This is a `close-to-reality` calibration:** Gemini's proposal was close but not quite right. The team correctly overrode it with the two-stage cap.
- **Gemini correctly identified the tension** (full ingest vs cap) but missed the attrition reality.
- **The two-stage cap is the right design:** it balances CPU cost, attrition headroom, and source dominance.
- **The 50% buffer (1500 vs 1000) is a good heuristic:** it accounts for attrition without being wasteful.
- **Cross-reference to I01 cross-critique, I02, I03, I04, I05, I06, F05, A01:** this entry is the foundation for much of the rest of the pipeline.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.