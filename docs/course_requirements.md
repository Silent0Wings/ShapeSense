---
title: "comp333-course-project"
file_type: ".pdf"
file_size_bytes: 150178
content_hash: "sha256:1d50b70dc2f9960d10ece91bb454a11130f14303b399d20914c7879231601609"
approx_token_count: 1517
converted_at: "2026-11-20T02:37:44Z"
generator: "MDForge RAG Context Engine"
---

# comp333-course-project

## 📋 Table of Contents

- [Goal](#goal)
- [0. Data discovery (optional)](#0-data-discovery-optional)
- [1. Data integration](#1-data-integration)
- [3. Modeling](#3-modeling)
- [4. Testing](#4-testing)
- [Baseline and improvement](#baseline-and-improvement)
- [Cleaning](#cleaning)
- [Transformation](#transformation)
- [Feature selection](#feature-selection)
- [2. Compare two LLMs](#2-compare-two-llms)
- [3. Compare the pipeline with direct LLM prediction](#3-compare-the-pipeline-with-direct-llm-prediction)
- [4. Verification](#4-verification)
- [5. Deliverables](#5-deliverables)
- [GitHub repository structure](#github-repository-structure)
- [Colab project](#colab-project)
- [2. The two LLMs used and the dataset-awareness check](#2-the-two-llms-used-and-the-dataset-awareness-check)
- [7. The verification process](#7-the-verification-process)
- [8. Lessons learned about working with LLMs](#8-lessons-learned-about-working-with-llms)
- [6. Evaluation](#6-evaluation)





<!-- Page 1 -->


Final Project Requirements:
An LLM-Assisted Data Science Pipeline

## Goal

In this final phase of the project,  build full data science pipeline stage by stage with
how LLM was used and validate LLM output,and exlpain [to iterate with human judgment, and not to trust that output blindly.]


1. stage by stage

## 0. Data discovery (optional)

## 1. Data integration

2. Data preparation: cleaning, transformation, and feature selection

## 3. Modeling

## 4. Testing

For each stage, report:

• What you asked the LLM (keep all prompts in the repository).

• What the LLM recommended or produced.

• How you validated it.

• What you changed based on your own judgment, and why.

• The measured effect of your change (see Baseline and improvement below).

## Baseline and improvement

1. Train a model on the collected dataset before any data preparation. This is your baseline.

2. After each data preparation step, retrain the model and report the difference in your evalua-
tion metric from the baseline.

Evaluation metric. Use F1 for classification (state macro or weighted F1 if there are more than
two classes) and RMSE for regression. Choose one main metric, report it in the team sheet, and
use it for every comparison in this project. For RMSE, lower is better, so a negative delta is an
improvement.

1


<!-- Page 2 -->


Data preparation step
Baseline score
New score
Delta (New −Baseline)

## Cleaning

## Transformation

## Feature selection

## 2. Compare two LLMs

• two different LLMs , opus 5.5 and gemini 4 neon .

• At each stage, compare their recommendations and results.

• Report whether working with both helped you improve the result. For example, you can ask
one LLM to critique the output of the other.

## 3. Compare the pipeline with direct LLM prediction

• Give the LLM the dataset with the target column, and ask it to analyze the data and make
the predictions directly.

• Compare its predictions with those of your trained model, using the same held-out test set
and the same metric.

• Explain the difference you observe.

## 4. Verification

• Describe the process you used to verify the final results.

• Check whether each LLM already knew your dataset, for example by asking it to describe the
dataset or to complete some of its rows. Report what you find. You do not need to change
your dataset.

## 5. Deliverables

• Public GitHub repository with all required material: code, all prompts and LLM re-
sponses, results, and the slides as a PDF.

• Google Colab project with only the final pipeline the team agreed on.
It must show
the improvement in the evaluation metric over the baseline after each data preparation step:
cleaning, transformation, and feature selection. Share access with the instructor and the TAs.

• Slides for a 10-minute presentation, given by at least two team members. The slides must
report your improvements over the baseline and compare your findings with the direct LLM
analysis from Section 3.

Due: December 18 at 9:00 am. Submit your slides as a PDF on Moodle. The slides must
include the links to your public GitHub repository and your Colab project.

2


<!-- Page 3 -->


## GitHub repository structure

• README.md: team members, topic, the LLMs used, and the Colab link.

• data/: the data, or links to it if it is too large.

• prompts/: all prompts and LLM responses, organized by stage and by LLM.

• notebooks/: a copy of the final Colab notebook.

• results/: the improvement table and the comparison results.

• slides.pdf

## Colab project

• Contains only the final pipeline the team agreed on.

• Runs from top to bottom without errors.

• Has one section per stage, and prints the evaluation metric after each data preparation step.

• Evaluates the baseline model, the final model, and the direct LLM prediction on the same
test set.

• View access is shared with the instructor and the TAs.

Presentation layout (10 minutes, about 8 slides)

1. Topic, prediction task, and dataset

## 2. The two LLMs used and the dataset-awareness check

3. The pipeline stages: where the LLM helped and where the team corrected it

4. The improvement table: baseline, then cleaning, transformation, and feature selection

5. Comparison of the two LLMs, and how working with both improved the results

6. The trained pipeline vs. direct LLM prediction

## 7. The verification process

## 8. Lessons learned about working with LLMs

## 6. Evaluation

state that 
Weight (%)
Per-stage LLM use, validation, and human judgment
30
Verification process and dataset-awareness check
20
Two-LLM comparison
15
Pipeline vs. direct LLM prediction
15
Repository and Colab completeness
10
Presentation
10
