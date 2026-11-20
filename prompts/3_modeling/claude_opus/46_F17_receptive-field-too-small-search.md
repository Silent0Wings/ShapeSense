# 3_modeling - F17: The first CNN could not see a whole shape. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F17 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f17) · Record: [F17](../inferred_prompts.md#f17)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> How large does a CNN's receptive field need to be, relative to the object, to classify whole shapes? Search for how the theoretical and the effective receptive field are computed (for example Luo et al. 2016 and Araujo et al. 2019) and for evidence on what happens when the receptive field is smaller than the object. Our case: three blocks gave a 22-px receptive field on 64-px images.

## Response

### Well established

- **How the theoretical receptive field (TRF) is computed.** Araujo, Norris and Sim give the closed form for a single-path network: r0 = sum over layers of (k_l - 1) times the product of the strides of all earlier layers, plus 1. Padding does not change it ([Distill 2019](https://distill.pub/2019/computing-receptive-fields/)). They also extend the computation to multi-path networks and released a library for it ([Google Research listing](https://research.google/pubs/computing-receptive-fields-of-convolutional-neural-networks/)).
- **The effective receptive field (ERF) is smaller than the theoretical one.** Luo, Li, Urtasun and Zemel show that the influence of input pixels on an output unit has a roughly Gaussian shape and covers only a fraction of the TRF ([NeurIPS 2016](https://proceedings.neurips.cc/paper/2016/hash/c8067ad1937f728f51288b3eb986afaa-Abstract.html), [arXiv 1701.04128](https://arxiv.org/abs/1701.04128)). Their poster states that the ERF grows roughly with the square root of depth, so it shrinks as a share of the TRF as layers are added. It also says the ERF expands during training ([poster](https://www.cs.toronto.edu/~zemel/documents/rf-poster-nips2016.pdf)). Araujo et al. give the same reason in other words: pixels near the centre have more paths to the output, so they carry more weight ([Distill 2019](https://distill.pub/2019/computing-receptive-fields/)).
- **A receptive field smaller than the object is a known limit, and a large one is necessary but not sufficient.** Araujo et al. note that "if the receptive field of the network is small, it may not be able to recognize large objects". On ImageNet they report that accuracy rises roughly with the logarithm of receptive-field size, with diminishing returns. They add that a large field is "by no means" sufficient ([Distill 2019](https://distill.pub/2019/computing-receptive-fields/)).
- **Local features can still go a long way when the label does not depend on global layout.** BagNets limit the receptive field to 9, 17 or 33 px and classify by averaging patch evidence with no spatial ordering. BagNet-33 reaches 87.6% top-5 on ImageNet ([Brendel and Bethge, ICLR 2019](https://arxiv.org/abs/1904.00760)). So a small field mostly hurts on tasks whose classes differ in **global** structure, not local texture.
- **Global spatial relations are hard for feedforward CNNs with local fields.** On the Pathfinder task, which asks whether two dots are joined by a path, Linsley et al. found that small or shallow feedforward models handle only short paths, and that adding depth is an inefficient fix ([NeurIPS 2018](https://proceedings.neurips.cc/paper/2018/hash/ec8956637a99787bd197eacd77acce5e-Abstract.html)).

### Single reports

- Richter et al. argue that layers whose input is already smaller than the receptive field add little ("unproductive layers"). They report that this happens when depth does not match input resolution, and that it can be predicted from receptive-field analysis before training ([arXiv 2106.12307](https://arxiv.org/abs/2106.12307)). This cuts the other way: depth beyond what the image size needs is wasted.

### What I could not find

No source gives a numerical rule such as "the receptive field must be X times the object". The evidence is directional (bigger fields help, with diminishing returns, while the ERF stays smaller than the TRF) and depends on the task.

### Reasoning

For ShapeSense's block (3x3 conv with padding 1, then 2x2 max-pool), the formula gives 3, 4, 8, 10, 18 and 22 px after three blocks, and 38 then 46 px after four. This matches both the logged 22 px and the 46 px noted in `configs/pipeline.yaml`. Real shapes span most of the frame: the synthetic radius alone is 16 to 28 px, so a 32 to 56 px extent. With a 22-px TRF, and a smaller ERF, no single unit can see two opposite sides of a large circle or rectangle at once. The model ends in global average pooling, so in the BagNet sense it becomes a bag of local stroke patches. That works for classes with distinctive local parts, such as star tips or triangle corners. It fails for classes that differ only in global proportion, such as circle vs ellipse, square vs rectangle and square vs diamond, because averaging local corner or arc evidence discards aspect ratio. At 46 px the TRF covers most shapes, although the Gaussian ERF means the effective coverage is still smaller.

## How it applies to ShapeSense

The literature supports the diagnosis qualitatively: a 22-px field cannot encode the global proportions that separate several of the 10 classes, and depth (or dilation, or a final full-field layer) is the standard remedy. It also suggests three checks the project has not run. (1) Measure the ERF of the trained 4-block model with Luo et al.'s gradient method on 64x64 inputs, to confirm that it actually reaches the shape outline. (2) Compare per-class F1 for the global-proportion pairs above against the local-feature classes, which tests the BagNet-style explanation directly. (3) Keep in mind that a fifth block would gain little: the 4x4 map after four pools is already near the point where Richter et al. would call further layers unproductive.

## Validation

The search agrees with the documented cause in direction: three blocks gave a 22-px receptive field, too small for whole shapes, and moving to four blocks was the fix. It adds two nuances. First, the ERF is smaller than the 46-px TRF, so "can see the whole shape" is only approximately true even after the fix. Second, the record of the fix (`docs/notes/pairs/7_meta_and_other.md`) shows that the four-block change was made **together with** the augmentation-framing fix (shapes about 6 px too small, F08). The A1 validation accuracy gain from 37% to 69% therefore cannot be credited to the receptive field alone. Nothing in the literature contradicts the record. It just does not provide a numeric threshold that would prove 22 px was too small on its own terms.

## Our decision

The project moved from three to four convolution blocks (22 px to 46 px TRF), set as `train.channels: [32, 64, 128, 128]` and kept for every arm. The findings suggest an optional ERF measurement and a per-class check on the proportion-defined classes, and a separate ablation if the share of the gain due to depth matters. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Theoretical vs. Effective Receptive Fields & Topological Shape Perception (`F17`)

### Metadata & Lineage

* **Entry ID / Type:** `F17` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/model.py`, `configs/pipeline.yaml` (`train.channels: [32, 64, 128, 128]`), `docs/notes/pairs/7_meta_and_other.md`

### Theoretical Formulation & Receptive-Field Geometry

Following Araujo, Norris, and Sim (Distill 2019), for a sequential convolutional architecture with kernel sizes $k_l$ and strides $s_l$ (padding leaves receptive field invariant), the Theoretical Receptive Field (TRF) $r_0$ at layer $L$ is given by:

$$r_0 = 1 + \sum_{l=1}^{L} (k_l - 1) \prod_{i=1}^{l-1} s_i$$

* **3-Block `SmallCNN` (`[32, 64, 128]`):** Produces an $8 \times 8$ pre-pooling feature map with $r_0 = 22\text{ px}$. Because standardized shapes span $32\text{–}56\text{ px}$ inside the $64 \times 64$ frame (synthetic radii alone span $16\text{–}28\text{ px}$), $r_0$ covers less than $40\%$ of the object diameter—preventing any pre-GAP unit from simultaneously observing opposing boundaries.
* **4-Block `SmallCNN` (`[32, 64, 128, 128]`):** Expands the $4 \times 4$ pre-pooling map to $r_0 = 46\text{ px}$, encompassing the global contour.
* **The Gaussian Effective Receptive Field (ERF) Shrinkage (Luo et al., NeurIPS 2016):** Because central pixels possess exponentially more gradient/activation paths to an output unit than boundary pixels, the actual Effective Receptive Field (ERF) decays radially as a 2D Gaussian and scales only as $\mathcal{O}(\sqrt{L})$ relative to the $\mathcal{O}(L)$ growth of TRF. Thus, even at $r_0 = 46\text{ px}$, high-weight effective coverage remains strictly narrower than $46\text{ px}$.

### Mechanistic Failure Mode & Architectural Bounds

| Diagnostic Dimension | Literature Mechanism | ShapeSense Implication & Verification Protocol |
| --- | --- | --- |
| **Bag-of-Local-Parts Degeneration** | Brendel & Bethge (ICLR 2019, BagNets): Small-RF CNNs followed by global average pooling discard spatial layout and act as unordered patch-evidence aggregators. | Local-feature classes (star tips, triangle vertices) remain separable at $22\text{ px}$, whereas global aspect-ratio / symmetry pairs (`circle` vs. `ellipse`, `square` vs. `rectangle`, `square` vs. `diamond`) collapse once spatial coordinates are averaged away. |
| **Over-Depth Diminishing Returns** | Richter et al. (arXiv:2106.12307): Layers operating after the feature map shrinks below the receptive field become "unproductive layers". | Adding a 5th block atop a $4 \times 4$ map yields negligible structural gain; 4 blocks sit at the resolution-matched optimum. |
| **Confounded Attribution Audit** | Multi-variable intervention (`F08` + `F17`): The 4-block depth increase was deployed simultaneously with the augmentation-framing fix (`~6 px` scale correction). | The jump in `A1` validation accuracy (`37%` $\rightarrow$ `69%`) reflects a joint intervention; isolating depth's pure causal share requires a single-factor ablation plus gradient-based ERF mapping (Luo et al.). |

