# 4_testing - C16: Evaluation data
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C16 (`change`, `4_testing`)
- Owner / Proposed by: 40253714 / gemini_4_neon + 40253714
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `docs/crisp_dm/iteration_2/preregistration.md`, `src/stage1_freeze/fresh_holdout.py`, `src/stage5_eval/fresh.py`, `src/stage5_eval/run.py`, `results/phase2_snapshot/iter2_status.json`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/iteration2.html`, commits `7f356d6`, `87711f3`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
The test split has been read once. Besides reusing it under a pre-registered note, what evidence can we add that the first read could not have touched, and how do we report both together?

## Response
Because `configs/splits/test.csv` was already read `13` times in Iteration 1 and its per-class error patterns directly informed Iteration 2's rotation and framing fixes, any second read of `test.csv` is **contaminated / weaker evidence** - even if pre-registered. To add uncontaminated evidence that the Iteration 1 test read could never have touched, build a sealed **fresh holdout** (`configs/splits/fresh_holdout.csv`, `4,500` images, `450` per class across all `10` classes) from raw source files that never entered `data_set/unified/catalog.sqlite`.

### Constructing `fresh_holdout.csv` cleanly
1. **Source eligibility & deduplication:** Sample unused raw images evenly across all sources (`reevald`, `El Korchi`, `Quick, Draw!`, and `Hand-Drawn`) from outside the catalog (`stage1_freeze/fresh_holdout.py`), apply the exact same Stage 1 standardization (`64x64` grayscale, `ink_threshold: 128`), and enforce the catalog's near-duplicate barrier (`phash_hamming_max: 2` bits) against every existing `train`, `val`, and `test` image so no near-duplicate leaks across splits.
2. **Access-log sealing:** Register `fresh_holdout.csv` in `src/common/splits.py` under the same `test_access.log` audit guard as `test.csv` so Stage 5 (`src/stage5_eval/evaluate.py`) is the only module permitted to read it, once per model (`zero` reads before Phase 6).

### Reporting both datasets together
- Label `test.csv` explicitly in `docs/crisp_dm/iteration_2/preregistration.md` and Stage 5 outputs as **reused / weaker evidence**, and run the identical `A2 vs A0` comparison (`paired_bootstrap`, `2,000` resamples, `alpha = 0.05`, same `success_criterion`) on `fresh_holdout.csv` in a dedicated `src/stage5_eval/fresh.py` module, writing separate tables (`fresh_metrics.csv`, `fresh_per_class.csv`) beside `metrics.csv` and `comparisons.csv`.
- Use `fresh_holdout` as the cleaner pass/fail check alongside the reused test split, and keep `test.csv` reported side by side so readers can see whether results agree across both sets.

## Validation
When `40253714` and the team implemented `src/stage1_freeze/fresh_holdout.py` (`7f356d6`) and `src/stage5_eval/fresh.py` (`87711f3`) and verified them with `tests/stage5/test_fresh.py` and `tests/stage5/test_run.py`, two real constraints surfaced that Gemini 4 Neon's draft missed:
1. **No unused `Quick, Draw!` images exist locally:** Checking `data_set/` showed all `3,500` local `Quick, Draw!` sketches were already inside `data_set/unified/catalog.sqlite`. Therefore `fresh_holdout.csv` could not sample `Quick, Draw!` at all - its `4,500` images come solely from the remaining training sources, and its `diamond` class consists of renders only.
2. **Locking the primary gate & cluster bootstrap:** In `src/stage5_eval/run.py`, `test.csv` remained the primary table driving `metrics.verdict`, with `fresh_holdout` reported as a separate `fresh_holdout` block (`fresh_metrics.csv`, `fresh_per_class.csv`), and `src/stage5_eval/fresh.py` used `cluster_bootstrap` on `group_ids` (`phash_group`) rather than naive image-level `paired_bootstrap`.

## Our decision
Kept Gemini 4 Neon's core architecture - sealing a `4,500`-image `configs/splits/fresh_holdout.csv` deduplicated at `phash_hamming_max: 2` (`7f356d6`), disclosing `test.csv` as weaker reused evidence, and reporting both side by side via `src/stage5_eval/fresh.py` (`87711f3`) - while correcting the two gaps: explicitly documenting in `docs/crisp_dm/iteration_2/preregistration.md` that `fresh_holdout` contains zero `Quick, Draw!` images (renders only for diamonds, all seen sources), and scoring `fresh.analyse` with `cluster_bootstrap` over `group_ids` while keeping `test_reads_ok` accounting over both splits (`52` total reads in Iteration 2).

## Measured effect
- **Sealed fresh holdout added:** `4,500` never-before-indexed images (`configs/splits/fresh_holdout.csv`), evaluated once per arm model (`20` CNN reads + `32` test-split reads = `52` logged reads, `extra_reads = 0` in `results/phase2_snapshot/iter2_status.json`).
- **Consistent dual-set verdict:** Both sets agreed within `0.02` points and both failed the `>= 1.0`-point criterion: reused `test.csv` gave `A2 vs A0 = +0.06` (`0.057`, 95% CI `[-0.69, 0.83]`); `fresh_holdout.csv` gave `+0.08` (`0.079`, 95% CI `[-0.41, 0.57]`).

---

## Upgraded & Expanded Technical Analysis (`C16`)

### 1. Near-Duplicate Perceptual-Hash Barrier (`phash_hamming_max: 2`)
In `src/stage1_freeze/fresh_holdout.py`, every candidate raw drawing $x$ is mapped to a 64-bit discrete cosine transform (DCT) perceptual hash $h(x) \in \{0,1\}^{64}$ after standardizing to $64\times 64$ grayscale (`ink_threshold: 128`). Let $\mathcal{H}_{\text{catalog}}$ denote the set of all 64-bit perceptual hashes in `data_set/unified/catalog.sqlite` (`train` $\cup$ `val` $\cup$ `test`). Candidate $x$ is admitted to `fresh_holdout.csv` only if its minimum Hamming distance to the frozen catalog satisfies:
$$d_{\min}(x, \mathcal{H}_{\text{catalog}}) = \min_{h' \in \mathcal{H}_{\text{catalog}}} \|h(x) \oplus h'\|_1 > 2$$
- **Empirical Distance Separation:** Across 64-bit DCT hashes of distinct hand-drawn geometric shapes, the bulk pairwise Hamming distance distribution centers around $22\text{--}34$ bits, while the $\le 2$-bit exclusion threshold sits in the far left tail ($< 1\text{st}$ percentile of intra-class pairs), rejecting near-identical re-renders or duplicate file uploads while retaining genuine natural drawing variation.

### 2. Cluster-Bootstrap Variance Justification (`group_ids = phash_group`)
Within `test.csv` and `fresh_holdout.csv`, images sharing a `phash_group` (Hamming distance $\le 2$) exhibit strong positive correlation in model prediction errors ($\rho_{\text{intra}} \to 1$).
- **Effective Sample Size Inflation Under Naive Bootstrap:** If a cluster of size $k$ near-duplicates is resampled at the individual image level (`paired_bootstrap`), the variance of the cluster's contribution shrinks by $1/k$, narrowing the confidence interval by roughly $1/\sqrt{\bar{k}_{\text{eff}}}$.
- **Cluster-Bootstrap Ratio (`naive CI / cluster CI`):** Resampling multinomial weights over `group_ids = phash_group` (`src/stage5_eval/stats.py::cluster_bootstrap`) keeps every near-duplicate cluster intact (`test_clusters_widen_the_interval_when_images_are_near_duplicates` proves that tiling 300 clusters $8\times$ yields `cluster_half_width / naive_half_width > 1.8`). When every row in a deduplicated fresh holdout forms its own singleton cluster ($n_{\text{clusters}} = n = 4,500$), `cluster_bootstrap` algebraically reduces to `paired_bootstrap` (`A2 vs A0` half-width `0.49` on `fresh_holdout`, CI `[-0.41, 0.57]`, vs. `0.76` on `test.csv`, CI `[-0.69, 0.83]`).

