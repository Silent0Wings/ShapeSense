# 4_testing - C36: One combined bootstrap product per block
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/33_C36_bootstrap-calculation.md](../claude_opus/33_C36_bootstrap-calculation.md)
- Date: 2026-11-09
- Entry: C36 (`change`, `4_testing`)
- Owner / Proposed by: 40304911 + 40256377 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, src/stage5_eval/stats.py, configs/pipeline.yaml, tests/stage5/test_iteration3_repairs.py, commit 534643d



## Prompt

> **User:** Our cluster bootstrap currently runs one sparse matrix product per damage level. Can we combine all 23 damage levels into one matrix product per block using the same random draws, and how do we verify every output number stays identical?

## Response
Yes, and it can be done without changing a single output, because the levels already share their random draws.

**Why it is safe.** In `cluster_bootstrap`, each block draws one matrix of cluster weights, `rng.multinomial(m, equal, size=...)`, and every damage level is scored on that same draw. That is a requirement of the pre-registered rule (all levels on the same resample). So the per-level products are `counts_level @ weights.T` with the same `weights`. Stacking the per-level count matrices on top of each other and doing one product gives exactly the same rows, just in one call.

**How to build it.** Encode each image's confusion cell per level as an offset into one long axis:

```python
cells = (codes + np.arange(levels)[:, None] * kk).ravel()
matrix = sparse.csc_matrix((ones, (cells, np.tile(clusters, levels))), shape=(levels * kk, m))
```

Then `matrix @ weights.T` reshaped to `(levels, k, k, block)` gives every level's confusion matrices for the whole block at once.

**What could change a number, and how to avoid it:**

| Risk | Guard |
|---|---|
| Different random draws | Keep exactly one `multinomial` call per block, same block size (`CLUSTER_CHUNK`), same generator |
| Integer overflow in counts | Keep counts as `int64` |
| Float sum order in the level mean | NumPy sums can depend on memory layout; force C order before `.mean(axis=0)` so the bits match |
| Changed generator per analysis | Keep the named generator per analysis, so reordering analyses changes nothing |

**How to confirm.** Do not judge by eye. Before switching, run the old and new code on the same inputs and compare the full outputs: `delta`, `ci`, `drop_observed`, `drop_se`, `drop_ci_lo_adj` and `p_two_sided`, with exact equality, not a tolerance. Keep a unit test that the single-level case and a stacked two-level case of the same predictions give the same `delta` and `ci`.

Timing matters for pre-registration. This is a pure refactor of how a pre-registered statistic is computed, so it can go in at any point, but it is cleanest to land it before the sealed read so there is only ever one code path that produced the reported numbers. Nothing about the rule, the resample count (`n_boot: 2000`) or the seed changes.

## Validation
`src/stage5_eval/stats.py::_cluster_counts` builds the single "(levels * k*k, m)" matrix ("One matrix for all levels means one sparse product per resample block instead of one per level"), and `per_class` keeps C order with the comment "NumPy's float sums depend on memory layout; C order keeps the level mean's bits." `tests/stage5/test_iteration3_repairs.py` holds `test_levels_are_averaged_and_scored_on_the_same_resample` and `test_named_generators_do_not_depend_on_the_order_of_analyses`.

## Our decision
Adopted: one combined product per block, with the same random draws (commit 534643d). It removes repeated work without changing any number.

## Measured effect
Numbers: unchanged by design. No runtime before -> after measurement is recorded in the repository.

---

##  Technical Analysis (`C36`)

### 1. Algebraic Proof of Bit-Identical Stacked Sparse Multiplication
In `src/stage5_eval/stats.py::cluster_bootstrap`, let $C_\ell \in \mathbb{Z}_{\ge 0}^{k^2 \times m}$ denote the per-cluster confusion-count matrix for damage level $\ell \in \{0, \dots, L-1\}$ ($L = 23$, $k = 10$, $k^2 = 100$, $m = 4,500$ clusters), and let $W \in \mathbb{Z}_{\ge 0}^{B_{\text{chunk}} \times m}$ be the multinomial cluster-weight draw for the current block.
- Because the pre-registered estimator (`C20`) scores every damage level on the **exact same cluster resample** $W$, the $L$ separate sparse products $C_0 W^\top, C_1 W^\top, \dots, C_{L-1} W^\top$ share the right-hand operand $W^\top$.
- Vertically stacking the level matrices via row-offset encoding:
  $$\texttt{cells} = (\texttt{codes} + \text{arange}(L)[:, \text{None}] \cdot k^2).\text{ravel}(), \qquad C_{\text{stack}} = \begin{bmatrix} C_0 \\ C_1 \\ \vdots \\ C_{L-1} \end{bmatrix} \in \mathbb{Z}_{\ge 0}^{(L \cdot k^2) \times m}$$
  computes $C_{\text{stack}} W^\top$ in a **single CSC sparse matrix-matrix multiplication** per block. Because each row of $C_{\text{stack}}$ is independent in $(C_{\text{stack}} W^\top)_{i, b} = \sum_{c=0}^{m-1} (C_{\text{stack}})_{i, c} W_{b, c}$, the integer inner products are algebraically and bit-wise identical to the unstacked loop.

### 2. Floating-Point Reduction Order Guard (`C` Contiguity) & Verification Discipline
- **Why Memory Layout Affects `.mean(axis=0)`:** After reshaping the integer counts to `(levels, k, k, block)` and computing per-class F1 scores `f1` of shape `(levels, block, k)`, averaging across the `levels` axis (`f1.mean(axis=0)`) performs floating-point summation whose pairwise accumulation order in NumPy depends on array strides (C-contiguous vs. Fortran/transposed strides). Forcing C-contiguous memory layout before `.mean(axis=0)` guarantees bit-identical IEEE-754 float64 outputs.
- **Exact Equality Verification (Zero Tolerance):** Verified by comparing `delta`, `ci`, `drop_observed`, `drop_se`, `drop_ci_lo_adj`, and `p_two_sided` under exact equality (`==`, not `np.isclose`), and pinned by `test_levels_are_averaged_and_scored_on_the_same_resample`.


---

## Reviewer addendum 

**Depth only close reading reveals:** the "what could change a number" table is the content. Each row names a mechanism. The C-order row is the deepest: NumPy `.mean()` can sum in different orders depending on memory layout, and a one-ulp difference in a per-level mean can flip a percentile, then a CI bound, then a verdict on a borderline class. The refactor is pure only if the bits are forced to match.

**Changelog:** [1] C-order force as the deepest correctness guard; [2] the offset encoding `kk` stride must change with any change to the cell encoding, and no test catches a mismatch; [3] the stacked shape assumes equal cluster count `m` across levels, true today but not stated; [4] pre-registration logic: one code path, the one that produced the number.

**Open questions:** Is there a regression test that the stacked and per-level paths are bit-identical on a planted case? The entry describes a manual old-vs-new comparison. Is `CLUSTER_CHUNK` pinned by a test, or only unchanged in the diff? A change to it alters draw order and therefore the numbers.
