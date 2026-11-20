# 3_modeling - F11: A1 was still improving when training ended, and early stopping is unstable. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F11 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f11) · Record: [F11](../inferred_prompts.md#f11)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> When is early stopping unreliable, and how should the training budget be set fairly across compared methods? Search for evidence on noisy validation curves at high learning rates, methods that are still improving when the budget ends, and fixed-budget comparison protocols. Our case: validation swung by up to 30 points between epochs at learning rate 0.003.

## Response

### Well established

- **Real validation curves are not smooth, so early stopping on them is noisy.** Prechelt's classic study found that a real validation curve showed as many as 16 local minima. Across 14 stopping criteria and 12 tasks, slower criteria gave about 4% better generalisation on average at about 4 times the training time ([Prechelt, "Early Stopping - but when?"](https://publikationen.bibliothek.kit.edu/7498/1832)). Patience-based stopping on a noisy curve tends to stop at an arbitrary dip.
- **Large learning rates cause short-term oscillation by design.** Cohen et al. show that full-batch gradient descent on neural networks typically runs at the "edge of stability". The sharpness hovers just above 2 / step size, and the training loss is "non-monotonic over short timescales, yet consistently decreases over long timescales" ([arXiv 2103.00065](https://arxiv.org/abs/2103.00065), [ICLR 2021](https://iclr.cc/virtual/2021/poster/2577)). This was shown for full-batch training, and its extension to minibatch AdamW is an inference, but it explains why epoch-to-epoch validation swings at lr 0.003 need not mean divergence.
- **Under a fixed budget, the schedule should be fitted to the budget.** Li, Yumer and Ramanan find that a budget-aware schedule is critical, and that simple decay to zero over the budget (linear, with cosine reported as similar) is robust across ImageNet, Kinetics, COCO and Cityscapes. They describe "budgeted convergence": the gradient shrinks at the end of whatever budget is allowed ([ICLR 2020, arXiv 1905.04753](https://arxiv.org/abs/1905.04753)). So a decaying schedule makes the end-of-budget model stable, and a method "still improving" at the end is partly an artefact of where the schedule ends.
- **Comparisons should be matched on updates, not on a stopping rule.** Hoffer et al. show that the large-batch generalisation gap came from too few updates and disappears when the number of iterations is adapted ([NeurIPS 2017, arXiv 1705.08741](https://arxiv.org/abs/1705.08741)). AlgoPerf fixes hardware, workloads and validation targets and measures time to reach them ([Dahl et al., arXiv 2306.07179](https://arxiv.org/abs/2306.07179)).
- **Seeds and data order matter as much as the stopping point.** Dodge et al. fine-tuned BERT hundreds of times per task. Weight initialisation and data order contributed about equally to variance, and many runs on small datasets diverged partway ([arXiv 2002.06305](https://arxiv.org/abs/2002.06305v1)).

### Reasoning

Early stopping is unreliable when (a) the epoch-to-epoch noise is comparable to the differences between methods, (b) the validation set is small enough that macro F1 on rare classes jumps, or (c) one method converges more slowly than another, so a common patience cuts it off first. All three bias a comparison: the method with the noisier or slower curve is stopped at an arbitrary point. Picking the best validation epoch from a noisy curve also inflates the validation score (a maximum over noisy draws), but it does not touch the sealed test. Fair options, in order of preference: (1) a fixed number of updates per arm with a schedule that decays to zero, scoring the last checkpoint or an average of the last few; (2) if the best epoch is selected, use the same rule for every arm and report the gap between the best and the last epoch; (3) set the budget from the slowest arm's learning curve on validation, not from the fastest.

## How it applies to ShapeSense

The 30-point swings at lr 0.003 fit the edge-of-stability picture plus a small validation set split over 10 classes. With `schedule: cosine` tied to `max_epochs`, the learning rate decays toward zero at the end, so the late epochs should be calm. If A1 was still improving at epoch 30, the cosine schedule had compressed its useful low-lr phase, and Li et al.'s finding suggests that extending the budget for every arm is the right fix, not changing the stopping rule for one. Iteration 3 did exactly that: 60 epochs and patience 999 for all arms (`configs/pipeline.yaml`). One remaining question is whether the reported checkpoint is the last epoch or the best one (`selection_metric: val_macro_f1`). If it is the best, a record of best-epoch vs last-epoch validation F1 per arm would show whether selection, rather than training, drives any arm differences.

## Validation

The literature agrees with the documented cause (a budget too short for A1 and validation noise at a high learning rate) and with the fairness rule the project applied (same budget and same stopping rule for every arm). It adds a mechanism for the swings (edge of stability), the point that a decaying schedule matched to the budget is what makes a fixed budget fair, and a caution that best-epoch selection on noisy curves inflates validation scores. Nothing contradicts the record. The "Partly" state fits, because iteration 2's results stay at 30 epochs.

## Our decision

Iteration 2 kept the same 30-epoch budget and stopping rule for every arm, and iteration 3 trained every arm for 60 epochs with no effective early stopping. The findings suggest optionally logging best-epoch vs last-epoch validation F1 per arm, to confirm that checkpoint selection is not a hidden source of differences between arms. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Edge-of-Stability Dynamics & Budget-Matched Convergence (`F11`)

### Metadata & Lineage

* **Entry ID / Type:** `F11` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `configs/pipeline.yaml` (`max_epochs: 60`, `early_stopping_patience: 999`, `schedule: cosine`)

### Optimization Dynamics Behind 30-Point Validation Swings

* **Edge-of-Stability Regimes (Cohen et al., ICLR 2021, arXiv:2103.00065):** At large step sizes ($\eta = 0.003$), Hessian sharpness hovers near the stability threshold $2 / \eta$, producing non-monotonic, oscillatory short-term loss/metric trajectories superimposed on steady long-term descent. Combined with macro-F1 sensitivity on small per-class validation slices, patience-based early stopping triggers prematurely on arbitrary downward spikes (Prechelt, 1998, observed up to 16 local minima on real validation curves).
* **Budget-Aware Cosine Annealing (Li, Yumer, & Ramanan, ICLR 2020, arXiv:1905.04753):** Because cosine annealing decays $\eta_t \rightarrow 0$ at $T_{\max}$, truncating training at 30 epochs compressed the low-learning-rate stabilization phase for slower-converging augmented streams (`A1`, `A2`, `B`), creating an artifact where `A1` appeared "still improving" at cutoff.
* **Update-Matched Fairness (Hoffer et al., NeurIPS 2017; Dahl et al., AlgoPerf, arXiv:2306.07179):** Matching arms on total optimizer updates (`60 epochs × 49 steps = 2,940` updates) with `early_stopping_patience: 999` eliminates asymmetric stopping bias.
* **Diagnostic Check:** Logging `val_macro_f1(best_epoch) - val_macro_f1(epoch_60)` per arm verifies that best-checkpoint selection (`selection_metric: val_macro_f1`) does not disproportionately inflate noisier arms via selection-over-maxima bias.

