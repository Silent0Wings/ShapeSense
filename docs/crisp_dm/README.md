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
| Iteration 3 | Open, Phase 4 of 9: 108 validation experiments are running |
| Iteration 3 results | None yet. Every statement about them below is a hypothesis |
| Sealed data | No sealed set has been read in iteration 3 |
| Git | Branch `iteration-3`, local only, nothing pushed |

## What is next, in order

1. **Finish iteration 3.** Write up the experiments, tune, retrain, evaluate once on sealed data, then report and close out..
2. **Add "All models vote".** An equal-weight average of the exported models' class probabilities, with no retraining and no claimed score..
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
| Data Preparation | Validation-only tests are running on whether re-framing and binarising alone cause errors, and on each transform alone |
| Modeling | Added arm P, grouped cross-validation in the search, and equal-real, real-fraction and training-length options. Experiments are running |
| Evaluation | Repaired before any result: bootstrap on near-duplicate groups, exact McNemar under 25 discordant pairs, corrected harm rule, Holm on one metric, real read accounting, checked caches |
| Deployment | Not started. Planned after evaluation: iteration 3 report section, dashboard pages and re-export |

Two of the 27 outside-review points stay open until the experiments finish: unequal real images per step, and BatchNorm statistics in B and A2.

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

## Failures in iteration 3 so far

Listed in full in the log and on the dashboard's Failure timeline.

| Failure | Handling | State |
|---|---|---|
| A time limit killed the second holdout build and left a partial folder | Deleted it and rebuilt with no limit | Overcome |
| The first experiment launch crashed while the training code was being edited | Relaunched with no edits during start-up | Overcome |
| The experiment run hung silently after 6 of 108 trials, found about 2 hours later | Relaunched, reusing finished trials, and added the 5-minute watcher | Partly: the cause is not known |

## Decisions still open

For the user:

- Which dashboard readability improvements to build.
- Whether to push.

For the team:

- The project license, which Stage 7 also requires.
- Whether orientation is part of each class's definition.
- The Phase 2 rubric and deadline, `CODEOWNERS` and the six student IDs.
- The raw-archive hash check on a second machine and the 60-drawing live check.
