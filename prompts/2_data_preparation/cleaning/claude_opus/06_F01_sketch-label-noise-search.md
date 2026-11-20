# 2_data_preparation/cleaning - F01: Most Quick, Draw! diamonds were not rhombi (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F01 · Question from [failure_search_prompts.md](../../../failure_search_prompts.md#f01) · Record: [F01](../inferred_prompts.md#f01)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How much label noise and off-definition drawing is there in crowd-sourced sketch datasets such as Quick, Draw!, and how do published works detect and handle samples that do not match a class's definition (drop, relabel or keep)? How much label noise can a small CNN tolerate before a class's accuracy drops? Our case: most Quick, Draw! 'diamonds' were gems, cones or shields, not rhombi.

## Response

### Well established

- **Quick, Draw! is the noisiest of the common benchmarks.** Northcutt, Athalye and Mueller ([NeurIPS 2021 Datasets and Benchmarks](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/f2217062e9a397a1dca429e7d70bc6ca-Paper-round1.pdf); [arXiv 2103.14749](https://arxiv.org/pdf/2103.14749)) estimate a 10.12% label-error rate for QuickDraw, the highest of the ten datasets they studied. They flagged candidates with confident learning and had humans verify them, and about half of the flagged candidates proved to be real errors. Their headline point is that errors in **test** sets can change which model ranks best.
- **Google says the game labels are noisy.** The [Kaggle challenge announcement](https://research.google/blog/introducing-the-kaggle-quick-draw-doodle-recognition-challenge/) explains that training labels come from the game, where drawings may be incomplete or may not match the label. Its test set was labelled by hand. It notes that players can have different ideas in mind for a word, citing saws drawn for "seesaw". The `recognized` flag records only whether the game's model recognised the word, so it is not a quality label ([dataset README](https://github.com/googlecreativelab/quickdraw-dataset)). The same README says the drawings were moderated but may still contain inappropriate content.
- **Three families of handling methods.** Frénay and Verleysen ([IEEE TNNLS 2014](https://research.dial.uclouvain.be/handle/2078.5/254107)) group methods as noise-robust (keep the data, use a robust model), noise-cleansing (detect, then drop or relabel), and noise-tolerant (model the noise). Song et al. ([IEEE TNNLS 2023, arXiv 2007.08199](https://arxiv.org/pdf/2007.08199v5)) cover the deep-learning versions: sample selection (co-teaching, DivideMix), loss correction, and others. Patrini et al. ([CVPR 2017](https://openaccess.thecvf.com/content_cvpr_2017/html/Patrini_Making_Deep_Neural_CVPR_2017_paper.html)) correct for **class-dependent** noise when the corruption matrix is known or can be estimated.
- **Deep nets can memorise wrong labels.** Zhang et al. ([ICLR 2017](https://research.google/pubs/understanding-deep-learning-requires-rethinking-generalization/)) showed that standard CNNs reach zero training error on completely random labels. A clean training loss is therefore no evidence that the labels are clean.

### Single reports, or results that depend on the setting

- **How much noise is tolerable depends on its structure.** Rolnick et al. ([arXiv 1705.10694](https://arxiv.org/abs/1705.10694)) report that MNIST test accuracy stays above 90% even when each clean example is mixed with 100 randomly labelled ones. They say this holds across several noise patterns, including noise biased toward confusable classes, and that it needs more data. That is uniform or diluted noise spread across many examples. I found no published threshold for the ShapeSense case: one source supplies a block of off-definition drawings that look like other classes. I could not confirm a general per-class tolerance number.
- Kaggle competitors' write-ups mention many wrongly labelled doodles. My search surfaced this only as a snippet that I could not tie to one page, so treat it as anecdotal and uncited.

### Reasoning (mine, not from a source)

- The ShapeSense case is not random label noise. It is a **definition mismatch**: the Quick, Draw! prompt "diamond" means a gem to many players, which is the seesaw/saw effect in Google's post. The wrong labels cluster at about 70-80% of one source's diamonds. They resemble pentagons, hexagons and triangles, so they push the diamond boundary into those classes. This is class-dependent, structured noise. Rolnick's dilution result does not cover it, and the recorded symptom fits: 59% recall on Quick, Draw! diamonds, with 16 of 76 called triangle.
- The noise also sat in **validation and test**. Northcutt et al. show this can reorder model rankings, which matters for a project that compares arms by macro F1 differences of under one point.
- Dropping by rule beats relabelling here. Most off-definition drawings have no correct label among the 10 classes, so relabelling would mean inventing a class. Hand review keeping clear rhombi would work but costs reviewer time and introduces a reviewer effect.

### How it applies to ShapeSense

The literature supports noise-cleansing over noise-robust training for this case, because the noise is structured, clustered in one source, and present in the test split. The cost of dropping the drawings is that diamond becomes a single-source class, which links this failure to F05. Confident learning (Northcutt et al.) could be applied to the remaining Quick, Draw! classes as a check that no other class has a hidden mismatch. Flagged items would still need human review, since only about half of flagged candidates are real errors.

## Validation
The record's cause was that most Quick, Draw! diamonds contradict the rhombus definition, which made them harmful label noise. Google's own description of the game, the measured 10% QuickDraw error rate, and the class-dependent noise literature all agree. The literature adds that off-definition labels in test data distort model comparisons, which supports the decision to drop them before any test read and re-freeze. It also adds that no general tolerance threshold covers structured noise. Nothing found contradicts the record.

## Our decision
The project excluded all 500 Quick, Draw! diamonds by a written rule in Stage 1, re-froze the split before any test read, retrained every model, and listed diamond as a render-only class. A further step the findings suggest is a confident-learning screen of the other Quick, Draw! classes, with human review of what it flags. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
