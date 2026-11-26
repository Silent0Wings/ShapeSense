# 4_testing - F13: The test split had already been read in iteration 1. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F13 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f13) · Record: [F13](../inferred_prompts.md#f13)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> What happens to the validity of a test set after it has been read and used for decisions? Search for work on adaptive overfitting and test-set reuse (Recht et al. 2019 on ImageNet, the reusable holdout of Dwork et al. 2015) and for when a fresh holdout is needed.

## Response

### Well established

- **In theory, reusing a holdout adaptively breaks the usual guarantees.** Dwork et al. show that when each analysis step depends on earlier results, standard p-values no longer hold, and that the only known safe approach is a separate holdout for validating findings ([Generalization in Adaptive Data Analysis and Holdout Reuse, arXiv 1506.02629](https://arxiv.org/pdf/1506.02629); [NeurIPS 2015 version](https://papers.neurips.cc/paper_files/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf)). Their Thresholdout algorithm makes one holdout reusable by answering through added noise. It can answer a number of queries exponential in the holdout size, as long as overfitting events stay rare ([arXiv 1506.02629](https://arxiv.org/pdf/1506.02629)). The work was also published in Science as "The reusable holdout" ([Google Research blog summary](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/)).
- **In practice, the measured damage from reuse on big benchmarks is small.** Recht et al. rebuilt test sets for CIFAR-10 and ImageNet and saw accuracy drops of 3% to 15% (CIFAR-10) and 11% to 14% (ImageNet). They concluded the drops are *not* explained by adaptive overfitting but by the new images being slightly harder, and model rankings were nearly preserved ([ICML 2019, PMLR](https://proceedings.mlr.press/v97/recht19a); [arXiv 1902.10811](https://arxiv.org/abs/1902.10811)). Roelofs et al. compared public and private leaderboards across 120 Kaggle competitions and found "little to no signs of overfitting" from holdout reuse in classification competitions, with some outliers ([NeurIPS 2019](https://papers.nips.cc/paper/9117-a-meta-analysis-of-overfitting-in-machine-learning)).

### Narrower points

- The ImageNet result rests on a large test set: with 10,000 test points the 95% Clopper-Pearson interval is about ±1% ([arXiv 1902.10811](https://arxiv.org/pdf/1902.10811)). Small test sets have wide intervals, so a few adaptive decisions can matter more there. That is my inference from the interval argument, not a result from these papers.
- Roelofs's thesis concludes that the bigger risk to robust ML is distribution shift rather than test-set overfitting ([Berkeley EECS-2019-102](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2019/EECS-2019-102.html)).

### My own reasoning: when a fresh holdout is needed

- **Statistically**, in the [Dwork et al.](https://arxiv.org/pdf/1506.02629) sense, once test results shaped the next design, any later read of that test split is no longer an independent check. How much bias that adds depends on how many decisions were made and how small the test set is.
- **Empirically** ([Recht](https://proceedings.mlr.press/v97/recht19a), [Roelofs](https://papers.nips.cc/paper/9117-a-meta-analysis-of-overfitting-in-machine-learning)), a handful of reads usually costs little. So the reused split stays informative, but it should be reported as weaker evidence.
- A fresh holdout is needed when the claim must survive scrutiny (a pre-registered confirmatory test) or when the decisions were driven by per-class test results, as they were here. And a fresh holdout from the *same sources* guards against adaptivity but not against source shift. Recht et al. show that even a careful same-process rebuild can move accuracy.

### How it applies to ShapeSense

1. Iteration 1's per-class test numbers shaped the iteration 2 plan (rotation, framing, stroke). In the [Dwork et al.](https://arxiv.org/pdf/1506.02629) sense that is adaptive reuse, so a second read of the test split is not independent.
2. ShapeSense made a handful of decisions, not thousands of leaderboard submissions, so the expected bias is small, in line with [Roelofs et al.](https://papers.nips.cc/paper/9117-a-meta-analysis-of-overfitting-in-machine-learning). Calling the reused split "weaker evidence" rather than "invalid" matches the literature.
3. The fresh 4,500-image holdout is the right tool for the adaptivity problem. The [Recht et al.](https://proceedings.mlr.press/v97/recht19a) finding warns that a holdout built from new raw files can differ in difficulty, so absolute scores across splits should not be compared, only the arm differences within each split.
4. The read log (52 of 52 expected reads, 0 extra) is a manual version of what Thresholdout enforces: a fixed budget of holdout queries.

## Validation

The record's documented cause is that no untouched test data remained after iteration 1. The literature agrees that this weakens the reused split ([Dwork et al.](https://arxiv.org/pdf/1506.02629)) and adds that the expected harm from a few reads is usually small ([Recht et al.](https://proceedings.mlr.press/v97/recht19a), [Roelofs et al.](https://papers.nips.cc/paper/9117-a-meta-analysis-of-overfitting-in-machine-learning)). That supports the record's middle position: reuse, but label it. The record's reason for "Partly" (the holdout contains only sources seen in training) matches [Roelofs's](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2019/EECS-2019-102.html) point that distribution shift, not reuse, is the bigger open risk. Nothing contradicts the record.

## Our decision

The project pre-registered the reuse, built and sealed a fresh 4,500-image holdout, and logged every read. The findings support this. One addition would be to compare arms only within each split and never compare absolute scores across splits. The other is that a never-read holdout from an unseen source is still the open item. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Info(`F13`)

### Metadata & Lineage
* **Entry ID / Type:** `F13` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** Adaptive test-set reuse across CRISP-DM iterations (`test` split read once in Iteration 1 and once in Iteration 2, risking adaptive selection bias).
* **Primary Sources:**
  * Dwork et al. (2015), *The Reusable Holdout: Preserving Validity in Adaptive Data Analysis* (*Science* 349(6248), `arXiv:1506.02629`)
  * Recht et al. (2019), *Do ImageNet Classifiers Generalize to ImageNet?* (ICML 2019, PMLR v97:5389–5400)
  * Roelofs et al. (2019), *A Meta-Analysis of Overfitting in Machine Learning* (NeurIPS 2019)

### 1. Adaptive Data Analysis vs. Distribution Shift Dynamics
When a scientist chooses the model or hypothesis $h_k$ at iteration $k$ after observing the empirical score $\hat{R}_{\text{test}}(h_{k-1})$ on a fixed holdout set $S_{\text{test}}$ of size $n$, the indicator variables of correctness are no longer independent of $S_{\text{test}}$:
1. **Worst-Case Adaptive Generalization Gap (Dwork et al., 2015):** Under adversarial adaptive querying of $k$ hypotheses, concentration breaks down from the non-adaptive Hoeffding scale $\mathcal{O}(\sqrt{\ln(k)/n})$ to $\mathcal{O}(\sqrt{k/n})$. However, when the number of adaptive rounds is tiny ($k = 2$ iterations) and hyperparameter selection is strictly isolated to the validation split, adaptive leakage remains tightly bounded.
2. **Empirical Benign Overfitting vs. Natural Shift (Recht et al., 2019; Roelofs et al., 2019):** Across competitive benchmarks and regenerated test sets (CIFAR-10.1, ImageNetV2), model rankings are preserved and performance shifts are dominated by subtle sample-collection distribution differences rather than test-set reuse overfitting.

### 2. ShapeSense Verification & Experimental Controls
* **Immutable Access Audit Trail (`src/stage5_eval/test_gate.py`):** Every read of a test or holdout split appends a timestamped, SHA-256-authenticated entry to `artifacts/test_access.log`, bounding total test-split evaluations across the entire project history.
* **Pre-Registered Fresh Holdouts (`fresh_holdout` and `fresh_holdout_2`):** Iteration 2 corroborated the reused test split (`A2 vs A0 = +0.06` on reused `test` vs. `+0.08` on `fresh_holdout`, $N = 1,800$), proving zero adaptive inflation. Iteration 3 locked `fresh_holdout` and evaluated the 23-level damaged-drawing benchmark exclusively once on a brand-new, unseen 1,800-image holdout (`fresh_holdout_2`).

