# 3_modeling - F02: Leave-one-source-out training could not run on all ten classes. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F02 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f02) · Record: [F02](../inferred_prompts.md#f02)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

> How do domain-generalization studies run leave-one-domain-out evaluation when some classes exist in only one domain? Search for protocols for partial or open domain generalization and for how they score a held-out domain that lacks some classes. Our case: ellipses exist only in the Hand-Drawn source.

## Response

### Well established

- **Standard leave-one-domain-out assumes a shared label space.** DomainBed, the reference benchmark, trains on all but one domain and tests on the held-out one across seven datasets. It also defines a "leave-one-domain-out" model-selection rule that trains one model per held-out training domain ([Gulrajani and Lopez-Paz, arXiv 2007.01434](https://arxiv.org/abs/2007.01434)). Its datasets share one label set across domains, so the protocol does not say what to do when a class is missing from the training domains.
- **Open Domain Generalization (ODG) is the named setting for source domains with different label sets.** Shu et al. define it as follows: "the distributions and label sets of each individual source domain and the target domain can be different". They also name ShapeSense's exact difficulty: some classes exist in many more domains than others, and the minor classes lack diversity ([CVPR 2021](https://openaccess.thecvf.com/content/CVPR2021/html/Shu_Open_Domain_Generalization_with_Domain-Augmented_Meta-Learning_CVPR_2021_paper.html), [arXiv 2104.03620](https://arxiv.org/abs/2104.03620)). The task in ODG is to classify the **known** classes in the unseen domain and to **detect** the classes never seen in training as "open". Search summaries of the paper report the metrics as accuracy on known classes plus an H-score that combines known and open performance ([CVPR listing](https://openaccess.thecvf.com/content/CVPR2021/html/Shu_Open_Domain_Generalization_with_Domain-Augmented_Meta-Learning_CVPR_2021_paper.html)). I could not open the full PDF (HTTP 403), so I have not verified the exact split protocol from the paper's text.
- **Heterogeneous DG** is a related setting in which source and target label spaces differ completely. There the trained feature extractor is evaluated with a new classifier fitted on the target label space (an SVM on Visual Decathlon) ([Li et al., ICML 2019](https://arxiv.org/abs/1901.11448), [slides](https://ICML.cc/media/icml-2019/Slides/4363.pdf)). That protocol tests features, not the trained classifier head.

### Single reports

- DAML's own fix fills the missing classes in each domain by mixup across domains and soft labels ([arXiv 2104.03620](https://arxiv.org/abs/2104.03620)). It is a training method, not an evaluation protocol, and it was shown on PACS, Office-Home and a multi-dataset benchmark, not on line drawings.
- A later paper argues that domain-wise cross-validation is a better selection objective than DomainBed's instance-wise rule ([arXiv 2202.00563](https://arxiv.org/abs/2202.00563)). This concerns model selection, not missing classes.

### What I could not find

I found no standard protocol for "leave-one-domain-out, then score only on the shared classes" under a closed-set metric such as macro F1. The closest established practice is ODG's split between known-class accuracy and open-class detection.

### Reasoning

Restricting the held-out run to classes that appear in the training sources is ODG's "known classes" score, the scientifically valid part. Two points from that framing matter. First, held-out-domain images of the missing class are not just noise to drop. They are the "open" test, and ODG would at least report what the model does with them. Second, a closed-set score on a two-class subset is not comparable to 10-class macro F1, and its chance level depends on the model's nine possible outputs, not on two.

## How it applies to ShapeSense

In ODG terms, holding out Hand-Drawn makes ellipse an open class. The project's design (train on nine classes, score Hand-Drawn triangles and rectangles, report separately as unseen-source generalization) matches ODG's known-class protocol, and the rule against synthetic-only ellipses stands in for an augmentation trick like DAML's. The literature suggests two low-cost additions that use the same runs: (1) report the confusion of held-out Hand-Drawn ellipses, that is, which of the nine classes they fall into and with what softmax confidence, as an open-class check; (2) state the chance and majority-class baselines next to the 63.6 to 72.2% hold-out accuracy so that readers do not read it against 50%. Neither changes the main 10-class comparison.

## Validation

The literature agrees with the documented cause: a held-out domain that alone holds a class leaves that class with no training data, and the standard leave-one-domain-out protocol does not cover this case. It agrees with the outcome too: scoring only the classes the model could learn is ODG's known-class evaluation. It adds that the setting has a name and a literature, and that the missing class is normally kept as an open-set test rather than discarded. Nothing found contradicts the record. The "Partly" state fits: generalization of ellipses to an unseen source is untestable without a second source of ellipses, and ODG methods do not remove that limit.

## Our decision

The project runs hold-out runs on nine classes, scores them on Hand-Drawn triangles and rectangles only, and reports them apart from the 10-class comparison. Ordinary runs with an empty class still fail loudly. The findings suggest optionally reporting where held-out ellipses land (open-class behaviour) and a chance baseline for the hold-out score. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Open Domain Generalization (ODG) & Missing-Class Evaluation (`F02`)

### Metadata & Lineage

* **Entry ID / Type:** `F02` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/sweep.py`, `src/stage5_eval/`

### Taxonomy of Cross-Domain Label-Space Shift

Standard domain-generalization benchmarks (e.g., DomainBed, Gulrajani & Lopez-Paz, arXiv:2007.01434) assume identical label sets $\mathcal{Y}_s = \mathcal{Y}_t$ across all domains. Holding out the Hand-Drawn source violates this assumption because `ellipse` exists exclusively in Hand-Drawn ($\mathcal{Y}_{\text{train}} \subsetneq \mathcal{Y}_{\text{test}}$, $\vert\mathcal{Y}_{\text{train}}\vert = 9$, $\vert\mathcal{Y}_{\text{test}}\vert = 10$).

* **Open Domain Generalization (ODG — Shu et al., CVPR 2021, arXiv:2104.03620):** Formally defines cross-domain evaluation under heterogeneous source/target label spaces, decomposing evaluation into known-class accuracy ($\mathcal{Y}_{\text{train}} \cap \mathcal{Y}_{\text{test}}$) and open-class novelty detection ($\mathcal{Y}_{\text{test}} \setminus \mathcal{Y}_{\text{train}}$), combined via the harmonic H-score.
* **Heterogeneous Domain Generalization (Li et al., ICML 2019, arXiv:1901.11448):** Evaluates frozen feature extractors by fitting a linear probe on target-domain classes, testing representation transfer rather than end-to-end classifier heads.

### Protocol Calibration for ShapeSense LOSO Runs

* **Known-Class Isolation:** Training on 9 classes and scoring strictly on Hand-Drawn `triangle` and `rectangle` instances (`63.6%–72.2%` accuracy) aligns directly with ODG's known-class evaluation, while avoiding synthetic-only class fabrication (such as DAML's cross-domain mixup) that would confound synthetic-data comparisons.
* **Baseline & Open-Set Diagnostics:** Because the 9-class head outputs a 9-way softmax rather than a binary choice, reporting 9-class uniform chance (`11.1%`) and majority-class baselines alongside `63.6%–72.2%` prevents readers from misinterpreting the score against a `50%` binary baseline, while logging confusion/softmax entropy on held-out Hand-Drawn `ellipse` samples characterizes open-set behavior at zero training cost.

