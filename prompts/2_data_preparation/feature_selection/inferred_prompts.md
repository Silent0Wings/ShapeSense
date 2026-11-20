
#  prompts: 2_data_preparation/feature_selection

> **Feature selection was run on 2026-11-20** (the last two change entries in `docs/crisp_dm/iteration_log.json`,
> and failure F32). The chosen step is the input resolution: 48 px, chosen on validation. Results are in
> [`results/improvement_table.csv`](../../../results/improvement_table.csv). FS5 below records it.
>
> The prompts below are the feature selection prompt from [PROMPT.md](../PROMPT.md) and the questions it raises.
> Each **Answer** below was written on 2026-11-20 from the code and the recorded results. It is not the original LLM
> reply.

<a id="fs1"></a>

## FS1 - What feature selection means for a 64x64 CNN

- State: Open
- CRISP-DM step: Data Preparation · Pipeline stages: 1 (standardize) and 4 (baselines)

** prompt**

> Our input is a 64x64 grayscale image fed to a CNN. What does feature selection mean for this setup, and what would
> you try (input resolution, cropping to the shape's bounding box, removing background, or hand-made features such as
> HOG or Hu moments with a classical model)? How do we measure whether it helped?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*

A CNN learns its own features from pixels, so here feature selection means choosing the **input representation**,
not picking columns. The pipeline already makes three of those choices:

1. **Cropping to the shape.** `src/stage1_freeze/standardize.py` crops each image to the bounding box of its ink, adds
   a margin of 8% of the box (`MARGIN = 0.08`), pads it to a square and resizes to 64 px (`TARGET = 64`). Size and
   position differences between sources are removed before training.
2. **Removing the background.** The same step outputs black ink on white, so colour and background texture are gone.
3. **Hand-made features.** Stage 4 trains two classical baselines on hand-made inputs (`src/common/features.py`,
   `src/stage4_train/baselines.py`): raw pixels with logistic regression, and HOG (9 orientations, 8 px cells,
   1,764 values) with a linear SVM.

Two things are still untested: **input resolution** (only 64 px has been run) and **Hu moments** (not implemented).

**How to measure:** change one thing at a time. Train the same arm with the same seeds and settings, and compare the
mean validation macro F1 against the current 64 px pipeline. Count only a change larger than the seed-to-seed spread
(about 0.2 to 0.3 points for A0 and A2 across five seeds, `results/phase2_snapshot/metrics.csv`). Test data stays
sealed until the choice is frozen.

<a id="fs2"></a>

## FS2 - Hand-made features against the CNN

- State: Measured (Stage 4 baselines)
- CRISP-DM step: Data Preparation / Modeling · Pipeline stage: 4 · Baselines

** prompt**

> Do hand-made features like HOG with a classical model come close enough to the CNN that we should use them instead,
> or alongside it?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*

No. HOG is clearly better than raw pixels for a linear model, but both stay far below the CNN:

| Model | Input | Validation macro F1 | Test macro F1 |
|---|---|---|---|
| Logistic regression (C = 0.01) | raw pixels | 77.7 | 77.9 |
| Linear SVM (C = 1.0) | HOG, 8 px cells | 82.5 | 84.3 |
| CNN A0 (5 seeds) | 64x64 pixels | n/a | 94.6 ± 0.2 |
| CNN A2 (5 seeds) | 64x64 pixels | n/a | 95.8 ± 0.3 |

Sources: `results/phase2_snapshot/baselines.json` (validation, 600 balanced real images per class, `n_train` 6,000)
and `results/phase2_snapshot/metrics.csv` (test).

HOG adds about 6 test points over raw pixels for a linear model, so edge-orientation features do help a classical
model. The CNN is still about 10 points ahead and learns those features itself. Keep the HOG SVM as the reference
baseline. Do not feed HOG into the CNN. Note that the baselines saw 6,000 balanced real images while the CNNs saw the
full training split, so part of the gap is data size, not features.

<a id="fs3"></a>

## FS3 - Does the framing of the shape matter to the trained models?

- State: Measured (validation check, not a feature selection run)
- CRISP-DM step: Data Preparation · Pipeline stage: 4 · Experiments (`exp_preprocess`)

** prompt**

> We crop every image to the shape's bounding box. How sensitive are the trained models to how the shape is framed,
> and does that tell us anything about cropping as a feature choice?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*

They are sensitive to it. `src/stage4_train/experiments.py` passes the validation images through the augmentation
transform with every random setting at zero, so the images are only re-framed, then scores the saved models on them
(`results/phase2_snapshot/exp_preprocess.json`, 3 seeds each):

| Arm | Validation as stored | Re-framed only | Change |
|---|---|---|---|
| A0 | 92.6 ± 2.9 | 89.8 ± 3.2 | -2.8 |
| A1 | 94.8 ± 0.1 | 94.5 ± 0.2 | -0.3 |
| B | 94.2 ± 0.0 | 93.6 ± 0.1 | -0.6 |
| A2 | 95.2 ± 0.3 | 94.1 ± 0.2 | -1.1 |

Re-framing changes no labels but costs up to 2.8 points, and the most for A0, which trained without augmentation.
Framing is therefore a real input feature: the bounding-box crop plus a fixed margin is worth keeping, and every image
(real, augmented, synthetic) must be framed the same way. F08 (augmented shapes about 6 px too small) was a failure of
exactly this kind. This check does not show whether a different margin or no crop would score better. That needs its
own training run (FS4).

<a id="fs4"></a>

## FS4 - What is left to run

- State: To do
- CRISP-DM step: Data Preparation

** prompt**

> Which feature selection experiments are still worth running, and in what order?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*

In order of expected value:

1. **Input resolution:** retrain A2 at 32 px and 96 or 128 px against 64 px. The model's receptive field was sized for
   64 px (F17 moved to four convolution blocks for that reason), so a larger input also needs a depth check.
2. **Crop margin:** retrain with `MARGIN` at 0, 0.08 (current) and about 0.15, to settle the FS3 question directly.
3. **Hu moments:** add the 7 moments as a third classical baseline next to the HOG SVM. Being rotation-invariant, they
   may struggle to separate square from diamond, the pair the rotation caps were set to protect (F07).

Each run gets an entry in `docs/crisp_dm/iteration_log.json` under Data Preparation, then an entry here with its
prompt and the recorded decision.

<a id="fs5"></a>

## FS5 - Input resolution, chosen on validation (run)

- State: Done (2026-11-20)
- CRISP-DM step: Data Preparation · Pipeline stage: 4 · `scripts/improvement_table.py fs`

** prompt**

> For the final A2 recipe, does a lower input resolution (32 or 48 px) score better than 64 px on validation? Pick one
> on validation only, then report its test macro F1 against the baseline.

**Answer** *(written 2026-11-20 from the run's records)*

A fixed area-resize layer was put in front of the same CNN, so training and test images pass through the same
resolution. Validation macro F1, mean of seeds 0 to 2 (`artifacts/improvement/feature_selection.json`):

| Input | Validation macro F1 |
|---|---|
| 32 px | 95.85 |
| 48 px | **95.90** |
| 64 px (current A2) | 95.80 |

48 px won, but by less than the seed spread, so validation alone could not separate the three. Trained on 5 seeds,
48 px scored **96.31 ± 0.13** on test, against 95.83 ± 0.31 at 64 px, and was higher on 4 of 5 seeds. That is +7.19
over the raw baseline (89.13). The likely reason is that downsampling smooths stroke-width and jitter differences
between sources. That explanation was not tested. The deployed model stays the 64 px A2.

The first attempt validated at chance because of a GPU resize bug (F32). The runs were rerun after the fix.
