# 2_data_preparation/transformation - F07: Rotation up to ±180° hurt the classes that depend on orientation (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F07 · Question from [failure_search_prompts.md](../../../failure_search_prompts.md#f07) · Record: [F07](../inferred_prompts.md#f07)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> When does rotation augmentation hurt classes whose identity depends on orientation (square vs diamond, rectangle orientations)? Search for work on label-preserving vs label-changing augmentation and on class-dependent effects of augmentation (for example Balestriero et al. 2022), and for how safe ranges are chosen per class.

## Response

### Well established

- **One augmentation strength can hurt some classes badly.** Balestriero, Bottou and LeCun ([NeurIPS 2022](https://proceedings.nips.cc/paper_files/paper/2022/file/f73c04538a5e1cad40ba5586b4b517d3-Paper-Conference.pdf); [arXiv 2204.03632](https://arxiv.org/abs/2204.03632v2)) show that the amount of data augmentation (or weight decay) chosen by cross-validation over all classes can lead to "disastrous" performance on some classes. Their examples are ImageNet per-class drops with a ResNet-50, and a fall from 70% to 30% on one iNaturalist class when random-crop augmentation was used in pretraining. Their message is that averaged metrics hide this.
- **Rotation does not preserve labels when orientation defines the class.** The textbook case is 6 vs 9. Work on learned, class-conditional augmentation ("Rotating spiders and reflecting dogs", [arXiv 2106.04009](https://arxiv.org/pdf/2106.04009)) builds a benchmark that rotates digits over the full range except 6s and 9s, which get only ±45°. The authors show that a single learned invariance can mix up 6s and 9s when it is too strong. Self-supervised label augmentation ("Self-supervised Label Augmentation via Input Transformations", [arXiv 1910.05872](https://arxiv.org/pdf/1910.05872)) goes the other way and treats rotation as something that changes the label.
- **Invariance can be learned per class.** Augerino ([Benton et al., NeurIPS 2020](https://proceedings.nips.cc/paper_files/paper/2020/file/cc8090c4d2791cdd9cd2cb3c24296190-Paper.pdf)) learns one augmentation distribution from training data. The class-conditional extension above learns one per class and reports a small MNIST gain (96.90% to 97.49%). InstaAug ([Miao et al., ICML 2023](https://proceedings.mlr.press/v202/miao23a.html)) learns ranges for each input.

### Single reports

- Zhou et al. (ICLR 2022), as summarised in the search results for the papers above, report that networks are much less invariant on small classes. I did not open that paper, so treat this as unverified.
- A review summary says a class-specific InstaAug variant did worse than global augmentation on Tiny-ImageNet cropping ([Liner review](https://liner.com/review/learning-instancespecific-augmentations-by-capturing-local-invariances)). Per-class ranges are not always better, especially with few samples per class.
- I could not retrieve Simard et al. (2003) to confirm its exact advice on small affine distortions, so I do not cite it.

### Reasoning (mine, not from a source)

- In ShapeSense, rotation fails in two ways for square, rectangle and diamond:
  - **Label change:** a square turned 45° is a diamond by the project's own definition (rhombus, no right angles shown upright), yet it keeps the label "square". That is augmentation-induced label noise, the 6/9 mechanism.
  - **Lost cue:** most real squares and rectangles are within ±5° of upright in some sources. Full rotation trains the model to ignore orientation, which the test data still carries.
- Rotation-invariant classes (circle, hexagon, octagon, star) gain from rotation. One global range therefore trades their gain against the orientation classes' loss, which is exactly Balestriero's warning about tuning on the average.
- A safe range per class follows from the class definition. For square vs diamond the decision boundary is at 45°, so any range well below ±22.5° keeps the label. The data's own orientation spread (±5° for most samples) suggests the cap does not need to be much wider than the natural jitter.

### How it applies to ShapeSense

1. Search the range on validation, with per-class F1 reported, not only macro F1. That is the protocol Balestriero et al. imply, and it is what the ablation did.
2. A shared cap for the three orientation classes is a small, hand-specified form of class-conditional invariance. It is simpler than learning ranges (Augerino-style). With about 1,000 training images per class, a learned per-class range risks the small-class problem above.
3. The 0° runs stopped early (11 to 13 epochs), so the 0° vs ±15° comparison mixes augmentation with training length. Read that comparison with care.

## Validation
The record's cause was that full rotation removed an orientation cue, and that a square at 45° looks like a diamond. The literature agrees on both points: augmentation that changes labels (6/9) and class-dependent harm from one augmentation strength (Balestriero et al.). It adds that the effect is general, not specific to shapes, and that macro F1 alone can hide it. The recorded per-class drops (diamond 96.1 to 86.9 F1, from ±15° to ±180°) match the pattern. Nothing contradicts the record.

## Our decision
The project searched a global rotation range plus a shared cap for square, rectangle and diamond on validation. The winner was ±20° with a ±10° cap. The findings support this design. An optional extra would be to report per-class F1 for every searched augmentation setting, not only rotation, since Balestriero et al. found the same class-dependent effect for crops and weight decay. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
