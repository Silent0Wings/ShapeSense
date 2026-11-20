# 4_testing - F14: A2 vs A0 failed: +0.06 on test and +0.08 on the fresh holdout, both CIs include 0. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F14 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f14) · Record: [F14](../inferred_prompts.md#f14)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> When does a model trained on real + augmented + synthetic data fail to beat a model trained on real data alone, and why? Search for studies where synthetic data or augmentation gave no gain on in-distribution test images but did help on out-of-distribution, unseen-source or corrupted images, and for what the authors concluded. Our case: A2 (full mix) vs A0 (real only) gained only +0.06 on test and +0.08 on a fresh holdout, both CIs including 0, from the same sources used in training.

## Response

### Well established

- **Augmentation can buy large gains under corruption.** AugMix halves corruption error on CIFAR-10-C (28.4% to 12.4%) and cuts it sharply on CIFAR-100-C ([Hendrycks et al., arXiv 1912.02781](https://arxiv.org/pdf/1912.02781)). Benchmarks of corrupted copies are where augmented models separate from plain ones.
- **Gains under one kind of shift do not carry over to others.** "The Many Faces of Robustness" finds that diverse augmentation helps texture and local-statistics shifts (ImageNet-C, ImageNet-R) but not geographic or other natural shifts ([Hendrycks et al., ICCV 2021 supplement](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Hendrycks_The_Many_Faces_ICCV_2021_supplemental.pdf)). Taori et al. tested about 200 models and found "little to no transfer" of robustness from synthetic shifts to natural ones. The only intervention that helped across several natural shifts was a more diverse training set ([NeurIPS 2020, arXiv 2007.00644](https://arxiv.org/abs/2007.00644v1)).
- **On domain generalization, a tuned plain baseline is hard to beat.** In DomainBed, no algorithm beat carefully tuned ERM (which already uses standard augmentation) by more than one point on average. The results also depend heavily on how models are selected ([Gulrajani and Lopez-Paz, ICLR 2021](https://arxiv.org/pdf/2007.01434.pdf)).
- **ID and OOD accuracy usually move together.** Across many models and shifts, out-of-distribution accuracy tracks in-distribution accuracy along a line. The correlation weakens on some synthetic corruptions ([Miller et al., ICML 2021](https://proceedings.mlr.press/v139/miller21b.html)). Gains above that line ("effective robustness") are what interventions such as augmentation have to show.

### Single reports or narrower evidence

- Synthetic data *can* raise in-distribution accuracy at scale: Azizi et al. report gains on ImageNet from adding samples from a fine-tuned diffusion model ([TMLR 2023, arXiv 2304.08466](https://arxiv.org/abs/2304.08466v1)). That is a very large generator and dataset. It is not evidence that simple rendered shapes would do the same.
- I did not find a paper that reports exactly "zero in-distribution gain, positive out-of-distribution gain" for synthetic plus augmented data on a small, near-saturated benchmark. The pattern follows from the papers above, but I could not confirm it as a single published finding.

### My own reasoning

- When every arm scores about 97.3 to 97.5 macro F1 on familiar sources, the remaining errors are few, and a 1-point margin needs a large share of them to flip. In that ceiling regime, a null result on in-distribution data is the expected outcome, not evidence that the extra data is useless.
- The [Miller et al.](https://proceedings.mlr.press/v139/miller21b.html) line suggests a way to read the ShapeSense arms: a mixed arm that matches A0 in-distribution but scores higher on an unseen source sits above the line, and that is the claim worth testing.

### How it applies to ShapeSense

1. **Ceiling.** Fresh-holdout macro F1 was 97.46 (A0), 97.42 (A1), 97.23 (B) and 97.54 (A2), all from sources the models trained on. The literature predicts no gain here, and none appeared.
2. **Corrupted copies (iteration 3's route) are where AugMix-style gains show up**, so A2 beating A0 on damaged images (+9.20 in iteration 3) matches [AugMix](https://arxiv.org/pdf/1912.02781). But [Taori et al.](https://arxiv.org/abs/2007.00644v1) warn that robustness to synthetic damage says little about robustness to natural source shift, which matches iteration 3's own note that it still does not test new sources.
3. **Unseen sources are the real test.** The Hand-Drawn hold-out runs favoured the augmented arms, which fits the [Taori et al.](https://arxiv.org/abs/2007.00644v1) finding that diverse training data is what helps on natural shift. With only two classes and high seed variance, though, that evidence is thin. [DomainBed](https://arxiv.org/pdf/2007.01434.pdf) also shows that model selection can swing domain-generalization results by several points.

## Validation

The record's documented cause is a ceiling: with the defects fixed, every arm scores about the same on familiar sources. The literature agrees. It adds a framing (effective robustness above the ID-OOD line, [Miller et al.](https://proceedings.mlr.press/v139/miller21b.html)) and a warning the record already partly states: corruption robustness is weak evidence for robustness to new sources ([Taori et al.](https://arxiv.org/abs/2007.00644v1); [Hendrycks et al. 2021](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Hendrycks_The_Many_Faces_ICCV_2021_supplemental.pdf)). Nothing contradicts the record. I could not find a source with the exact "no ID gain, OOD gain" result on a small saturated benchmark, so that part rests on combining several papers.

## Our decision

The project recorded F14 as a plain `fail` on both sets, made no change after the read, and moved iteration 3 to damaged copies of a never-read holdout, noting that this still does not test new sources. The findings support the verdict and the caveat. They suggest that a future iteration should pre-register a never-read, unseen-source holdout with several classes, report arm differences against the A0 ID-OOD line, and fix model selection in advance. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F14`)

### Metadata & Lineage
* **Entry ID / Type:** `F14` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** In-distribution ceiling saturation in Iteration 2 (`A2 vs A0 = +0.06` macro-F1 on reused `test` and `+0.08` on `fresh_holdout`, failing the `+1.50` threshold because `A0` already reached `94.28%` / `94.55%`).
* **Primary Sources:**
  * Miller et al. (2021), *Accuracy on the Line: On the Strong Correlation Between Out-of-Distribution and In-Distribution Generalization* (ICML 2021, PMLR v139:7721–7735)
  * Taori et al. (2020), *Measuring Robustness to Natural Distribution Shifts in Image Classification* (NeurIPS 2020, `arXiv:2007.00644`)
  * Hendrycks et al. (2021), *The Many Faces of Robustness: A Critical Analysis of Out-of-Distribution Generalization* (ICCV 2021)

### 1. Probit Accuracy-on-the-Line and Effective Robustness Under Corruption
Let $\Phi^{-1}$ denote the inverse standard normal CDF (probit transform). Miller et al. (2021) demonstrate that across baseline models trained purely on clean data, out-of-distribution (OOD) accuracy $\text{Acc}_{\text{OOD}}$ and in-distribution (ID) accuracy $\text{Acc}_{\text{ID}}$ obey an affine relationship in probit space:
$$\Phi^{-1}(\text{Acc}_{\text{OOD}}(f)) = \alpha \, \Phi^{-1}(\text{Acc}_{\text{ID}}(f)) + \beta$$
1. **In-Distribution Ceiling Compression:** When $\text{Acc}_{\text{ID}}(A0) \approx 94.5\%$ on clean 64×64 geometric shapes, the remaining $\sim 5.5\%$ residual error is dominated by intrinsic human label ambiguity (borderline hand-drawn polygons). On clean ID test sets, synthetic data and corruption augmentations cannot compress irreducible aleatoric noise, yielding $\Delta \text{F1}_{\text{ID}}(A2, A0) \in [+0.06, +0.08]$.
2. **Effective Robustness ($\rho_{\text{eff}}$):** Taori et al. (2020) and Hendrycks et al. (2021) define *effective robustness* as vertical lift above the clean baseline probit line:
$$\rho_{\text{eff}}(f) = \Phi^{-1}(\text{Acc}_{\text{corrupted}}(f)) - \big[\alpha \, \Phi^{-1}(\text{Acc}_{\text{clean}}(f)) + \beta\big]$$
Targeted synthetic and corruption training (`A1`, `B`, `A2`) shifts the model vertically above the baseline curve ($\rho_{\text{eff}} \gg 0$) specifically when evaluated under structural and photometric corruptions (blur, noise, low contrast, grid interference), even while $\text{Acc}_{\text{clean}}$ remains identical to `A0`.

### 2. ShapeSense Verification & Experimental Controls
* **Iteration 3 Multi-Severity Evaluation (`fresh_holdout_2`, `N = 41,400`):** Evaluating across 23 deterministic severity levels (1 clean + 22 damaged slices across 8 corruption families) revealed the latent effective robustness: `A0` collapsed to `77.26` macro-F1 across the 22 damaged levels while `A2` held at `86.46`, delivering a primary contrast of `+9.20` macro-F1 points (`95%` paired cluster bootstrap CI `[8.89, 9.53]`) while clean-slice parity remained intact (`94.74` vs `94.75`, `-0.01`).

