# 4_testing - C21: Harm rule ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/34_C21_harm-rule.md](../gemini_4_neon/34_C21_harm-rule.md)
- Date: 2026-11-09
- Worksheet entry: C21 (`change`, `4_testing`)
- Owner / Proposed by: `40297573 + 40304911` / `opus_medium_5.5`
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `ShapeSense/src/stage5_eval/stats.py`, `ShapeSense/src/stage5_eval/criterion.py`, `ShapeSense/tests/stage5/test_iteration3_repairs.py`, `ShapeSense/docs/crisp_dm/iteration_3/preregistration.md`, `ShapeSense/docs/crisp_dm/iteration_log.json`, commit `4c7cb90`, `ShapeSense_Deployed/web/stage5.html`



## Prompt ()

> **User:** Our harm rule runs one test per class with no multiple-testing correction across ten classes. How should we control false alarms, and what corrected interval and standard error of the paired drop should we use?

## Response ()

> **Opus 5.5:** Testing ten classes independently at `α = 0.05` inflates the chance of at least one false harm flag to roughly `1 - 0.95^10 ≈ 40%`. You also want the drop threshold tied to the actual paired uncertainty rather than a fixed single-arm binomial formula.
>
> For the paired-drop standard error, compute `drop_se` directly as the bootstrap standard deviation of the paired class drops (`drops.std(axis=0, ddof=1)` across the `n_boot` cluster resamples), and set each class's threshold to `max(min_drop_points, drop_se)`.
>
> To control false alarms across the ten classes, you have two clean options:
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Uncorrected per-class 95% CI | ~40% family-wise false-alarm rate across 10 classes | Replace |
> | **Holm-Bonferroni step-down (or BH FDR)** on the 10 two-sided bootstrap p-values | Controls family-wise error (Holm) or false discovery rate while keeping slightly higher power to catch real per-class regressions | **Initial lean** if you want a less conservative harm screen |
> | **Bonferroni-corrected lower CI bound** (`1 - α / 10 = 99.5%`, quantile `100 * α / (2k)`) | Directly maps to `criterion.py`'s interval-based check (`drop_ci_lo_adj > 0`) with zero p-value wiring | Simpler CI-native alternative if you want a pure interval rule |
>
> Both Holm and Bonferroni control the family-wise error rate over 10 classes; Holm saves a bit of power when multiple classes regress, whereas Bonferroni gives each class a single self-contained `drop_ci_lo_adj` bound you can inspect directly in the table.

## Why this reading fits

An outside review specifically called out the uncorrected 10-class harm rule (`iteration_log.json` audit). While Opus 5.5 initially leaned toward Holm/FDR for slightly higher power when screening 10 classes, the team chose **Bonferroni-corrected percentile bounds (`1 - 0.05 / 10` via `drop_ci_lo_adj`) paired with `max(min_drop_points, drop_se)`** in `robust_verdict` (`src/stage5_eval/criterion.py`, `stats.py`, commit `4c7cb90`) because it keeps the harm check purely interval-based, avoids mixing p-value step-down logic into `criterion.py`, and reserves Holm for the secondary comparison families.

## Validation

Covered by `test_harm_needs_the_corrected_interval_and_the_standard_error_floor` in `tests/stage5/test_iteration3_repairs.py`: a `3.0`-point drop flags as harmful when `drop_se = 1.0` and `drop_ci_lo_adj = 0.2`, stays non-harmful when `drop_ci_lo_adj = -0.2` (fails Bonferroni correction), and stays non-harmful when `drop_se = 4.0` (inside the bootstrap standard-error floor).

## Our decision

Updated `cluster_bootstrap` (`src/stage5_eval/stats.py`) to compute `drop_se` (`ddof=1`) and `drop_ci_lo_adj` at `100.0 * alpha / (2.0 * n_classes)`, and implemented `criterion.robust_verdict` (`src/stage5_eval/criterion.py`) using `max(min_drop_points, drop_se)` and `drop_ci_lo_adj > 0` (`4c7cb90`, pre-registered in `docs/crisp_dm/iteration_3/preregistration.md`).

## Measured effect

Zero false-alarm harm flags on `fresh_holdout_2` (`harmful_classes: []` across all 10 classes for `A2 vs A0`), while keeping the rule unit-tested against synthetic 3-point drops.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C21`)

### The multiple-testing derivation

Testing $k = 10$ classes independently at $\alpha = 0.05$: under the global null (no class harmed),

$$P(\text{at least one false flag}) = 1 - (1-\alpha)^k = 1 - 0.95^{10} \approx 0.4013$$

So a "clean" system has a **40% chance of showing a spurious harmed class** — the uncorrected harm rule is a false-alarm machine.

### The two-floor threshold

A class is flagged harmful iff:

$$\text{drop}_{\text{observed}} > \max(\text{min\_drop\_points},\ \text{drop\_se}) \quad \text{AND} \quad \text{drop\_ci\_lo\_adj} > 0$$

Why the max of two floors?
- $\text{min\_drop\_points}$ (e.g., `3.0` or `2.0`) is a **practical-significance floor** — a 0.5-point drop is noise even if statistically real.
- $\text{drop\_se}$ is a **statistical-power floor** — if the paired bootstrap SE of the drop is `4.0`, a `3.0`-point observed drop is inside one SE and cannot be distinguished from zero regardless of CI arithmetic.

### Why Bonferroni over Holm here (the deep reason)

Holm is uniformly more powerful and controls FWER, so naively it dominates. But `criterion.py` is **interval-native**: it inspects `drop_ci_lo_adj > 0` as a boolean. Holm requires a step-down over sorted p-values, which introduces state and ordering into what was a pure per-class interval check. Bonferroni needs only a **quantile shift**: evaluate the bootstrap percentile at $100\alpha/(2k)$ instead of $100\alpha/2$. The decision rule stays a single comparison per class, so `criterion.py` stays a pure function. **Holm is reserved for the secondary comparison families where p-values are already computed and a step-down costs nothing extra.** This is a *purity-versus-power* trade-off resolved in favor of purity at the gate and power in the secondary layer.

### The standard-error floor, derived

The paired drop for class $c$ is $d_c^{(b)} = F1_c^{(b)}(A0) - F1_c^{(b)}(A2)$ across bootstrap draws $b$. Then $\text{drop\_se}_c = \text{std}(d_c^{(b)}, \text{ddof}=1)$. Because macro-F1 on smaller classes has higher variance, the `max(..., drop_se)` rule **automatically scales the required drop to the class's own uncertainty**.

### Verification

The unit test exercises all three branches: flags at `(drop 3.0, se 1.0, ci_lo_adj 0.2)`; does not flag at `(ci_lo_adj -0.2)` [fails Bonferroni]; does not flag at `(se 4.0)` [inside SE floor].

