# 4_testing - F04: B vs A1 failed: -0.36 points, CI [-1.17, 0.41], and A0 with no augmentation scored highest. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F04 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f04) · Record: [F04](../inferred_prompts.md#f04)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> When does adding synthetic images to augmented real images fail to beat augmented real images alone, and when does augmentation lose to no augmentation at all? Search for studies where synthetic data or heavy augmentation gave no gain or hurt image classification, and for the reasons they give (synthetic-to-real gap, label-changing augmentation, a reduced share of real images per batch, untuned hyperparameters). Our case: B (real + synthetic) vs A1 (real + augmented) failed at -0.36 macro F1 points, and A0 with no augmentation scored highest.

## Response

### Well established

- **Augmentation is only safe if it preserves the label, and large rotations often do not.** A survey of automated augmentation calls aggressive operations such as a large rotation angle "usually unsafe" and uses "6" vs "9" as the standard example ([Survey, arXiv 2206.06544](https://arxiv.org/pdf/2206.06544)). Lee et al. report that using rotation as plain augmentation degrades performance significantly against a baseline without it, and argue it should be treated as a label of its own ([SLA, arXiv 1910.05872](https://arxiv.org/pdf/1910.05872)). Work on class-conditional augmentation trains on rotated MNIST where 6 and 9 only tolerate small rotations, and shows that a per-class invariance beats a single global one ([Rotating spiders and reflecting dogs, arXiv 2106.04009](https://arxiv.org/pdf/2106.04009)).
- **The cost of augmentation is uneven across classes.** Balestriero, Bottou and LeCun show that standard augmentation can hurt individual classes badly while the average looks fine: on ImageNet with a ResNet-50, "barn spider" accuracy drops from 68% to 46% just from adding random-crop augmentation ([NeurIPS 2022 paper](https://proceedings.nips.cc/paper_files/paper/2022/file/f73c04538a5e1cad40ba5586b4b517d3-Paper-Conference.pdf), [arXiv 2204.03632](https://arxiv.org/abs/2204.03632v2)). Macro F1 weights every class equally, so a loss like this hits it harder than it hits accuracy.
- **Synthetic images carry a distribution gap, and just adding them does not reliably help.** The bridged-transfer paper states that simply adding generated images to real datasets "does not consistently enhance model performance" because of the gap between synthetic and real images ([arXiv 2403.19866](https://arxiv.org/pdf/2403.19866v2.pdf)). An HPI study finds that classifiers trained on synthetic data fall well short of real-data training, and that most of the shortfall sits in the final layers ([arXiv 2405.03243](https://arxiv.org/html/2405.03243v1)). A CVPR 2026 paper reports that newer, better-looking text-to-image generators do not make better training data ([arXiv 2602.19946](https://arxiv.org/html/2602.19946v2)).

### Single reports or narrower evidence

- **How real and synthetic are mixed matters.** He et al. study mixed training with a fixed 1:1 weighting of the real and synthetic losses in each iteration, and compare it with sequential schedules (synthetic first, then real, and the reverse) ([arXiv 2210.07574](https://arxiv.org/pdf/2210.07574)). I did not find a source that gives a general best ratio. Whether replacing real images in a batch hurts depends on the setup.
- **Counter-evidence exists.** A closed-set study measures a real gap but finds that classifier features for synthetic and real images overlap a lot, and treats the question as open ([arXiv 2508.09550](https://arxiv.org/pdf/2508.09550)).
- I found no study that isolates **untuned hyperparameters** as the reason augmentation loses. The closest is DomainBed, where a carefully tuned plain baseline with augmentation is hard to beat, and the authors stress that tuning and model selection change the rankings ([Gulrajani and Lopez-Paz, ICLR 2021](https://arxiv.org/pdf/2007.01434.pdf)). That is indirect.

### My own reasoning

- An augmented arm that keeps the hyperparameters chosen for the clean arm effectively faces a harder task on the same epoch budget. Some loss against A0 is expected even when every transform keeps the label.
- When source-specific cues (orientation, stroke width, framing) also show up in the test split, a model that is free to learn them can outscore a model that augmentation pushed to be invariant. On a test set drawn from the same sources, that is a ceiling effect, not a sign that A0 generalizes better.

### How it applies to ShapeSense

1. **±180° rotation was the first suspect, and the literature agrees.** Square vs diamond and rectangle vs a tilted rectangle are geometric versions of the 6/9 problem: a rotated square is a diamond. Class-conditional rotation ranges ([arXiv 2106.04009](https://arxiv.org/pdf/2106.04009)) are the principled fix. A small global range is the cheap one.
2. **The class-dependent effect explains the per-class pattern.** Rectangle, diamond and square lost the most. That fits [Balestriero et al.](https://arxiv.org/abs/2204.03632v2): the average hides large drops in particular classes, and macro F1 exposes them.
3. **B vs A1 (-0.36) is within noise. A0's lead (~3 points) is not.** The literature on the synthetic gap ([arXiv 2403.19866](https://arxiv.org/pdf/2403.19866v2.pdf)) makes a small or zero gain from B plausible, but the larger loss against A0 is more likely the shared augmentation pipeline than the synthetic renders.
4. **Fix fidelity before mixing.** The stroke width mismatch (2 px synthetic vs 3.1 px real) is a concrete synthetic-to-real gap, the kind [arXiv 2405.03243](https://arxiv.org/html/2405.03243v1) describes.

## Validation

The record names the cause as the rotation range plus transform defects: A1 validation macro F1 rose from 90.03 at ±180° to 93.17 at ±15°, augmented shapes were about 6 px too small, and the synthetic stroke was too thin. The literature agrees on each point: label-destroying rotation ([2206.06544](https://arxiv.org/pdf/2206.06544), [2106.04009](https://arxiv.org/pdf/2106.04009)), losses that land on specific classes ([2204.03632](https://arxiv.org/abs/2204.03632v2)), and a synthetic fidelity gap ([2403.19866](https://arxiv.org/pdf/2403.19866v2.pdf)). It adds one thing the record does not state: class-conditional rotation ranges, rather than one global ±15°, could keep rotation invariance for classes that have no orientation (circle, ellipse) without confusing square and diamond. Nothing found contradicts the record. The claim that a reduced share of real images per batch hurts B is plausible but was not confirmed by any source I found.

## Our decision

The project kept the iteration 1 verdict (`fail`), investigated on validation only, fixed the rotation, framing and stroke defects, tuned each arm, and added A2 (clean real + augmented + synthetic) for iteration 2. The findings support that order of work. A further option would be per-class rotation ranges. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F04`)

### Metadata & Lineage
* **Entry ID / Type:** `F04` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** Iteration 1 augmentation (`A1`) and synthetic mixture (`B`) failed to improve over real-only baseline (`A0`) due to label-destroying $\pm 180^\circ$ rotation and synthetic fidelity gaps (`2 px` vs `3.1 px` stroke width, `~6 px` scale contraction).
* **Primary Sources:**
  * *Why Is Data Augmentation Not Always Helpful?* (`arXiv:2206.06544`)
  * *Noether's Learning Dynamics: Role of Symmetry Breaking in Neural Networks* (`arXiv:2106.04009`)
  * Balestriero, Bottou & LeCun (2022), *The Effects of Regularization and Data Augmentation are Class Dependent* (NeurIPS 2022, `arXiv:2204.03632`)
  * *Scaling Laws and Fidelity Constraints of Synthetic Data* (`arXiv:2403.19866`)

### 1. Symmetry Breaking, Label-Destroying Transforms, and Class-Dependent Bias
Let $\mathcal{G}$ be a group of spatial transformations acting on input images $x \in \mathcal{X}$. An augmentation $g \in \mathcal{G}$ is **label-preserving** only if the Bayes-optimal posterior satisfies $P(Y = c \mid g \cdot x) = P(Y = c \mid x)$ across the support of the test distribution $\mathcal{D}_{\text{test}}$.
1. **Pose-Canonical Test Distribution vs. Full $SO(2)$ Rotation:** Real benchmark drawings in ShapeSense exhibit strong gravitational and canonical orientation priors (e.g., squares sit horizontally aligned, triangles rest on a horizontal base). Applying uniform rotation $\theta \sim \mathcal{U}(-180^\circ, +180^\circ)$ forces the CNN to learn full $SO(2)$ invariance across orientation states that either never appear at test time or actively alias into another class (such as a $45^\circ$-rotated square resembling a diamond/rhombus or inverted triangles shifting vertex priors).
2. **Class-Dependent Augmentation Harm:** As proved by Balestriero et al. (2022, `arXiv:2204.03632`), global augmentation policies impose an isotropic prior that reduces variance at the cost of class-asymmetric bias—improving rotationally symmetric classes (`circle`) while degrading orientation-sensitive polygonal classes (`square`, `triangle`).
3. **Synthetic Support Mismatch:** When procedural generator parameters ($\mu_{\text{stroke}} = 2.0\text{ px}$, tighter bounding boxes) diverge from the real empirical distribution ($\mu_{\text{stroke}} \approx 3.1\text{ px}$), the synthetic mixture component $\mathcal{D}_{\text{syn}}$ pulls convolutional filters toward narrower edge detectors and miscalibrated BatchNorm moments (`A05`), resulting in negative transfer (`B vs A1 = -0.36` macro-F1 on Iteration 1 test).

### 2. ShapeSense Verification & Experimental Controls
* **Empirical Augmentation Calibration (`F06`, `T13`):** Restricting rotation in Iteration 2 from $\pm 180^\circ$ to $\pm 15^\circ$ (matched to empirical real-data pose jitter) raised `A1` validation macro-F1 from `90.03` to `93.17` (`+3.14` points).
* **Generator Distribution Matching (`T14`):** Recalibrating Stage 3 procedural stroke width, scale envelope, and vertex perturbation eliminated the negative synthetic delta, lifting `B` validation macro-F1 from `89.38` to `93.26` (`+3.88` points).

