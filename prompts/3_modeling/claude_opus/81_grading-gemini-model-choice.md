# 3_modeling - Grading Gemini's answer on which models to compare
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/21_model-choice-for-shape-recognition.md](../gemini_4_neon/21_model-choice-for-shape-recognition.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon answer on which models to compare for geometric shape recognition, as Claude Opus 5.5.

The exchange being judged: the user quoted the lecture ("choose at least three models") and asked which models suit geometric shape recognition. Gemini recommended a feature-based pipeline with SVM, Random Forest, KNN and an MLP. The user then said the data is augmented, mixed with synthetic shapes and noisy on purpose, and Gemini switched to a CNN compared with classical classifiers.

## Response

### Grade: B (80 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 21 / 25 | Comparing several models empirically, augmenting the training side only, and testing on clean and noisy data are all sound. The second reply's case for a CNN on noisy, synthetic data is right. |
| Read the question correctly | 15 / 20 | The first reply assumed clean, isolated shapes and recommended against raw pixels without asking what the data looked like. It had to reverse its main recommendation once the user described the data. |
| Fit to this project | 14 / 20 | It scores models by accuracy (`scoring="accuracy"`), but the course requires F1 for classification and this project reports macro F1. It recommends a stratified random split, which would put near-duplicate images on both sides; the project splits by near-duplicate group (`group_by: phash` in `configs/pipeline.yaml`). |
| Actionable advice | 18 / 20 | Runnable feature-extraction and comparison code, a clear split table, and a model list. The "report wording" paragraph is usable almost as written. |
| Accuracy of details | 12 / 15 | The feature list (circularity, convexity, Hu moments) and the OpenCV calls are correct. "Do not feed raw pixels" is too strong as a general rule; it only holds for small, clean images and small models. |

### What it got right
- At least three models, compared on the same training data and the same held-out test set.
- Augmentation and synthetic data on the training side only, with validation and test left untouched.
- Report both a clean test result and a noisy test result, which is what iteration 3 does with damaged copies of `fresh_holdout_2`.

### What it got wrong or missed
- **Metric:** accuracy instead of macro F1. The course says to use F1 for classification and to use one metric for every comparison.
- **Split:** stratified random splitting leaks near-duplicates. The project's group-aware split exists for exactly that reason.
- **First reply:** it recommended a contour-feature pipeline before knowing the data, then reversed. One question about the data would have saved the first reply.
- **What already exists:** it could not know that the project already compares the CNN with logistic regression on raw pixels and a linear SVM on HOG features. That comparison already meets the lecture's "at least three models".

### What I would have answered for this project
Keep the CNN. Its comparison models are already in Stage 4 (`src/stage4_train/baselines.py`): logistic regression on pixels scored 77.7 and the HOG SVM 82.5 validation macro F1 (`results/phase2_snapshot/baselines.json`). That is three models scored with one metric. If a fourth is wanted, a Random Forest on HOG plus Hu moments would add a feature-based model, trained on the same split and scored by macro F1.

## Validation

- Checked against the Gemini file, `configs/pipeline.yaml` (split by `phash`), `results/phase2_snapshot/baselines.json` (77.7 and 82.5 validation macro F1) and `docs/course_requirements.md` (F1 for classification).
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the CNN with logistic regression and the HOG SVM as its comparison models, scored by macro F1, with the group-aware split. A feature-based Random Forest stays optional.

## Measured effect

None. No change was made.
