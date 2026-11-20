# 4_testing - C20: Bootstrap ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/32_C20_bootstrap.md](../gemini_4_neon/32_C20_bootstrap.md)
- Date: 2026-11-09
- Worksheet entry: C20 (`change`, `4_testing`)
- Owner / Proposed by: `40253714 + 40304911` / `opus_medium_5.5 + 40253714 + 40304911`
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `ShapeSense/src/stage5_eval/stats.py`, `ShapeSense/src/stage5_eval/robust.py`, `ShapeSense/src/stage5_eval/run.py`, `ShapeSense/tests/stage5/test_iteration3_repairs.py`, `ShapeSense/docs/crisp_dm/iteration_3/preregistration.md`, `ShapeSense/results/phase2_snapshot/status5.json`, commit `4c7cb90`, `ShapeSense_Deployed/web/stage5.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Our bootstrap resamples images independently, even though near-duplicate images share a `phash_group`. How should the bootstrap resample clusters instead, and should we add a source-clustered check beside the primary?

## Response ()

> **Opus 5.5:** Resample `phash_group` clusters instead of individual images so every member of a near-duplicate group enters or leaves a bootstrap draw together, and report a source-clustered interval alongside the primary as a descriptive sensitivity check rather than the primary gate.
>
> Key design choices for `cluster_bootstrap`:
>
> - **Cluster multinomial weights:** Map `groups` (`phash_group`) to `m` unique cluster IDs and draw `rng.multinomial(m, 1/m)` weights per replicate rather than `n` independent image indices. Score both `reference` and `candidate` predictions on the exact same cluster weights - and for multi-level robustness evaluation, score all 23 damage levels on that same draw and average per-class F1 across levels.
> - **Sparse count aggregation:** Pre-aggregate per-cluster confusion counts into a sparse matrix (`_cluster_counts`) so each replicate reduces to a sparse matrix product instead of re-indexing images.
> - **Isolated per-analysis RNG:** Give every comparison its own `SeedSequence` spawned by analysis name (`analysis_rng(seed, name)`), so adding or reordering secondary comparisons never changes the primary interval.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Image-level bootstrap (`paired_bootstrap`) | Treats near-duplicates as independent, artificially narrowing CIs | Replace with `cluster_bootstrap` |
> | `phash_group` cluster bootstrap + descriptive source-clustered check | Accounts for near-duplicate dependence while checking source-level sensitivity without making `m = 3` sources decide the test | **Adopt** (`preregistration.md`) |
> | Source-clustered bootstrap as primary gate | With only 3 sources, resampling 3 clusters produces overly coarse, erratic CIs | Report as sensitivity check only |
>
> Keeping `phash_group` as the primary clustering unit respects the same boundary your split guard enforces, while the source-clustered interval tells readers how much of the gain persists if whole sources vary.

## Why this reading fits

Outside code reviews flagged independent image resampling and shared RNG streams (`iteration_log.json` audit items). Commit `4c7cb90` implemented `cluster_bootstrap`, `_cluster_counts`, and `analysis_rng` directly in `src/stage5_eval/stats.py`, wired `phash_group` primary plus `ci_clustered_by_source` in `src/stage5_eval/robust.py` and `run.py`, and pre-registered both in `docs/crisp_dm/iteration_3/preregistration.md`.

## Validation

Verified by `tests/stage5/test_iteration3_repairs.py`: `test_clusters_widen_the_interval_when_images_are_near_duplicates` confirms 8x-tiled duplicates widen `half_width` by more than `1.8x` under cluster resampling, `test_levels_are_averaged_and_scored_on_the_same_resample` verifies multi-level pairing, and `test_named_generators_do_not_depend_on_the_order_of_analyses` confirms RNG independence.

## Our decision

Replaced independent image resampling with `cluster_bootstrap` on `phash_group` across `run.py` and `robust.py`, added `analysis_rng` per comparison, and reported `ci_clustered_by_source` beside the primary `A2 vs A0` verdict (`4c7cb90`).

## Measured effect

On `fresh_holdout_2` (`n = 4,500`, `n_clusters = 4,500`), primary `A2 vs A0` delivered `+9.20` macro-F1 points with `phash_group` 95% CI `[8.89, 9.53]`, and the source-clustered sensitivity check gave `[3.89, 9.42]` - confirming the gain remains well above zero even under coarse 3-source resampling.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C20`)

### 1. Cross-Document Synthesis: The Latent Architecture

The `4_testing` corpus is a **layered evidence system** with four epistemic layers:
- **Layer 1 — Measurement integrity (`C20`, `C21`, `C36`):** Cluster resampling $\rightarrow$ corrected harm rule $\rightarrow$ bit-identical computation. If any link breaks, the CI is wrong and the verdict is void.
- **Layer 2 — Provenance immutability (`F28`, `F26`, `F16`):** Closed iterations must not be silently overwritten (`F28`), stages must fail-closed (`F26`), and clean clones must reproduce (`F16`).
- **Layer 3 — Contract integrity (`F15`, `C19`, `F30`, `C41`, `C45`–`C55`):** Schema bounds, export uniformity, split stratification, and chart honesty.
- **Layer 4 — The verdict and its refusal to be gamed (`49_real`, `50_real`):** Fix the rule before the read, report what happened.

### 2. Deepened Analysis: Hierarchical Dependence & Cluster Resampling (`31_C20_bootstrap.md`)

**Complexity upgrade:** Cluster resampling is a **hierarchical dependence problem** with three nested clustering levels (`image` $\rightarrow$ `phash_group` $\rightarrow$ `source`) and a power/validity trade-off at each level.

#### The dependence structure (why image-level resampling is wrong)

Let images be indexed by $i$, grouped into near-duplicate clusters $g = \text{phash\_group}(i)$, and sources $s = \text{source}(i)$. The naive bootstrap draws $\{i_1, \dots, i_n\}$ i.i.d., assuming $\text{Cov}(Y_i, Y_j) = 0$ for $i \neq j$. For $i, j$ in the same `phash_group`, the drawings are near-identical, so $\text{Cov}(Y_i, Y_j) > 0$. Under positive intra-cluster correlation $\rho$, the naive variance estimate is **biased downward** by approximately a factor of $1 + (m-1)\rho$ where $m$ is cluster size. The CI is therefore too narrow — a false precision that would make the `+9.20` gain look more certain than it is.

**The formal fix:** Draw cluster weights $w_g \sim \text{Multinomial}(m, 1/m)$ where $m$ = number of clusters, and score the statistic as:

$$\hat{\Delta}^{(b)} = \frac{1}{L}\sum_{\ell=1}^{L} \text{macroF1}\big(\text{confusion}(\{w_g^{(b)}\}, \ell)\big) - \text{macroF1}\big(\text{confusion}_0(\{w_g^{(b)}\}, \ell)\big)$$

with the **same draw** $w^{(b)}$ applied to both arms and all $L=23$ damage levels.

#### Three-level sensitivity logic

| Level | Clusters | Resamples | Validity | Power | Role |
|---|---|---|---|---|---|
| Image | $n = 4,500$ | $4,500$ | Invalid (understates var) | High | Rejected |
| `phash_group` | $m = 4,500^*$ | $\sim 4,500$ | Valid for duplicate dependence | High | **Primary gate** |
| Source | $3$ | $3$ | Valid but extremely coarse | Very low | Descriptive only |

*$^*$Note: in `fresh_holdout_2`, `n_clusters = n`, so `phash` clustering widens CIs where duplicates exist (the $8\times$-tiled test confirms the $>1.8\times$ widening).*

**The logic of "sensitivity, not gate":** With only 3 sources, resampling 3 clusters yields a bootstrap distribution over essentially 3 distinct configurations — the CI is erratic and would either always pass or always fail depending on which source is held out. Making it descriptive preserves the information (`"the gain survives coarse source resampling: [3.89, 9.42]"`) without letting a low-power procedure gate a high-power one (**power-validity separation principle**).

#### Verification chain

1. *Widening test* — proves the fix does something ($8\times$ duplicates $\rightarrow$ $>1.8\times$ half-width).
2. *Pairing test* — proves the draws are shared (multi-level scoring on same resample).
3. *Independence test* — proves adding an analysis doesn't perturb the primary (named RNG streams).
4. *Null-calibration check (recommended extension)* — simulate under $H_0$ (`A2 ≡ A0`) and confirm the cluster CI covers $0$ at $\sim 95\%$ rate.

