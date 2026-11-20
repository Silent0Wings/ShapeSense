# 1_data_integration - F05: The images reveal which source they came from (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F05 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f05) · Record: [F05](../inferred_prompts.md#f05)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Can a classifier tell which dataset an image came from, and what does that mean for a model trained on the merged datasets? Search for work on dataset bias and the 'Name That Dataset' experiment (Torralba and Efros 2011), shortcut learning (Geirhos et al. 2020), and how to measure and report the risk. Our case: a classifier named the source 91.7% of the time against a 46.7% baseline.

## Response

### Well established

- **Datasets carry a recognisable signature.** Torralba and Efros ([CVPR 2011 PDF](https://people.csail.mit.edu/torralba/publications/datasets_cvpr11.pdf)) played "Name That Dataset" with twelve recognition datasets. Researchers in their labs mostly scored above 75%. A 12-way linear SVM trained on 1,000 images per dataset could also tell them apart. They concluded that, despite their creators' efforts, the datasets carry strong built-in bias. They also measured that bias as a cross-dataset generalisation drop: train on one dataset, test on another.
- **The effect has grown with stronger models.** Liu and He ([ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/66772e6aa61e54ae16443ae1d78a7319-Abstract-Conference.html), [arXiv 2403.08632](https://arxiv.org/abs/2403.08632?context=cs)) reran the experiment on YFCC, CC and DataComp, three large datasets built to be diverse. A modern network named the source with 84.7% held-out accuracy. They report that the features learned for this task transfer to semantic tasks, which they argue memorisation alone cannot explain.
- **Shortcut learning is the mechanism.** Geirhos et al. ([Nature Machine Intelligence 2020](https://is.mpg.de/publications/geirhosetal20), preprint arXiv 2004.07780) define shortcuts as decision rules that work on standard benchmarks but fail under harder test conditions. They recommend testing out of distribution rather than only on i.i.d. test sets.
- **When source correlates with label, models use the source.** Zech et al. ([PLOS Medicine 2018](https://doaj.org/article/86bad117ffd645d7bd86f36b7db6dd6f)) found that CNNs identified the source hospital of a chest X-ray almost perfectly (99.95% NIH, 99.98% Mount Sinai). Pneumonia prevalence differed by site, so the hospital alone predicted the label with AUC 0.861. Internal test scores overstated external performance in 3 of 5 comparisons. DeGrave et al. ([Nature Machine Intelligence 2021](https://www.x-mol.com/paper/1399850931057049600); [UW summary](https://news.cs.washington.edu/2021/06/01/allen-school-researchers-discover-medical-ai-models-rely-on-shortcuts-that-could-lead-to-misdiagnosis-of-covid-19-and-other-diseases)) showed that COVID-19 detectors built from positives and negatives taken from different sources learned dataset-specific text markers and patient positioning. They also warned that an external test alone does not prove the model uses the right features.
- **The standard check is to hold out a whole domain.** DomainBed ([Gulrajani and Lopez-Paz, ICLR 2021](https://arxiv.org/abs/2007.01434)) evaluates generalisation by leaving one domain out. It also treats model selection as part of the method and reports leave-one-domain-out validation as one of its selection criteria.

### Single reports

- Liu and He's claim that dataset-classification features carry semantic content comes from one paper. For ShapeSense, the safer reading is "fingerprints are easy to learn", not "fingerprints are harmless".
- Li, Gouk and Hospedales ([arXiv 2202.00563](https://ar5iv.labs.arxiv.org/html/2202.00563)) argue that cross-validating domain by domain is a better selection rule than validating instance by instance. This disputes part of DomainBed's conclusion.

### Reasoning (mine, not from a source)

- A source classifier that is far above its baseline proves that a fingerprint exists. It does not prove the shape model uses it. What matters is whether source is **confounded with label**. In the medical cases the harm came from that confound, not from the fingerprint itself.
- In ShapeSense the confound is complete for single-source classes: ellipse, pentagon, and after F01 also diamond. For those classes, source and label cannot be separated in training, validation or test. Sealed test data from the same sources measures in-distribution skill only, which is exactly the overstatement Zech et al. warn about.
- The 91.7% result came from a linear model on 16x16 pooled pixels. That is a lower bound on how separable the sources are. A CNN can probably do better.

### How it applies to ShapeSense

1. The literature supports the project's framing: the fingerprint is expected with merged sources, and it cannot be removed, only measured and reported.
2. Leave-one-source-out is the right test. The recorded drop on held-out `github_handdrawn`, from 90.2% to about 64-70% for A0 and about 70-72% for B, is the external-test gap the papers predict.
3. To follow Geirhos et al. and DeGrave et al. more closely, report per-source F1 beside macro F1 for every arm. Flag single-source classes in every table. Consider one attribution check, for example whether the shape model's errors on held-out sources cluster by source style.
4. For arm B and arm P, synthetic data is a fifth source with its own fingerprint (see F10). A source classifier that includes synthetic images would show whether the generator is easy to tell apart from real data.

## Validation
The record's cause was that the images carry a source fingerprint, so a model can lean on style instead of shape. Every source above agrees, and the Name That Dataset result has been reproduced at scale. The literature adds two refinements. First, harm depends on how source is confounded with label, which makes the single-source classes the real exposure rather than the 91.7% figure itself. Second, an external or held-out-source test can miss a shortcut, so held-out-source runs are necessary but not sufficient (DeGrave et al.). Nothing found contradicts the record.

## Our decision
The project already reports the source-classifier number beside the results. It also runs held-out-source experiments, publishes per-source accuracy, and marks single-source classes. The findings suggest two optional additions: a source-attribution check that includes synthetic images, and a fixed per-source table for every arm in the final report. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
