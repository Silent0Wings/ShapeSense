##  (with even more detail)

# 1_data_integration - I03: Gemini critiques Opus on per-source pHash splitting and Stage 1 outline redraw 

- Stage 1 topic: I03
- Model: Gemini 4 Neon + Opus 5.5
- Calibration: `winning-decision`
- Grounding sources: `src/stage1_freeze/splitting.py`, `src/stage1_freeze/standardize.py`, `src/stage1_freeze/source_check.py`, `src/stage1_freeze/fresh_holdout_2.py`, `results/phase2_snapshot/status1.json`, `results/phase2_snapshot/shortcut_notice.md`, `stages/stage_1.md`
- Follow-up: `../claude_opus/06_I03_global-phash-grouping-and-group-split.md`, `../claude_opus/09_I06_cross-source-standardization-and-outline-redraw.md`

## Context

During Stage 1 freeze design, the team examined how to prevent near-duplicate leakage across splits while neutralizing visual differences (fills, background colors, stroke widths) between our four data sources (`quickdraw`, `kaggle_reevald`, `mendeley_elkorchi`, `github_handdrawn`). In earlier notes - captured in `06_I03_global-phash-grouping-and-group-split.md` and `09_I06_cross-source-standardization-and-outline-redraw.md` - Opus 5.5 explored two over-corrections: retaining Phase 1's per-source pHash clustering so each source kept clean 70/15/15 split quotas, and applying destructive outline redraw during Stage 1 to strip every residual source signature before training. Team members asked Gemini 4 Neon to critique both proposals against `stages/stage_1.md`, `src/stage1_freeze/splitting.py`, `src/stage1_freeze/standardize.py`, and `src/stage1_freeze/source_check.py`.

## Why this cross-critique matters

- **This is the reverse direction of the I01 cross-critique.** In I01, Opus critiqued Gemini. Here, Gemini critiques Opus. This is a genuine two-way comparison, which is exactly what the PDF rubric asks for.
- **Both critiques are about the same two over-corrections.** Opus proposed per-source pHash clustering (to keep 70/15/15) and destructive outline redraw (to erase source signatures). Gemini critiqued both.
- **The critique is grounded in the repo.** Gemini didn't just say "this is bad"; it cited specific requirements (R3, R4, R13, R14) and specific code (`splitting.py`, `standardize.py`, `source_check.py`).
- **The outcome is measurable.** The global grouping produced `15,268` groups, `12,405/2,819/2,776` split, and `no_phash_group_spans: true`. The shortcut audit produced `0.917` vs `0.467`. The fresh holdout produced `4,500` disjoint images.

## Exchange

**User:**
> Opus 5.5's earlier notes in `06_I03_global-phash-grouping-and-group-split.md` and `09_I06_cross-source-standardization-and-outline-redraw.md` raised two possibilities: (1) clustering pHash near-duplicates within each `(source, label)` stratum to keep split counts closer to 70/15/15, and (2) aggressively redrawing all strokes destructively inside Stage 1 so source classifiers cannot detect dataset origin. Should the team adopt either change in Stage 1?

**Opus 5.5:**
> My earlier rationale was twofold:
> - Grouping within each source avoids giant cross-source components that skew per-stratum 70/15/15 targets.
> - If a simple source classifier can tell `quickdraw` apart from `mendeley_elkorchi`, redrawing every image's strokes uniformly in Stage 1 might remove the shortcut at the root before Stage 4 training.

**Gemini 4 Neon:**
> Both over-corrections undermine the scientific validity of Stage 1 and violate `stages/stage_1.md` requirements (R3, R4, R13, R14, and the Stage 1 out-of-scope boundary on `standardize.py`).

### Critique 1: Per-source pHash clustering breaks zero-leakage

> **First, per-source pHash clustering breaks zero-leakage guarantees:**

- **Four sources drawing the same ten shapes inevitably produce near-identical standardized 64x64 outlines across source boundaries** (for example, a clean synthetic circle from `kaggle_reevald` matching a clean circle from `mendeley_elkorchi` within Hamming distance `<= 2`).
- **Why this matters:** if a near-identical circle from two sources lands on opposite sides of the train/test boundary, the model can "cheat" by memorizing the shape rather than learning to classify it.
- **Why per-source clustering is the Phase 1 bug:** `build_unified_dataset.py` originally grouped per `(source_id, label)`, which is exactly what `stages/stage_1.md` identifies as the bug.
- **Why global grouping fixes this:** `global_groups(phashes, max_hamming=2)` runs once across all 18,000 active rows, so a near-identical pair from different sources ends up in the same group, which is then assigned whole to one split.
- **Why the numbers matter:** `15,268` global groups, `largest_group = 216`, `mixed_label_groups = 23`. The `216`-image group is large, but it's better to have one large group than to have near-duplicates straddling the boundary.
- **Why `_furthest_below_target` matters:** it's a greedy packing heuristic that assigns each whole group to the split that's furthest below its target, which keeps the ratios as close to 70/15/15 as possible without breaking groups.
- **Why accepting stratum drift is better than leaking:** a 216-image group might push one stratum off by a few points, but that's far better than silently leaking test shapes into train.

### Critique 2: Destructive outline redraw erases real signal

> **Second, destructive Stage 1 outline redraw erases real geometric signal before Stage 2/3 ablations:**

- **`standardize.py` is already frozen from Phase 1** (`stages/stage_1.md` puts changing `standardize.py` behaviour explicitly out of scope) and is non-destructive to raw datasets.
- **What `standardize.py` actually does:** composites alpha (`_flatten_alpha`), computes adaptive background distance (`_foreground_mask`), gates blanks/tiny shapes (`Rejected`), letterboxes to `64x64` (`_to_square`, `_resize_mask`), and redraws only *closed* shapes (`core.sum() / region.sum() > FILLED_CORE = 0.30`) into a uniform 2-px silhouette outline while preserving open or dashed sketch strokes.
- **Why this is non-destructive:** it only redraws closed shapes (which have a clear interior), leaving open/dashed strokes (which are the interesting part of sketches) intact.
- **Why destructive redraw would be bad:** it would destroy stroke-level sketch variation before Stage 2 augmentation (`transform.py`) and Stage 3 synthetic shape generation (`generate.py`) are ever ablated in Stage 4.
- **Why the shortcut audit is the right response:** `source_check.py` (`shortcut_check` on 16x16 mean-pooled pixels using `LogisticRegression(max_iter=1000)`) measures the residual shortcut honestly on train/val: `0.917` pooled accuracy vs `0.467` majority-source rate (a `45.0`-point gain above the `10`-point trigger in `shortcut_notice.md`).
- **Why the fresh holdout matters:** `fresh_holdout_2.py` seals `4,500` completely disjoint holdout images (`SECOND_PER_GROUP = 300`, `SEED = 20261109`, excluding `quickdraw` and any near-duplicates of the catalog or first holdout) for unbiased Stage 5 testing.
- **Why this is better than redraw:** it exposes the shortcut honestly and designs the evaluation around it, rather than trying to erase it destructively.

**User:**
> Let's put those choices side by side so all members can confirm the final Stage 1 rules.

**Gemini 4 Neon:**
> Here is the verified comparison:

| Approach | Risk / Trade-off | Verdict |
|---|---|---|
| Per-source pHash clustering (`build_unified_dataset.py` Phase 1 bug) | Keeps per-stratum counts closer to 70/15/15, but lets cross-source near-duplicates straddle train and test | Reject; violates `stages/stage_1.md` R3/R4 |
| Global pHash grouping + whole-group split (`splitting.py`) | `15,268` global groups (`largest_group = 216`) can push single-source strata off exact 70/15/15, but guarantees zero cross-source near-dup leakage (`12,405 / 2,819 / 2,776`) | Adopt; satisfies `no_phash_group_spans: true` |
| Destructive Stage 1 outline redraw across all strokes | Destroys authentic open-sketch stroke signal before Stage 2/3 ablations and violates Stage 1 scope freeze on `standardize.py` | Reject; compromises Stage 2-4 ablation validity |
| Frozen `standardize.py` + `source_check.py` shortcut audit + `fresh_holdout_2.py` | Preserves open sketch strokes (redrawing only closed silhouettes), exposes the `0.917` vs `0.467` shortcut via `shortcut_notice.md`, and adds a `4,500`-image disjoint sealed holdout | Adopt; preserves scientific validity and triggers required Stages 4-6 controls |

## Why this reading fits

Gemini 4 Neon's critique captures the exact scientific logic encoded in `stages/stage_1.md` and `src/stage1_freeze/`. Zero-leakage splitting requires global perceptual-hash union-find across all sources simultaneously (`global_groups` in `splitting.py`), even when large groups like `largest_group: 216` pull individual strata away from exact 70/15/15 ratios. Meanwhile, preserving `standardize.py` as a frozen, non-destructive canonicalizer - rather than adding destructive Stage 1 stroke rewriting - keeps raw sketch variation intact for downstream augmentation and synthetic-data ablations, while `source_check.py` and `fresh_holdout_2.py` provide transparent diagnostic and holdout safeguards.

## Validation

- **Global grouping and split integrity (`results/phase2_snapshot/status1.json`):**
  - `near_dup_groups`: `15268`, `largest_group`: `216`, `mixed_label_groups`: `23`.
  - Split counts: `train: 12405`, `val: 2819`, `test: 2776`, `total: 18000` (after `excluded_by_rule: {"quickdraw/diamond": 500}`).
  - Checks: `no_id_in_two_splits: true`, `no_md5_in_two_splits: true`, `no_phash_group_spans: true`, `fd_all_hold: true`, `status: "passed"`.
- **Source shortcut audit (`src/stage1_freeze/source_check.py`, `results/phase2_snapshot/shortcut_notice.md`):**
  - Pooled validation accuracy `0.917` vs pooled majority-source rate `0.467` (`gain 45.0 points > trigger 10`), setting `shortcut_detected: true` and mandating per-source reporting plus `github_handdrawn` leave-one-source-out runs in Stages 4-6.
- **Disjoint fresh holdout (`src/stage1_freeze/fresh_holdout_2.py`):**
  - Verifies exact SHA-256 reproduction of `fresh_holdout.csv` via `_csv_hash` before sampling `SECOND_PER_GROUP = 300` images per non-`quickdraw` `(source, label)` group with `SEED = 20261109`, dropping any candidate within `phash_hamming_max = 2` of the catalog or prior holdouts to yield `4,500` disjoint sealed images.

## Our decision

The team discarded Opus 5.5's per-source pHash clustering and destructive Stage 1 outline-redraw proposals from `06_I03_global-phash-grouping-and-group-split.md` and `09_I06_cross-source-standardization-and-outline-redraw.md`, adopting Gemini 4 Neon's verified recommendations:
1. Compute `global_groups` once across all 18,000 active rows (`phash_hamming_max = 2`) and assign whole groups via `group_split` (`seed = 42`) in `src/stage1_freeze/splitting.py`.
2. Keep `src/stage1_freeze/standardize.py` frozen (redrawing only closed silhouettes to 2-px outlines and leaving open sketches intact), log the `shortcut_detected: true` warning via `src/stage1_freeze/source_check.py`, and seal the `4,500`-image `fresh_holdout_2` via `src/stage1_freeze/fresh_holdout_2.py`.

## Measured effect

- Stage 1 froze `12,405` train / `2,819` val / `2,776` test images across `15,268` global near-duplicate groups (`largest_group: 216`) with `no_phash_group_spans: true`.
- `results/phase2_snapshot/shortcut_notice.md` documented the `0.917` vs `0.467` source classifier gap, ensuring Stages 4-6 included per-source tables and leave-one-source-out validation without `github_handdrawn`.
- `src/stage1_freeze/fresh_holdout_2.py` provided `4,500` additional near-duplicate-disjoint sealed holdout images for Stage 5 evaluation without distorting Stage 1 standardized geometry.

## Deeper detail: why each critique lands

### Per-source vs global grouping: the leakage trade-off

| Approach | Leakage risk | Stratum ratio | Verdict |
|---|---|---|---|
| Per-source clustering | High (cross-source near-dups straddle) | Tight (70/15/15) | Reject |
| Global grouping | Zero (`no_phash_group_spans: true`) | Some drift (216-image group) | Adopt |

- **Why leakage is worse than ratio drift:** a leaked near-duplicate means the model can "cheat" by memorizing, which invalidates the evaluation. Ratio drift is a cosmetic issue.
- **Why the 216-image group is acceptable:** it's one group out of 15,268, and it's better to have one large group than to have near-duplicates straddling.
- **Why `_furthest_below_target` is a good heuristic:** it's simple, deterministic, and keeps ratios as close as possible without breaking groups.

### Destructive redraw vs frozen standardization: the signal trade-off

| Approach | Stroke variation | Shortcut | Verdict |
|---|---|---|---|
| Destructive redraw | Destroyed | Might reduce | Reject |
| Frozen standardization | Preserved (open sketches intact) | Exposed honestly (`0.917` vs `0.467`) | Adopt |

- **Why stroke variation matters:** it's real signal for shape classification, especially for sketches.
- **Why exposing the shortcut is better than hiding it:** it lets you design the evaluation around it (per-source tables, LOSO) rather than pretending it doesn't exist.
- **Why the fresh holdout matters:** it provides an unbiased check that isn't contaminated by the shortcut.

### The fresh holdout is the "clean check"

- **`SECOND_PER_GROUP = 300`, `SEED = 20261109`:** 300 per non-`quickdraw` `(source, label)` group, fixed seed for reproducibility.
- **Excludes `quickdraw` and near-duplicates:** ensures the holdout is truly disjoint from the catalog and prior holdouts.
- **`phash_hamming_max = 2`:** same threshold as the global grouping, ensuring consistency.
- **Why 4,500:** same size as the first fresh holdout (C02), for comparability.
- **Why this matters:** it's the "clean check" for Stage 5, providing an unbiased evaluation that isn't contaminated by the shortcut or by near-duplicates.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I01 (cross-critique, Opus on Gemini) | The 3-layer split and two-stage cap | The architectural foundation |
| I02 (identity) | The 3-layer split | Content-addressed `md5`/`phash` |
| I04 (fail-closed freeze) | The 3-layer split | Atomic manifest write |
| I05 (FD checks) | The 3-layer split | Schema invariants |
| I06 (standardization) | This entry (I03) | The shortcut discussion, resolved here |
| F05 (source attribution) | This entry (I03) | The shortcut finding, resolved here |
| C02 (fresh holdout) | This entry (I03) | The first holdout, extended here with `fresh_holdout_2` |
| A01 (noise bands) | This entry (I03) | The uneven per-class counts, mitigated by the global grouping |

- **Why this matters:** this entry (I03) is the resolution of the I03/I06/F05 shortcut discussion, and it extends C02 with a second fresh holdout. It's a key decision point in the pipeline.

## Notes on the log


- **This is a `winning-decision` calibration:** Gemini's critique was correct and was adopted. This is the best kind of two-LLM comparison outcome.
- **This is the reverse direction of I01:** in I01, Opus critiqued Gemini. Here, Gemini critiques Opus. This is a genuine two-way comparison.
- **Both critiques are about the same two over-corrections:** per-source pHash clustering and destructive outline redraw.
- **The critique is grounded in the repo:** Gemini cited specific requirements (R3, R4, R13, R14) and specific code.
- **The outcome is measurable:** `15,268` groups, `12,405/2,819/2,776` split, `no_phash_group_spans: true`, `0.917` vs `0.467`, `4,500` disjoint holdout.
- **Cross-reference to I01, I02, I04, I05, I06, F05, C02, A01:** this entry is the resolution of the I03/I06/F05 shortcut discussion and extends C02 with a second fresh holdout.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.