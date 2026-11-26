# 2_data_preparation/cleaning - Cross-critique: Rule-based exclusion of Quick, Draw! diamonds (F01 / C01)
- LLM: Claude Opus 5.5 & Gemini 4 Neon (cross-model review of C01 and F01)
- Category: Two-LLM comparison
- Date: 2026-11-20

Cross-critique of [Gemini 4 Neon's rule-based exclusion proposal (`C01`)](../gemini_4_neon/01_C01_quick-draw-diamonds.md) and [Claude Opus 5.5's diamond review (`F01`)](../claude_opus/03_f01-quickdraw-diamond-review.md).

## Prompt

> Another assistant recommended the following for the cleaning step of our pipeline: exclude all 500 `quickdraw/diamond` drawings by a declarative rule (`exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml`) before any test read and re-freeze the train/val/test split (`12,405 / 2,819 / 2,776`), rather than cherry-picking individual rhombi via a manual ID list (`gemstone_ids.csv`) or relabeling them. Check it for errors, risks of data leakage between train and test, and steps that would not help. Say which points you agree with, which you reject, and why.

## Response

### 1. Points of agreement
- **Rule-based `(source, label)` exclusion over manual cherry-picking (`gemstone_ids.csv`):** Because the Quick, Draw! game prompted players for the English word *"diamond"*, most of the 500 drawings depict cut gemstones, rings, cones, or baseball diamonds rather than geometric rhombi (`configs/taxonomy.yaml`). Attempting to cherry-pick the ~20–30% rhombi introduces annotator subjectivity and risks inconsistent filtering across splits. Excluding `["quickdraw", "diamond"]` via a declarative rule in `configs/pipeline.yaml` (`src/stage1_freeze/exclusions.py`) is deterministic, fail-closed, and auditable.
- **No test-split leakage:** The diagnostic that surfaced F01 (`docs/crisp_dm/iteration_1_quickdraw_diamonds.json`, where `quickdraw/diamond` recall was ~59% vs. >97% on `kaggle_reevald/rhombus`) ran strictly on **validation** predictions before the test split was ever unsealed.
- **Atomic split re-freeze (`12,405 / 2,819 / 2,776`):** Because pHash near-duplicate grouping and stratified group splitting depend on the active row pool, dropping 500 rows requires re-running Stage 1 atomically rather than deleting rows in place from existing split manifests.

### 2. Risks and trade-offs checked
- **Single-source exposure for `diamond`:** Dropping `quickdraw/diamond` leaves `kaggle_reevald` (`rhombus`, 2,500 images capped to 1,500 in the unified catalog) as the sole real source for the `diamond` class, alongside `pentagon` (Mendeley El Korchi only) and `ellipse` (GitHub frobertpixto only). This is an acceptable trade-off because keeping ~350 non-rhombus gemstone doodles under the `diamond` label directly corrupts the class definition, and Stage 3 synthetic rhombi (`Arm B` / `Arm A2`) supply multi-style geometric rhombi during training.
- **Why raw-baseline vs. cleaned-baseline delta is small (`+0.50` Macro F1):** In `results/improvement_table.csv`, removing the 372 rejected/excluded rows raises test Macro F1 from `89.13 ± 0.43` to `89.63 ± 0.74` (`+0.50`). Even though `+0.50` sits within the 5-seed spread, the cleaning step is mandatory for **label validity** so that `diamond` test accuracy measures rhombus recognition rather than gemstone-doodle recognition.

## Validation

Checked against `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`, `configs/pipeline.yaml`, `src/stage1_freeze/exclusions.py`, and `results/improvement_table.csv`.

## Our decision

Adopt Gemini 4 Neon's rule-based exclusion (`exclude_source_labels: [[quickdraw, diamond]]`), supersede `configs/gemstone_ids.csv`, re-freeze the split at `12,405 / 2,819 / 2,776`, and disclose in Stage 1 (`F02` / `F05`) that `diamond`, `ellipse`, and `pentagon` each come from a single real source after cleaning.

## Measured effect

- Split re-frozen at `12,405` train / `2,819` val / `2,776` test (0 functional-dependency or leakage violations in `fd_check.json` and `guards.json`).
- Course improvement table (`results/improvement_table.csv`): Cleaning improves raw 64×64 CNN test Macro F1 from `89.13 ± 0.43` to **`89.63 ± 0.74`** (`+0.50`).
