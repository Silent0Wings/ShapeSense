# ShapeSense CRISP-DM record

Where the project stands, what each trip round the CRISP-DM cycle found, and every decision that set the direction. Last updated 2026-11-09.

Detailed evidence is in [`iteration_log.json`](iteration_log.json), which feeds the dashboard. If this page and the log disagree, the log wins. Closed iterations are never rewritten.

## The project in brief

ShapeSense trains a small CNN to name ten 2D shapes from a 64×64 drawing. The research question began as "does adding generated (synthetic) shapes to training help?" After two negative results it became "which training mix survives damaged images, and when does synthetic data help?"

| Arm | Training data | Since |
|---|---|---|
| A0 | Real images only | Iteration 1 |
| A1 | Real images with class-safe augmentation | Iteration 1 |
| B | Real and synthetic images in each batch, all augmented | Iteration 1 |
| A2 | Clean real, augmented real and synthetic images in each batch | Iteration 2 |
| P | Pretrained on synthetic images, then fine-tuned on real images | Iteration 3 |

## Current position

| Item | State |
|---|---|
| Iteration 1 | Closed. Verdict: fail |
| Iteration 2 | Closed. Verdict: fail on both evaluation sets |
| Iteration 3 | Closed. A clean-clone rehearsal reproduced the results |
| Iteration 3 verdict | **Pass.** A2 vs A0 on damaged images: +9.20 macro-F1 points, 95% CI [8.89, 9.53], no harmed class |
| Sealed data | Read once per model in Phase 7: 92 reads of 92 expected |
| Git | Branch `iteration-3`, local only, nothing pushed |

## What is next, in order

1. **Iteration 3 is finished.** The handoff is in `ignore/handoff_iteration3.md`.
2. **"All models vote" is built.** An equal-weight average of the exported models' class probabilities, with no retraining and no claimed score. Equal weights beat per-class weights on held-apart validation, 95.59 against 94.80..
3. **Publish a frozen dashboard, if earned.** Stage 7 builds a static Vercel site with live ONNX models, only after all four gates in [`stages/stage_7.md`](../../stages/stage_7.md) are met, including written user approval.

## Iteration 1: does synthetic data help?

Primary test: B vs A1. **Fail: -0.36 macro-F1 points, 95% CI [-1.17, 0.41].**

| CRISP-DM step | What happened |
|---|---|
| Business Understanding | Locked success rule: a gain of at least 1 point, a CI excluding 0, and no harmed class |
| Data Understanding | Most Quick, Draw! diamonds were gems, cones, shields or scribbles, not rhombi |
| Data Preparation | Excluded those 500 drawings by rule before any test read. The split became 12,405 / 2,819 / 2,776 |
| Modeling | Four-block CNN, three seeds per arm. Augmentation and generator ranges were set by hand, and only A1 was tuned |
| Evaluation | Test macro-F1: A0 93.88, A1 90.86, B 90.50. The arm with no augmentation scored highest |
| Deployment | ONNX bundle and draw-and-predict demo |

## Iteration 2: why did augmentation lose?

Primary test: A2 vs A0. **Fail on both sets:** +0.06 points, CI [-0.69, 0.83] on the reused test split, and +0.08, CI [-0.41, 0.57] on a fresh 4,500-image holdout.

| CRISP-DM step | What happened |
|---|---|
| Business Understanding | Asked whether this augmentation design suits these classes at all |
| Data Understanding | Orientation carries class information in some sources. Images also reveal their source (91.7% against 46.7% for always guessing the largest source) |
| Data Preparation | Rotation cut from ±180° to ±20°, capped at ±10° for square, rectangle and diamond. Fixed shape framing, broken thin strokes and synthetic stroke width. Ranges searched on validation |
| Modeling | Added A2. Tuned every arm on validation (166 trials). Five seeds per arm |
| Evaluation | Every arm reached about the same test score: A0 95.3, A1 95.2, B 95.3, A2 95.4. On unseen Hand-Drawn triangles and rectangles, accuracy was A0 66.6, A1 74.5, B 72.6, A2 73.8 |
| Deployment | Exported A2_2, chosen by validation macro-F1. The studio serves all four arms |

## Iteration 3: robustness and scarcity

Pre-registered in [`iteration_3/preregistration.md`](iteration_3/preregistration.md). Primary test: A2 vs A0, averaged over 23 damage levels on fresh holdout 2, a sealed set of 4,500 images that has never been read.

The pass rule: a gain of at least 1.0 macro-F1 point, a 95% CI excluding 0, and no harmed class.

| CRISP-DM step | State |
|---|---|
| Business Understanding | The question moved to survival under damage. Hypotheses, not results: A0 is weakest under damage, A1 better, A2 best. B helps most when real data is scarce. Synthetic pretraining recovers any domain gap |
| Data Understanding | Built fresh holdout 2, after first reproducing the earlier holdout's manifest so its images could be excluded unopened |
| Data Preparation | Re-framing and binarising alone costs 0.3 to 1.1 points for the arms trained on it, so it is not the main source of errors. The transforms work together: all on scored 77.7 under damage, and no single transform passed 70.1 |
| Modeling | Added arm P, grouped cross-validation in the search, and equal-real, real-fraction and training-length options. The 108 experiments are done, and every arm moves to 60 epochs with no early stopping |
| Evaluation | Repaired before any result: bootstrap on near-duplicate groups, exact McNemar under 25 discordant pairs, corrected harm rule, Holm on one metric, real read accounting, checked caches |
| Deployment | Done. Exported all five arms, shipped A2_0 by the validation selection rule, added report Section L, the dashboard's sealed results and the All models vote. The public site, Stage 7, has not started |

### The sealed result

**Pass.** Full mix (A2) against Real only (A0), averaged over 23 damage levels of fresh holdout 2, which had never been read: **+9.20 macro-F1 points, 95% CI [8.89, 9.53], no harmed class.** It also passes the stricter reading, where the interval's lower bound must clear the 1-point target. The interval clustered by source, which is coarse with three sources, is [3.89, 9.42].

| Arm | Damaged macro-F1 | Clean macro-F1 |
|---|---|---|
| Real only (A0) | 75.6 | 97.8 |
| Real + augmented (A1) | 82.6 | 98.3 |
| Real + synthetic (B) | 83.2 | 98.0 |
| Full mix (A2) | 84.8 | 98.5 |
| Synthetic pretraining (P) | 84.3 | 98.0 |

| Hypothesis | Sealed answer |
|---|---|
| A0 is weakest on rotated and noisy data | Yes, by a wide margin |
| A1 improves robustness | Yes, +6.98 points over A0 |
| A2 is best overall | Yes on damaged images (+2.22 over A1, +1.68 over B), though A2 vs A1 did not have the same sign on every seed. P is close behind A2, reported descriptively |

Clean images still separate the arms only slightly: A2 vs A0 is +0.64, CI [0.19, 1.07]. The earlier evaluation sets, which had already been read, show no pass: the reused test split is +0.52, CI [-0.24, 1.22], and the first fresh holdout is +0.54, CI [0.10, 0.99]. The gain is in surviving damage, not in clean accuracy. Fresh holdout 2 uses sources seen in training, so this does not test new sources.

### What the validation experiments found

Three seeds, on validation images only. These answer the questions below, but none is a verdict, and only the sealed test in Phase 7 decides the pre-registered result.

| Question | Answer on validation |
|---|---|
| Is A0 weakest on damaged images? | Yes. Macro-F1 on damaged images was A0 66.3, A1 77.7, B 77.1, A2 80.3, P 75.6 |
| Does A1 improve robustness? | Yes, by 11.4 points over A0 |
| Is A2 best overall? | Highest on clean (95.2) and damaged (80.3) images, with all real images |
| Does B help most when real data is scarce? | Not beyond augmentation. At 10% of real images, A1 and B both scored 91.6, against 81.3 for A0 |
| Does synthetic pretraining recover a domain gap? | Partly. P was best at 10% and 25% of real images (92.6 and 93.5), but with all of them it matched B (94.3 and 94.2) and stayed below A2 (95.2) |
| Do equal real images per step help? | No. B fell 2.0 points and A2 fell 0.5 |
| Does BatchNorm recalibration help? | No. B fell 0.7 points and A2 fell 0.8 |
| Does re-framing alone cause errors? | Not much. It keeps shape proportions, and arms trained on it lost 0.3 to 1.1 points |
| Do validation and test differ in balance? | No. Class shares differ by 1.1% in total and source shares by 0.9% |

### Optimization stage (part of Modeling)

CRISP-DM has six standard steps, so Optimization is a named stage inside Modeling rather than a seventh step. A speed change is registered here once measurement shows it helped. Anything not built or not proven stays listed as a candidate.

| Version | Time per 60-epoch trial |
|---|---|
| Original, image preparation on one core | About 5 to 7.5 minutes effective, with two trials at once |
| First parallel version | About 3.7 minutes on average, between 2.6 and 5 |
| Latest optimized code | Median 92 to 184 seconds by phase, across the real search. Other programs were closed part way through, so part of this gain is a quieter machine |

The two reruns matched the earlier trials exactly, on every logged number across all 60 epochs.

| Step | Evidence | Result |
|---|---|---|
| Measured a training step | Preparing a batch took 226 to 376 ms, and the GPU step about 70 ms | Preparation was about 80% of the time |
| Built batches on 7 CPU processes, with one random generator per step | Scores were identical with 4 and 7 processes | An epoch fell from about 20 seconds to between 2 and 6 |
| Stopped each worker reloading PyTorch | Pool start-up had cost about 2 minutes a trial | Start-up cost is now only a few seconds |
| Replaced the worker pool | The old pool failed with an invalid-handle error on Windows | Workers start together, and a stalled batch raises an error |
| Trained one run at a time | Nested pools were the setup that had hung | The GPU is not shared between runs |
| Investigated the remaining slow epochs | The CPU was 99% busy in slow epochs and 90% in fast ones, with temperature unchanged | Windows Defender used about 2 cores, and other programs used several more |

Later optimizations, audited against measurements on 2026-11-09. Do not edit this code while a search runs, because workers reload it for every trial.

| Change | Measured size | State |
|---|---|---|
| Cache each stored image's ink points and thin-line flag | About 18% of the transform's time, from a profile | Applied |
| Keep one worker pool across trials | 16 seconds of about 220 per trial were outside the epochs | Applied |
| Send batches as 1 MB of bytes, with an exact GPU pixel lookup | Saves at most about 3 ms of a roughly 69 ms step | Applied |
| Stop syncing with the GPU on every step | Not measured separately | Applied |
| Cache validation images on the GPU | Conversion was 43 ms of a roughly 3.4 second epoch | Applied |
| Skip the training-curve plot for search trials | 0.57 seconds per trial | Applied |
| Reduce other CPU load on the machine | Slow epochs had the CPU at 99% | Defender exclusion added by the user |
| Mixed precision or relaxed determinism | Not measured | Not used, because they change results or repeatability |

All 27 outside-review points are now handled. The last two, unequal real images per step and BatchNorm statistics, were closed by these measurements.

## Decisions

### Evidence and evaluation

| Decision | Why |
|---|---|
| Earlier verdicts stand and are never revised | A later result cannot rewrite what was pre-registered and measured |
| Every choice uses train and validation only | Sealed data must stay clean evidence |
| Sealed sets are read once per final model, only by Stage 5, and the access log is never truncated | Each read weakens a set as evidence |
| A new iteration needs a new pre-registration and, for a clean claim, new sealed data | The test split and first holdout have already been read |
| Keep the fixed split. Use grouped 3-fold CV only inside the search, and never on sealed data | Averages out validation luck without touching sealed data |
| Group folds on near-duplicate groups, not on source | Ellipse, pentagon and diamond each come from one source |
| The outside review's re-frame test runs on validation, not test | The review proposed test, which would have broken the seal |
| Same seeds, step budget, architecture and search rules for every arm | The comparison must be fair |
| A negative result is a valid finish | The rule is never loosened to get a pass |

### Modeling

| Decision | Why |
|---|---|
| Arm P is reported descriptively, outside the corrected comparisons | Its value was unknown when the test was pre-registered |
| All arms move to a longer training budget only if each tested arm gains at least 0.5 points | One shared budget keeps arms comparable |
| Every arm trains for 60 epochs with no early stopping | That rule was met: A0 gained 1.99, A1 0.51 and A2 0.71 points |
| Batches are built by 7 CPU processes, one training run at a time, with one random generator per step | Image preparation was about 80% of each step. An epoch fell from about 20 seconds to between 2 and 6, and scores are identical at any process count |
| The 108 validation experiments are not retrained after that change | They measured the design questions. Their random image stream differs from later runs, which is recorded as a deviation |
| The final vote uses equal weights | Nothing to tune or overfit. Per-class weights rely on differences that are mostly noise |
| Per-class weights are adopted only if they win by at least 0.5 points on held-apart validation, and the user agrees | They have to earn the added complexity |
| "All models vote" claims no score | Proving it better needs a new pre-registered iteration |

### Process and record-keeping

| Decision | Why |
|---|---|
| Every failure and change is filed under its CRISP-DM step and shown in the dashboard with a visual | The project is judged on how failures were found and overcome |
| Each failure has its own dashboard page, naming its CRISP-DM step and pipeline stages | One place for each story |
| The user is the only author of every commit, and commits go through `.commit_guard/safe_commit.py` | Standing project rule |
| Nothing is pushed unless the user asks | Standing project rule |
| Long jobs run with a stall watcher, checked every 5 minutes | A hang cost over 2 hours because nothing was watching for one |
| Work runs without check-ins, inside each goal's written rules | User instruction |

### Deployment

| Decision | Why |
|---|---|
| The public site is a frozen, static copy in `deployment/` at the root | One fixed record that cannot drift |
| Models run in the visitor's browser | No server to run, and drawings stay on the device |
| The site is gated on a finished project, a Pass, a chosen license and written user approval | It must not publish a result that has not been earned |

## Failures in iteration 3

Listed in full in the log and on the dashboard's Failure timeline.

| Failure | Handling | State |
|---|---|---|
| A time limit killed the second holdout build and left a partial folder | Deleted it and rebuilt with no limit | Overcome |
| The first experiment launch crashed with an invalid-handle error in the worker pool | Relaunched, then later replaced that pool | Partly: first blamed on code edits, but it came back without them |
| The experiment run hung silently after 6 of 108 trials, found about 2 hours later | Relaunched, reusing finished trials, and added the 5-minute watcher | Partly: the cause is not known |
| Image preparation made training about five times slower than the GPU allowed | Batches are now built by 7 processes | Overcome |
| The search stopped at 66 of 191 trials with a GPU error | Confirmed the GPU worked and relaunched, reusing finished trials | Partly: the cause is not known |
| The first shared worker pool had five bugs | Found and fixed by a code audit before they caused harm | Overcome |
| GPU pixel conversion would have changed every result | Measured first, then used an exact lookup table | Overcome |
| The GPU looked idle in Task Manager during training | Confirmed with `nvidia-smi` that training was on the RTX 3080 | Overcome |
| Stage 6 could pass with a failed report check | A failed check now fails the stage | Overcome |
| Report macro names broke for A2 and collided for hold-out runs | Digits spelled out, and hold-out runs named separately | Overcome |
| Report Section K would have shown iteration 3 numbers | It now reads the frozen iteration 2 tables | Overcome |
| The dashboard listed arm P twice | Removed the duplicate | Overcome |
| The first vote comparison scored an absent class as zero | Halves balanced by class, and absent classes left out of the score | Overcome |

## Decisions still open

For the user:

- Which dashboard readability improvements to build.
- Whether to push.

For the team:

- The project license, which Stage 7 also requires.
- Whether orientation is part of each class's definition.
- The Phase 2 rubric and deadline, `CODEOWNERS` and the six student IDs.
- The raw-archive hash check on a second machine and the 60-drawing live check.
