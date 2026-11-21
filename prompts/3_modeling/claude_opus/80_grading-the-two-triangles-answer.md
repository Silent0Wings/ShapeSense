# 3_modeling - Grading Gemini's answer on two triangles labelled "triangle"
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/22_two-triangles-classified-as-triangle.md](../gemini_4_neon/22_two-triangles-classified-as-triangle.md)
- Date: 2026-11-21

## Prompt

> you are opus generate a prompt md file where you judge tahat prompt grade it and put your answer in the equivalent opus folder

The exchange being judged: the user asked why the CNN labels an image with two triangles as "triangle" when it was "only trained on 1 triangle image", then whether that is an acceptable limitation, then whether more synthetic data or augmentation would have fixed it.

## Response

### Grade: B (76 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 22 / 25 | A single-label classifier must output one label for the whole image and has no way to count. Augmentation changes how examples look, not what the labels say, so it cannot teach counting. Both points are right and are the heart of the answer. |
| Read the question correctly | 10 / 20 | It took "trained on 1 triangle image" to mean one training image, and built two of its five causes on that (memorising one image, no negative examples). The user meant one triangle per image. It also assumed a binary or one-class "triangle" classifier. A short clarifying question would have avoided both. |
| Fit to this project | 14 / 20 | The project is a 10-class classifier trained on thousands of images per class, so "no negative examples" does not apply: the other nine classes are the negatives. Its main recommended fix, contour counting, suits clean shapes, but much of this data is hand-drawn with open strokes and gaps, where contours break, as the user had said in the earlier exchange. |
| Actionable advice | 18 / 20 | Clear options for each goal: keep the classifier for presence, count labels, a detector, or contour geometry. The table of label setups in the third reply is the most useful part. |
| Accuracy of details | 12 / 15 | Mostly sound. Two soft spots: convolution is translation-equivariant, and the "invariance" comes from pooling and the classifier head, which the answer runs together. And it never names the real gap for this project, which is rejecting input that fits none of the 10 classes, not counting. |

### What it got right
- The diagnosis is a task and label mismatch, not a training failure.
- More augmentation or synthetic data cannot fix it while the labels stay the same. Count labels, boxes or masks would.
- An augmented image must keep its label true: a crop that cuts off a triangle would make a count label wrong. The same rule applies to this project's shape labels, which is why shear and non-uniform scaling are limited for some classes.

### What it got wrong or missed
- **Premise:** it answered a question about one training image, which was not what was asked.
- **The relevant failure for this project:** the model cannot say "none of these." An image with two triangles, a letter or a scribble still gets one of the 10 labels. The answer mentions a "none / background" class only in passing, as a diagnostic.
- **The existing guard:** the demo already shows "not sure" when the top probability is below 0.5 (`demo/logic.py`). The answer's tip to "inspect the softmax probability" points the right way, but softmax scores are often high on inputs unlike the training data, so a threshold alone is a weak guard. It did not say so.

### What I would have answered for this project
1. It is expected. The model answers "which of the 10 shapes is this one drawing?" It was never asked to count, and it has no way to answer "none of these."
2. It is an acceptable limitation if the report and slides state it. The task is single-shape classification.
3. More augmentation or synthetic data would not change it, because no label describes "two shapes" or "not a shape."
4. If it has to be handled, two options cost little:
   - Measure it: build a small out-of-scope set (two shapes, letters, scribbles) and count how often the demo says "not sure." That turns the limitation into a number for the report. It has not been run.
   - Add an `other` class with out-of-scope examples. `docs/phase1_report_plan.md` already recommends this, pending the team's approval. It would mean retraining every arm and repeating the evaluation.

   A detector or count labels would be a different project.

## Validation

- Checked against the Gemini file, `configs/taxonomy.yaml` (10 classes, no reject class), `demo/logic.py` (`NOT_SURE_THRESHOLD = 0.5`) and `docs/phase1_report_plan.md` (the `other` class recommendation).
- The grade is my judgment against the criteria in the table. No second grader checked it.
- The out-of-scope measurement in point 4 is a proposal and was not run, so no number is claimed.

## Our decision

Keep Gemini's answer as the record of the exchange, with this grade beside it. The limitation goes into the report and slides as stated in point 1. Whether to measure it or add an `other` class is the team's call.

## Measured effect

None. No change was made.
