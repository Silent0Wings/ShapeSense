# 4_testing - F04: B vs A1 failed: -0.36 points, CI [-1.17, 0.41], and A0 with no augmentation scored highest. ()
[49_real_was-the-evaluation-a-failure.md](49_real_was-the-evaluation-a-failure.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/01_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md](../gemini_4_neon/01_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md)
- Date: 2026-11-09
- Worksheet entry: F04 (`failure`, `4_testing`)
- Owner / Proposed by: all members / all members
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `ShapeSense/docs/crisp_dm/iteration_1/data/stage5_status.json`, `ShapeSense/docs/crisp_dm/iteration_1/data/comparisons.csv`, `ShapeSense/docs/crisp_dm/iteration_1/data/per_class.csv`, `ShapeSense/docs/crisp_dm/iteration_2/investigation/report.md`, `ShapeSense/docs/crisp_dm/iteration_log.json`, commit `d5c6e2d`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/iteration2.html`
- Follow-up: [`../gemini_4_neon/01_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md`](../gemini_4_neon/01_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md)



## Prompt ()

> **User:** Our pre-registered test `B` vs `A1` failed (-0.36 macro-F1 points, 95% CI [-1.17, 0.41]) and `A0` with no augmentation scored highest (93.88 vs `A1` 90.86 and `B` 90.50). Without touching the test split again, how should we investigate why augmentation and synthetic data did not help - and why can synthetic or heavy augmentation lose to no augmentation at all?

## Response ()

> **Opus 5.5:** Keep the Iteration 1 verdict locked as `fail` and move every diagnostic step strictly onto training and validation (`2,819` images). Do not re-tune against the test split, and do not launch a multi-day brute-force sweep before you know whether the loss came from data transforms or training settings.
>
> Your numbers split cleanly into two separate questions: why `A1` and `B` trailed `A0` by ~3 points (`A1 vs A0` -3.03, `B vs A0` -3.38), and why `B` trailed `A1` (-0.36). In the literature and in your per-class breakdown (`rectangle` 93.3 to 80.2, `diamond` 99.0 to 86.0, `square` 97.6 to 90.3), three mechanisms explain this pattern:
>
> - **Label-destroying or shortcut-breaking rotation:** `±180°` rotation erases source orientation cues that `kaggle_reevald` and `quickdraw` carry on clean splits, and a square rotated 45° mimics a diamond.
> - **Transform and synthetic-fidelity defects:** Warping can shrink shapes or fragment `1-px` strokes, while a synthetic-to-real stroke-width mismatch hurts `B` when synthetic images replace real ones in each batch.
> - **Zero clean real images and budget:** `A1` and `B` saw no unaugmented real images during training and ran under a 30-epoch cap, which penalizes harder augmented streams relative to `A0` memorizing clean styles.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Targeted validation probes (~16 runs) + transform inspection | Isolates rotation range, framing size, stroke breaks, budget, and label integrity in hours without touching test | **Use this first** to pinpoint defects before pre-registering Iteration 2 |
> | Upfront per-arm sweep across hundreds of runs | Burns ~2 days of GPU compute while baking in any transform bugs | Defer tuning until transform defects are ruled out or fixed |
> | Re-evaluate candidate fixes on the Iteration 1 test split | Leaks test information and invalidates the locked comparison | Never do this; keep Iteration 1 frozen and pre-register a new test |
>
> Run targeted validation ablations first: test `A1` with rotation off and `±15°`, measure bounding-box sizes and thin-line fragmentation, check `A0` vs `A1`/`B` under held-out `github_handdrawn` (LOSO) and rotated validation, and check 60 epochs vs 30. Only after fixing any transform defects should you tune per arm and introduce a clean + augmented + synthetic arm (`A2`) in Iteration 2.

## Why this reading fits

Team members split after Iteration 1 between blaming the data pipeline and blaming training hyperparameters, while Gemini 4 Neon proposed a ~2-day per-arm search over hundreds of models. Opus 5.5's mediated approach matches what actually unlocked Iteration 2 in `docs/crisp_dm/iteration_2/investigation/report.md` and commit `d5c6e2d`: 16 fast validation-only trainings and targeted measurements cleanly ruled out label, loss, and polarity bugs while pinpointing the exact defects before any Iteration 2 search ran.

## Validation

The 16-run validation investigation (`docs/crisp_dm/iteration_2/investigation/report.md`) confirmed label attachment had 0 mismatches across 179 tracked images and ranked the true causes: `±180°` rotation destroyed an orientation cue (`A1` validation macro-F1 jumped from `90.03` at `±180°` to `93.15` with rotation off and `93.17` at `±15°`, vs `A0` `91.69`), augmented shapes were ~6 px too small (`51.0` px vs `56.0-57.8` px real), `1-px` strokes broke into `17.2` pieces, and the synthetic stroke was `2 px` vs `3.1 px` real. On held-out `github_handdrawn` triangles and rectangles, augmentation already helped (`A1` `66.4%`, `B` `71.8%` vs `A0` `53.5%` mean accuracy).

## Our decision

Kept the Iteration 1 verdict (`fail`) unchanged, documented the validation investigation, opened Iteration 2 (`d5c6e2d`), fixed the transform and synthetic stroke defects, tuned per arm on validation, and added arm `A2` (clean real + augmented real + synthetic) for a pre-registered Iteration 2 test.

## Measured effect

Iteration 1 sealed verdict remained `B vs A1 = -0.36` macro-F1 points (`95% CI [-1.17, 0.41]`, `A0 93.88`, `A1 90.86`, `B 90.50`, `13 of 13` test reads). The validation probes lifted `A1` by `+3.14` points (`90.03` to `93.17`) once rotation was narrowed to `±15°` and identified every defect addressed in Iteration 2.

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`F04`)

### The problem, stated precisely

- Pre-registered `B vs A1`: `−0.36` macro-F1, 95% CI `[−1.17, 0.41]` → `fail`
- `A0` (no augmentation) highest: `93.88` vs `A1 90.86`, `B 90.50`

### Deepened logic: decompose the question before acting

The record splits the failure into **two separate questions**:
1. Why do `A1` and `B` trail `A0` by ~3 points? (`A1 vs A0 = −3.03`, `B vs A0 = −3.38`)
2. Why does `B` trail `A1` by `−0.36`?

Conflating them would send you tuning the wrong thing. Opus's constraint — **diagnose on train/validation only (2,819 images), never re-touch the test split** — is the methodological core: the test split was read `13 of 13` times and is now *frozen*; any further read invalidates the comparison.

### Mechanism hypotheses (then confirmed by the 16-run probe)

| Mechanism | Predicted symptom | Confirmed by |
|---|---|---|
| Label-destroying / shortcut-breaking rotation | `±180°` erases orientation cues; square rotated 45° → diamond | `A1` val macro-F1 `90.03` at `±180°` → `93.15` rotation-off, `93.17` at `±15°` (vs `A0 91.69`) |
| Transform/synthetic-fidelity defects | warping shrinks shapes, fragments `1-px` strokes; stroke-width mismatch | shapes ~`6 px` too small (`51.0` vs `56.0–57.8` real); `1-px` strokes broke into `17.2` pieces; synthetic stroke `2 px` vs `3.1 px` real |
| Zero clean real images + 30-epoch cap | harder augmented stream penalized vs `A0` memorizing clean styles | consistent with `A0` leading on clean seen-source splits |
| Label attachment bug (ruled out) | mislabeled targets | **0 mismatches across 179 tracked images** |

### Why the *ordering* of investigation mattered

Opus explicitly rejected a ~2-day, hundreds-of-runs per-arm sweep (Gemini's proposal) **before** transform defects were ruled out — because a sweep run on buggy transforms *bakes the bugs in* and wastes compute. The 16 fast validation-only runs cost hours, cleanly ruled out label/loss/polarity bugs, and *pinpointed the exact defects*. Only then was per-arm tuning and the new `A2` arm (clean + augmented real + synthetic) justified for Iteration 2.

### The generalization hint

On held-out `github_handdrawn` triangles and rectangles, augmentation *already helped*: `A1 66.4%`, `B 71.8%` vs `A0 53.5%` mean accuracy. This is the same signal that later drives F14's pivot: **augmentation's value shows up under distribution shift, not on clean seen-source splits.**

### Outcome chain

- Iteration 1 verdict stays `fail` (`−0.36`, `13 of 13` test reads).
- Validation probes lifted `A1` by `+3.14` points (`90.03 → 93.17`) once rotation narrowed to `±15°`.
- Iteration 2 opened (`d5c6e2d`); transform and synthetic-stroke defects fixed; per-arm tuning on validation; `A2` added for a pre-registered Iteration 2 test.

> **Connecting thread to F14:** F04 diagnoses *why augmentation initially lost* and fixes the transform pipeline. F14 then tests whether the fixed `A2` beats `A0` on clean seen-source images — it doesn't (ceiling effect). Both failures, read together, are what justify Iteration 3's shift to a *damage-based* evaluation, where the effect finally appears (`+9.20`).

