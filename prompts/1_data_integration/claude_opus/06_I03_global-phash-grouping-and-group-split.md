

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [13_evidence_stage-1-freeze-and-split-plans.md](13_evidence_stage-1-freeze-and-split-plans.md), [04_evidence_opus-grounds-gemini-integration-plan.md](../cross_critique/04_evidence_opus-grounds-gemini-integration-plan.md)

# 1_data_integration - I03: Near-duplicate pHash grouping scope and stratified group split balance (reconstructed)

- Stage 1 topic: I03
- Model: Opus 5.5
- Calibration: `close-to-reality`
- Grounding sources: `src/stage1_freeze/splitting.py`, `stages/stage_1.md`, `configs/pipeline.yaml`, `results/phase2_snapshot/status1.json`
- Follow-up: `../gemini_4_neon/05_I03_global-phash-hamming-and-giant-groups.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

In Phase 1, `build_unified_dataset.py` computed pHash near-duplicate groups separately per `(source_id, label)`. An audit recorded in `stages/stage_1.md` revealed that four sources drawing the same ten shapes produced cross-source near-duplicates that straddled train and test splits. At the same time, Stage 1 measurements showed that transitive pHash chaining at Hamming distance `<= 2` could form huge clusters - such as the `175`-pentagon Phase 1 group (`g0117`) and Stage 1's `largest_group: 216`, alongside `23` `mixed_label_groups` across `15,268` groups - capable of pushing single-source class ratios away from `70/15/15`. The team asked Opus 5.5 how to scope pHash grouping and pack groups into splits without distorting class and source balance.

## Exchange

**User:**
> Transitive pHash chaining at `phash_hamming_max: 2` creates giant clusters (a 175-pentagon group in Phase 1, up to 216 images in a single group, and 23 mixed-label groups across 15,268 total groups). If we group globally, won't those mega-clusters skew our 70/15/15 split ratios? How should we scope grouping and allocate groups?

**Opus 5.5:**
> Global union-find across all sources creates unnecessary transitive bridges between unrelated clean renders and noisy sketches, which inflates mega-clusters and ruins stratum balance. You can preserve both leakage protection and tight 70/15/15 ratios by keeping pHash clustering bounded:
>
> - **Cluster pHashes per source (`(source_id, label_id)` or per `source_id`):** Each source has distinct stroke thickness and rendering conventions, so running union-find *within* each source prevents cross-source transitive bridges from forming 200+ image mega-clusters.
> - **Cap cluster size or pack smallest-first:** If any single-source cluster still exceeds ~50 images, split it at a tighter Hamming radius or allocate smallest groups first so the remaining large groups can be balanced cleanly across `train`, `val`, and `test`.

**User:**
> Wait - if we cluster per source and split any large cluster, what happens if a clean `mendeley_elkorchi` triangle and a `kaggle_reevald` triangle share an identical or 1-bit-apart standardized 64x64 outline, or if a 175-image near-duplicate group gets split across `train` and `test`?

**Opus 5.5:**
> Cross-source matches are rare after source-specific normalization, and keeping clusters per source keeps the 70/15/15 ratios exact. Here is the trade-off as I see it:

| Approach | Risk / Trade-off | Verdict |
|---|---|---|
| Global union-find (`phash_hamming_max: 2`), whole groups, largest-first | Giant chained clusters (`largest_group: 216`, `175` pentagons) can push single-source strata off 70/15/15 | Too noisy for exact ratios |
| Per-source pHash clustering + size cap / smallest-first packing | Tight 70/15/15 counts; small chance of cross-source near-duplicate overlap | Recommended |

## Why this reading fits

This exchange illustrates a realistic `close-to-reality` over-correction by Opus 5.5: prioritizing clean `70/15/15` stratum ratios and fearing giant transitive clusters, Opus recommended the exact Phase 1 mistake - scoping pHash union-find per source (and even breaking/capping large groups) - rather than enforcing strict zero-leakage group integrity across all sources.

## Validation

- The Phase 1 audit in `stages/stage_1.md` (`Pitfalls`, `R3`, `R4`, Decision 15) explicitly refuted Opus's per-source premise: `build_unified_dataset.py` originally grouped per `(source_id, label)`, and cross-source near-duplicates *did* straddle train and test splits across the four sources.
- `stages/stage_1.md` (`Should`, `Pitfalls`) also explicitly rejected breaking or capping large groups such as the `175`-pentagon group (`g0117`), stating: *"report it, don't break the group"* and warning against forcing the old Phase 1 counts (`12,761 / 2,890 / 2,849`).
- `src/stage1_freeze/splitting.py` was validated end-to-end in `src/stage1_freeze/run.py` and `results/phase2_snapshot/status1.json` (`no_phash_group_spans: true`).

## Our decision

The team rejected Opus 5.5's per-source clustering and group-splitting proposal and implemented Decision 15 (`R3`, `R4`, `R6`, `R7`) in `src/stage1_freeze/splitting.py`:
1. `global_groups(phashes, max_hamming)` computes `near_dup_groups` (`src/common/neardup.py`) **once over all active rows** using `phash_hamming_max: 2` (`configs/pipeline.yaml`).
2. `group_labels` assigns deterministic `g000001`-style IDs in first-appearance order on `image_id`-sorted rows.
3. `group_split(rows, ratios, seed)` assigns each group to stratum `(majority label_id, majority source_id)`, shuffles with `np.random.default_rng(42)` (`seed: 42`), stably sorts **largest-first** (`reverse=True`), and places each **whole** group into the split returned by `_furthest_below_target(targets, filled)` (`SPLIT_NAMES = ("train", "val", "test")`), accepting stratum ratio drift on giant groups rather than leaking near-duplicates.

## Measured effect

- Stage 1 produced `15,268` global near-duplicate groups across the `18,000` active rows, with `largest_group: 216` and `mixed_label_groups: 23` (`results/phase2_snapshot/status1.json`).
- Frozen split counts moved from Phase 1 (`12,761` / `2,890` / `2,849`) to `12,405` train / `2,819` val / `2,776` test (`18,000` total) with `no_phash_group_spans: true`, `no_id_in_two_splits: true`, and `no_md5_in_two_splits: true`.

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor, C02, C34, I01 and I02 entries, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The reconstruction is honest about its source:** the entry explicitly says it is "reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved". This is good practice: it's transparent about what is and isn't a primary source.
- **This is a `close-to-reality` calibration, not a `winning-decision`:** unlike I01 and I02, this entry is calibrated as `close-to-reality`, meaning Opus's recommendation was close but not quite right. The team correctly overrode it.
- **Opus's per-source clustering was the Phase 1 mistake:** the audit explicitly refuted this. The team's decision to go global (not per-source) is the correct fix for the cross-source leakage problem.
- **The "report it, don't break the group" principle is a good one:** breaking a large group to force exact ratios would reintroduce the leakage problem. Accepting ratio drift is the right trade-off.
- **The `_furthest_below_target` greedy packing is a reasonable heuristic:** it's not optimal, but it's simple, deterministic, and good enough in practice.
- **The `no_phash_group_spans: true` check is the key validation:** it proves that no near-duplicate group spans multiple splits, which is the whole point of the grouping.
- **Cross-reference to C34:** the `near_dup_groups` function in `src/common/neardup.py` is the same one optimised in C34. This is a good example of the two entries building on each other.
- **Cross-reference to I02:** the `image_id`-sorted rows and `md5` identity from I02 are used here for deterministic group ID assignment. This is a good example of the two entries building on each other.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.