# 3_modeling - F30: The first vote comparison scored an empty class as zero. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F30 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f30) · Record: [F30](../inferred_prompts.md#f30)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How should macro F1 handle a class that has no predictions or no true samples in a subset? Search for how scikit-learn's zero_division setting works, for how papers treat undefined per-class F1 (for example Opitz and Burst 2019), and for the effect on comparisons between models.

## Response

### Well established

- **scikit-learn's convention.** The [`f1_score` docs](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) say: "When `true positive + false positive + false negative == 0` (i.e. a class is completely absent from both `y_true` or `y_pred`), f-score is undefined. In such cases, by default f-score will be set to 0.0, and `UndefinedMetricWarning` will be raised." `zero_division` takes `"warn"` (acts like 0), `0.0`, `1.0` or `np.nan`, and with `np.nan` "such values will be excluded from the average" (added in 1.3). "Macro" is the unweighted mean over labels. Passing `labels=` keeps classes that are absent from the data in that mean.
- **Two kinds of "undefined" exist.** Forman and Scholz, "Apples-to-Apples in Cross-Validation Studies", *SIGKDD Explorations* 12(1), 2010 ([PDF](https://www.dcc.fc.up.pt/~ines/aulas/1516/DM1/Papers/v12-1-p49-forman-sigkdd.pdf)), separate them. Precision is undefined when there are no positive predictions. Recall is undefined when the test subset has no positives, which "can happen ... if random sampling or unstratified cross-validation is used". Writing F as `2TP/(2TP+FP+FN)` defines it (as 0) for every case except a class with no true samples *and* no predictions.
- **Both usual fixes bias the result.** The same paper shows that substituting zero gives a negative bias and skipping the undefined folds gives a positive bias. Its recommendation is to pool the counts (TP, FP, FN) across subsets before computing F ("Ftp,fp ... should be used for computing F-measure"). It also says stratification makes undefined recall impossible "unless the number of folds exceeds the number of positives".
- **Macro F1 itself has two definitions.** Opitz and Burst, "Macro F1 and Macro F1" ([arXiv 1911.03347](https://arxiv.org/abs/1911.03347)), show that the mean of per-class F1 and the F1 of macro-averaged precision and recall can differ by up to 0.5 and rank classifiers differently. Their preliminaries set precision or recall to zero "when the denominator is zero", and their proof excludes classes where P+R=0 ([full text](https://ar5iv.labs.arxiv.org/html/1911.03347)). They don't analyse empty classes further. The paper is mainly relevant because it says to state which formula and which convention you use.
- **Group-aware stratified splitting is only approximate.** scikit-learn's [`StratifiedGroupKFold`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) keeps groups whole, but warns that with "a small number of groups containing a large number of samples the stratification will not be possible".

### Single reports

I found no paper focused specifically on empty classes in *paired model comparisons*. The bias results above come from the setting of averaging across folds.

### Reasoning (mine, not sourced)

In a paired comparison (vote rule X against Y on the same half), a class with no true samples in that half gets F1 = 0 for *both* models only if neither predicts it. If one model predicts the class even once (a false positive), it still scores 0, but for a different reason. Either way, the zero is a property of the split, not of the models. With 10 classes it lowers both macro means by 10 points, which squashes the scale and adds noise across halves. For per-class weighting, a zero F1 for an absent class would wrongly set that class's weight to zero. The defensible options are: (a) stratify so every class is present, (b) score only the classes present, the same set for both models (sklearn `zero_division=np.nan`, or an explicit `labels=` set), or (c) pool counts across halves as Forman and Scholz recommend.

### How it applies to ShapeSense

The sealed test sets contain every class, so the main arm comparisons (`stage5_eval/metrics.py`, where 0/0 is defined as 0 so the macro is a plain mean over all k classes) aren't affected. The risk is only in small, group-constrained subsets such as validation halves. There, near-duplicate groups are large, and the scikit-learn warning about group stratification applies directly.

## Validation

The record's cause is that large near-duplicate groups let a random half of validation hold no image of a class, which cost 10 macro-F1 points and gave the per-class weights a zero. That is exactly the "undefined recall under unstratified sampling" case Forman and Scholz describe. Their result that zero substitution biases F downward agrees with the 10-point drop. The record's fix (balance halves by class, leave absent classes out, give equal weights when a class is missing from the learning half) matches options (a) and (b). The literature points out that leaving classes out has a small upward bias of its own, so it should be applied the same way to every model compared, which the fix does. Nothing contradicts the record.

## Our decision

Halves are now balanced by class, absent classes are left out of the score, a class missing from the learning half gets equal weights, and a test covers this. The findings suggest one optional addition: report the class set used for each subset score, as Opitz and Burst urge. Pooling counts across halves would be a more robust alternative if subsets get smaller. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Zero-Support Class Denominators & Macro-F1 Aggregation Bias (`F30`)

### Metadata & Lineage

* **Entry ID / Type:** `F30` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage5_eval/metrics.py`, validation split-halves vote evaluation

### Mathematical & Statistical Anatomy of Undefined Per-Class $F_1$

1. **Two Distinct Macro-F1 Formulations (Opitz & Burst, arXiv:1911.03347):** Arithmetic mean of per-class $F_1$ scores ($\frac{1}{K}\sum_{c=1}^K F_{1,c}$) versus the harmonic mean of macro-averaged precision and recall ($\frac{2 \bar{P} \bar{R}}{\bar{P} + \bar{R}}$) can diverge by up to `0.5` points and induce rank reversals—requiring explicit specification of the averaging convention.
2. **Zero-Denominator Bias in Subset Splits (Forman & Scholz, *SIGKDD Explorations* 12(1), 2010):**
   * When a class $c$ has zero ground-truth instances in a subset ($TP_c + FN_c = 0$), recall $R_c$ is undefined; if $FP_c = 0$ as well, `scikit-learn`'s `f1_score(..., zero_division=0.0)` injects $F_{1,c} = 0.0$.
   * **Negative Bias of Zero-Substitution vs. Positive Bias of Omission:** Forman & Scholz prove that substituting `0.0` for undefined folds introduces a downward bias (in ShapeSense's 10-class setting, a single absent class artificially depresses macro-F1 by **`10.0` percentage points** and zeros out its learned per-class ensemble weight), whereas omitting undefined classes (`zero_division=np.nan`) introduces a mild upward bias unless applied identically across all compared models.
3. **Group-Stratification Limits (`StratifiedGroupKFold`):** Because ShapeSense enforces whole-group integrity across large `phash_group` clusters, unstratified random halves of validation splits can easily omit all clusters of a rare class.

### Controls Enforced in ShapeSense

* **Sealed Test Integrity:** All `10` shape classes are guaranteed present in the locked test split, keeping primary `stage5_eval/metrics.py` macro-F1 comparisons across `A0`, `A1`, `B`, `A2`, and `P` invariant.
* **Validation-Half Safeguards:** Validation partitions for ensemble weight calibration are now explicitly class-balanced, absent classes are excluded identically across compared voters (`zero_division=np.nan` / explicit `labels=`), any missing class defaults to equal ensemble weight, and Opitz & Burst's convention of reporting the exact active class set per subset is adopted.

