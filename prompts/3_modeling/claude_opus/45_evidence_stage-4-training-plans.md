# 3_modeling - Stage 4 plan: training baselines and A0, A1, B

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-08
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner brief for Stage 4 (training) and one implementation plan each for the loader, the classical baselines and CNN training.

## Response (saved output, verbatim)

### `stages/stage_4.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 4 — Training (baselines + A0 / A1 / B)

> Owner brief. Everything here is about Stage 4 only. The full project
> plan is `../implementation.md`; shared rules live there under
> *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 4` (one run per arm × seed)
- **Code folder:** `src/stage4_train/`
- **Depends on:** Stage 1 (splits); Stage 2 for A1 and B; Stage 3 for B.
  Loader, baselines and A0 can start before 2 and 3 finish.
- **Blocks:** Stage 5
- **Effort:** 2.5–3 days (the heaviest stage)

## Focus

Train the **same CNN under three data recipes** — with repeated seeds —
everything else held identical, so that any difference Stage 5 measures
can only come from the data. Stage 4 is a controlled experiment, not a
leaderboard: fairness between arms matters more than the best accuracy.

## Goals

1. Build the on-demand data loader (SQLite catalog → batches).
2. Train two scikit-learn baselines to show how hard the task is.
3. Train the CNN for three arms × 3–5 seeds — up to 23 runs in total
   once the tuning grid and the optional leave-one-source-out runs are
   counted (Decision 6):
   - **A0** real only (the report's "Model A")
   - **A1** real + augmentation
   - **B** 70% real + 30% synthetic, all augmented (the report's "Model B")
4. Select each model on the **validation** split only.

## Out of scope

- Computing test metrics or comparing arms (Stage 5).
- Writing the augmentation or the generator (Stages 2 and 3 — you only
  call `transform` and `generate`).
- Tuning anything on the test split. You cannot even load it:
  `common.load_split("test")` raises for Stage 4.

## Inputs

| Input | Where |
|---|---|
| Train and validation manifests | `common.load_split("train" / "val")` |
| `transform(img, label, rng)` | `stage2_augment` |
| `generate(label, rng)` | `stage3_synth` |
| Arms, seeds, synthetic ratio, step budget, hyperparameters | `configs/pipeline.yaml#runs`, `#train`, `#evaluation` |

## Requirements

**Must**
- R1. One architecture, optimizer, **step budget**, LR schedule, batch
  size and early-stopping rule for all arms — read from
  `configs/pipeline.yaml`.
- R2. The **only** difference between arms is the data stream.
- R2b. Decision 13: because sampling is class-balanced, an epoch is a
  fixed number of optimizer steps, not a pass over the data. Compute
  `steps_per_epoch` **once** from arm A0 (`ceil(n_train / batch_size)`),
  freeze it in `configs/pipeline.yaml#train`, and use the same value for
  every arm. Record in `status.json` that arm B therefore draws
  0.7 × `batch_size` real images per step — the comparison is equal
  compute with substitution, and Stage 6 has to say so.
- R3. The same seed list for every arm (seed 1 of A0 pairs with seed 1
  of A1 and B), so paired robustness checks are valid.
- R4. Tune once on **A1 validation** using the small grid in Decision 7;
  freeze the winner for all arms and seeds. No arm-specific tuning.
- R5. Use Decision 8's CNN/training defaults as the starting point and
  record the selected epoch for every run.
- R6. Use class-balanced real sampling in every arm. Arm B's synthetic
  share is evenly distributed across all 10 classes.
- R7. Arm B batches are 70% real / 30% synthetic (ratio from
  `configs/pipeline.yaml`); synthetic images are augmented too.
- R8. Never read the test split. No line in `artifacts/test_access.log`
  may carry this run's `run_id`. (The log is append-only and shared
  across runs — never truncate it to make this pass.)
- R9. Each run is reproducible from (arm, seed), including loader workers.
- R10. Benchmark at least 100 batches on the intended Windows machine
  before the full sweep; record throughput, estimated time per run, and
  the estimated time for **all** runs in the budget. A 23-run estimate
  on D3 is what tells the team whether 5 seeds are affordable.
- R11. Measure validation prediction disagreement between seeds of the
  same arm and write it to `seed_disagreement.json`. This is a
  robustness number for the report. It is **not** the power check —
  Decision 10 moved that to Stage 5, because the primary CI is a
  bootstrap over test images between two ensembles, which seed spread
  does not estimate.
- R12. Save validation **softmax probabilities**, not just predicted
  labels. Stage 5's power check is a paired bootstrap over A1's and B's
  validation probabilities and cannot run without them.
- R13. Decision 14: train both baselines — logistic regression on raw
  pixels and a linear SVM on HOG features — on the same class-balanced
  real stream as A0, selected on validation. Stage 5 evaluates them on
  test, so they must be saved in a loadable form.
- R14. If the Stage 1 source-shortcut trigger fired, train the required
  Hand-Drawn leave-one-source-out versions of A1 and B with frozen
  settings.

**Should**
- Run the baselines first; they take minutes and they calibrate what
  "easy" looks like before three days of CNN runs.
- Start with 3 seeds; add seeds 4–5 only if the D3 estimate allows.
- Log training/validation loss and accuracy per epoch.
- On Windows, give every loader worker its own read-only SQLite
  connection; never share one connection across worker processes.

## Deliverables

- `artifacts/stage4/<arm>_<seed>/model.pt`, `train_log.csv`,
  `val_curve.png`, validation predictions **and softmax probabilities**
- `artifacts/stage4/baselines/` — the two fitted baselines plus
  `baselines.json` (validation scores)
- `artifacts/stage4/tuning.json`, `loader_benchmark.json`,
  `seed_disagreement.json`
- `artifacts/stage4/status.json` — list of runs, frozen
  `steps_per_epoch`, selected epochs, val scores, realized batch mix

## Done when

- [ ] Every required arm × seed and both baselines are trained.
- [ ] The single A1 tuning result and frozen settings are recorded.
- [ ] `steps_per_epoch` is frozen and identical across arms.
- [ ] Validation-based model selection is recorded for each run.
- [ ] Validation softmax probabilities are saved for every run.
- [ ] Baseline scores, loader benchmark and seed disagreement recorded.
- [ ] Required leave-one-source-out runs exist if the trigger fired.
- [ ] No line in `test_access.log` carries this run's `run_id`.

## Interfaces you use and provide

- Uses: `stage2_augment.transform`, `stage3_synth.generate` (the only two
  cross-stage imports allowed), `common.load_split`.
- Provides: the trained models + logs in `artifacts/stage4/`, consumed only
  by Stage 5.

## Pitfalls

- **Different step budgets per arm** — B "wins" because it trained
  longer. Freeze `steps_per_epoch` once and never recompute it per arm.
- **Leaving "epoch" undefined** — with class-balanced sampling it is no
  longer a pass over the data, and arm B's batches are only 70% real.
  Without a frozen step budget the comparison quietly becomes "equal
  epochs" for one arm and "equal real images" for another.
- **Choosing the best seed per arm** — cherry-picking; report all seeds.
- **Early-stopping on test** — impossible by design here, but also don't
  "peek" at Stage 5 numbers and come back to retune.
- **Synthetic ratio applied per epoch instead of per batch** — the model
  sees long synthetic-only stretches.
- **Data-loader randomness not seeded** — workers each need a seed
  derived from the run seed.

## Glossary

- **Arm**: one variant of an experiment that differs in a single
  factor. Example: A1 differs from A0 only by augmentation.
- **Controlled comparison**: everything except the tested factor is held
  equal. Example: same CNN, same 30 epochs, same LR for A0, A1, B.
- **Seed**: the number that fixes all randomness of a run. Example:
  seed 3 gives the same initial weights in every arm.
- **Paired design**: matching runs across arms by seed so differences are
  compared like-for-like. Example: A1-seed-3 vs B-seed-3.
- **Batch mixing ratio**: the share of each batch drawn from each
  source. Example: 179 real + 77 synthetic in a 256 batch (70/30).
- **Step budget**: a fixed number of optimizer updates per epoch, used
  instead of "one pass over the data" when sampling is balanced.
  Example: 50 steps of 256 images, identical for A0, A1 and B.
- **Substitution vs addition**: whether synthetic images replace real
  ones in a batch or are added to them. Example: B substitutes, so at
  equal steps it sees 30% fewer real draws than A1.
- **Early stopping**: stop training when validation stops improving and
  keep the best epoch. Example: best val macro-F1 at epoch 18 of 30.
- **Baseline**: a simple model that sets the floor. Example: logistic
  regression on raw pixels reaching 71% validation accuracy.
- **HOG**: Histogram of Oriented Gradients, a hand-made edge-direction
  feature. Example: `skimage.feature.hog(img, pixels_per_cell=(8, 8))`.

## Missions

### M1 Find the unfair arm (recognition)
Prompt: which setting makes this comparison invalid?

```yaml
runs:
  - {arm: A0, seed: 1, epochs: 30, steps: 50, lr: 0.001, aug: false, synth: 0.0}
  - {arm: A1, seed: 1, epochs: 30, steps: 50, lr: 0.001, aug: true,  synth: 0.0}
  - {arm: B,  seed: 2, epochs: 40, steps: 72, lr: 0.001, aug: true,  synth: 0.3}
```
Expected outcome: B differs in **three** extra ways — seed 2 instead of
1 (breaks pairing, R3), 40 epochs instead of 30 (breaks R1), and 72
steps instead of 50 (breaks R2b; someone "compensated" for the 30%
synthetic share by giving B more steps, which hands it more gradient
updates). Only `aug` and `synth` may differ.

### M2 A 70/30 batch mixer (application)
Prompt: build one training batch for any arm.

```python
def make_batch(arm, real_ids, batch_size, rng, cfg):
    n_syn = round(batch_size * cfg["synthetic_ratio"]) if arm == "B" else 0
    real = [load_image(i) for i in rng.choice(real_ids, batch_size - n_syn)]
    syn  = [generate(lbl, rng) for lbl in ...]      # TODO: balanced labels
    imgs, labels = ...                               # TODO: combine + shuffle
    if arm in ("A1", "B"):
        imgs = [transform(im, lb, rng) for im, lb in zip(imgs, labels)]
    return to_tensor(imgs), labels
```
Expected outcome: for B with batch 256 and ratio 0.3, exactly 77
synthetic and 179 real images, with the 77 spread evenly over the 10
classes; A0 batches contain no augmented and no synthetic images; the
same `rng` seed gives the same batch. Note that B drew 179 real images
where A1 drew 256 — that gap is the experiment, not a bug.

### M3 One fair run end-to-end (synthesis)
Prompt: write `train_one(arm, seed)` with validation-based early
stopping and record it in `status.json`.

```python
def train_one(arm, seed, cfg):
    set_all_seeds(seed)
    model = SmallCNN(n_classes=10)
    best, best_epoch, wait = -1, None, 0
    for epoch in range(cfg["epochs"]):
        train_epoch(model, arm, seed, cfg)      # exactly cfg["steps_per_epoch"] steps
        f1 = macro_f1(model, load_split("val"))
        # TODO: keep best checkpoint, patience counter, break on patience
    save(model_best, f"artifacts/stage4/{arm}_{seed}/model.pt")
    save_probs(model_best, f"artifacts/stage4/{arm}_{seed}/val_probs.npz")
    return {"arm": arm, "seed": seed, "best_epoch": best_epoch, "val_macro_f1": best}
```
Expected outcome: three runs (A0/A1/B, seed 1) produce three model files
and three validation probability files, each with a recorded best epoch;
all three ran the same number of optimizer steps per epoch; rerunning A0
seed 1 reproduces the same validation macro-F1; no line in
`test_access.log` carries this run's `run_id`.

When you finish M3, run `quiz-topic` on "controlled training
experiments".
````

### `26_s4_loader.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E26 evidence line

# Plan 26: S4 loader, batch mixer, benchmark

**Stage:** `stages/stage_4.md` R6, R7, R9, R10, Should 4, Mission M2 · **Plan refs:** `implementation.md` Decisions 6, 11, 13
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E26) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Training needs reproducible batches identical in recipe across arms except the data stream.

## 2. Root Cause & Investigation
No loader exists; `Batch` lives in `common.batch`.

## 3. Architecture & Modular Design Strategy
Pure: `batch_plan(...)` → balanced real labels; synthetic count `round(bs*frac)` balanced across classes. `ImageStore` loads train/val images once (paths from the read-only SQLite catalog, one connection per process). `make_batch(...)` → `Batch` with `is_synthetic`. Worker seeds derived from (run seed, worker id). `benchmark(...)` ≥ 100 batches → `loader_benchmark.json`.

## 4. Proposed Changes by File
- `src/stage4_train/sampling.py`, `data.py`, `benchmark.py`.
- `tests/stage4/test_sampling.py`, `tests/stage4/test_data.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_b_batch_77_synthetic_179_real` (M2), `::test_synthetic_labels_balanced`, `::test_real_labels_balanced`, `::test_a0_no_aug_no_synth`, `::test_same_seed_same_batch`; `test_data.py::test_store_refuses_test_split`.
- **Break verification**: compute the synthetic count per epoch → per-batch test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Plan says 'query SQLite per batch'; an in-memory store loaded once from the catalog is the simplest way to hit CPU throughput — recorded as an interpretation.
````

### `27_s4_baselines.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E27 evidence line

# Plan 27: S4 baselines (logistic regression on pixels, linear SVM on HOG)

**Stage:** `stages/stage_4.md` R13, Should 1 · **Plan refs:** `implementation.md` Decision 14
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E27) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Baselines calibrate task difficulty and are evaluated on test by Stage 5.

## 2. Root Cause & Investigation
None exist.

## 3. Architecture & Modular Design Strategy
Pure features: `pixel_features(X)`, `hog_features(X)`. Training on a class-balanced real sample (same sampler as A0), C chosen on validation macro-F1 from a small grid; saved with `joblib` to `artifacts/stage4/baselines/` + `baselines.json`.

## 4. Proposed Changes by File
- `src/stage4_train/baselines.py`.
- `tests/stage4/test_baselines.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_hog_shape`, `::test_selection_uses_val_only`, `::test_saved_model_reloads_and_predicts`.
- **Break verification**: select on train score → `test_selection_uses_val_only` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- LinearSVC has no `predict_proba`; Stage 5 uses its predictions only.
````

### `28_s4_cnn_training.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 28: S4 CNN, tuning grid, arm × seed sweep, seed disagreement

**Stage:** `stages/stage_4.md` R1–R5, R8, R11, R12, R14, Should 2–3, Done-when D1–D8, Missions M1, M3 · **Plan refs:** `implementation.md` Decisions 6–9, 12, 13
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E28) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The controlled experiment: same CNN, same budget, only the data stream differs.

## 2. Root Cause & Investigation
No model or training loop exists.

## 3. Architecture & Modular Design Strategy
`model.py` SmallCNN (3 × [Conv3×3→BN→ReLU→MaxPool2] 32/64/128 → GAP → Dropout → Linear 10). `train.py` `train_one(...)`: AdamW, cosine schedule, early stopping patience 5 on val macro-F1, best checkpoint, logs, val curve, `val_probs.npz`. `steps_per_epoch = ceil(n_train / batch_size)` from A0, frozen into config; training refuses to start on mismatch. `tuning.py` Decision 7 grid on A1 → `tuning.json`. `sweep.py` runs `config.runs`, `seed_disagreement.json`, LOSO if `shortcut_detected`. Status records frozen steps, selected epochs, realized batch mix and the B real-draw note.

## 4. Proposed Changes by File
- `src/stage4_train/model.py`, `train.py`, `tuning.py`, `sweep.py`, `run.py`.
- `tests/stage4/test_model.py`, `tests/stage4/test_train.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_param_count_about_100k`, `::test_same_steps_every_arm`, `::test_reproducible_val_f1_same_seed`, `::test_refuses_mismatched_steps_per_epoch`, `::test_early_stopping_keeps_best_epoch`, `::test_val_probs_rows_sum_to_one`.
- **Pipeline**: background sweep; no access-log line for the run_id.
- **Break verification**: give B more steps → `test_same_steps_every_arm` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- CPU wall-clock decides 3 vs 5 seeds. Determinism via seeded torch/NumPy.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Status lines record 'verified in tree' or 'evidence in ignore/todo.md' (E26 to E28).

## Our decision

Classical baselines (logistic regression on pixels, SVM on HOG) before the CNN arms.

## Measured effect

Baselines: logistic regression 77.9 and SVM on HOG 84.3 macro F1 (results/phase2_snapshot/baselines.json).

---

## Stage 4 Owner Brief & Modular Implementation Plans (`E26`–`E28`)

### Metadata & Lineage

* **Date:** `2026-11-06` to `2026-11-08`
* **Owner / LLM:** `40256377` / `opus_medium_5.5`
* **Artifacts:** `stages/stage_4.md`, `ignore/plan/26_s4_loader.md` (`E26`), `27_s4_baselines.md` (`E27`), `28_s4_cnn_training.md` (`E28`)

### Decomposition of Stage 4 into Three Verified Engineering Deliverables

| Plan ID | Target Modules & Tests | Core Engineering Contract & Edge-Case Mitigations |
| --- | --- | --- |
| **`26_s4_loader.md` (`E26`)** | `src/stage4_train/{sampling,data,benchmark}.py`<br>`tests/stage4/test_{sampling,data}.py` | Implements class-balanced real sampling, per-batch balanced synthetic mixing (`round(256 * frac)`), and an in-memory `ImageStore` backed by per-process read-only SQLite catalog connections (refusing `"test"`). Enforces ≥100-batch throughput benchmarking (`loader_benchmark.json`) and break-tested per-batch vs. per-epoch mixing. |
| **`27_s4_baselines.md` (`E27`)** | `src/stage4_train/baselines.py`<br>`tests/stage4/test_baselines.py` | Implements `pixel_features(X)` (Logistic Regression) and `hog_features(X)` (`skimage.feature.hog`, `8×8` cells, LinearSVC) trained on `A0`'s class-balanced stream, tuning regularization $C$ strictly on validation macro-F1 (**77.9** and **84.3** validation macro-F1 respectively) and serializing models via `joblib` for single-read Stage 5 test evaluation. |
| **`28_s4_cnn_training.md` (`E28`)** | `src/stage4_train/{model,train,tuning,sweep,run}.py`<br>`tests/stage4/test_{model,train}.py` | Implements `SmallCNN`, `train_one` (AdamW, cosine schedule, validation macro-F1 checkpointing, `val_probs.npz` export for Stage 5's power check), strict `steps_per_epoch` equality enforcement across arms, intra-arm `seed_disagreement.json` quantification, and conditional Hand-Drawn LOSO execution. |

