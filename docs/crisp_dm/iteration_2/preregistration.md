# CRISP-DM iteration 2: pre-registration

Written 2026-11-09, before any iteration 2 tuning, and committed before the first tuning run.

## Why this iteration exists

Iteration 1 ended with a valid `fail`: B vs A1 was -0.36 macro-F1 points, 95% CI [-1.17, 0.41]. A0, with no augmentation, scored highest. A validation-only investigation then found that the ±180° rotation range, set by hand and never tested, was costing the augmented arms their score (rotation off, or ±15°, reached a mean of about 93.2 against 90.0 for A1 and 91.7 for A0). Iteration 1's verdict stands and is not rewritten. This is a separate experiment.

## The arms

| Arm | Training stream |
|---|---|
| A0 | Real images only |
| A1 | Real images, augmented |
| B | Real and synthetic images, all augmented |
| A2 | Clean real + augmented real + synthetic, in each batch |

All arms use the same batch size, step budget (49 steps per epoch, up to 30 epochs), architecture and early-stopping rule. Each arm gets its own learning-rate and dropout tuning, A0 included.

## Evidence and what it can show

The test split was read in iteration 1, and its per-class numbers shaped this plan. A second read is therefore **weaker evidence** than a first read and is labelled as such.

The fresh holdout is the cleaner check. `configs/splits/fresh_holdout.csv` holds 4,500 images covering all 10 classes, drawn from raw files that never entered the catalog, with the same standardization, and with anything within the catalog's near-duplicate threshold removed. Its limits: all of its images come from sources seen in training, and it has no Quick, Draw! sketches, because all 3,500 local Quick, Draw! drawings are already in the catalog. Its diamonds are renders only.

No model output on the holdout is looked at before Phase 6.

## Primary comparison

**A2 vs A0**, ensemble macro-F1, soft vote over 5 seeds. On the reused test split, A2 passes only if all of these hold, the same locked thresholds as iteration 1:

1. Macro-F1 gain of at least 1.0 point.
2. 95% paired bootstrap CI excluding 0.
3. No harmful class (a drop above max(2 points, the class noise band) with a CI excluding 0).

The same comparison is reported on the fresh holdout, as the cleaner check.

## Secondary comparisons (Holm-corrected)

- Tuned A1 vs A0
- Tuned B vs A0
- A2 vs tuned B

Also reported: the Hand-Drawn hold-out runs for all four arms with 3 seeds each, scored on Hand-Drawn triangle and rectangle.

## Seeds

The final retrain uses seeds 0, 1, 2, 3, 4 for every arm. Tuning uses the seeds listed below.

## Search (validation only)

Fixed search seed 20261109. Each trial uses the unchanged step budget. Budgets are upper limits.

1. **Ablation on A1**, three seeds each, starting from the iteration 1 settings: rotation range 0, ±15, ±45, ±90, ±180; then scale jitter off, translation off, noise off, blur off, and shear with non-uniform scale off.
2. **Random search over augmentation on A1**, 24 trials, one seed:
   rotation range from {0, 5, 10, 15, 20, 30, 45, 90, 180}; scale minimum 0.75 to 1.0, maximum up to 1.1; non-uniform scale 0 to 0.2; shear 0 to 20°; translation 0 to 6 px; noise and blur probability 0 to 0.5; rotation cap for square, rectangle and diamond from {none, 0, 5, 10, 15, 30}.
3. **Generator search on B**, 16 trials, one seed:
   synthetic share 0.1 to 0.5; radius ranges; centre jitter 0 to 8 px; vertex jitter 0 to 2 px; ellipse and rectangle largest ratio 1.5 to 4; diamond and star ranges inside their current limits. Ambiguity margins are never reduced.
4. **A2 batch-share search**, 12 trials, one seed: clean share 0.1 to 0.6, synthetic share 0.1 to 0.4, with their total at most 0.8.
5. **Learning-rate and dropout grid** (3 x 2) for each of A0, A1, B and A2, on that arm's best setting so far.
6. **Confirmation:** each arm's top 5 settings are re-run on seeds 0, 1 and 2, and the setting with the highest mean validation macro-F1 is frozen.

Selection is by validation macro-F1 only. The final report states how many trials each arm received.

## What would count as a change

After this file is committed, the primary comparison, thresholds, search spaces and budgets do not change. Any change is recorded as a deviation with its reason. Nothing is changed after a test read.
