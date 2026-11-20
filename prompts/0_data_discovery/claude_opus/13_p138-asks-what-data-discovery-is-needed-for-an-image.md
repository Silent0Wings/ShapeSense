# 0_data_discovery - P138: Asks what data discovery is needed for an image CNN project
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P138. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[

<pasted_content id="18fa">
Show more


for image training cnn what kind of data discovery shoudl we do ?


For a CNN image project, data discovery means understanding the images, labels, and deployment conditions before you build or train a model. The goal is to find coverage gaps, label errors, leakage, and distribution mismatch—not just count files. CNN training typically requires labeled images, consistent preprocessing, and separate train/validation/test splits.

Core discovery questions
Area	What to discover	Why it matters
Task definition	Classification, detection, segmentation, retrieval, or regression; exact output labels	Determines annotation format and evaluation metric
Source and rights	Where images came from, licenses, privacy/PII, whether redistribution is allowed	Prevents legal and deployment problems
Population	Who or what generated the images; devices, locations, time periods, capture conditions	Reveals whether training data matches real-world use
Labels	Class definitions, annotation guidelines, annotator identity, disagreement rate	Ambiguous or inconsistent labels directly cap model accuracy
Class balance	Number of images per class, rare classes, near-duplicate classes	Imbalance can make a CNN biased toward frequent classes
Image properties	Resolution, aspect ratio, color mode, file format, corruption, EXIF metadata	Determines resizing, normalization, and preprocessing choices
Visual variation	Lighting, blur, occlusion, pose, scale, background, camera angle, season/time	Shows whether the CNN must generalize beyond the collected samples
Duplicates	Exact duplicates, near-duplicates, repeated scenes, same patient/object across images	Prevents inflated validation performance and data leakage
Deployment mismatch	Images the model will see in production versus training images	A model trained on clean stock photos may fail on phone-camera images
Practical discovery checklist
Inventory the dataset

Count images per class, source, capture device, date, and split.

Record image dimensions, channels, file formats, corrupt files, and total storage.

Compute basic statistics: mean/std per RGB channel, resolution distribution, aspect-ratio distribution, and grayscale/color mix.

Inspect labels before trusting them

Read the annotation guideline; resolve ambiguous cases explicitly.

Sample 50–200 images per class and visually verify labels.

Have a second annotator label a subset; measure agreement (e.g., Cohen’s kappa for classification).

Look for classes that overlap semantically, such as “car” versus “truck,” or “benign” versus “malignant” without clear criteria.

Check class coverage

Build a grid: class × lighting × camera/device × background × pose/scale × image quality.

Identify empty cells—these are likely failure cases.

Pay special attention to minority classes and visually confusing pairs.

Find duplicates and leakage

Hash raw files to detect exact duplicates.

Use perceptual/image embeddings or feature matching for near-duplicates.

Ensure that images from the same subject, patient, scene, video, or capture session do not appear in both train and validation/test sets.

Split by the natural grouping unit, not by individual image, when appropriate.

Analyze errors and difficulty

Run a quick baseline CNN or pretrained model.

Inspect the highest-loss and most-confused validation samples.

Determine whether errors come from bad labels, insufficient data, domain shift, tiny objects, occlusion, or ambiguous classes.

Measure deployment realism

Collect or reserve a held-out test set that resembles production images as closely as possible.

Test on subsets: dark images, motion blur, unusual viewpoints, different devices, and unseen classes if relevant.

Do not tune the model using this final test set.

Useful visualizations
Class-count bar chart: exposes imbalance.

Image-size/aspect-ratio histogram: guides resizing and cropping policy.

t-SNE/UMAP of image embeddings: reveals clusters, outliers, and possible mislabeled images.

Confusion matrix: identifies visually similar classes.

Sample montage per class: makes annotation and quality problems obvious.

Metadata scatter plots: e.g., brightness versus class, resolution versus source, date versus label.

Decisions discovery should produce
At the end, you should be able to state:

The exact label taxonomy and annotation rules.

Which classes are rare, ambiguous, or poorly covered.

The preprocessing policy: resize/crop, color conversion, normalization, and augmentation.

The split policy and leakage-prevention rule.

The primary metric: accuracy, balanced accuracy, F1, mAP, IoU/Dice, etc.

The expected production distribution and a realistic held-out evaluation set.

A prioritized data-collection plan for the biggest gaps.

Example
For a “defective vs. acceptable part” classifier:

Discover that 92% of images are from one camera and normal lighting.

Find that defective samples are only 3% of the data.

Detect that several defect images were duplicated across train and test.

Realize that “scratch” and “dent” were inconsistently labeled.

Then collect more defective samples under varied lighting, split by production batch, clarify the defect taxonomy, and evaluate on a separate factory-camera test set.

Avoid these traps
Do not decide augmentation before checking whether flips, rotations, crops, or color changes preserve the label. For example, horizontal flip may be invalid for text, directional defects, or left/right anatomy.

Do not normalize test data using statistics computed from the test set.

Do not rely on random splits when images are correlated by patient, scene, video, or capture session.

Do not treat a high validation score as proof of real-world performance if the validation set has the same biases as training data.

Augmentation such as cropping, flipping, brightness/contrast/color jitter, and noise can improve robustness, but it should be chosen after discovering which transformations are valid for your task. Standard CNN preparation also includes resizing, normalization, augmentation, and a clean train/validation/test split.

How to check for data leakage in image splits
Tools for exploratory data analysis on images
How to find class imbalance and bad labels
What resolution and aspect ratio checks to run
How to audit dataset diversity for lighting and angles
</pasted_content id="18fa">

]

## Response

I already answered this paste above, so there is nothing new to add. Here is the fuller version of that answer.

This is a repeat of the earlier answer with more detail. I did not run anything new for it. I checked the status of each item against the repo notes, so the list below reflects what the notes record, not a fresh run on the data.

##### Where things stand

- **Covered by the repo:**
  - Duplicate checks: the removal of identical files on 2026-10-19, confirmed by MD5 of every file ([docs/source.md](../../../docs/source.md), "Removed duplicates").
  - Source holdouts: the repo lists sealed holdout sets at `data_set/fresh_holdout/` and `data_set/fresh_holdout_2/`. Whether these are split by source is unconfirmed in this pass.
  - Class counts: per-source counts are recorded in [docs/source.md](../../../docs/source.md).
- **Still open** (listed in the notes at `docs/notes/pairs/7_meta_and_other.md`, "What is still to do", and `docs/notes/session_history_2026-11-19.md`):
  1. **Label agreement.** Have a second person label a sample of the ambiguous pairs (square vs rectangle, circle vs ellipse, diamond vs square) and measure agreement, for example with Cohen's kappa. The repo records the label rules but no agreement score, so the reliability of the labels is unmeasured.
  2. **Coverage grid.** Check class by source by stroke width, rotation and framing. The repo has per-source counts but not this grid, so empty cells, which would be the likely failure cases, are not yet visible.
  3. **Demo mismatch.** Compare the drawing demo's input with the training images, since a hand-drawn sketch and a clean render can look very different. The demo's "not sure" threshold of 0.5 (`demo/logic.py`) has not been tuned on real drawings.
  4. **Reject class.** The 10-class model has no reject class, so a letter or scribble still gets a confident answer from the demo. [docs/phase1_report_plan.md](../../../docs/phase1_report_plan.md) recommends an 11th `other` class, but it is a recommendation for approval, and the taxonomy must not be changed until that approval is given.
- The notes also list a fifth item, checking valid augmentations. It is not one of the four open items named in this answer. The repo already restricts shear and non-uniform scale for the classes where they would change the label ([configs/taxonomy.yaml](../../../configs/taxonomy.yaml)), and the notes ask that this still holds for the new transforms.

##### Choosing the next step

Please tell me which open item you want me to run first. The label-agreement check needs a second labeller, so it cannot start until you have picked the sample to be labelled. The other items can be run without that input, but the order is your call.

Suggested order, with the reason for each step: the label-agreement check comes first if the labels are not yet trusted, because every later measurement depends on them. The reject class and the demo threshold come next if the demo is the deliverable, because they decide what the demo does with out-of-scope input. The coverage grid can run at any time from the existing per-source counts, so it is a good fill-in step while waiting for a labeller.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
