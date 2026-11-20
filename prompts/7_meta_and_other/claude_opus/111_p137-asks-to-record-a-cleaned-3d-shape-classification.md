# 7_meta_and_other - P137: Asks to record a cleaned 3D shape classification project idea
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P137. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

record these =[

<pasted_content id="18fa">
Show more


clean this project idea =merging many datasets of shapes datasets , combine them , and use data synthesising and data augmentation , and train a model on them to do shapes classification

Cleaned Project Idea
Project: Build a unified 3D shape classification model. Merge several public shape datasets into one standardized corpus, expand it with augmentation and synthetic data, then train a classifier on it.

Goal
Train a single model that classifies shapes (for example chair, table, airplane) and generalizes across data sources, not just within one benchmark.

Pipeline
Collect datasets. Choose sources such as ModelNet40, ShapeNet, ScanObjectNN, and Objaverse. Check each license first, since some are non-commercial or research-only.

Standardize format. Convert everything to one representation, such as point clouds of N points (1024 or 2048) or watertight meshes. Normalize scale, center, and orientation.

Unify labels. Map each dataset's class names to one shared taxonomy. Drop or merge classes that don't align, and record the mapping in a file.

Deduplicate and split. Remove near-duplicate shapes across datasets. Split by object, never by augmented copy, to avoid train/test leakage. Keep one source dataset held out for cross-domain testing.

Augment. Apply random rotation, scaling, jitter, point dropout, anisotropic stretching, and partial crops or occlusion.

Synthesize. Generate parametric primitives and procedural variants. Add simulated scans with noise and missing regions. Optionally use generative models for extra samples, and tag these as synthetic.

Train. Start with a baseline such as PointNet++ or DGCNN. Then try a stronger model such as Point Transformer or a multi-view CNN. Handle class imbalance with weighted loss or resampling.

Evaluate. Report accuracy and per-class F1. Run an ablation of real data only, real plus augmented, and real plus augmented plus synthetic. Test on the held-out dataset and on noisy data.

Deliverables
Reproducible conversion and merge scripts

Label taxonomy file and dataset card with licenses

Trained model weights and an evaluation report

A simple inference demo, such as a script or a viewer

Main Risks
Label mismatch between datasets

Domain gap between clean CAD models and real scans

Leakage from duplicates or augmented copies across splits

Synthetic data that doesn't resemble real shapes and hurts performance

If you meant 2D shapes (circles, triangles, polygons) instead of 3D, tell me. The pipeline stays similar, but the data sources and models change to images and a CNN or ViT.

2d shapes not 3d

Cleaned Project Idea (2D Shapes)
Project: Build a unified 2D shape classifier. Merge several public shape datasets into one standardized corpus, expand it with augmentation and procedurally generated synthetic data, then train a model to classify shapes such as circle, triangle, square, pentagon, star, and ellipse.

Goal
Train one model that recognizes 2D shapes across clean digital renders, hand-drawn sketches, and photos, so it generalizes beyond any single dataset.

Pipeline
Collect datasets. Look for geometric-shape image sets on Kaggle and Hugging Face, plus sketch sets such as Quick, Draw! and TU-Berlin. Check each license before merging.

Standardize format. Convert to one size (for example 64×64 or 128×128), grayscale or binary, with a consistent background and centered, scale-normalized shapes. For stroke data, rasterize it first.

Unify labels. Map class names to one taxonomy (such as "rectangle" vs "square"; "oval" vs "ellipse"). Store the mapping in a file and decide how to treat ambiguous classes.

Deduplicate and split. Remove near-duplicates using perceptual hashing. Split by source image before augmenting, and hold out one dataset for cross-domain testing.

Augment. Apply rotation, scale, translation, shear, flips, stroke-width changes, blur, noise, elastic distortion, and random backgrounds. Be careful that augmentations don't change the class (heavy shear can turn a square into a parallelogram).

Synthesize. Generate shapes procedurally with code (Pillow, OpenCV, or SVG): random size, rotation, color, line style, fill, and wobble to mimic hand drawing. Add clutter, overlaps, and texture backgrounds. Tag synthetic samples in the metadata.

Train. Start with a small CNN baseline, then try ResNet or MobileNet fine-tuning, and optionally a small ViT. Use class-weighted loss if classes are imbalanced.

Evaluate. Report accuracy, per-class F1, and a confusion matrix. Run an ablation: real only, real plus augmented, real plus augmented plus synthetic. Test on the held-out dataset and on noisy or hand-drawn inputs.

Deliverables
Merge and preprocessing scripts

Label mapping file and dataset card with licenses

Trained weights and evaluation report

A small demo, such as a drawing canvas that predicts the shape live

Main Risks
Ambiguous classes (square vs rectangle, circle vs ellipse)

Domain gap between clean synthetic shapes and messy hand-drawn ones

Augmentations that alter the true label

Leakage from duplicates across splits


⠙
</pasted_content id="18fa">

]

## Response

I saved both cleaned versions as a reference file in the repo's `docs` folder, and labeled which one matches this project. The project in question is the 2D one. The 3D version is kept only for reference.

#### Recording the candidate datasets
The dataset list is recorded as a separate candidate-datasets file, marked as unverified. I won't run the follow-up requests (benchmarks, the dSprites loader, code) until you say which one you want first.

##### Why the 2D version is the project
The user's message said "2d shapes not 3d", and the 2D cleaned idea matches the shapes the ShapeSense repo classifies (circle, triangle, square and similar). The 3D version is kept only as reference, so it does not compete with the repo's scope.

##### Why the candidate list is marked unverified
The dataset names (Kaggle, Hugging Face, Quick, Draw!, TU-Berlin) come from the pasted idea, not from a check of their licenses or contents. The answer marks them unverified, and each license must be checked before merging, as the idea itself says.

##### What the 2D idea adds to the repo
It states the risks that the repo already handles: ambiguous classes (square vs rectangle), domain gap from synthetic to hand-drawn, label-changing augmentations, and leakage across splits. Those map onto the existing stage checks, but the mapping was not re-checked here.

#### Planning the discovery work
I wrote this as a plan file for the agent, not as the report itself. The plan includes your answers, the report structure and the checks, plus the places where the repo already disagrees with the plan. Before relying on a review that makes claims about `search.py`, I checked the search phases, the confirm step and the seed usage in the repo. Two of the review's claims didn't match what I found. The confirm step does retrain seed 0, but line 449 of `train.py` already reads the loss and accuracy once per epoch, not per step.

#### What is already covered in the repo
- **Duplicates and leakage:** perceptual-hash grouping keeps near-duplicates in one split (`configs/pipeline.yaml`, `split.group_by: phash`).
- **Source shift:** held-out sources and two fresh 4,500-image holdouts test unseen data.
- **Class balance:** per-class counts are recorded, and the diamond imbalance was found and fixed (500 Quick, Draw! diamonds removed).
- **Image properties:** all images are resized to 64x64 grayscale, so resolution and colour mode are settled.

#### What is still to do for this project
1. **Label agreement:** have a second person label a sample of the ambiguous pairs (square vs rectangle, circle vs ellipse, diamond vs square) and measure agreement, for example with Cohen's kappa. The repo records the label rules but not an agreement score.
2. **Coverage grid:** check class by source by stroke width, rotation and framing. The repo has per-source counts but not this grid, so empty cells are not yet visible.
3. **Deployment mismatch:** compare the drawing demo's input with the training images. A hand-drawn sketch and a clean render can look very different. The demo has a "not sure" threshold of 0.5 (`demo/logic.py`) that hasn't been tuned on real drawings.
4. **Out-of-scope inputs:** the 10-class model has no reject class. The demo can label any drawing as one of the 10 shapes, so a letter or a scribble still gets a confident answer. This is the open question from the earlier message.
5. **Valid augmentations:** the repo already restricts shear and non-uniform scale for the classes where they would change the label (`configs/taxonomy.yaml`). Confirm that this list still holds for the new transforms.

Ask if you want me to check any of these against the data, starting with the label-agreement check or the demo's threshold.

##### Why the plan was checked against the code first
The plan makes claims about `search.py` and the seed use. Before relying on them, the answer read the code. Two claims did not match: the confirm step does retrain seed 0, and the loss and accuracy are read once per epoch (line 449 of `train.py`), not per step. A plan that repeats a wrong claim would send the agent to fix something that is not broken.

##### Why the open items are phrased as checks
Each item is a gap the repo does not yet measure: label agreement (no kappa score exists), the coverage grid, the demo threshold, the lack of a reject class, and the validity of the augmentations for the new transforms. Stating them as checks keeps them from being mistaken for results.

##### What is unverified
The demo threshold of 0.5 and the "not tuned on real drawings" claim come from `demo/logic.py` as the answer read it. The reject-class gap is a design fact of the 10-class model, not a tested failure.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
