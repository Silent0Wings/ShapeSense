# 4_testing - C20: Bootstrap resamples near-duplicate clusters
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/31_C20_bootstrap.md](../claude_opus/31_C20_bootstrap.md)
- Date: 2026-11-09
- Entry: C20 (`change`, `4_testing`)
- Owner / Proposed by: 40253714 + 40304911 / opus_medium_5.5 + 40253714 + 40304911
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, src/stage5_eval/stats.py, src/stage5_eval/criterion.py, configs/pipeline.yaml, docs/crisp_dm/iteration_3/preregistration.md, tests/stage5/test_iteration3_repairs.py, results/phase2_snapshot/status5.json, commit 4c7cb90



## Prompt

> **User:** Our bootstrap resamples images independently, even though near-duplicate images share a `phash_group`. How should the bootstrap resample clusters instead, and should we add a source-clustered check beside the primary?

## Response
Yes. Resampling images independently assumes each image is an independent draw. Near-duplicates are not: if two images in one group are almost the same picture, both arms tend to get them both right or both wrong. An image bootstrap then counts that agreement twice and the interval comes out narrower than the evidence supports. That makes it easier to pass the "CI excludes 0" condition than it should be.

**The cluster bootstrap.** Resample whole `phash_group` clusters with replacement, so a group enters or leaves a resample together. Keep it paired: draw one set of cluster weights per resample and score both arms on that same resample. Everything else in the rule stays as in iteration 2: 2,000 resamples, seed 0, 95% percentile interval (`evaluation.n_boot`, `bootstrap_seed` and `success_criterion.ci_level` in `configs/pipeline.yaml`).

A sketch of the core loop:

```python
weights = rng.multinomial(m, equal, size=block)   # m clusters, equal probability
fa, fb = per_class(counts_a, weights), per_class(counts_b, weights)
deltas[start:stop] = fb.mean(axis=1) - fa.mean(axis=1)
```

Counting confusion cells per cluster once, and then weighting those counts, avoids looping over images in every resample.

**The source-clustered interval.** It answers a different question: how much would the gain move if the mix of sources changed? I would report it beside the primary as a sensitivity check, not as the decision interval. With three sources in the holdout it is coarse: a bootstrap over three units gives very few distinct resamples, so its interval is wide and unstable. Making it the primary would turn the rule into "pass only if all three sources agree", which is a different hypothesis from the one we want to test.

| Interval | Unit | Role | Caution |
|---|---|---|---|
| Image bootstrap | image | none (replaced) | Too narrow with near-duplicates |
| `phash_group` bootstrap | near-duplicate cluster | primary | Equals the image bootstrap where every group has one image |
| Source-clustered | source | reported sensitivity check | Three units: coarse |

**Timing.** This has to be committed in the pre-registration before any iteration 3 tuning or sealed read. Choosing the resampling unit after seeing the result would be choosing the interval.

Tests I would add: on a planted case with duplicated images, the cluster interval is wider than the image interval; and several damage levels are scored on the same resample.

## Validation
`src/stage5_eval/stats.py::cluster_bootstrap` resamples clusters with a multinomial draw and scores both arms on the same weights. `tests/stage5/test_iteration3_repairs.py` holds `test_clusters_widen_the_interval_when_images_are_near_duplicates` and `test_levels_are_averaged_and_scored_on_the_same_resample`. The iteration 3 pre-registration states: "resampling `phash_group` clusters with both arms scored on the same resample. A source-clustered interval is reported as a sensitivity check; with three sources it is coarse."

## Our decision
Adopted: `phash_group` clusters resampled, with a source-clustered check beside the primary (commit 4c7cb90), because near-duplicate images are not independent.

## Measured effect
On the sealed iteration 3 primary (`status5.json`, A2 vs A0 on damaged fresh holdout 2): +9.20 points, cluster CI [8.89, 9.53], with 4,500 clusters for 4,500 images. The source-clustered interval is [3.89, 9.42]. No image-bootstrap interval on the same data is recorded for a before -> after comparison.

---

##  Technical Analysis (`C20`)

### 1. Design-Effect Variance Inflation Math (`deff`)
When $n$ evaluation images are partitioned into $m$ near-duplicate `phash_group` clusters of mean size $\bar{n}_c = n / m$ with intra-cluster error correlation $\rho \in [0, 1]$, the true sampling variance of the mean score difference is inflated relative to naive i.i.d. image resampling ($\sigma^2 / n$) by Kish's design effect:
$$\text{deff} = 1 + (\bar{n}_c - 1)\rho, \qquad \text{Var}_{\text{cluster}}(\hat{\Delta}) \approx \text{deff} \cdot \frac{\sigma^2_{\text{paired}}}{n}$$
- For near-duplicate drawings ($\text{Hamming} \le 2$), both arms almost always succeed or fail together on members of the same cluster ($\rho \to 1$), so $\text{deff} \approx \bar{n}_c$ and the effective sample size collapses from $n$ images to $m$ clusters. Naive image-level bootstrap understates the CI half-width by roughly $\sqrt{\text{deff}}$, making `ci[0] > 0` artificially easy to pass.
- **Degenerate Singleton Reduction:** When every cluster in a deduplicated split has size $1$ ($m = n = 4,500$, so $\bar{n}_c = 1$ and $\text{deff} = 1$), multinomial cluster resampling (`rng.multinomial(m, equal, size=block)`) is mathematically identical to i.i.d. image resampling — making `cluster_bootstrap` a strict generalization of `paired_bootstrap`.

### 2. Paired Weight Sharing & Primary vs. Sensitivity Roles
- **Paired Multinomial Weighting:** Drawing a single weight vector `weights` per resample and scoring both `counts_a` and `counts_b` (and all 23 damage levels) on that exact same weight vector preserves the positive inter-arm covariance $\text{Cov}(\hat{F}_1(A), \hat{F}_1(B))$, avoiding the spurious CI widening of unpaired resampling.
- **Why Source-Clustered (`[3.89, 9.42]`) Is Sensitivity-Only:** Resampling over only $m = 3$ sources produces at most $\binom{3+3-1}{3} = 10$ unique unweighted multiset combinations per draw, answering *"how much would the gain move if the source mix shifted?"* rather than testing fixed-population performance. Pre-registering `phash_group` as primary and `source` as a sensitivity check before any tuning or sealed read prevents post-hoc interval shopping.


---

## Reviewer addendum 

**Depth only close reading reveals:** the mechanism is double counting. Near-duplicate images get both arms right or both wrong, so an image bootstrap counts that agreement twice and the interval is too narrow. That is why the rule is easier to pass than it should be.

**Changelog:** [1] mechanism stated, not only the rule; [2] equivalence on singleton groups is the correctness anchor and should be a test; [3] three source units give at most 10 distinct resamples, so the source interval is barely a distribution.

**Open questions:** Is `equal` in `rng.multinomial(m, equal, ...)` uniform over clusters, or weighted by cluster size? Equal-probability clusters and size-weighted images estimate different things.
