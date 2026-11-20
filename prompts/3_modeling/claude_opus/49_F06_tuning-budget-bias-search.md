# 3_modeling - F06: Augmentation and generator ranges were set by hand, and only A1 was tuned. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F06 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f06) · Record: [F06](../inferred_prompts.md#f06)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> Is it a fair comparison to tune hyperparameters on one method and reuse them for the others? Search for evidence on tuning-budget bias in ML comparisons (for example Melis et al. 2018 and Bouthillier et al. 2021) and for recommended protocols when arms differ in their training data.

## Response

### Well established

- **Unequal tuning can reverse a ranking.** Melis, Dyer and Blunsom re-tuned several language-model architectures with large-scale automatic black-box search and found that standard LSTMs, properly regularised, beat newer models, "contra the published claims". They recommend flagging methods that need many hyperparameters or work only in narrow ranges ([arXiv 1707.05589](https://arxiv.org/abs/1707.05589v2), [ICLR 2018](https://iclr.cc/virtual/2018/poster/214)).
- **The search space and the budget decide the result.** Choi et al. show that optimizer rankings depend on the tuning protocol and can be reversed by changing search spaces. With enough tuning, rankings settle according to which method includes which. They advise skepticism toward claims that do not detail the tuning protocol ([arXiv 1910.05446](https://arxiv.org/abs/1910.05446v3)).
- **Hyperparameter choice is a source of variance, alongside data sampling and initialisation.** Bouthillier et al. model the whole benchmarking process and find that all three sources noticeably move results. They recommend randomising over more sources of variation. They report that a biased estimator that includes more sources can sit closer to the ideal one at 51 times lower cost ([MLSys 2021](https://proceedings.mlsys.org/paper_files/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html), [arXiv 2103.03098](https://arxiv.org/abs/2103.03098)).
- **Report performance as a function of budget.** Dodge et al. propose expected validation performance: the expected best validation score after n trials, plotted for n = 1..N. They show that which model is best can change with the budget, and that the curve can be computed from trials already run ([EMNLP 2019](https://aclanthology.org/D19-1224/), [arXiv 1909.03004](https://arxiv.org/abs/1909.03004v1)). A follow-up criticises the estimator and shows how it can mislead ([Tang et al., ACL 2020](https://aclanthology.org/2020.acl-main.246)).
- **Fixed tuning budgets, declared in advance.** The MLCommons AlgoPerf benchmark compares training algorithms under fixed hardware and a defined tuning procedure, and concludes that good search spaces must be tailored to the tuning budget ([Dahl et al., arXiv 2306.07179](https://arxiv.org/abs/2306.07179)).

### Single reports and broader context

- Dehghani et al. argue that many factors other than real algorithmic superiority, such as benchmark choice and evaluation setup, decide which method looks best ([The Benchmark Lottery, arXiv 2107.07002](https://arxiv.org/abs/2107.07002)). This is a position paper, not a controlled study of tuning budgets.

### What I could not find

I found no protocol written specifically for comparing **training-data arms** (real vs augmented vs synthetic) rather than models or optimizers. The principles transfer directly, though, because each arm changes the effective data distribution and so its best learning rate and regularisation.

### Reasoning

Reusing A1's winner gives A1 a home advantage. Its settings were fit to augmented data, while A0 sees less variety and probably wants more regularisation, and B sees synthetic data with a different noise profile. The fair version that follows from the sources: (1) the same search space and the same **number** of trials per arm for the shared knobs (learning rate, dropout); (2) arm-specific knobs (augmentation ranges, generator ranges, synthetic share) searched with declared trial counts; (3) every selection on validation only, with seeds varied; (4) report trial counts and an expected-performance curve so readers can see whether the ranking depends on budget.

## How it applies to ShapeSense

Iteration 2's search follows most of this: per-arm (lr, dropout) grids, preregistered counts, validation only, three-seed confirmation. One residual imbalance remains. Trial counts differ (iteration 2: A0 6, A1 30, B 22, A2 18; iteration 3: A0 6, A1 30, B 22, A2 34, P 18). Part of that is structural, because A0 has no augmentation or generator knobs. But under Dodge et al.'s and Choi et al.'s findings, an arm searched over more trials gets a higher expected best validation score even when it is not better. The cheap check is to compute expected validation macro F1 at a matched budget (for example, best of 6 trials) for every arm, using results already logged, and see whether the ranking of A0 against A2 holds. A second point: B and A2 reused A1's searched augmentation ranges, a smaller version of the same reuse problem, and it is disclosed in the log.

## Validation

The literature agrees with the documented cause: tuning only A1 and reusing its winner is a recognised source of bias, and Melis et al. and Choi et al. show that it can flip conclusions. It agrees with the fix in principle: a per-arm, validation-only, preregistered search. It adds that equal search spaces and comparable trial counts, or budget-matched reporting, matter as much as tuning every arm at all, and that the expected-performance curve is the standard way to show this. Nothing contradicts the record.

## Our decision

The project replaced A1-only tuning with a per-arm validation search of augmentation, generator and hyperparameters (166 trials in iteration 2) and disclosed the trial count per arm and the inherited augmentation ranges. The findings suggest an optional budget-matched re-reading of the existing search logs, with no new training. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Tuning-Budget Asymmetry & Expected Validation Curves (`F06`)

### Metadata & Lineage

* **Entry ID / Type:** `F06` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_3/search/winners.json`

### Statistical Foundations of Hyperparameter Selection Bias

* **Ranking Reversals Under Asymmetric Tuning (Melis et al., ICLR 2018; Choi et al., arXiv:1910.05446):** Tuning hyperparameters on a single baseline arm (`A1` seed 0 in Iteration 1) and broadcasting them to competing arms confers a systematic "home advantage" to `A1` while mis-regularizing clean (`A0`) or synthetic-heavy (`B`) streams.
* **Multi-Source Benchmark Variance (Bouthillier et al., MLSys 2021) & Budget-Dependent Rankings (Dodge et al., EMNLP 2019):** Even when every arm receives its own validation search, unequal trial budgets (`A0: 6, A1: 30, B: 22, A2: 34, P: 18` in Iteration 3) inflate the expected maximum validation score $\mathbb{E}[\max_{1 \le i \le n} V_i]$ for arms with larger $n$ purely through order statistics.

### Zero-Compute Post-Hoc Verification Control

Using the already-logged validation trials, compute Dodge et al.'s Expected Validation Performance curve $\hat{V}(n)$ at a matched trial budget ($n = 6$, matching `A0`'s grid size) across all five arms to verify that `A2 > A0` holds independently of search-budget cardinality—requiring zero additional GPU runs.

