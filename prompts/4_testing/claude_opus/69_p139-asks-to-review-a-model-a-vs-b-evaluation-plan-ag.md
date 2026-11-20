# 4_testing - P139: Asks to review a Model A vs B evaluation plan against the repo
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P139. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[

<pasted_content id="18fa">
Plan: Model A vs Model B evaluation
I've organized this around your Figure 2 stages. Note that your pipeline already has a stage the figure doesn't show: dedup-grouped splitting. The source facts below come from your report. I checked the Quick, Draw! and reevald dataset pages for format and licence details.

Phase 0: Freeze the data (done)
Stage 0.1: Real data pool (all installed sources)

Pool: Quick, Draw! (CC BY 4.0, 256×256 simplified vectors ), reevald (CC0, 224×224 RGB ), El Korchi, and Hand-Drawn. After standardization it holds 18,500 images at 64×64, single channel.

Treat the SQLite catalog as the single source of truth. Record a hash of the catalog and a fixed random seed.

Quick checks before splitting:

Per-class and per-source counts match Table 2.

Quick, Draw! diamond gemstones: decide whether to filter them now, because filtering later changes the test set.

Stage 0.2: Split (before any augmentation)

Do a 70/15/15 split by near-duplicate group (pHash). This gives 12,761 train, 2,890 val and 2,849 test.

Stratify by class and source where possible. The report should state each source's share of the test set.

Lock the test split. Nothing tunes against it, and it is touched only once at final evaluation.

Phase 1: Train split (real images)
Stage 1.1: Real-only training set

Training set = the 12,761 real train images only. Validation (2,890) is used for early stopping and hyperparameter choice.

Leakage test: assert that no image_id or pHash group appears in more than one split.

Pentagons (El Korchi only) and ellipses (Hand-Drawn only) each come from a single source. Report per-source accuracy so the model isn't just detecting the source.

Stage 1.2: Augmentation and synthetic generator (training only)

Augmentations: rotation, scale, shear, noise and blur (Albumentations). Shear and non-uniform scaling are disabled for circle, ellipse, square, rectangle and diamond.

Synthetic: Pillow ImageDraw renders shapes with randomized parameters, in the same 64×64 outline format. About 30% of each batch, generated on the fly and never stored.

Visual QA: dump 10 samples per class and check for label-changing artifacts. Examples: a slightly stretched square becoming a rectangle, or a near-round ellipse becoming a circle.

Keep class-ambiguity margins explicit. For example, ellipse axis ratio must be ≥ some threshold (e.g. 1.2), and diamond angles must stay clearly off 90°.

Phase 2: Train Model A and Model B
Stage 2.1: Model A (real only)

Baselines: scikit-learn (logistic regression or SVM on raw pixels or HOG features).

Main model: a small PyTorch CNN.

No augmentation and no synthetic data, so it is a clean control.

Stage 2.2: Model B (real + aug/synthetic)

Same architecture, optimizer, epochs, learning-rate schedule and seed as Model A. The only change is the data stream: 70% real, 30% synthetic, with augmentation.

Run 3–5 seeds for each model so you can report mean ± std rather than one lucky run.

There is a design decision to make. Your text says Model A is "real only" and the figure also says "+ Augmentation". Choose one:

Option 1: A has no augmentation. This is cleaner, but B's gain mixes augmentation and synthetic data.

Option 2: A gets augmentation of real images. B adds synthetic on top, which isolates the synthetic effect.

Best: run three arms (A0 raw, A1 real+aug, B real+aug+synthetic), which separates both effects.

Phase 3: Compare on the same held-out real test set
Stage 3.1: Evaluation protocol

Run the 2,849-image test set once per trained model, using the same preprocessing.

Metrics:

Accuracy and macro-F1.

Per-class F1.

Confusion matrices. The three ambiguous pairs are the key ones: square/diamond, square/rectangle and circle/ellipse.

Accuracy per source and per domain (render vs sketch).

Stage 3.2: Statistical comparison

McNemar's test on paired predictions for A vs B.

Bootstrap 95% confidence intervals for the accuracy difference.

Seed-level mean ± std.

Stage 3.3: Success criterion (decide in advance)

Example: B counts as better if macro-F1 improves by ≥ 1 point with a CI excluding 0, and no class drops by more than 2 points.

If it fails, follow your CRISP-DM loop back to Business Understanding. Likely fixes are adjusting the synthetic ratio, the generator or the label rules.

Phase 4: Analysis and deployment
Stage 4.1: Ablations (optional)

Synthetic ratio: 0%, 15%, 30%, 50%.

Per-augmentation removal.

Sketch-only test slice, to see whether synthetic data helps sketches more than renders.

Stage 4.2: Report and packaging

Include a results table, confusion matrices, error galleries and a limitations section. Limitations to cover: reevald's dashed-line hint, the Quick, Draw! gemstone diamonds, and the near-duplicate pentagon groups.

Export the best model (ONNX or TorchScript) with the standardize.py preprocessing bundled.

Timeline sketch
Phase	Output	Rough effort
Phase	Output	Rough effort
0 Freeze data	Locked splits, leakage assert	0.5 day
1 Generator + aug	Loader, synthetic renderer, QA sheet	2 days
2 Training	A and B, multi-seed	2 days
3 Comparison	Metrics, tests, figures	1–2 days
4 Report	Phase report, export	1–2 days
LaTeX-ready extension of Figure 2
Add one box labeled "Validation split (early stopping only)" between Train and the models. Add a "3 seeds" annotation on the Model A and Model B boxes. I can write the updated TikZ for it if you'd like.
</pasted_content id="18fa">

]

## Response

This plan mostly describes work the repo has already done. I have not changed anything. Below, I compare the plan with the repo in two parts. I checked each claim against the repo's pre-registration, taxonomy config, split and results files, and the iteration 2 report. Where I could not confirm a claim from a file, I say so.

##### Matches the repo
- **Three arms:** A0 (raw), A1 (real plus augmentation) and B (plus synthetic) are the repo's design. The plan's recommendation of three arms is the same. The pre-registration (`docs/crisp_dm/iteration_2/preregistration.md`) adds a fourth arm, A2 (clean real, augmented real and synthetic mixed in each batch), which is the primary comparison (A2 vs A0). All four arms share the batch size, step budget (49 steps per epoch, up to 30 epochs), architecture and early-stopping rule. Each arm gets its own learning-rate and dropout tuning, A0 included.
- **Splits:** a 70/15/15 split by near-duplicate group, with the test split locked and read only for final results. The repo also keeps a separate fresh holdout (`configs/splits/fresh_holdout.csv`, 4,500 images, all 10 classes), which the plan does not mention. The pre-registration says no output on it is looked at before Phase 6. Its limits are that all its images come from sources seen in training and it has no Quick, Draw! sketches.
- **Statistics:** McNemar's test (the `mcnemar_b` and `mcnemar_c` columns in `docs/crisp_dm/iteration_2/data/comparisons.csv`), bootstrap intervals (a paired bootstrap, per the pre-registration), Holm correction (the `p_holm` column, on the three secondary comparisons) and multiple seeds (seeds 0 to 4 for each arm in the final retrain, within the plan's 3 to 5) are all in use. The plan's reasoning holds: one run per arm would not show whether a gap is larger than seed noise.
- **Success criterion:** it was registered before tuning, in `docs/crisp_dm/iteration_2/preregistration.md`, written 2026-11-09 before any iteration 2 tuning. Its thresholds match the plan's example in kind: a macro-F1 gain of at least 1.0 point, a 95% paired bootstrap CI excluding 0, and no harmful class (a drop above max(2 points, the class noise band) with a CI excluding 0). The plan's example is written for B. The repo's primary comparison is A2 vs A0, so the plan's wording should be adjusted to match.
- **Ambiguity margins:** these are in `configs/taxonomy.yaml`: ellipse minimum axis ratio 1.2, rectangle minimum side ratio 1.2, and diamond angle at least 10 degrees off 90. Shear and non-uniform scaling are disabled for the same five classes the plan lists (circle, ellipse, square, rectangle, diamond). This matters because a sheared square can turn into a rectangle, and the config blocks that.

##### Differs from the repo
- **Split numbers:** the plan's 12,761 / 2,890 / 2,849 sum to 18,500, the pool before the removal. The repo's current split is 12,405 / 2,819 / 2,776, which sums to 18,000. The difference is the 500 Quick, Draw! diamonds excluded by rule, after which the split was re-frozen (`docs/crisp_dm/iteration_2/report/changes.tex`). `docs/crisp_dm/iteration_2/data/power.csv` confirms n_val 2,819 and n_test 2,776. The plan's numbers are out of date, and the report should use the current split so it does not disagree with the data.
- **Diamond filter:** the plan lists this as a decision still to be made. `changes.tex` and `docs/crisp_dm/iteration_log.json` record the exclusion as applied. The earlier answer dated the decision 2026-11-08. I did not confirm that date in the files I read, so it is unconfirmed. Either way, the filter is applied and the decision is closed, so the plan should not leave it open.
- **Synthetic share:** the plan says about 30% of each batch. The repo's configured shares are 27.8% for B and 19.8% for A2. The report (`changes.tex`) says the realised batches hold 71 and 51 of 256 images, or 27.7% and 19.9%. The gap is rounding, and the configured values are the ones to quote.
- **Per-source results:** the plan asks for per-source accuracy for pentagons and ellipses. The repo reports accuracy by source (Hand-Drawn, reevald, El Korchi and Quick, Draw!) and by domain (render vs sketch) for all four arms in `docs/crisp_dm/iteration_2/data/per_source.csv`, on the test split (451, 750, 1,122 and 453 images by source). Per-source test accuracy ranges from 88.9 to 92.0 percent on Hand-Drawn and from 99.6 to 100.0 percent on El Korchi, which is where the pentagons come from. The plan says ellipses come only from Hand-Drawn. I did not verify that against the taxonomy or the data files. Per-class pentagon and ellipse numbers are in `docs/crisp_dm/iteration_2/data/per_class.csv`, which I did not check.
- **Unseen-source results:** the same CSV has leave-one-source-out runs for Hand-Drawn (302 images held out per run). Accuracy there ranges from 58.3 to 80.5 percent across arms and runs, which is well below the seen-source numbers. The plan does not mention this, and the report's limitations section should.

##### Suggested next step
If the plan goes into the Phase 1 report, update the numbers to the current split and mark the diamond filter as applied. Use the four-arm design (A0, A1, B, A2) and the pre-registered success criterion, so the report matches the pre-registration. That way the report does not contradict the data.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
