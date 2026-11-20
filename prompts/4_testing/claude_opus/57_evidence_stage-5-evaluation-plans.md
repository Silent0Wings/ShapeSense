# 4_testing - Stage 5 plan: evaluation and statistics

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-08
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner brief for Stage 5 (evaluation and statistics) and one implementation plan each for the statistics and the evaluation run.

## Response (saved output, verbatim)

### `stages/stage_5.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 5 — Evaluation and statistics

> Owner brief. Everything here is about Stage 5 only. The full project
> plan is `../implementation.md`; shared rules live there under
> *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 5` · **Code folder:** `src/stage5_eval/`
- **Depends on:** Stage 4 (trained models) and Stage 1 (locked test split)
- **Blocks:** Stage 6 results tables
- **Effort:** 1–1.5 days

## Focus

Open the locked test set **once per trained model**, measure every
model the same way, and deliver a **verdict** on the success criterion
— with confidence intervals, not just a single number. Stage 5 is the
only stage allowed to read the test split; its job is to be the honest
referee.

## Goals

1. Compute metrics for every arm × seed and both baselines on the test
   split.
2. Answer three paired questions:
   - A0 vs A1 → does augmentation help?
   - A1 vs B → does synthetic data help? (**the main question**)
   - A0 vs B → the report's original Model A vs Model B question
3. Attach statistical evidence: McNemar's test and bootstrap 95% CIs.
4. Apply the success criterion, which was locked before any results.

## Out of scope

- Retraining or retuning models (go back to Stage 4 only via a failed
  verdict and a new CRISP-DM loop, never by peeking).
- Writing the report text (Stage 6) — you produce tables and figures.

## Inputs

| Input | Where |
|---|---|
| Trained models | `artifacts/stage4/<arm>_<seed>/model.pt` |
| Baselines | `artifacts/stage4/baselines/` |
| Validation softmax probabilities | `artifacts/stage4/<arm>_<seed>/val_probs.npz` |
| Test split | `common.load_split("test")` — allowed only here |
| Success criterion and aggregation rules | `configs/pipeline.yaml#criterion`; plan Decisions 9–10 |
| Per-class test counts and noise bands | `artifacts/stage1/split_stats.csv` |
| Source-shortcut flag | `artifacts/stage1/source_classifier.json` |

## Requirements

**Must**
- R1. The test split is read **once per evaluated model** — one read per
  trained seed model plus one per baseline, so exactly `len(runs) + 2`
  lines carry this run's `run_id` in `artifacts/test_access.log`. Cache
  predictions and softmax probabilities so ensembles never require
  another read. Copy the per-run count into
  `status.json → checks.test_reads`; `artifacts/` is gitignored, so that
  field is how the guarantee reaches a reader who never saw the machine.
- R2. Metrics per seed model, per arm ensemble and per baseline:
  accuracy, macro-F1, per-class F1, confusion matrix; accuracy per
  source and per domain (render vs sketch). Baselines are context, not
  part of the primary hypothesis, but they are measured on the same data
  so the report can put them in the same table.
- R3. Confusion pairs reported explicitly: square/diamond,
  square/rectangle, circle/ellipse.
- R4. **Primary hypothesis:** B vs A1 macro-F1, α = 0.05. Combine each
  arm's seeds by averaging softmax probabilities (soft vote), producing
  one prediction per test image per arm.
- R5. Give the primary ensemble macro-F1 difference a paired bootstrap
  95% CI. Run McNemar's test on paired correctness as a supporting
  accuracy comparison, not as a macro-F1 test. Report per-seed mean ± std
  and paired per-seed differences separately; never pool duplicate test
  images.
- R6. Secondary A0 vs A1 and A0 vs B comparisons apply Holm correction
  to their two McNemar p-values, with macro-F1 CIs reported alongside.
  Per-class/per-source results are descriptive.
- R7. Locked criterion: **B passes if ensemble macro-F1 improves by at
  least 1 point with a CI excluding 0, and no class has both an F1 drop
  above its own threshold and a paired bootstrap CI for that drop
  excluding 0.** The per-class threshold is
  `max(2.0, noise_band_c)` read from `artifacts/stage1/split_stats.csv`
  — classes are **not** equally sized, and a flat 2-point rule sits
  inside the noise for the smallest ones. A drop inside the band is
  reported but does not fail.
- R8. **Before any test prediction**, run the power check: the same
  paired bootstrap on A1's and B's *validation* probabilities, rescaled
  by `sqrt(n_val / n_test)` (≈ 1.01, since the two splits are nearly the
  same size). If the expected half-width exceeds 1 point, disclose the
  limited power without changing the criterion. Do **not** use Stage 4's
  seed disagreement for this — the primary CI resamples test images
  between two ensembles, which seed spread does not estimate.
- R8b. Render the error galleries: misclassified test images for the
  three key confusion pairs. Stage 6 may not read test images, so if you
  do not produce these, the report cannot show a single misclassified
  example.
- R9. The verdict goes in `status.json → metrics.verdict`. A verdict of
  `fail` still means the *stage* `passed`.
- R10. If Stage 1's source-shortcut trigger fired, per-source tables are
  mandatory and the leave-one-source-out models are evaluated on
  Hand-Drawn only, labelled as unseen-source generalization.

**Should**
- Flag pentagon (El Korchi-only) and ellipse (Hand-Drawn-only) results
  with an asterisk if Stage 1's source classifier found a shortcut.
- Secondary finding: if A1 already closes most of the A0 → B gap, say
  that the generator adds little.

## Deliverables (`artifacts/stage5/`)

- `predictions/<arm>_<seed>.npz`, `predictions/baseline_<name>.npz` and
  the ensemble predictions
- `tables/metrics.csv` and `tables/metrics.tex` (overwriting Stage 0's
  placeholder, so the report picks up real numbers with no edit)
- `tables/comparisons.csv` (difference, CI, corrected/raw p as applicable)
- `figures/confusion_<arm>.png`, `figures/errors_<pair>.png`
- `power_check.json`
- `status.json` with `verdict`, `checks.test_reads`, key numbers

## Done when

- [ ] The power check ran **before** the first test read and is recorded.
- [ ] Verdict delivered with CIs and the power limitation stated.
- [ ] `test_access.log` shows exactly `len(runs) + 2` lines for this
      `run_id`, and the count is echoed in `status.json`.
- [ ] Class-drop thresholds came from `split_stats.csv`, not a literal.
- [ ] Primary/secondary tests and per-seed robustness results are separate.
- [ ] Error galleries exist for the three key confusion pairs.
- [ ] Required source-generalization results exist if the trigger fired.
- [ ] Tables exist in CSV and LaTeX form for Stage 6.

## Interfaces you provide

Tables and figures in `artifacts/stage5/` — Stage 6 reads them directly and
never retypes numbers.

## Pitfalls

- **Comparing unpaired runs** (A1 seed 1 vs B seed 3) — breaks McNemar's
  assumptions.
- **Reporting accuracy only** — with unequal classes, macro-F1 shows
  whether rare classes were sacrificed.
- **"Significant" ≠ "meets criterion"** — p < 0.05 with a +0.4 point gain
  still fails the ≥ 1 point rule.
- **Evaluating twice "just to check"** — every extra look weakens the
  honesty of the test set; the access log will show it.
- **Changing the criterion after seeing results** — the criterion is
  locked; report a near-miss as a near-miss.

## Glossary

- **Held-out test set**: data never used for training or tuning.
  Example: the test images frozen in Stage 1. (The count is whatever
  Stage 1 published — the Phase 1 figure of 2,849 predates the gemstone
  filter and the global pHash regrouping.)
- **Noise band**: the F1 movement a class shows from sampling alone,
  `100 × sqrt(0.9 × 0.1 / n)` points. Example: ellipse has n = 150, so
  2.4 points — a 2-point "drop" there is not evidence of anything.
- **Macro-F1**: the plain average of per-class F1 scores, so each class
  counts equally. Example: F1s of 0.80, 0.84, 0.95 → macro-F1 0.865.
- **Confusion matrix**: a table of true class (rows) vs predicted class
  (columns). Example: row *square*, column *diamond* = 12 squares
  misread as diamonds.
- **Paired comparison**: comparing two models on the same test images,
  image by image. Example: A1 right / B wrong on image 517.
- **McNemar's test**: tests whether two models' disagreements are
  lopsided, using only the images where they differ. Example: b = 30,
  c = 50 → χ² = 4.51, p ≈ 0.034.
- **Bootstrap confidence interval**: resample the test set with
  replacement many times and read the 2.5th–97.5th percentile of the
  statistic. Example: Δ macro-F1 = +1.8, 95% CI [+0.6, +3.0].
- **Success criterion**: the pass/fail rule fixed before results exist.
  Example: R7 above.

## Missions

### M1 Read a confusion matrix (recognition)
Prompt: rows are true classes, columns are predictions. Compute accuracy,
per-class F1 and macro-F1.

```
              pred square  pred diamond  pred rectangle
true square        8            1              1
true diamond       2            8              0
true rectangle     0            0             10
```
Expected outcome: accuracy 26/30 = 0.867. F1: square 0.80, diamond
≈ 0.84, rectangle ≈ 0.95. Macro-F1 ≈ 0.865. The weakest pair is
square ↔ diamond.

### M2 McNemar on paired predictions (application)
Prompt: given per-image correctness of A1 and B, run McNemar's test.

```python
import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

a1_ok = (pred_a1 == y_true)
b_ok  = (pred_b  == y_true)
table = [[np.sum(a1_ok & b_ok),  np.sum(a1_ok & ~b_ok)],
         [np.sum(~a1_ok & b_ok), np.sum(~a1_ok & ~b_ok)]]
res = mcnemar(table, exact=False, correction=True)
```
Expected outcome: with 30 images "A1 right, B wrong" and 50 "A1 wrong,
B right", the statistic is (|30−50|−1)²/80 = 4.51 and p ≈ 0.034.
Explain in one sentence why the 2,700 images both got right don't
matter.

### M3 Deliver the verdict (synthesis)
Prompt: combine soft-vote ensembles, a paired bootstrap and the locked
criterion into one function that returns `pass` or `fail` with reasons.
`probs_a1` and `probs_b` have shape `(n_seeds, n_images, 10)`.

```python
def verdict(y, probs_a1, probs_b, thresholds, n_boot=2000,
            rng=np.random.default_rng(0)):
    """thresholds: per-class max(0.02, noise_band_c) from split_stats.csv."""
    pa1, pb = probs_a1.mean(axis=0), probs_b.mean(axis=0)  # soft vote
    pred_a1, pred_b = pa1.argmax(axis=1), pb.argmax(axis=1)
    n = len(y)
    diffs, drops = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)                  # same images for both models
        fa1, fb = per_class_f1(y[idx], pred_a1[idx]), per_class_f1(y[idx], pred_b[idx])
        diffs.append(fb.mean() - fa1.mean())
        drops.append(fa1 - fb)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    delta = macro_f1(y, pred_b) - macro_f1(y, pred_a1)
    observed_drop = per_class_f1(y, pred_a1) - per_class_f1(y, pred_b)
    drop_lo = np.percentile(drops, 2.5, axis=0)
    harmful_drop = (observed_drop > thresholds) & (drop_lo > 0)   # per class
    ok = delta >= 0.01 and lo > 0 and not harmful_drop.any()
    return {"verdict": "pass" if ok else "fail", "delta": delta,
            "ci": [lo, hi], "harmful_classes": np.flatnonzero(harmful_drop).tolist()}
```
Expected outcome: a dict like `{"verdict": "fail", "delta": 0.006,
"ci": [-0.004, 0.016], ...}` written to `status.json`, with the reason
readable from the numbers (here: gain below 1 point and CI includes 0).
A 3-point drop on ellipse whose CI includes 0 is reported but does not
fail the criterion; neither does a 2.2-point drop on ellipse, whose own
threshold is 2.4. Swap the per-class `thresholds` array for a flat 0.02
and watch the small classes start failing on noise — that is the bug
this argument exists to prevent.

When you finish M3, run `quiz-topic` on "paired model evaluation".
````

### `29_s5_statistics.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E29 evidence line

# Plan 29: S5 pure metrics + statistics + verdict

**Stage:** `stages/stage_5.md` R2 (metric functions), R4–R7, Missions M1–M3 · **Plan refs:** `implementation.md` Decisions 9, 10
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E29) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Stage 5 needs correct, tested statistics before the test set is opened.

## 2. Root Cause & Investigation
No metrics code exists.

## 3. Architecture & Modular Design Strategy
Pure NumPy (+ statsmodels McNemar): `confusion`, `per_class_f1`, `macro_f1`, `accuracy`, `soft_vote`, `paired_bootstrap`, `mcnemar_test`, `holm`, `verdict(...)`. All F1 values in **points** (×100) at the API boundary; thresholds from `split_stats.csv`.

## 4. Proposed Changes by File
- `src/stage5_eval/metrics.py`, `stats.py`, `criterion.py`.
- `tests/stage5/test_metrics.py`, `test_stats.py`, `test_criterion.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: M1 values; McNemar M2 (χ² 4.51, p ≈ 0.034); Holm known values; bootstrap uses identical indices for both models; verdict: small gain fails, drop inside band does not fail, flat 2-point threshold fails a small class on noise (M3), pass case.
- **Break verification**: unpaired bootstrap → paired-indices test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- The M3 sketch mixes fractions and points; this module uses points consistently.
````

### `30_s5_evaluation_run.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 30: S5 power check, test evaluation, tables, figures, galleries

**Stage:** `stages/stage_5.md` R1–R3, R8–R10, R8b, Should 1–2, Done-when D1–D8 · **Plan refs:** `implementation.md` Decisions 9, 10, 12, 14
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E30) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The only stage allowed to read the test split; exactly `len(runs) + 2` reads per run_id.

## 2. Root Cause & Investigation
Depends on E28 artifacts and E29 functions.

## 3. Architecture & Modular Design Strategy
`run(config)`: power check on validation probabilities **before** any test read; one `load_split('test')` per model in `runs` and per baseline, predictions cached; ensembles from cache; metrics per seed/ensemble/baseline incl. per-source/per-domain; primary + Holm secondaries; verdict; CSV + LaTeX tables; confusion figures; galleries for the three pairs; LOSO on Hand-Drawn if triggered; `checks.test_reads` from the log.

## 4. Proposed Changes by File
- `src/stage5_eval/power.py`, `evaluate.py`, `tables.py`, `figures.py`, `run.py`.
- `tests/stage5/test_power.py`, `tests/stage5/test_tables.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_rescale_factor`, `::test_power_check_before_test_read` (fake loader ordering); `::test_csv_and_tex_match`.
- **Pipeline**: `--stages 5`; access-log count == len(runs)+2.
- **Figure review**: confusion matrices and galleries opened with `Read`.
- **Break verification**: re-read test inside the ensemble step → read-count assertion fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Stage 6 may not read test images, so galleries are rendered here.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Status lines record 'verified in tree' or 'evidence in ignore/todo.md' (E29, E30).

## Our decision

Bootstrap CIs, McNemar tests with Holm correction, and one pre-registered primary comparison.

## Measured effect

Produced the iteration 1 verdict: B vs A1 -0.36 macro F1, CI [-1.17, 0.41] (F04).

---

## Upgraded & Expanded Analysis: Stage 5 Statistical Evaluation Architecture (`E29`, `E30`, `E31`)

### Decomposition of Stage 5 into Three Verification Modules

Stage 5 (`stages/stage_5.md` and modular plans `29_s5_inference.md`, `30_s5_stats.md`, `31_s5_verdict_outputs.md`) implements the single authorized read path for sealed evaluation splits:

| Plan ID | Target Modules | Statistical & Leakage-Prevention Contract |
|---|---|---|
| **`E29` (`29_s5_inference.md`)** | `src/stage5_eval/evaluate.py` | Executes the pre-test validation power check (`power_check.json`, rescaled by $\sqrt{n_{\text{val}}/n_{\text{test}}} \approx 1.01$ with `0` test reads), then scores each trained seed model and baseline **exactly once** on the sealed split (`len(runs) + 2` reads), caching softmax probabilities to form 5-seed soft-vote ensembles (`D01`) without re-reading test images. |
| **`E30` (`30_s5_stats.md`)** | `src/stage5_eval/stats.py` | Computes paired bootstrap 95% confidence intervals on macro-F1 and per-class F1 alongside exact McNemar accuracy tests and Holm step-down multiplicity correction across secondary comparisons (upgraded in Iteration 3 to `phash_group` cluster resampling `C20` and C-contiguous combined 23-level matrix products `C36`). |
| **`E31` (`31_s5_verdict_outputs.md`)** | `src/stage5_eval/{criterion,run}.py` | Applies the pre-registered decision gate ($\Delta \ge +1.0$ macro-F1, 95% CI excluding $0$, and zero classes failing the noise-aware / Bonferroni-corrected harm floor `C21`) and renders confusion matrices and error galleries so Stage 6 never touches test images. |

