# 4_testing - F30: The first vote comparison scored an empty class as zero. ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/39_F30_the-first-vote-comparison-scored-an.md](../gemini_4_neon/39_F30_the-first-vote-comparison-scored-an.md)
- Date: 2026-11-10
- Worksheet entry: F30 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / opus_medium_5.5 + 40248536
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `scripts/vote_check.py`, `docs/crisp_dm/iteration_3/experiments/vote_check.json`, `tests/studio/test_vote.py`, `studio/inference/predict.py`, `docs/crisp_dm/iteration_log.json`, commit `916e7df`, `ShapeSense_Deployed/web/live.html`, `ShapeSense_Deployed/web/experiments.html`, `ShapeSense_Deployed/web/failures.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Our first validation comparison between equal-weight and per-class-weight voting scored some classes as zero on a random half of validation, dragging the score down by 10 points. Why is that happening, and how should we split and score so absent classes don't distort the comparison?

## Response ()

> **Opus 5.5:** You are hitting a cluster-split artifact combined with zero-division macro-F1 averaging:
>
> - **Why a class vanishes:** Keeping near-duplicate `phash_group`s intact is required so duplicates do not leak across halves, but some `phash_group`s are large. An unstratified random split of groups can put every image of one class into one half, leaving the other half with `0` true examples of that class.
> - **Why that costs 10 macro-F1 points:** With 10 classes, scoring an empty class as `0.0` (standard `zero_division=0` averaged over all `n_classes`) subtracts `10.0` points directly from the mean, and also assigns a `0.0` weight to that class in the learned per-class weighting.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Keep random group split + `zero_division=0` | Penalizes empty classes by 10 points and zeroes out weights | Skip |
> | Stratified group split (`StratifiedGroupKFold`) + score only present classes + equal-weight fallback (`1.0`) for missing learning-half classes | Preserves `phash_group` integrity, balances classes across halves, and avoids phantom zeros | **Do this** |
> | Drop `phash_group` grouping during the split | Leaks near-duplicates between learning and evaluation halves | Skip |
>
> Implement `StratifiedGroupKFold(n_splits=2, shuffle=True, random_state=20261109)` in `scripts/vote_check.py`, average `macro_f1` only over `np.unique(labels)` in `_score`, fall back to weight `1.0` for any class absent in the learning half in `_class_weights`, and lock both behaviors with unit tests in `tests/studio/test_vote.py`.

## Why this reading fits

Commit `916e7df` implements this exact design in `scripts/vote_check.py` (`split_groups` using `StratifiedGroupKFold`, `_score` indexing `[np.unique(labels)].mean()`, and `_class_weights` setting missing classes to `1.0`), verified by `tests/studio/test_vote.py` and matching `iteration_log.json` (`F30`).

## Validation

- Added `tests/studio/test_vote.py` (8 tests), including `test_validation_halves_keep_each_group_whole` and `test_a_class_missing_from_a_half_is_not_scored_as_zero` (asserting `_score` returns `100.0` rather than `66.7` when class 2 is absent from a 3-class subset).
- Ran `python -m scripts.vote_check`, producing `docs/crisp_dm/iteration_3/experiments/vote_check.json` over 2 stratified group halves of validation (`n_val = 2,819`).

## Our decision

Switched `scripts/vote_check.py` to `StratifiedGroupKFold` (`n_splits=2`), excluded absent classes from `_score`, assigned equal fallback weight `1.0` to any class missing from the learning half, and kept equal-weight probability averaging for "All models vote" in `studio/inference/predict.py` and `ShapeSense_Deployed/web/js/infer/math.js` (with no claimed score).

## Measured effect

On held-apart validation halves (`docs/crisp_dm/iteration_3/experiments/vote_check.json`), equal-weight voting scored `95.59` macro-F1 (`95.06` and `96.12` across the two halves) against `94.80` for per-class weights (`per_class_gain_over_equal = -0.79` points, below the `0.5`-point adoption margin) and `95.77` for the best single arm (`A2`), confirming equal weights stay (`keep: "equal"`). All 8 tests in `tests/studio/test_vote.py` pass.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`F30`)

### The $-10$ penalty derivation

Macro-F1 over 10 classes with `zero_division=0`, when one class is absent from the evaluation half: if the true mean over the present 9 classes is $m$, the reported mean is $(9m + 0)/10 = 0.9m$, a **10% relative drop** ($m/10$ points; at $m \approx 95$ it is $9.5$ points, or $10.0$ points at $m = 100$).

### The split-stratification requirement

`phash_group` integrity (no duplicate leakage across halves) and class balance are **in tension**: an unstratified group split can put all of a class's groups in one half. `StratifiedGroupKFold` resolves it by stratifying on class *subject to* group integrity — finding a partition of groups into halves that preserves approximate class proportions.

### The weighting collapse (second bug)

`_class_weights` learns per-class weights from the learning half. If a class is absent from the learning half, its weight is undefined — the naive implementation assigns `0`, which **zeroes that class's contribution to the vote** in the evaluation half, compounding the scoring bug. The fix assigns the neutral weight `1.0` (equal weight) for absent classes, so absence degrades to the baseline rather than to zero.

### The outcome logic

Equal voting (`95.59`) beat per-class weights (`94.80`) by `-0.79` points — below the `0.5`-point adoption margin, so equal weights stay. Even after fixing both the split artifact and the weighting collapse, per-class weighting did not clear the pre-set margin — enforcing the same pre-commitment discipline as the main verdict: **don't adopt a change that doesn't clear its pre-set margin.**

