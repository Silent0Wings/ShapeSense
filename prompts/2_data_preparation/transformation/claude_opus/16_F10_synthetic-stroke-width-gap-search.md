# 2_data_preparation/transformation - F10: Synthetic strokes were thinner than real ones (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F10 · Question from [failure_search_prompts.md](../../../failure_search_prompts.md#f10) · Record: [F10](../inferred_prompts.md#f10)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How much does a mismatch in low-level statistics such as stroke width between synthetic and real images contribute to the synthetic-to-real gap? Search for studies that compare matching synthetic statistics to the real data with domain randomization. Our case: synthetic strokes were 2 px against about 3.1 px real.

## Response

### Well established

- **There are two strategies: randomise widely, or match the target.**
  - **Domain randomisation** varies the simulator's nuisance parameters so widely that the real world looks like one more variation. Tobin et al. ([IROS 2017, arXiv 1703.06907](https://arxiv.org/abs/1703.06907v1)) trained an object localiser on randomised synthetic images only and transferred it to real images. Tremblay et al. ([CVPR Workshops 2018](https://openaccess.thecvf.com/content_cvpr_2018_workshops/w14/html/Tremblay_Training_Deep_Networks_CVPR_2018_paper.html)) randomised lighting, pose and texture for car detection. With fine-tuning on real data, they beat real data alone.
  - **Matching** makes synthetic data resemble the target. SimGAN ([Shrivastava et al., arXiv 1612.07828](https://arxiv.org/pdf/1612.07828)) refines synthetic images with an adversarial loss against unlabelled real images. Meta-Sim ([Kar et al., ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Kar_Meta-Sim_Learning_to_Generate_Synthetic_Datasets_ICCV_2019_paper.html)) learns generator attributes to shrink the distribution gap. Structured domain randomisation ([Prakash et al., ICRA 2019](https://research.nvidia.com/publication/2019-04_structured-domain-randomization-bridging-reality-gap-context-aware-synthetic)) sits in between: it randomises, but along distributions tied to the real scene.
- **Stroke width is a standard rendering parameter in synthetic handwriting.** Krishnan and Jawahar ([arXiv 1608.04224](https://ar5iv.labs.arxiv.org/html/1608.04224)) render synthetic word images and vary "kerning level ... [and] stroke width, from a defined distribution". Kang et al. ([arXiv 2204.05539](https://arxiv.org/abs/2204.05539)) report a "significant style bias between synthetic and real data" that limits recognition gains.

### Single reports

- One historical-document paper ([Spoto et al. 2022](https://arodes.hes-so.ch/record/13205/files/Spoto_2022_improving_handwriting_recognition.pdf)) reports that a fixed stroke width in some generators makes generated text look unrealistic. That is an observation about one setting.
- A 2026 preprint ([arXiv 2609.35473](https://arxiv.org/pdf/2609.35473)) states that synthetic-only handwriting models show a gap that does not close without real samples. I could only see the abstract excerpt, so this is unverified.
- **I found no study that isolates stroke width alone and measures its share of the synthetic-to-real gap.** The papers above vary width among many other parameters. The evidence on its specific contribution is thin.

### Reasoning (mine, not from a source)

- A consistent, class-independent difference (2 px synthetic vs about 3.0-3.1 px real) is the kind of low-level cue a CNN picks up cheaply. Combined with the source fingerprint (F05), it makes "thin stroke" a marker of "synthetic". In arm B the labels are balanced across sources, so it does not directly predict class. It does mean the first-layer filters tuned on synthetic data respond to a width the real test never shows. That matters most for arm P, where synthetic pretraining sets those filters.
- Thin strokes also interact with augmentation: 2-px synthetic lines are closer to the 1-px failure in F09 than 3-px lines.
- **Match or randomise?** Matching the mean (3 px) removes the bias. Randomising around it (for example 2-4 px, or each source's own spread) also covers the real variation: real class means range from 2.47 px (hexagon) to 3.30 px (diamond). Domain-randomisation results suggest the randomised option generalises better when the target is diverse. Matching is cheaper and adds no search dimension. A reasonable middle ground, in the spirit of structured randomisation, is to sample width from the real per-class distribution.

### How it applies to ShapeSense

1. Setting `synth.stroke_px: 3` follows the matching strategy and removes the bias, which is the more important half.
2. The record notes that no re-measurement of synthetic strokes at 3 px exists. Without one, the match is assumed, not shown. Running the same stroke-width measurement on generated images is the obvious check.
3. If arm B or arm P still trails A0 or A1, the next generator change worth trying is width sampled from the real distribution. A source classifier that includes synthetic images (see F05) would show whether the synthetic fingerprint shrank.

## Validation
The record's cause was that the generator drew 2-px strokes against about 3.1 px in real images. The literature agrees that low-level style mismatch is part of the synthetic-to-real gap, and that stroke width is a parameter generators should control, either matched or randomised. It does not quantify how much of the gap stroke width alone accounts for. The record's own argument (a cheap "synthetic" cue, plus fragility under warping) is reasoning, not a measured result. Nothing contradicts the record. The evidence on this specific contribution is thin.

## Our decision
The project set the generator stroke to 3 px, the integer closest to the real mean. The findings suggest two follow-ups: re-measure synthetic stroke width after the change, and, if synthetic arms still lag, try width sampled per image from the real distribution. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
