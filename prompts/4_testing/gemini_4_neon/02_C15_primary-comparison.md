# 4_testing - C15: Primary comparison
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C15 (`change`, `4_testing`)
- Owner / Proposed by: 40253714 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `docs/crisp_dm/iteration_2/preregistration.md`, `configs/pipeline.yaml`, `src/stage5_eval/run.py`, `src/stage5_eval/criterion.py`, `results/phase2_snapshot/iter2_status.json`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/iteration2.html`, commit `7f356d6`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Iteration 2 asks whether the full mix beats real images alone. Which comparison should be the single pre-registered primary test (B vs A1 or A2 vs A0), and how do we register it before any tuning?

## Response
Choose **`A2 vs A0`** as the single pre-registered primary comparison, and commit the pre-registration document before running a single Iteration 2 tuning trial.

### Why `A2 vs A0` instead of `B vs A1`
1. **Matches the business and scientific question:** Iteration 1 asked the incremental ablation `B vs A1` (does adding synthetic data improve over augmented real data?), where neither arm saw clean real images (`A0` beat both at `93.88` vs `90.86` and `90.50`). Iteration 2 introduces arm `A2` (clean real + augmented real + synthetic in every 256-image batch) specifically to test whether the full training mix outperforms real images alone (`A0`). Keeping `B vs A1` as primary would leave `A2` untested as a binding decision and ignore the fact that `A1` and `B` omit clean real images.
2. **Preserves family-wise error control:** Locking a single primary comparison (`A2 vs A0`) avoids inflating false positives across multiple unadjusted candidate pairs, while still letting `A1 vs A0`, `B vs A0`, and `A2 vs B` run as Holm-corrected secondary comparisons in `src/stage5_eval/run.py` (`evaluation.secondary`).

### How to register it before any tuning
1. **Create and commit `docs/crisp_dm/iteration_2/preregistration.md` before tuning starts:** Explicitly state the primary comparison (`A2 vs A0`, soft-vote ensemble macro-F1 over 5 seeds `0..4`), the locked 3-part `success_criterion` (`delta >= 1.0` macro-F1 point, 95% paired bootstrap CI excluding `0`, and no class dropping by more than `max(2.0, noise_band_c)` with CI excluding `0`), the Holm secondary family (`A1 vs A0`, `B vs A0`, `A2 vs B`), the exact validation search spaces and trial counts (ablation, 24-trial augmentation search on `A1`, 16-trial generator search on `B`, 12-trial batch-share search on `A2`, 3x2 `lr`/`dropout` grid per arm, top-5 3-seed confirmation), and the change-control rule that nothing changes after a test read.
2. **Drive Stage 5 from config rather than hard-coded constants:** In `configs/pipeline.yaml`, configure `evaluation.primary: { reference: A0, candidate: A2 }` and read it through `primary_roles(config)` in `src/stage5_eval/run.py` instead of hard-coding `ARM_AUG` and `ARM_SYNTH` (`B vs A1`), so the pipeline contract and pre-registration match mechanically.

## Validation
`40253714` and the team verified the pre-registration commit (`7f356d6`) timestamped `2026-11-09 01:41:37 -0500` - prior to the Iteration 2 implementation and tuning commit (`87711f3`) - and checked `src/stage5_eval/run.py::primary_roles(config)` and `secondary_pairs(config)` against `configs/pipeline.yaml` via `tests/stage5/test_run.py` and `tests/stage5/test_tables.py`. During the Iteration 2 Stage 5 run (`results/phase2_snapshot/iter2_status.json`), `power_check_before_test` was `True` and `primary.label` resolved to `"A2 vs A0"`.

## Our decision
Adopted Gemini 4 Neon's recommendation in full: committed `docs/crisp_dm/iteration_2/preregistration.md` before tuning (`7f356d6`), updated `configs/pipeline.yaml` (`evaluation.primary: { reference: A0, candidate: A2 }`, `evaluation.secondary: [[A0, A1], [A0, B], [B, A2]]` for Iteration 2), and wired `primary_roles(config)` in `src/stage5_eval/run.py` so Stage 5 evaluates `A2 vs A0` under the locked `success_criterion`.

## Measured effect
- **Pre-registration integrity:** `docs/crisp_dm/iteration_2/preregistration.md` committed prior to all `166` Iteration 2 validation search trials.
- **Iteration 2 primary result (`A2 vs A0`):** Failed on both the reused test split (`+0.06` macro-F1 points, 95% CI `[-0.69, 0.83]`, ensembles `A0 = 95.3`, `A2 = 95.4`) and `fresh_holdout` (`+0.08` points, 95% CI `[-0.41, 0.57]`), cleanly rejecting the hypothesis under the pre-registered rule without post-hoc switching.

---

## Upgraded & Expanded Technical Analysis (`C15`)

### 1. Pre-Registration Power and Minimum Detectable Effect (`power_check_before_test`)
Locking the primary minimum gain threshold at $\Delta_{\min} = 1.0$ macro-F1 point in `docs/crisp_dm/iteration_2/preregistration.md` is grounded in the validation power calculation (`src/stage5_eval/power.py`):
- Across $n_{\text{val}} = 2,819$ validation images ($n_{\text{test}} = 2,776$, rescale factor $\sqrt{2819 / 2776} \approx 1.008$), the paired bootstrap 95% half-width between ensembles is $h_{\text{val}} \approx 0.62\text{--}0.76$ macro-F1 points (standard error $\text{SE} \approx h / 1.96 \approx 0.32\text{--}0.39$ points).
- At two-sided $\alpha = 0.05$ and $80\%$ statistical power ($z_{0.975} + z_{0.80} \approx 2.80$), the minimum detectable effect size (MDE) for the paired bootstrap is $\text{MDE}_{80\%} \approx 2.80 \times \text{SE} \approx 0.9\text{--}1.1$ points (and $\sim 0.6\text{--}0.76$ points for clearing the `ci_lo > 0` superiority boundary).
- Setting $\Delta_{\min} = 1.0$ with `limit_points: 1.0` ensures the locked target sits safely above the paired sampling noise floor rather than relying on an arbitrary convention.

### 2. Explicit Multiplicity Ledger
Every pairwise comparison in Iteration 2 (and extended in Iteration 3) is assigned to an explicit inferential family so no comparison escapes family-wise error rate (FWER) control:

| Comparison | Inferential Role | Family & Multiplicity Adjustment | Test Statistic & $p$-Value Source |
|---|---|---|---|
| `A2 vs A0` | **Primary Hypothesis** | Single pre-registered primary gate ($\alpha = 0.05$, 3-part conjunctive `success_criterion`) | Paired cluster-bootstrap macro-F1 (`delta >= 1.0`, 95% CI `ci_lo > 0`, per-class harm check) |
| `A1 vs A0` | Secondary Ablation | Secondary Holm-Bonferroni family ($m = 3$ in Iter 2; $m = 4$ in Iter 3) | Holm step-down on `p_two_sided` from paired bootstrap macro-F1 distribution (`stats.py`) |
| `B vs A0` | Secondary Ablation | Secondary Holm-Bonferroni family ($m = 3$ in Iter 2; $m = 4$ in Iter 3) | Holm step-down on `p_two_sided` from paired bootstrap macro-F1 distribution (`stats.py`) |
| `A2 vs B` | Secondary Ablation | Secondary Holm-Bonferroni family ($m = 3$ in Iter 2; $m = 4$ in Iter 3) | Holm step-down on `p_two_sided` from paired bootstrap macro-F1 distribution (`stats.py`) |
| `A2 vs A1` | Secondary Ablation (added in Iter 3, `A27`) | Secondary Holm-Bonferroni family ($m = 4$ in Iter 3) | Holm step-down on `p_two_sided` from paired bootstrap macro-F1 distribution (`stats.py`) |

