# Stage 4 — Training (baselines + A0 / A1 / B)

> **Current state (2026-11-09).** There are five arms: A0, A1, B, A2 and P. The CNN has four blocks,
> every arm is tuned on validation, and each trains on five seeds. Iteration 3
> adds grouped 3-fold CV inside the search. At most two runs share the GPU, and
> long jobs run with a stall watcher.
> The rest of this brief is the original design. The record of what changed is
> [`docs/crisp_dm/README.md`](../docs/crisp_dm/README.md).

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
