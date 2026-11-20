# 2_data_preparation/transformation - F08: Augmented shapes came out about 6 px too small (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F08 · Question from [failure_search_prompts.md](../../../failure_search_prompts.md#f08) · Record: [F08](../inferred_prompts.md#f08)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How do geometric augmentations shift object scale and framing away from the real data, and how much does a train-test scale mismatch cost a CNN? Search for evidence such as FixRes (Touvron et al. 2019) and for how augmentation pipelines keep object size realistic. Our case: augmented shapes filled about 51 px against 57 px for real images.

## Response

### Well established

- **Augmentation itself shifts apparent object size.** Touvron, Vedaldi, Douze and Jégou ([FixRes, NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/file/d03a857a23b5285736c4d55e0bb067c8-Paper.pdf); [arXiv 1906.06423](https://arxiv.org/pdf/1906.06423v3.pdf)) show that random-resized-crop training with center-crop testing makes objects look larger in training than at test time. The CNN therefore sees a different object-size distribution at evaluation. Their fix aligns the sizes, either by training at a lower resolution than testing or by fine-tuning a couple of layers at the test resolution. Aligning gave better test accuracy for a given test resolution, which shows that the mismatch had a measurable cost. Keras has a [reproduction](https://keras.io/examples/vision/fixres).
- **CNNs are not scale invariant.** Singh and Davis ([SNIP, CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/papers/Singh_An_Analysis_of_CVPR_2018_paper.pdf)) analysed classification of small objects on ImageNet and concluded that CNNs are not robust to changes in scale. They recommend training and testing at matching scales, and they back-propagate only for objects near the pretraining scale to avoid domain shift.

### Single reports, or numbers I could not confirm

- I could not confirm from snippets an exact accuracy cost per pixel of scale mismatch for small images. FixRes gives ImageNet numbers at high resolution, and SNIP's numbers are for detection. Neither transfers directly to 64x64 line drawings.
- Sketch pipelines often apply scale jitter around the data's own scale. One sketch-rnn reimplementation uses a random scale factor of 0.15 ([eyalzk/sketch_rnn_keras](https://github.com/eyalzk/sketch_rnn_keras)). That is one repo's default, not a confirmed value from Ha and Eck's paper.

### Reasoning (mine, not from a source)

- The ShapeSense gap differs from FixRes in kind. FixRes is a side effect of random cropping. In ShapeSense the transform re-framed shapes to a fixed target that did not match Stage 1's standardization. The result is a **constant bias** (about 6 px, about 10% of the long side), not added variance. Scale jitter around the right mean adds robustness. A biased mean only moves the training distribution away from evaluation, because validation and test images are never augmented.
- The cost should be modest but real. Shapes are defined by angles and vertex counts, which do not depend on scale. But a 3-block CNN with a limited receptive field (F17) and fixed-size stroke features responds to size, and stroke width relative to shape size also changes. The fact that the gap was the same for every class, including circles, points to a framing constant, as the record says.
- The general rule, consistent with both papers: measure the object-size distribution of the evaluation data, and make every training transform (augmentation and the synthetic generator) reproduce its mean, with jitter around it.

### How it applies to ShapeSense

1. The fix, re-framing to `size / (1 + 2 * frame_margin)` with the margin shared with Stage 1, is the FixRes principle in simple form: match apparent object size between training and evaluation.
2. The check worth adding is a per-class size table after the fix, comparing real and augmented long-side means. The record says none exists. The test asserts the overall mean within 3 px, but a per-source or per-class check would catch a regression for one class.
3. The same check applies to the synthetic generator (arm B and arm P). Its framing should match the standardized real images in the same way.

## Validation
The record's cause was that the transform re-framed shapes to about 51 px against about 57 px for real images. The literature agrees that train-test object-size mismatch is a known cost of geometric augmentation, and that CNNs are not scale invariant (FixRes, SNIP). It adds that the remedy is to align the size distributions, not to add more scale augmentation. It also says the mean matters more than the spread. I found no source that quantifies the cost for small grayscale images, so the size of the effect on ShapeSense remains unmeasured. Nothing contradicts the record.

## Our decision
The project corrected the framing margin (`augment.frame_margin: 0.06`) and added a test on mean size over 100 seeds. The findings suggest a per-class real-vs-augmented size table after the fix, and the same check for synthetic images. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
