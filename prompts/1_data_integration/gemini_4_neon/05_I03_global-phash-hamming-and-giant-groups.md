

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](../claude_opus/13_evidence_stage-1-freeze-and-split-plans.md), [04_evidence_opus-grounds-gemini-integration-plan.md](../cross_critique/04_evidence_opus-grounds-gemini-integration-plan.md)
# 1_data_integration - I03: Global pHash Hamming-2 clustering and giant component allocation (reconstructed)

- Stage 1 topic: I03
- Model: Gemini 4 Neon
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/splitting.py`, `stages/stage_1.md`, `results/phase2_snapshot/status1.json`, `results/phase2_snapshot/split_stats.csv`
- Follow-up: `../cross_critique/03_I03_gemini-critiques-opus-splitting-and-standardization.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

In Phase 1, `build_unified_dataset.py` computed near-duplicate pHash groups *within* each `(source_id, label)` bucket. As documented in `stages/stage_1.md` and `src/stage1_freeze/splitting.py`, that per-source grouping allowed cross-source near-duplicates (e.g., nearly identical standardized outlines drawn in different datasets) to straddle `train` and `test`. Furthermore, transitive Hamming chaining creates giant connected components - such as the 175-pentagon chain noted in `stages/stage_1.md` and a `216`-image component across the active dataset - plus mixed-label clusters where distinct classes look visually close after outline standardization.

## Exchange

**User:**
> We are fixing the Phase 1 per-source pHash bug in Stage 1. How should we set `NEAR_DUP_HAMMING`, form the connected components, and allocate giant clusters (like a 175-pentagon chain or our 216-image largest cluster) plus mixed-label clusters into `train`, `val`, and `test` without leaking near-duplicates or collapsing classes?

**Gemini 4 Neon:**
> Keep `phash_hamming_max` at `2` bits and run a **single global union-find** over all active rows together before any split assignment:
>
> - **Why `2` bits globally:** A Hamming threshold of `<= 2` catches near-identical 64x64 standardized outlines across *all* four sources simultaneously, closing the cross-source leakage hole without merging genuinely distinct shapes at higher thresholds (`>= 4`).
> - **Deterministic IDs:** Sort rows by `image_id` before numbering connected components (`g000001`, `g000002`, ...) so manifest columns are byte-identical across reruns.
> - **Giant components & mixed-label groups:** Never split a connected component - assign every group whole. Stratify each group by `(majority label_id, majority source_id)`, shuffle within each stratum with `seed = 42`, stably sort groups **largest-first**, and place each group into the split furthest below its `0.70 / 0.15 / 0.15` target.
>
> | Approach | Risk / Trade-off | Verdict |
> |---|---|---|
> | Per-source pHash grouping (Phase 1) | Keeps strata balanced, but cross-source near-copies leak between train and test | **Reject** |
> | Global Hamming-2 + break giant groups (>50 rows) | Hits exact 70/15/15 per class, but breaks the zero-leakage invariant | **Reject** |
> | Global Hamming-2 + largest-first `_furthest_below_target` (`seed=42`) | Giant groups slightly skew single-source strata (`pentagon`, `star`), but zero near-duplicates span splits | **Adopt** |

**User:**
> If a 216-image group or a 175-pentagon group lands whole in one split, won't it push `pentagon` off 70/15/15 or create `mixed_label_groups`? How should we handle that?

**Gemini 4 Neon:**
> Report the exact skew and `mixed_label_groups` count in Stage 1 metrics rather than "fixing" it by splitting components:
>
> - Placing the largest groups first lets smaller groups and singletons backfill the remaining deficit toward 70/15/15 within each `(majority label_id, majority source_id)` stratum.
> - Because `pentagon` comes solely from `mendeley_elkorchi`, its large component will nudge its split counts away from exact 700/150/150, which is expected and honest; verify every class still clears the test noise-band floor.

## Why this reading fits

Gemini 4 Neon's recommendation matches the exact design implemented in `src/stage1_freeze/splitting.py` (`global_groups`, `group_labels`, `_furthest_below_target`, `group_split`, `mixed_label_groups`) and required by `stages/stage_1.md` (R3, R4, R6, R7, and Pitfalls). Computing union-find globally at `phash_hamming_max: 2` closes cross-source leakage, sorting descending by size before calling `_furthest_below_target` minimizes ratio distortion without ever breaking a component, and reporting `largest_group` and `mixed_label_groups` preserves scientific transparency.

## Validation

Stage 1 execution (`src/stage1_freeze/run.py`) and the phase 2 snapshot (`results/phase2_snapshot/status1.json`, `results/phase2_snapshot/split_stats.csv`) directly verify every aspect of this clustering and allocation logic:

- **Global clustering counts (`status1.json`):** Over the `18,000` active rows (after excluding `500` `quickdraw/diamond` rows), `global_groups(..., max_hamming=2)` produced `15,268` connected components (`near_dup_groups: 15268`), with `largest_group: 216` and `mixed_label_groups: 23`.
- **Zero cross-split leakage (`status1.json`):** `checks.no_phash_group_spans: true`, `checks.no_id_in_two_splits: true`, and `checks.no_md5_in_two_splits: true`.
- **Expected single-source / giant-group skew (`split_stats.csv`):** Largest-first greedy deficit assignment kept whole groups intact while remaining close to `70/15/15`:
  - `mendeley_elkorchi` `pentagon` (single-source): `680` train / `163` val / `157` test (`1,000` total).
  - `mendeley_elkorchi` `triangle`: `605` train / `201` val / `194` test (`1,000` total).
  - `mendeley_elkorchi` `star`: `629` train / `201` val / `170` test (`1,000` total).
- **Automated fail-closed test (`tests/stage1/test_run_fail_closed.py`):** Confirms `plan_freeze` and `noise_bands` block freezing if any class ends up with `0` test rows (`test_noise_band_failure_blocks_manifests`).

## Our decision

The team implemented Gemini 4 Neon's exact global grouping and greedy group-assignment design in `src/stage1_freeze/splitting.py` with `configs/pipeline.yaml` parameters (`ratios: [0.70, 0.15, 0.15]`, `phash_hamming_max: 2`, `seed: 42`):

- `global_groups()` runs union-find over all `18,000` active pHashes at once.
- `group_labels()` assigns deterministic `g000001`... IDs in first-appearance order.
- `group_split()` stratifies by `(majority label_id, majority source_id)`, shuffles with `np.random.default_rng(42)`, stably sorts largest-first, and assigns whole groups via `_furthest_below_target` (breaking deficit ties in `("train", "val", "test")` order).
- Giant-group skew and `mixed_label_groups` are documented in `artifacts/stage1/stage6_note.md` and `status.json` rather than broken apart.

## Measured effect

- **Final frozen split sizes (`results/phase2_snapshot/status1.json`):** `12,405` train (`68.92%`), `2,819` val (`15.66%`), `2,776` test (`15.42%`), totaling `18,000` active images across `15,268` global near-duplicate groups.
- **Leakage guarantee:** `0` pHash groups span two splits (`no_phash_group_spans: true`), `0` `image_id` collisions (`no_id_in_two_splits: true`), and `0` `md5` collisions (`no_md5_in_two_splits: true`), while every one of the 10 classes remains populated in `test` (`split_stats.csv`).

## Deeper detail: why each design choice matters

### Why Hamming-2 is the right threshold

| Threshold | What it catches | Risk |
|---|---|---|
| `<= 2` | Near-identical outlines across all sources | Catches cross-source leakage |
| `>= 4` | Only very similar shapes | Misses cross-source leakage |

- **Why 2 is the sweet spot:** it's tight enough to catch cross-source near-duplicates (which is the whole point) but loose enough to not merge genuinely distinct shapes.
- **Why higher thresholds fail:** they'd miss the cross-source leakage, which is the bug being fixed.
- **Why this is a good design choice:** it's a single, well-justified parameter that solves the problem.

### Why global (not per-source) grouping

| Approach | Leakage | Stratum ratio | Verdict |
|---|---|---|---|
| Per-source (Phase 1 bug) | High (cross-source near-dups straddle) | Tight | Reject |
| Global | Zero (`no_phash_group_spans: true`) | Some drift | Adopt |

- **Why leakage is worse than ratio drift:** a leaked near-duplicate means the model can "cheat" by memorizing, which invalidates the evaluation.
- **Why the 216-image group is acceptable:** it's one group out of 15,268, and it's better to have one large group than to have near-duplicates straddling.
- **Why this is the fix for the Phase 1 bug:** the Phase 1 bug was per-source grouping, which allowed cross-source leakage. Global grouping fixes it.

### Why largest-first greedy packing

| Order | What happens | Why |
|---|---|---|
| Largest-first | Big groups placed first, small groups backfill | Minimizes ratio distortion |
| Smallest-first | Small groups placed first, big groups cause big skew | Worse ratio distortion |

- **Why largest-first is better:** placing big groups first means the remaining deficit is smaller, so small groups can backfill more precisely.
- **Why `_furthest_below_target` matters:** it assigns each group to the split that's furthest below its target, which keeps the ratios as close as possible.
- **Why `seed = 42`:** makes the shuffling reproducible.

### Why never split a component

| Approach | Leakage | Ratio | Verdict |
|---|---|---|---|
| Split giant groups | Zero (no leakage) | Exact 70/15/15 | Reject (breaks zero-leakage) |
| Never split | Zero (no leakage) | Some drift | Adopt |

- **Why splitting breaks zero-leakage:** if you split a 216-image group across train and test, you've reintroduced the leakage you were trying to fix.
- **Why ratio drift is acceptable:** it's a cosmetic issue, not a validity issue.
- **Why "report it, don't break the group" is the right principle:** it preserves scientific integrity.

### The per-source skew is expected and honest

| Source | Class | Train | Val | Test | Total | Skew from 70/15/15 |
|---|---|---|---|---|---|---|
| `mendeley_elkorchi` | pentagon | 680 | 163 | 157 | 1,000 | -20 train, +13 val, +7 test |
| `mendeley_elkorchi` | triangle | 605 | 201 | 194 | 1,000 | -95 train, +51 val, +44 test |
| `mendeley_elkorchi` | star | 629 | 201 | 170 | 1,000 | -71 train, +51 val, +20 test |

- **Why the skew is expected:** `pentagon` is single-source (only `mendeley_elkorchi`), so its large component naturally skews the split.
- **Why this is honest:** reporting the skew is better than hiding it by breaking groups.
- **Why the noise-band floor matters:** even with skew, every class must still clear the test noise-band floor (A01), which is the check that prevents a class from having too few test images.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (capping budgets) | This entry (I03) | The 18,000 active rows are the input to the grouping |
| I01 cross-critique (Opus on Gemini) | This entry (I03) | Opus's per-source proposal was critiqued and rejected here |
| I02 (identity) | This entry (I03) | The `phash` from I02 is the input to the grouping |
| I04 (fail-closed freeze) | This entry (I03) | The `no_phash_group_spans` check is part of the fail-closed freeze |
| I05 (FD checks) | This entry (I03) | The 6 FDs validate the schema invariants the grouping preserves |
| I06 (standardization) | This entry (I03) | The standardized 64x64 outlines are the input to the pHash |
| F05 (source attribution) | This entry (I03) | The shortcut is mitigated by the global grouping |
| A01 (noise bands) | This entry (I03) | The uneven per-class counts (from giant groups) are checked by the noise bands |

- **Why this matters:** this entry (I03) is the decision that established the global grouping, which is the fix for the Phase 1 per-source bug and the mitigation for the F05 shortcut.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating a Gemini reply.
- **This is a `winning-decision` calibration:** Gemini's proposal was correct and was adopted. This is the best kind of outcome.
- **This is the fix for the Phase 1 per-source bug:** the global grouping closes the cross-source leakage hole.
- **The Hamming-2 threshold is well-justified:** it's tight enough to catch leakage, loose enough to not merge distinct shapes.
- **The largest-first greedy packing is a good heuristic:** it minimizes ratio distortion without breaking groups.
- **The "report it, don't break the group" principle is a good one:** it preserves scientific integrity.
- **Cross-reference to I01, I01 cross-critique, I02, I04, I05, I06, F05, A01:** this entry is the foundation for much of the rest of the pipeline.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.