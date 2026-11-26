# 4_testing - A23: Rule 1 needs the interval above 0, not above the minimum gain.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A23 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/criterion.py, ShapeSense/configs/pipeline.yaml, ShapeSense/stages/stage_5.md, ShapeSense/docs/crisp_dm/iteration_2/preregistration.md, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/tests/stage5/test_iteration3_repairs.py, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/iteration2.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Rule 1 needs the interval above 0, not above the minimum gain.

## Response
In `src/stage5_eval/criterion.py::verdict()` (driven by `configs/pipeline.yaml#success_criterion` and `stages/stage_5.md` R7), the pass condition splits into two separate checks:

- Rule 1 checks the point estimate: `delta >= min_gain_points` (`1.0` macro-F1 point).
- Rule 2 checks the confidence interval against zero: `ci_lo > 0.0` (95% paired bootstrap CI excludes `0`).

Because Rule 2 only requires `ci[0] > 0` rather than `ci[0] >= min_gain_points` (`1.0`), a comparison whose observed point gain is e.g. `+1.2` points with 95% CI `[0.2, 2.2]` passes the criterion even though the data remain statistically compatible with a true population gain as small as `+0.2` points - well below the `1.0`-point minimum gain target.

Statistically, testing `ci[0] > 0` combined with `delta >= 1.0` establishes superiority over zero plus a point-estimate gate, not statistical superiority over the `1.0`-point minimal clinically/practically important difference (`H0: delta <= 1.0`). If the intent were to prove with 95% confidence that the true gain exceeds `1.0` point, Rule 2 would need `ci[0] >= min_gain_points`. If the weaker pre-registered rule (`ci[0] > 0` and `delta >= 1.0`) is intentional, reporting the stricter check (`ci[0] >= 1.0`) alongside the verdict prevents misinterpretation.

## Validation
The team reviewed `src/stage5_eval/criterion.py`, `stages/stage_5.md` R7, `docs/crisp_dm/iteration_2/preregistration.md`, and `results/phase2_snapshot/iter2_status.json`. In iteration 2, `A2 vs A0` scored `delta = +0.06` (95% CI `[-0.69, 0.83]`) on the reused `test` split and `delta = +0.08` (95% CI `[-0.41, 0.57]`) on `fresh_holdout`, failing both Rule 1 (`< 1.00`) and Rule 2 (`ci_lo <= 0.0`) under either threshold. In iteration 3, the team added `strict_pass` (`not reasons and ci_lo >= float(min_gain_points)`) to `criterion.robust_verdict()` and verified both readings in `tests/stage5/test_iteration3_repairs.py::test_robust_rule_reports_the_strict_reading_without_requiring_it` (showing `delta = 1.5, ci = [0.5, 2.5]` yields `verdict == "pass"` and `strict_pass is False`, while `delta = 2.5, ci = [1.2, 3.5]` yields `strict_pass is True`).

## Our decision
**Verdict: Stands - No action on the rule.** Requiring `delta >= 1.0` and `ci[0] > 0` is the pre-registered criterion locked in `stages/stage_5.md` R7 and `docs/crisp_dm/iteration_2/preregistration.md`, and iteration 2 fails under both rules anyway. In `docs/crisp_dm/iteration_3/preregistration.md`, the team kept `ci[0] > 0` as the binding Rule 2 and explicitly documented that the stricter reading (`ci[0] >= 1.0`, surfaced as `strict_pass` in `robust_verdict()`) is reported beside it without changing the pre-registered rule.

## Measured effect
Iteration 2 remains `fail` on both splits (`+0.06`, CI `[-0.69, 0.83]` on reused `test`; `+0.08`, CI `[-0.41, 0.57]` on `fresh_holdout`, `ShapeSense_Deployed/web/iteration2.html`). In iteration 3 (`A2 vs A0` across 23 perturbation levels on `fresh_holdout_2`, `status5.json`), `delta = +9.20` and 95% CI `[8.89, 9.53]`, so both `verdict = "pass"` (`ci_lo > 0`) and `strict_pass = true` (`8.89 >= 1.0`) hold (`ShapeSense_Deployed/web/stage5.html`).

---

## Upgraded Audit Entry (A23)

### Part III — Statistical-Validity Cluster Context (`A19`, `A20`, `A22`, `A23`, `A24`, `A25`)

### A23 — Rule 1 needs interval above 0, not above minimum gain

**Expanded reasoning.** The criterion is `delta >= 1.0` (Rule 1) **and** `ci_lo > 0` (Rule 2). This proves *superiority over zero* plus a *point-estimate* gate — it does **not** prove `H0: delta <= 1.0` is rejected. A result of `delta=+1.2, CI=[0.2, 2.2]` passes while remaining statistically compatible with a true gain of `+0.2`, far below the `1.0` MPID (minimal practically-important difference). The statistically correct test for "beats the MPID" is `ci_lo >= 1.0`.

**Deepened verdict.** "Stands / No action" is correct *because the rule is pre-registered* (`stages/stage_5.md` R7, iteration-2 pre-registration) and iteration 2 fails under **both** readings (`+0.06`, CI `[-0.69, 0.83]`). The team's fix is **report, don't change**: `strict_pass = (not reasons) and ci_lo >= min_gain_points` surfaced in `robust_verdict()` and pinned by `test_robust_rule_reports_the_strict_reading_without_requiring_it` (`delta=1.5, CI=[0.5,2.5]` → `pass` but `strict_pass=False`; `delta=2.5, CI=[1.2,3.5]` → `strict_pass=True`). In iteration 3, `+9.20` / `[8.89, 9.53]` passes *both*, so the ambiguity is moot for the current result but documented for future readers. The residual tension — a pre-registered weak rule that a reader may over-interpret — is handled by *dual reporting*, which is the right mitigation when changing the rule is forbidden.

