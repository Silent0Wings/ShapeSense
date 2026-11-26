# 4_testing - C21: Harm rule with a corrected interval
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/32_C21_harm-rule.md](../claude_opus/32_C21_harm-rule.md)
- Date: 2026-11-09
- Entry: C21 (`change`, `4_testing`)
- Owner / Proposed by: 40297573 + 40304911 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, src/stage5_eval/criterion.py, src/stage5_eval/stats.py, configs/pipeline.yaml, docs/crisp_dm/iteration_3/preregistration.md, tests/stage5/test_iteration3_repairs.py, results/phase2_snapshot/status5.json, commit 4c7cb90



## Prompt

> **User:** Our harm rule runs one test per class with no multiple-testing correction across ten classes. How should we control false alarms, and what corrected interval and standard error of the paired drop should we use?

## Response
You are right to worry. With ten uncorrected 95% tests, a candidate that harms no class still has a fair chance of tripping at least one by noise alone. On the harm rule a false alarm means a false fail, so the current rule is biased against the candidate. The fix has two parts, and both belong in the pre-registration before any tuning.

**1. A Bonferroni-corrected interval for the drop.** Test each class at level 0.05 / 10, which keeps the family-wise false alarm rate at or below 0.05 across the ten classes. Using the cluster bootstrap (C20), this is just a lower percentile of the bootstrap distribution of each class's paired drop:

```python
"drop_ci_lo_adj": np.percentile(drops, 100.0 * alpha / (2.0 * n_classes), axis=0)
```

A class is "significant" only if this corrected lower bound is above 0.

Bonferroni is conservative, but here that is the right direction: with ten tests and no structure among them, Holm gives little extra power for a rule whose only job is to block real harm.

**2. A noise-aware threshold.** Iteration 2 used max(2 points, a noise band) where the band came from the class's test count at an assumed 90% accuracy. That band does not reflect the actual pair of models. Replace it with max(2 points, one bootstrap standard error of that class's paired drop), computed from the same resamples:

```python
"drop_se": drops.std(axis=0, ddof=1)
```

**The full harm condition** becomes: mean drop above max(2 points, one SE of the paired drop) **and** Bonferroni-corrected CI excluding 0. Both are needed: the floor stops tiny but precise drops from failing the candidate, and the correction stops noisy drops from doing so.

| Rule | False alarms across 10 classes | Catches real harm |
|---|---|---|
| Per-class 95%, no correction | Inflated | Yes |
| Bonferroni 0.05/10 + SE floor | Controlled at 0.05 family-wise | Yes, if the drop is clear |
| Drop threshold only, no interval | Many on noisy classes | Yes |

The 2-point floor itself (`max_class_f1_drop_points: 2.0`) stays as before; only the test around it changes. And this must not be revisited after the sealed read, whatever the per-class results look like.

Test I would add: a planted drop of 3 points flags the class when the corrected bound is above 0 and the SE is 1; it does not flag when the corrected bound includes 0, or when the SE is 4.

## Validation
`src/stage5_eval/criterion.py::robust_verdict` applies "a mean drop above max(`min_drop_points`, one bootstrap standard error of that drop) with a Bonferroni-corrected CI excluding 0". `tests/stage5/test_iteration3_repairs.py::test_harm_needs_the_corrected_interval_and_the_standard_error_floor` covers the three cases above. The iteration 3 pre-registration states the rule with "a Bonferroni-corrected CI (level 1 - 0.05 / 10)".

## Our decision
Adopted for iteration 3: Bonferroni-corrected interval and bootstrap standard error of the paired drop (commit 4c7cb90), because ten classes tested at once raise false alarms.

## Measured effect
On the sealed iteration 3 primary (`status5.json`): `harmful_classes` is empty and `reasons` is empty, verdict pass. No comparison with the old uncorrected rule on the same data is recorded.

---

##  Technical Analysis (`C21`)

### 1. Multiplicity Inflation Math & One-Sided Tail Allocation
Testing $k = 10$ shape classes simultaneously with unadjusted 95% intervals ($\alpha / 2 = 0.025$ lower tail per class) inflates the family-wise false-alarm probability under the global null to:
$$\text{FWER}_{\text{unadj}} \le 1 - (1 - 0.025)^{10} \approx 22.4\% \quad (\text{or } 1 - 0.95^{10} \approx 40.1\% \text{ two-sided})$$
Because a false alarm on Rule 3 triggers a **false fail** of the candidate arm, an unadjusted per-class check systematically penalizes harmless models on lower-count classes (`ellipse` $149$, `diamond` $150$).
- **Bonferroni Lower-Percentile Bound:** Evaluating each class at $\alpha / k = 0.05 / 10 = 0.005$ (the `100 * alpha / (2 * n_classes) = 0.25th` percentile of the paired cluster-bootstrap drop distribution `drops`, stored as `drop_ci_lo_adj`) bounds the family-wise false-harm rate at $\le 0.025$ one-sided ($\le 0.05$ two-sided).
- **Why Bonferroni Over Holm for Harm Blocking:** Unlike the secondary superiority family (where step-down Holm maximizes power to detect gains), Rule 3 is a *safety veto* across $10$ unstructured classes with no priority ordering; uniform per-class thresholds (`drop_ci_lo_adj > 0`) give every class the exact same safety standard.

### 2. Conjunctive Practical + Statistical Harm Gate
A class $c \in \{0..9\}$ is flagged as harmed in `src/stage5_eval/criterion.py::robust_verdict` if and only if:
$$\underbrace{\hat{d}_c > \max(2.0, \; \text{SE}_{\text{boot}}(\hat{d}_c))}_{\text{Practical floor \& empirical noise guard}} \quad \wedge \quad \underbrace{Q_{0.0025}(\hat{d}^*_c) > 0.0}_{\text{Family-wise multiplicity guard}}$$
where $\text{SE}_{\text{boot}}(\hat{d}_c) = \texttt{drops.std(axis=0, ddof=1)}$ replaces Iteration 2's static 90%-accuracy binomial proxy with the actual paired bootstrap standard error of the two compared ensembles. `test_harm_needs_the_corrected_interval_and_the_standard_error_floor` pins all three branches: a $3.0$-point drop flags when $\text{SE} = 1.0 \wedge \text{CI}_{\text{lo,adj}} > 0$, and passes when $\text{CI}_{\text{lo,adj}} \le 0$ or when $\text{SE} = 4.0$.


---

## Reviewer addendum 

**Depth only close reading reveals:** the original rule has two independent false-alarm sources: the per-class test, which is multiple testing, and the noise band, which assumes 90% accuracy. Fixing one leaves the other. Only the middle row of the table controls both.

**Changelog:** [1] two independent sources named; [2] regime table for SE floor vs floor-dominance; [3] `drop_se = 0` is intended behaviour and should be documented; [4] Bonferroni is right for a gating rule and wrong for a discovery rule.

**Open questions:** Is `n_classes = 10` derived or hardcoded? An 11th class would silently raise the family-wise rate unless the denominator updates. Does `drop_se` use `ddof=1`?
