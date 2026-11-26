# 3_modeling - F02: Leave-one-source-out training could not run on all ten classes.
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: F02 (`failure`, `3_modeling`)
- Owner / Proposed by: 40304911 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/sweep.py`, `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, `src/stage5_eval/run.py`, `configs/pipeline.yaml`, `configs/taxonomy.yaml`, `docs/crisp_dm/iteration_1/data/per_source.csv`, `results/phase2_snapshot/per_source.csv`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage4.html`, `ShapeSense_Deployed/web/failures.html`, commits `a71b5e1`, `8984a50`


## Prompt
Leave-one-source-out training fails because one class exists in only one source. How do we design a hold-out-source test that is still valid with this class imbalance across sources?

Literature/search framing: How do domain-generalization studies run leave-one-domain-out evaluation when some classes exist in only one domain? Search for protocols for partial or open domain generalization and for how they score a held-out domain that lacks some classes. Our case: ellipses exist only in the Hand-Drawn source.

## Response
In partial and open-set domain-generalization protocols, a leave-one-domain-out split cannot test zero-shot recognition of a closed-set label whose training support drops to zero when a domain is withheld. The standard protocol is to restrict both optimization and evaluation to the **shared label subspace** present across the remaining training sources, while explicitly disclosing the omitted classes so the hold-out metric is not conflated with full-taxonomy performance.

In ShapeSense, `github_handdrawn` (`LOSO_HOLDOUT_SOURCE = "github_handdrawn"`) is the only source containing `ellipse` (class index `1` in `configs/taxonomy.yaml`), whereas `pentagon` (`5`) comes only from `mendeley_elkorchi` and `diamond` (`9`) relies on non-`quickdraw` sources after `exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml`. When `load_stores(config, holdout_source="github_handdrawn")` in `src/stage4_train/sweep.py` filters out `github_handdrawn` from both `train` and `val`, `train_store.class_counts()` becomes zero for `ellipse`, causing `sample_real_indices` in `src/stage4_train/sampling.py` to raise `ValueError("class 1 requested but the store holds no image of it")`.

To keep a valid unseen-source generalization check without corrupting standard 10-class training:
1. **Detect empty classes only for hold-out runs:** Add `classes_lost_to_holdout(train_store)` in `src/stage4_train/sweep.py` returning `tuple(int(c) for c in np.flatnonzero(train_store.class_counts() == 0))` when `holdout_source` is set, while preserving the hard failure if an ordinary run ever has an empty class.
2. **Exclude lost classes from batch sampling and validation selection:** Thread `excluded_classes` into `BatchStream` and `_labels_for_batch` in `src/stage4_train/sampling.py` so neither real draws nor Stage 3 synthetic draws sample `ellipse`, and pass `excluded_classes` to `macro_f1_points` in `src/stage4_train/train.py` so the 9-class validation score selects `best_epoch` without dividing by an absent class. Keep the frozen `steps_per_epoch: 49` (Decision 13) so LOSO runs match the main sweep's compute budget.
3. **Restrict held-out scoring to shared classes:** On the held-out `github_handdrawn` test items, `ellipse` cannot be evaluated because the 9-class-trained model never saw `ellipse` in training (and synthetic `ellipse` alone would turn the check into synthetic-to-real transfer rather than unseen-source shape generalization). Score the held-out `github_handdrawn` test items on the classes present in both training and the held-out source - specifically Hand-Drawn `triangle` and `rectangle` (`n = 302` test images) - and report them descriptively under `"unseen-source generalization"` rather than mixing them into the primary 10-class comparison.

## Validation
- Unit and integration checks on `src/stage4_train/sampling.py`, `src/stage4_train/sweep.py`, and `src/stage5_eval/run.py` (`loso_excluded_classes`, `run.json` `excluded_classes`) verified that ordinary runs still raise on empty classes while `loso_handdrawn` runs sample only the remaining 9 classes (`0, 2..9`) and keep `steps_per_epoch: 49`.
- Stage 5 (`src/stage5_eval/run.py`) scored the `*_loso_handdrawn_*` models exclusively on the `n = 302` held-out `github_handdrawn` triangle and rectangle test images (`scored_macro_f1` and `accuracy`), keeping the `ellipse` omission explicitly tagged (`LOSO_LABEL = "unseen-source generalization"`).
- `ShapeSense_Deployed/web/failures.html` (and `stage4.html` / `experiments.html`) surfaces the resulting `github_handdrawn` hold-out runs alongside the per-source table (`per_source.csv`).

## Our decision
Adopted the 9-class training and Hand-Drawn triangle/rectangle hold-out evaluation design verbatim in `src/stage4_train/sweep.py`, `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, and `src/stage5_eval/run.py`. Marked F02's resolution state as `Partly` (`results/phase2_snapshot/iteration_log.json`) because `ellipse` cannot be tested under Hand-Drawn hold-out and unseen-source generalization remains descriptive rather than a full 10-class guarantee.

## Measured effect
- **Iteration 1 (`docs/crisp_dm/iteration_1/data/per_source.csv`):** `A1_loso_handdrawn_0` reached `65.6%` accuracy and `B_loso_handdrawn_0` reached `67.2%` accuracy on the `302` held-out `github_handdrawn` images.
- **Iteration 2 (`docs/crisp_dm/iteration_2/investigation/report.md`, `iteration_log.json`):** Mean accuracy across 3 seeds on held-out Hand-Drawn triangles and rectangles rose to `A0 66.6%`, `A1 74.5%`, `B 72.6%`, `A2 73.8%` (reversing A0's same-source lead).
- **Iteration 3 (`results/phase2_snapshot/per_source.csv`):** Over 3 seeds (`loso_seeds: 3`, `n = 302`), unseen-source accuracy was `A0` (`63.9%`, `63.6%`, `69.5%`), `A1` (`66.9%`, `69.9%`, `69.5%`), `B` (`69.9%`, `71.5%`, `69.5%`), `A2` (`71.9%`, `72.2%`, `71.5%`), and `P` (`65.6%`, `67.2%`, `69.5%`).

---

## : Gemini 4 Neon Corpus Synthesis (`F02` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F02` (`failure`)
* **Logic Depth:** **High** (feeds `T17`, `T22`, `C26`)
* **Risk if Wrong:** **High** (9-class hold-out and `excluded_classes` thread through sampling, sweep, and eval)
* **Adoption Status:** **Adopted verbatim** (three-part LOSO protocol: 9-class training, excluded classes in sampling and F1, $n = 302$ held-out scoring; left `Partly` because `ellipse` is untestable under Hand-Drawn hold-out).

### 2. Group Synthesis: The LOSO / Class-Imbalance Chain (`F02` $\rightarrow$ `T17` $\rightarrow$ `T22`)

* **`F02`** is the hardest logic in the corpus. `github_handdrawn` is the only source of `ellipse`; holding it out makes `sample_real_indices` raise `ValueError("class 1 requested but the store holds no image of it")`. The resolution has three coordinated parts: detect lost classes only for hold-out runs; exclude them from sampling **and** from `macro_f1_points`; score the held-out source only on shared classes (Hand-Drawn `triangle` + `rectangle`, **$n = 302$**), tagged `"unseen-source generalization"` and kept out of the primary 10-class comparison. Marked `Partly` because `ellipse` simply cannot be tested under this hold-out.
* **`T17`** implements the thread (`excluded_classes` in `sampling.py`, `classes_lost_to_holdout` in `sweep.py`, `ModelSpec.excluded_labels` in Stage 5) plus CUDA device resolution. The first full GPU sweep trained every run to completion but **crashed in `seed_disagreement`** on `2,371` vs. `2,819` shapes — because `train_one` never wrote `holdout_source` to `run.json`.
* **`T22`** is the minimal fix: enrich `run_sweep`'s return with `holdout_source` from the spec (no change to `train_one`'s signature), plus a regression test with deliberately mismatched `val_probs` lengths. Accepted the full retrain this triggers before any test read.

**Depth note:** `F02` $\rightarrow$ `T17` $\rightarrow$ `T22` is the corpus's clearest **implementation-caught-a-real-bug** sequence: the design was right, the first implementation missed a propagation, and validation on the first real sweep caught it.

### 3. Corpus Dependency Graph (`3_modeling` Gemini 4 Neon Entries)

```text
F17 (3→4 blocks, 46-px RF, 242,250 params)
 ├── D03 (critique that produced F17's depth change; only depth adopted)
 ├── A14 (model.py default still said 3 blocks → fixed iter 3)
 └── F17's 242k params is the fixed capacity every arm shares

F02 (LOSO: ellipse only in Hand-Drawn → 9-class hold-out)
 ├── T17 (implements excluded_classes in sampling/sweep/eval)
 ├── T22 (seed_disagreement must skip LOSO runs → run_sweep marks holdout_source)
 └── C26 (grouping on source_id would drop classes → must group on phash_group)

C12 (per-arm lr/dropout grid) ──→ T15/T23 (record the winner as a comment)
                                   └── recipe_fingerprint unchanged → no retrain

C11 (per-arm synthetic share) ──→ F06 (augmentation/generator ranges only tuned on A1)
                                   └── both are "tuning-budget bias" fixes

C27 (equal_real, real_fraction, budget) ──→ C29 (budget gate fires)
C29 (e60_nostop adopted) ──→ C26 (CV at 15 epochs to bound cost)
C26 (CV re-ranks top-5) ──→ C12 (per-arm grid feeds top-5)
                         └── C25 (P added as descriptive arm; CV changes 4/5 winners)

F19 (invalid handle) ──→ C30 (eager Pool, _light_children)
C30 (parallel prep) ──→ C31 (optimization stage) ──→ C39 (measured before/after)
F22 (cuDNN halt at 66/191) ──→ relies on C30's atomic result.json resume
F25 (GPU looks idle) ──→ explains C30/C31's CPU-bound pacing
```

### 4. Consolidated Adoption Ledger & Epistemic Rules

* **Adopted verbatim (or close):** `F02` (LOSO protocol), `F17` (4th block, 46 px), `C12` (per-arm $3 \times 2$ grid), `C27` (`ADOPT_GAIN = 0.5`), `C29` (`e60_nostop`), `C30` (`step_rng` + eager Pool + `uint8` IPC), `C31` (optimization stage), `C11` (dual reporting), `T15`/`T23` (comment-only recording), `T22` (`run_sweep` enrichment).
* **Adopted with correction:** `C26` (`phash_group` instead of `source_id`; `CV_EPOCHS = 15`), `C25` (descriptive `P` kept; LR reset and synthetic-phase checkpointing rejected), `C39` (speedup split between code and quieter machine), `F19` (initial blame disproved by recurrence; eager Pool adopted), `D03` (depth adopted; optional extras not recorded).
* **Rejected:** `C12` ("shared LR/dropout" claim does not stand), `C29` (extra `B`/`P` check and `patience=20` rejected as post-hoc), `C25` (LR reset), `C26` (`source_id` grouping), `F22` ("GPU damaged" unsupported).
* **Core Epistemic Principles:** (1) Pre-registration is load-bearing, not decorative; (2) Validation catches implementation bugs before any test read; (3) is a first-class epistemic label  (4) Measure, then register—never the reverse.

