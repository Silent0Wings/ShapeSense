# 4_testing - A27: A2 has no pairwise test against A1 or B.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A27 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/run.py, ShapeSense/configs/pipeline.yaml, ShapeSense/docs/crisp_dm/iteration_2/preregistration.md, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/results/phase2_snapshot/comparisons.csv, ShapeSense/results/phase2_snapshot/status5.json, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/iteration2.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: A2 has no pairwise test against A1 or B.

## Response
When iteration 2 introduced arm `A2` (clean real + augmented real + synthetic) and switched the primary comparison from `B vs A1` to `A2 vs A0`, the secondary comparison setup in `src/stage5_eval/run.py` did not fully adapt to the four-arm design:

- In `src/stage5_eval/run.py` (line 50), `SECONDARY_PAIRS` is still hardcoded as `((ARM_CONTROL, ARM_AUG), (ARM_CONTROL, ARM_SYNTH))` - i.e., `A1 vs A0` and `B vs A0` - while `primary_roles()` moved to `A2 vs A0`.
- That leaves `A2` tested only against the unaugmented baseline `A0` in the default Stage 5 pair list, with **no pairwise test of `A2` against either `A1` or `B`**. Without `A2 vs A1` and `A2 vs B` in the secondary Holm family, the evaluation cannot formally test whether mixing clean real images and synthetic images (`A2`) outperforms real-only augmentation (`A1`) or augmented + synthetic without clean real (`B`), or whether any `A2` gain over `A0` is already achieved by `A1` alone.

**Recommendation:** Add both `[A1, A2]` (`A2 vs A1`) and `[B, A2]` (`A2 vs B`) to `evaluation.secondary` in `configs/pipeline.yaml` (and update `SECONDARY_PAIRS` / pre-registration accordingly) so `A2` is directly tested against every active comparator under Holm correction.

## Validation
The team checked `src/stage5_eval/run.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/preregistration.md`, and `results/phase2_snapshot/iter2_status.json` against Gemini's claim. Inspection showed that Gemini had misread `SECONDARY_PAIRS` in `run.py` (the fallback default) as the active list: in iteration 2, `configs/pipeline.yaml` and `docs/crisp_dm/iteration_2/preregistration.md` had **already** included `A2 vs B` (`[B, A2]`) in `evaluation.secondary` alongside `A1 vs A0` and `B vs A0`. However, `A2 vs A1` (`[A1, A2]`) was genuinely missing from iteration 2's secondary comparisons. For iteration 3, `[A1, A2]` was added to `configs/pipeline.yaml#evaluation.secondary` (`[[A0, A1], [A0, B], [A1, A2], [B, A2]]`) and pre-registered in `docs/crisp_dm/iteration_3/preregistration.md` for both the 23-level perturbed and clean Holm families.

## Our decision
**Verdict: Partly.** Rejected the half of the claim regarding `A2 vs B` (already present in iteration 2's pre-registered secondary family via `configs/pipeline.yaml`), and accepted the half regarding `A2 vs A1`. Fixed in iteration 3 by adding `[A1, A2]` to `evaluation.secondary` so the Holm family tests all four comparisons: `A1 vs A0`, `B vs A0`, `A2 vs A1`, and `A2 vs B` (plus `A2 vs A0` in the clean secondary family).

## Measured effect
In iteration 3 on `fresh_holdout_2` across 23 perturbation levels (`status5.json`, `robust_comparisons.csv`, `ShapeSense_Deployed/web/stage5.html`), the newly added `A2 vs A1` comparison measures `+2.22` macro-F1 points (95% CI `[2.01, 2.44]`, `p_raw = 0.001`, `p_holm = 0.004`, though per-seed differences did not share the same sign across all 5 seeds: `1.29 ± 1.88`, seed 0 `-0.67`), while `A2 vs B` measures `+1.68` (95% CI `[1.50, 1.87]`, `p_holm = 0.004`). On clean `fresh_holdout_2`, `A2 vs A1` is `+0.21` (`[-0.07, 0.49]`, `p_holm = 0.242`) and `A2 vs B` is `+0.52` (`[0.23, 0.80]`, `p_holm = 0.005`); on the reused `test` split (`comparisons.csv`), `A2 vs A1` is `-0.1` (`[-0.7, 0.4]`, `p_holm = 1.000`).

---

## Upgraded Audit Entry (A27) & Cross-Cutting Stage 5 Audit Synthesis

### Part IV — Comparability & Coverage Cluster Context (`A21`, `A27`)

### A27 — A2 has no pairwise test against A1 or B

**Expanded reasoning — the half-right critique.** The critique read `SECONDARY_PAIRS` (the *fallback default* in `run.py`) as the *active* config. In iteration 2, `configs/pipeline.yaml` + pre-registration **already** included `[B, A2]`, so "A2 has no test against B" is false. But `[A1, A2]` was genuinely absent — so the critique is *partly* right on a real, consequential gap: without `A2 vs A1`, the design cannot test whether mixing clean+synthetic (A2) beats real-only augmentation (A1), i.e., whether A2's gain over A0 is already achieved by A1 alone.

**Deepened fix + measured nuance.** Adding `[A1, A2]` to `evaluation.secondary` pre-registers it for both the 23-level perturbed and clean Holm families. Results are *instructive*: perturbed `A2 vs A1 = +2.22` (`[2.01, 2.44]`, `p_holm=0.004`) **but** per-seed `{−0.67, +4.17, +1.83, +0.02, +1.10}`, `same_sign=false` — exactly the A20 scenario, where the tight test-sampling CI hides seed disagreement. Clean `A2 vs A1 = +0.21` (`[−0.07, 0.49]`, `p_holm=0.242`) is not significant; reused test is `−0.1`. So the newly added comparison *changes the scientific story*: A2's advantage over A1 is perturbation-specific and seed-inconsistent, not a clean-data effect. This is precisely why the missing comparison mattered — its absence suppressed an inconvenient result.

---

### Cross-Cutting Synthesis (Stage 5 Audit Meta-Lessons, `A15`–`A27`)

| Cluster | Entries | Root pathology | Why it's "silent" |
|---|---|---|---|
| Constant-as-check | A15, A16 | Assertion not measurement | Green check that cannot go red |
| Partial fingerprint | A18, A26 | Cache key < composed function | Stale hit on cached rerun only |
| Coupled accounting | A17 | Viz ↔ cache invalidation | Read is counted, so no harm — but design smell |
| Independence assumption | A19, A20 | Bootstrap unit ≠ data unit | Narrow CI looks *more* rigorous |
| Multiplicity / MPID | A22, A23, A24 | Hypothesis ≠ effect size | Wrong test with right-looking number |
| Optimism / coverage | A25, A21, A27 | Proxy ≠ target; partial path read | Under-estimate or missing test hides result |

**Three recurring failure signatures worth naming:**

1. **The green-constant (A15).** Any `checks.X == 0` where `X` is assigned a literal is a *claim*, not a *measurement*. Audit rule: every boolean in `status.json` must trace to a computed value with a failing counterexample in tests.
2. **The composed-function key (A16, A18).** If `f = g ∘ h`, the cache key must hash *both* `g` and `h`. Hashing weights but not preprocessing is the canonical instance.
3. **The conditional-vs-unconditional statistic (A20, A22, A25).** CIs conditional on trained seeds, tests unadjusted across classes, and power run on in-sample validation all *look* rigorous and are *systematically over-precise*. The correct mitigation when the primary rule is pre-registered and sealed is **dual reporting** (`strict_pass`, `same_sign`, `drop_ci_lo_adj`, "lower bound") — never silently swapping the rule post-read.

**Ordering dependency.** A26 (RNG isolation) is a *prerequisite* for A27 (adding a comparison) to be non-perturbing; A16 (stamp) is a *prerequisite* for A17's refresh to be correct rather than accidental. The audit's value comes from these couplings — fixing one entry in isolation can be inert or even harmful if its prerequisite is unaddressed.

**Residual risks the audit correctly leaves open** (each is honestly documented, not silently dropped): `tables.py` legacy `p_raw` column still shows McNemar for the old test-split table (A24); `ensemble()` has no internal size assertion if called outside `per_seed_differences` (A21); a reader of `comparisons.csv` alone could over-trust the test-sampling CI without `same_sign` (A20); and `crc32` stream aliasing is theoretically possible for colliding analysis names (A26). None are currently exploitable, and all are flagged rather than concealed — which is itself the mark of a trustworthy audit.

