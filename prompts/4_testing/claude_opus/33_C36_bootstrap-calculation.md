# 4_testing - C36: Bootstrap calculation ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/36_C36_bootstrap-calculation.md](../gemini_4_neon/36_C36_bootstrap-calculation.md)
- Date: 2026-11-09
- Worksheet entry: C36 (`change`, `4_testing`)
- Owner / Proposed by: `40304911 + 40256377` / `opus_medium_5.5`
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `ShapeSense/src/stage5_eval/stats.py`, `ShapeSense/docs/crisp_dm/iteration_log.json`, `ShapeSense/results/phase2_snapshot/status5.json`, commit `534643d`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Our cluster bootstrap currently runs one sparse matrix product per damage level. Can we combine all 23 damage levels into one matrix product per block using the same random draws, and how do we verify every output number stays identical?

## Response ()

> **Opus 5.5:** Yes - you can combine all `levels` into one sparse `csc_matrix` of shape `(levels * k * k, m)` in `_cluster_counts` and execute a single `matrix @ weights.T` product per `CLUSTER_CHUNK` (64 draws) with the exact same `rng.multinomial` draws.
>
> Two details matter to guarantee bit-identical output:
>
> - **Identical draw sequence:** Keep `CLUSTER_CHUNK = 64` and the same `rng.multinomial(m, equal, size=stop - start)` call per block so the random weight matrix `weights` does not change.
> - **C-contiguous layout before averaging levels:** After reshaping `matrix @ weights.T` to `(levels, k, k, -1)` and calling `np.moveaxis(cells, -1, 1)` for `f1_from_confusion`, copy or force C order (`np.asarray(scores, order="C").mean(axis=0)`) before taking the mean across levels. NumPy's floating-point summation order depends on memory layout, so averaging directly over a transposed/strided view can shift the last bit of `delta` or `drop_observed`.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Loop `matrix.T @ weights.T` separately for each of 23 levels | Repeats sparse dispatch overhead 23 times per block | Replace |
> | Combined `(levels * k * k, m)` `csc_matrix` product without `order="C"` | Fast, but strided `moveaxis` layout can alter float-sum rounding bits | Avoid |
> | **Combined `csc_matrix` product + `order="C"` before `.mean(axis=0)`** | Removes repeated matrix dispatch while preserving exact floating-point bits and identical RNG draws | **Adopt** |
>
> To confirm every number stays the same, compare `delta`, `ci`, `drop_observed`, `drop_se`, `drop_ci_lo_adj`, and `p_two_sided` on the same `analysis_rng` input against the per-level loop, then run the Stage 5 tests and a full clean-clone rehearsal.

## Why this reading fits

Commit `534643d` applied this exact refactor in `src/stage5_eval/stats.py` (`_cluster_counts` returning a stacked `(levels * kk, m)` `csc_matrix`, single `matrix @ weights.T` per 64-draw block, and the explicit `# NumPy's float sums depend on memory layout; C order keeps the level mean's bits.` guard) as part of the behavior-preserving optimization pass.

## Validation

Verified through `tests/stage5/test_stats.py`, `tests/stage5/test_iteration3_repairs.py`, and the clean-clone rehearsal (`iteration_log.json`), which passed all seven pipeline stages and reproduced the Stage 5 verdict, every robustness figure, and every results table.

## Our decision

Merged the combined-level `csc_matrix` block product with `order="C"` level averaging into `src/stage5_eval/stats.py` (`534643d`), preserving the `CLUSTER_CHUNK = 64` multinomial draw sequence.

## Measured effect

Eliminated 22 of 23 sparse matrix dispatches per 64-draw bootstrap block across `fresh_holdout_2` with zero numerical drift: the clean-clone rehearsal reproduced `A2 vs A0 = +9.20` (`95% CI [8.89, 9.53]`) and all secondary and clean tables identically.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C36`)

### The dispatch-cost problem

Per 64-draw block, the original loops over $L = 23$ levels, each doing a sparse `csc_matrix @ weights.T` of shape $(k^2, m) \times (m, 64)$. Sparse dispatch overhead (indexing, format checks) dominates for small $k^2$ (10 classes $\rightarrow$ 100 rows). Combining to one matrix of shape $(L \cdot k^2, m)$ does **one** dispatch per block — a $23\times$ reduction in dispatch, with the same arithmetic.

### Why `order="C"` is not cosmetic (the float-summation derivation)

After `matrix @ weights.T`, reshape to $(L, k, k, B)$ and `np.moveaxis(cells, -1, 1)` to get $(L, B, k, k)$ for `f1_from_confusion`. This is a **strided view** — the last axis (cells) is non-contiguous in memory. Then `.mean(axis=0)` sums over $L$. Floating-point addition is non-associative: $(a+b)+c \neq a+(b+c)$ in general. NumPy's reduction over a strided axis may traverse in a different memory order than over a contiguous axis, producing a **last-bit difference** in the mean. That last bit propagates into $\Delta$, the CI endpoints, and the harm flags. The fix — `np.asarray(scores, order="C").mean(axis=0)` — forces a contiguous copy so the summation order is fixed and identical to the per-level loop.

**The bit-identity contract, stated formally:**

$$\text{combined}(R) \equiv_{\text{bit}} \text{per-level}(R) \quad \forall R \in \{0,1\}^{\text{seed space}}$$

verified by comparing $\{\Delta, \text{ci}, \text{drop\_observed}, \text{drop\_se}, \text{drop\_ci\_lo\_adj}, p\}$ elementwise with `==` (not `allclose`) on the same `analysis_rng` seed.

### Two-Legged Verification: Code-Path Equivalence + Environment Independence

A clean clone is the **strongest differential integration test** because it re-runs the *entire* pipeline from a fresh checkout — so any bit drift anywhere (not just in `stats.py`) would surface as a verdict mismatch. The rehearsal reproduced `+9.20 [8.89, 9.53]` exactly. Together with the `==` unit comparison on the same seed, **both legs are satisfied** — one for code-path equivalence, one for environment independence.

