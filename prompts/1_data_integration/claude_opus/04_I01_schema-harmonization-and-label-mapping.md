

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_standardize-and-merge-sources.md](10_evidence_standardize-and-merge-sources.md), [09_evidence_integration-cases-draft.md](../gemini_4_neon/09_evidence_integration-cases-draft.md)

# 1_data_integration - I01: Schema harmonization, label mapping, and geometric ambiguity margins (reconstructed)

- Stage 1 topic: I01
- Model: Opus 5.5
- Calibration: `winning-decision`
- Grounding sources: `configs/taxonomy.yaml`, `configs/pipeline.yaml`, `src/stage1_freeze/build_unified_dataset.py`, `results/phase2_snapshot/status1.json`, `results/phase2_snapshot/fd_check.json`
- Follow-up: `../gemini_4_neon/03_I01_source-capping-and-label-harmonization.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

During Stage 1 data integration, the team needed to unify heterogeneous raw shape datasets totaling 196,353 files on disk (`ShapeSense_Deployed/web/js/content/explain.js`, `FACTS.archive_files`) into a single 10-class training contract without label drift, class-boundary ambiguity, or unclear dataset licensing. Five raw datasets were present locally, each with incompatible directory layouts, casing conventions, and class vocabularies (including out-of-taxonomy polygons and noisy sketches). Before freezing the Stage 1 splits, the team needed a deterministic schema mapping, explicit license gating, geometric boundary rules for confusable shape pairs, and a config-driven mechanism to exclude contaminated `(source, label)` subsets prior to splitting.

## Exchange

**User:**
> We have five raw shape datasets on disk (196,353 files total across sketches and renders) with mismatched label strings like `Rhombus` vs `diamond`, `Circle` vs `circle`, plus shapes outside our 10 classes (`kite`, `trapezoid`, `parallelogram`, `Heptagon`, `Nonagon`, `other`). One installed Kaggle source (`kaggle_dinesh`) lists its license as `"Unknown"`. How should we harmonize everything into `configs/taxonomy.yaml` without semantic drift or licensing exposure?

**Opus 5.5:**
> Treat schema harmonization as a strict deterministic contract over `(source_id, original_label) -> label_id` rather than ad-hoc folder cleanup:
>
> - **Enforce an explicit 10-class index and source allowlist:** Lock `0: circle` through `9: diamond` in `configs/taxonomy.yaml` and register only the four cleared sources in `SOURCES` inside `src/stage1_freeze/build_unified_dataset.py` (`quickdraw` CC BY 4.0, `kaggle_reevald` CC0, `mendeley_elkorchi` CC BY 4.0, `github_handdrawn` CC BY 4.0). Drop `kaggle_dinesh` outright: its Kaggle license reads `"Unknown"` and it only duplicates `circle`, `square`, and `triangle` already covered by three other sources.
> - **Codify `LABEL_MAP` deterministically:** Map every valid `(source_id, original_label)` pair - including `kaggle_reevald` `rhombus -> diamond` and `mendeley_elkorchi` title-cased names - to canonical taxonomy names, and map out-of-taxonomy labels (`kite`, `trapezoid`, `parallelogram`, `Heptagon`, `Nonagon`, `other`) to `None` so they are dropped before standardization.
> - **Encode geometric ambiguity margins in `configs/taxonomy.yaml`:** Because `circle`/`ellipse`, `square`/`rectangle`, and `square`/`diamond` form confusable boundary pairs, freeze explicit thresholds under `ambiguity_margins` (`ellipse_min_axis_ratio: 1.2`, `rectangle_min_side_ratio: 1.2`, `diamond_min_angle_offset_deg: 10`) and disable destructive transforms via `no_shear_no_nonuniform_scale` (`[circle, ellipse, square, rectangle, diamond]`).
> - **Use config-driven exclusions before splitting:** Keep the unified build reproducible (`CANDIDATES_PER_GROUP = 1500`, `MAX_PER_GROUP = 1000`, `SEED = 42`), then apply `exclude_source_labels` from `configs/pipeline.yaml` before `group_split` so contaminated `(source, label)` pairs never enter `test.csv`.

**User:**
> In Iteration 1 validation, `quickdraw` drawings labeled `diamond` turned out to be mostly gemstones, cones, and shields rather than non-square rhombi (`diamond`: `rhombus WITHOUT right angles, any rotation`). Should we hand-prune rows via `configs/gemstone_ids.csv` or exclude `[quickdraw, diamond]` as a rule?

**Opus 5.5:**
> Use `exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml` rather than an incomplete manual ID list, and fail loudly if a configured `(source, class)` pair matches zero rows. Here is how the harmonization options compare:

| Option | Effect | Recommendation |
|---|---|---|
| Include all 5 raw sources with permissive label matching | Exposes pipeline to `kaggle_dinesh` (`license="Unknown"`) and mixes `kite`/`Heptagon` noise | Reject |
| Manual `gemstone_ids.csv` pruning without rule exclusion | Leaves non-rhombus Quick, Draw! `diamond` doodles in train/val/test when `filter_gemstones: false` | Reject as incomplete |
| 4-source `LABEL_MAP` + `taxonomy.yaml` margins + `exclude_source_labels: [[quickdraw, diamond]]` | Enforces 21 valid `(source_id, original_label) -> label_id` mappings, drops 500 noisy rows pre-split, leaves 18,000 clean rows | Adopt |

## Why this reading fits

Every piece of Opus 5.5's recommendation matches the architecture implemented across `configs/taxonomy.yaml`, `configs/pipeline.yaml`, and `src/stage1_freeze/build_unified_dataset.py`. Specifically, `SOURCES` excludes `kaggle_dinesh` with an inline comment noting its `"Unknown"` license and redundant class coverage; `LABEL_MAP` explicitly maps the 21 kept `(source_id, original_label)` pairs while mapping the 6 out-of-taxonomy labels to `None`; `configs/taxonomy.yaml` defines `ambiguity_margins` and `no_shear_no_nonuniform_scale`; and `configs/pipeline.yaml` declares `exclude_source_labels: [[quickdraw, diamond]]` alongside `filter_gemstones: false`.

## Validation

- Functional dependency verification in `results/phase2_snapshot/fd_check.json` confirms `(source_id, original_label) -> label_id` holds across all `21` active groups (`n_groups: 21`, `n_violations: 0`, `holds: true`) and `label_id -> label_name` holds across all `10` classes (`n_groups: 10`, `n_violations: 0`, `holds: true`).
- `results/phase2_snapshot/status1.json` records `"gemstone_filter": "superseded_by_rule"`, `"gemstones_removed": 0`, `"excluded_by_rule": {"quickdraw/diamond": 500}`, and all four Stage 1 checks passing (`"fd_all_hold": true`, `"status": "passed"`).
- `src/stage1_freeze/exclusions.py` (`apply_source_label_exclusions`) enforces that every configured `[source, class]` pair matches at least one row before the split, raising `ValueError` on typos.

## Our decision

The team implemented the four-source deterministic `LABEL_MAP` in `src/stage1_freeze/build_unified_dataset.py` (`SEED = 42`, `CANDIDATES_PER_GROUP = 1500`, `MAX_PER_GROUP = 1000`), excluded `kaggle_dinesh`, codified the 10-class taxonomy and `ambiguity_margins` in `configs/taxonomy.yaml`, and applied `exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml` ahead of Stage 1 splitting.

## Measured effect

- Raw disk inventory of `196,353` files was harmonized into `18,500` standardized catalog rows across `4` cleared sources (`quickdraw`, `kaggle_reevald`, `mendeley_elkorchi`, `github_handdrawn`) and `21` active `(source_id, original_label)` mappings.
- Applying `exclude_source_labels: [[quickdraw, diamond]]` removed `500` ambiguous doodle rows prior to splitting, yielding `18,000` active rows frozen into `12,405` train / `2,819` val / `2,776` test (`results/phase2_snapshot/status1.json`).

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor, C02 and C34 entries, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The reconstruction is honest about its source:** the entry explicitly says it is "reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved". This is good practice: it's transparent about what is and isn't a primary source.
- **The four-part recommendation is well-structured:** source allowlist, LABEL_MAP, ambiguity margins, and config-driven exclusions are four separate but related concerns, each addressed clearly.
- **The `exclude_source_labels` mechanism is a good design:** it's config-driven, fails loudly on typos, and is applied before splitting so contaminated data never enters the test set.
- **The 500-row QuickDraw diamond exclusion is a concrete, measurable outcome:** this is the kind of specific, verifiable number that makes the decision auditable.
- **The functional dependency check is strong evidence:** `n_groups: 21`, `n_violations: 0`, `holds: true` for both `(source_id, original_label) -> label_id` and `label_id -> label_name` is a clean, machine-checkable validation.
- **Cross-reference to S07:** the ambiguity margins (`ellipse_min_axis_ratio: 1.2`, `rectangle_min_side_ratio: 1.2`, `diamond_min_angle_offset_deg: 10`) are the same ones defined in S07. This is a good example of the definitions doing real work in the pipeline.
- **Cross-reference to S02/S03:** the `kaggle_dinesh` exclusion is the same decision recorded in S02. This is worth noting so the exclusion is traced back to its original rationale.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.