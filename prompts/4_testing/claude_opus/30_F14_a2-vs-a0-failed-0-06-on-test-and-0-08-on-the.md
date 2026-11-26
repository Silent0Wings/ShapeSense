# 4_testing - F14: A2 vs A0 failed: +0.06 on test and +0.08 on the fresh holdout, both CIs include 0. ()
[33_real_iteration-2-plan-tuning-and-a2.md](../../3_modeling/claude_opus/33_real_iteration-2-plan-tuning-and-a2.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/31_F14_a2-vs-a0-failed-0-06.md](../gemini_4_neon/31_F14_a2-vs-a0-failed-0-06.md)
- Date: 2026-11-09
- Worksheet entry: F14 (`failure`, `4_testing`)
- Owner / Proposed by: `40256377` / `40256377`
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `ShapeSense/docs/crisp_dm/iteration_2/data/stage5_status.json`, `ShapeSense/docs/crisp_dm/iteration_2/data/comparisons.csv`, `ShapeSense/docs/crisp_dm/iteration_2/data/fresh_metrics.csv`, `ShapeSense/docs/crisp_dm/iteration_2/data/per_source.csv`, `ShapeSense/docs/crisp_dm/iteration_3/preregistration.md`, `ShapeSense/docs/crisp_dm/iteration_log.json`, commit `cf79298`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/robustness.html`, `ShapeSense_Deployed/web/iteration2.html`



## Prompt ()

> **User:** `A2` vs `A0` failed in Iteration 2: `+0.06` macro-F1 points on the reused test split (95% CI [-0.69, 0.83]) and `+0.08` on the fresh 4,500-image holdout (95% CI [-0.41, 0.57]), both from the same sources used in training. How should we report this, and what should a third iteration test instead?

## Response ()

> **Opus 5.5:** Report both comparisons directly as `fail` with no post-read model or threshold changes, and clearly separate the two sets in your write-up: the reused test split is contaminated evidence from Iteration 1, while the fresh holdout is clean evidence on seen sources.
>
> The reason `A2` and `A0` tied is a classic in-distribution ceiling effect: once the transform fixes landed, `A0` already scored `95.3` on test and `97.5` on the fresh holdout (`98.6%` on `kaggle_reevald` and `99.4%` on `mendeley_elkorchi`). On clean drawings from the same sources seen in training, a 4-block CNN trained on `12,405` real images has enough capacity and source style cues that adding augmented and synthetic variety has almost no headroom left to gain.
>
> For Iteration 3, you need an evaluation target where `A0`'s source-template memorization actually breaks down:
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Target an **unseen-source** benchmark (or elevate 9-class LOSO) | Directly tests whether augmentation and synthetic shapes generalize when source style shifts, where `A0` dropped in `github_handdrawn` hold-outs | **Primary lean** if you can assemble or formalize an unseen-source test split |
> | Target **perturbed / corrupted copies** of a never-read holdout | Tests survival under rotation, noise, blur, compression, lighting shifts, and occlusion without needing new sources | Good alternative if a clean 10-class external source is unavailable |
> | Keep tuning on clean seen-source splits | Repeats the same ceiling regime where all arms cluster around `95-98` | Do not pursue |
>
> Start Iteration 3 by checking whether you can source an unseen 10-class evaluation set; if `github_handdrawn` missing `ellipse` limits LOSO to 9 classes, document the clean failure honestly and decide between collecting an unseen source or shifting the primary test to image perturbations.

## Why this reading fits

This matches both commit `cf79298` - where F14's initial resolution recorded *"A third iteration would need to target unseen sources"* - and how empirical constraints refined that plan before Iteration 3 pre-registration. Because `github_handdrawn` is the only source containing `ellipse` (preventing a 10-class LOSO test, `F02`) and no clean 10-class external source was available, the team ran a validation robustness check (`docs/crisp_dm/iteration_2/robustness/results.json`) that revealed a sharp gap under damage; Iteration 3 therefore pre-registered `A2 vs A0` averaged across 23 perturbation levels on a never-read 4,500-image `fresh_holdout_2` instead, while keeping unseen-source LOSO as descriptive context.

## Validation

Recorded in `docs/crisp_dm/iteration_2/data/stage5_status.json` (`52 of 52` test reads, `0` extra reads): on the reused test split, `A0 95.32`, `A1 95.19`, `B 95.32`, `A2 95.37` (`A2 vs A0 +0.06`, CI `[-0.69, 0.83]`); on the first fresh holdout, `A0 97.46`, `A1 97.42`, `B 97.23`, `A2 97.54` (`A2 vs A0 +0.08`, CI `[-0.41, 0.57]`). Held-out `github_handdrawn` (9-class LOSO) showed higher mean accuracy for augmented arms (`A0` `58.3-75.8%`, `A1` `72.5-77.5%`, `A2` `62.3-80.5%`), while validation robustness later exposed `A0`'s collapse under image damage.

## Our decision

Recorded Iteration 2 as a failure (`cf79298`) with zero post-read changes, closed Iteration 2, repaired the Stage 5 evaluation issues from the outside audits, built `fresh_holdout_2` (`4,500` never-read images), and pre-registered Iteration 3 (`docs/crisp_dm/iteration_3/preregistration.md`) with `A2 vs A0` over 23 damage levels as the primary comparison.

## Measured effect

Iteration 2 stayed closed as `fail` (`+0.06` and `+0.08` macro-F1 points). Pivoting Iteration 3 from clean seen-source images to 23 perturbation levels on `fresh_holdout_2` delivered `+9.20` macro-F1 points (`95% CI [8.89, 9.53]`, `PASS`; damaged ensemble macro-F1 `A2 84.8` vs `A0 75.6`, clean `fresh_holdout_2` `+0.64`, CI `[0.19, 1.07]`).

---

## Expanded & Upgraded Analysis — Deeper Logic, Complexity, and Evidence Chains (`F14`)

### The problem, stated precisely

Two comparisons, both null:
- Reused Iteration-1 test split: `A2 − A0 = +0.06` macro-F1, 95% CI `[-0.69, 0.83]`
- Fresh 4,500-image holdout (same sources): `A2 − A0 = +0.08`, 95% CI `[-0.41, 0.57]`

Both CIs straddle zero. The pre-registered hypothesis — that adding augmented + synthetic variety (`A2` = clean real + augmented real + synthetic) beats `A0` (clean real only) — is **not supported**.

### Deepened logic: why this is a *true* failure, not an underpowered one

A lazy read says "CIs include zero, so maybe it just needs more data." The record lets us reject that:

1. **The effect size is tiny relative to the CI width.** A +0.06 point effect with a ±0.76 half-width is not a hidden signal — it is a *flat* result. To detect a real effect of that magnitude you'd need an implausibly large sample.
2. **The mechanism is a ceiling effect, which the numbers confirm.** `A0` scores `95.32` on test and `97.46` on the fresh holdout — with per-source `98.6%` on `kaggle_reevald` and `99.4%` on `mendeley_elkorchi`. When the *baseline* arm is at 95–99%, headroom is structurally ~1–5 points, and the transform fixes already captured it.
3. **A 4-block CNN on 12,405 real images has enough capacity to memorize seen-source style.** On clean drawings from *seen* sources, source-style cues act as a shortcut; augmentation and synthetic variety add information the model doesn't need.
4. **The two evaluations are not independent corroboration.** The reused test split is *contaminated* (read in Iteration 1, 52 of 52 reads recorded). The fresh holdout is *clean* but on the *same sources*. So both measure the same regime — seen-source clean drawings — and both correctly report "no headroom."

> **Inference (not a quoted result):** The consistency of the two near-zero effects (+0.06 and +0.08) across a contaminated and a clean split is itself evidence that contamination isn't driving the result — the ceiling regime dominates either way.

### The critical distinction the report must make

| Evidence set | Status | What it licenses |
|---|---|---|
| Reused test split | Contaminated (read in Iter 1) | Descriptive only; cannot be the basis of a fresh claim |
| Fresh 4,500-image holdout | Clean, but seen sources | A legitimate null on *seen-source clean* images |
| Held-out `github_handdrawn` (9-class LOSO) | Descriptive context | Directional signal that augmented arms generalize better (`A0 58.3–75.8%`, `A1 72.5–77.5%`, `A2 62.3–80.5%`) — but not a pre-registered primary test |

The honest verdict is therefore: **`fail`, frozen, zero post-read changes.** The LOSO numbers are the *hint* for where to go next, not a rescue of the failed claim.

### Deepened next-step logic

Opus's ranking of Iteration 3 options is a **cost-of-evidence** argument, not just a preference:

- **Unseen-source benchmark** directly attacks the failure mode (source-style shortcut). *Constraint discovered later:* `github_handdrawn` is the only source with `ellipse`, so 10-class LOSO is impossible (`F02`); a clean 10-class external source was unavailable. So the "primary lean" was blocked by data reality.
- **Perturbed/corrupted copies of a never-read holdout** tests survival under rotation, noise, blur, compression, lighting, occlusion — *no new sources needed*. This is the fallback that the empirical constraints later made the actual choice.
- **Keep tuning on clean seen-source splits** repeats the ceiling regime → explicitly rejected.

### The pivot, with its logic made explicit

Because the clean unseen-source option was infeasible, the team ran a **validation robustness check** (`docs/crisp_dm/iteration_2/robustness/results.json`) that exposed `A0`'s collapse under image damage. That is a *mechanism discovery*: `A0`'s seen-source advantage is brittle — it depends on clean, orientation-consistent, full-resolution strokes. Iteration 3 therefore pre-registered **`A2 vs A0` averaged over 23 perturbation levels on a never-read 4,500-image `fresh_holdout_2`**, keeping unseen-source LOSO as *descriptive context only*.

### Outcome chain (why the pivot was correct)

- Iteration 2 stays closed as `fail` (`+0.06`, `+0.08`).
- Iteration 3 delivers **`+9.20` macro-F1 points** (`95% CI [8.89, 9.53]`, `PASS`; damaged ensemble `A2 84.8` vs `A0 75.6`), clean `fresh_holdout_2` only `+0.64` (`CI [0.19, 1.07]`).
- **Interpretation:** the benefit of augmentation+synthetic data is *conditional on distribution shift*. On clean seen-source images the effect is ~0 (Iteration 2); under damage the same arm gains ~9 points (Iteration 3). The Iteration-2 "failure" was actually the correct discovery that the *evaluation target* was wrong — which is exactly what the pre-registered pivot was designed to test.

### Cross-cutting synthesis (the upgraded meta-logic)

1. **Freeze discipline is enforced mechanically, not promised.** T56 (forbid early holdout reads), T71 (expect all arms), C28 (single sealed read path), and "157 reads unchanged" (T84) are four independent guards that together make the sealed holdouts *actually sealed*.
2. **Temporal integrity is defended in three layers.** T46 (report inputs), T73 (dashboard), T82 (failure charts) all enforce *"a record shows its own iteration's numbers."* Repetition across layers signals it was treated as a first-class requirement.
3. **Statistical credibility precedes the headline number.** C20 (cluster bootstrap), C21 (Bonferroni), C22 (Holm + McNemar) mean the Iteration-3 `+9.20` CI `[8.89, 9.53]` is *earned*, not merely computed.
4. **Failures are productive because they are frozen and decomposed.** F04 (why augmentation lost → fix transforms) and F14 (no gain on clean seen sources → ceiling) are not dead ends; each narrows the *evaluation target* until Iteration 3 finds the regime where the effect is real.
5. **Deployment claims are tied to evaluated artifacts.** T86's 1e-4 logit agreement and T84's byte-identical A2 export are provenance proofs that the public site serves what was measured.
6. **The record refuses to overclaim.** "Not re-verified" (T87), "target, unverified" (T88), G3/G4 "still open" (T84), "optimistic" reused validation (C40) — honesty is built into the entries rather than added as a disclaimer.

