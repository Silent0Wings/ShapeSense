# CRISP-DM iteration 3: pre-registration

Committed before any iteration 3 tuning or training. Nothing here changes after a sealed read. Any change before one is recorded as a deviation with its reason.

## Question

Does the full training mix make the classifier more robust to damaged images, and when does synthetic data help?

## Evidence status

- The test split was read in iterations 1 and 2. The first fresh holdout was read in iteration 2. Neither is clean evidence.
- **Fresh holdout 2** (`configs/splits/fresh_holdout_2.csv`, 4,500 images, ten classes, 300 per source and class) has never been read. It uses the same three sources as the first holdout, so it does not test generalisation to new sources and has no Quick, Draw! images.
- The validation robustness check from iteration 2 suggested these questions. It set the perturbation list below. It did not choose any model setting.

## Primary comparison

**A2 vs A0, on perturbed copies of fresh holdout 2.** The score is ensemble macro-F1 averaged over the 23 perturbation levels below.

Levels, built once inside Stage 5 from one read per model, using `robustness.perturb` and seed 20261109:

| Family | Levels |
|---|---|
| Rotation | 15, 30, 45, 90, 135, 180° |
| Gaussian noise | σ 0.02, 0.05, 0.1, 0.2 |
| Salt and pepper | 1%, 5% |
| Gaussian blur | radius 1 |
| JPEG | quality 90, 50, 20 |
| Brightness | -0.2, +0.2, +0.4 |
| Contrast | × 0.75 |
| Occlusion | 8, 16, 24 px |

Excluded in advance, because every arm scored under 30% on perturbed validation in iteration 2: salt and pepper 10% and 20%, blur radius 2 and 3, brightness -0.4, contrast × 0.5 and × 0.25.

## Success rule

All three must hold:

1. Gain of at least 1.0 macro-F1 point.
2. 95% paired bootstrap CI excluding 0. The stricter reading, a CI lower bound of at least 1.0, is reported beside it and is not required.
3. No harmful class: a class's mean F1 drop above max(2 points, one bootstrap standard error of that paired drop), with a Bonferroni-corrected CI (level 1 - 0.05 / 10) excluding 0.

## Statistics

- Paired bootstrap, percentile interval, 2,000 resamples, resampling `phash_group` clusters with both arms scored on the same resample. A source-clustered interval is reported as a sensitivity check; with three sources it is coarse.
- Each analysis has its own generator from `SeedSequence.spawn`.
- Seed variation is reported next to each interval: per-seed paired differences, their mean and standard deviation, over 5 seeds.
- McNemar on accuracy is descriptive, exact when `b + c` is under 25.

## Secondary comparisons

Holm-corrected, using two-sided bootstrap p-values on the same metric as the primary:

- A1 vs A0, B vs A0, A2 vs A1, A2 vs B.

The same four plus A2 vs A0 are repeated on clean fresh holdout 2, as a separate Holm family. Results on the reused test split and the first holdout are reported descriptively as contaminated evidence.

Arm P (synthetic pretraining, then real fine-tuning) is reported descriptively against A0 and A2, outside the Holm families, because its value is unknown until Phase 4.

## Experiments on validation only

Three seeds each unless stated. These are descriptive and choose no primary comparison.

| Experiment | Runs |
|---|---|
| Real-data scarcity: A0, A1, B, A2, P at 10, 25, 50, 100% of real training images | 60 |
| Equal real images per step: B and A2 against their equal-real versions | 6 |
| BatchNorm recalibration on real images: B and A2, trained models | none |
| Budget: 30 against 60 epochs, early stopping on and off, A0, A1, A2 | 27 |
| Re-frame and binarise only, on validation, trained models, with aspect-ratio and stroke histograms | none |
| One transform on: rotation, scale, noise, blur, re-frame only, on A1 | 15 |
| Validation against test: class and source balance from aggregate counts | none |

**Budget rule.** All arms move to the longer budget, or to early stopping off, only if the tested arms each improve by at least 0.5 validation macro-F1 points on the mean of three seeds. Otherwise the iteration 2 budget stays. All arms always share one budget.

## Search

The iteration 2 search spaces and trial limits are reused. Per arm: learning rate and dropout grid; generator search for B, A2 and P; batch shares for A2.

Each arm's top 5 settings are re-scored by grouped 3-fold CV over train and validation, stratified on class and grouped on `phash_group`, at a 15-epoch budget. The winner is the setting with the best mean **clean** CV macro-F1, confirmed on three seeds. Perturbed validation is reported for each winner and does not pick it, so the damage in the primary test stays unseen during selection.

## Final training

Seeds 0 to 4 for each of A0, A1, B, A2 and P, the same for every arm, plus Hand-Drawn hold-out runs on three seeds. One read per model of each sealed set.

## What a result means

A negative result is a valid finish. Verdicts from iterations 1 and 2 are not revised.
