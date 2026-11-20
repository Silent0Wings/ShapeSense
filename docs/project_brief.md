# Project brief (recorded from the original idea)

> Recorded as a reference. The project in this repo is the 2D version (Part B). The 3D version (Part A) is kept for context only and is not part of the work here.

## Part A: 3D shape classifier (not this project)

**Project:** Build a unified 3D shape classification model. Merge several public shape datasets into one standardized corpus, expand it with augmentation and synthetic data, then train a classifier on it.

**Goal:** Train a single model that classifies shapes (for example chair, table, airplane) and generalizes across data sources, not just within one benchmark.

**Pipeline**
1. **Collect datasets.** Sources such as ModelNet40, ShapeNet, ScanObjectNN and Objaverse. Check each license first, since some are non-commercial or research-only.
2. **Standardize format.** Convert everything to one representation, such as point clouds of N points (1024 or 2048) or watertight meshes. Normalize scale, center and orientation.
3. **Unify labels.** Map each dataset's class names to one shared taxonomy. Drop or merge classes that don't align, and record the mapping in a file.
4. **Deduplicate and split.** Remove near-duplicate shapes across datasets. Split by object, never by augmented copy. Keep one source dataset held out for cross-domain testing.
5. **Augment.** Random rotation, scaling, jitter, point dropout, anisotropic stretching, partial crops or occlusion.
6. **Synthesize.** Parametric primitives and procedural variants. Simulated scans with noise and missing regions. Optionally generative models. Tag all synthetic samples.
7. **Train.** Baseline PointNet++ or DGCNN, then Point Transformer or a multi-view CNN. Handle class imbalance with weighted loss or resampling.
8. **Evaluate.** Accuracy and per-class F1. Ablation: real only, real plus augmented, real plus augmented plus synthetic. Test on the held-out dataset and on noisy data.

**Deliverables:** reproducible conversion and merge scripts; label taxonomy file and dataset card with licenses; trained weights and evaluation report; simple inference demo (script or viewer).

**Main risks:** label mismatch between datasets; domain gap between clean CAD models and real scans; leakage from duplicates or augmented copies across splits; synthetic data that doesn't resemble real shapes and hurts performance.

## Part B: 2D shape classifier (this project)

**Project:** Build a unified 2D shape classifier. Merge several public shape datasets into one standardized corpus, expand it with augmentation and procedurally generated synthetic data, then train a model to classify shapes such as circle, triangle, square, pentagon, star and ellipse.

**Goal:** Train one model that recognizes 2D shapes across clean digital renders, hand-drawn sketches and photos, so it generalizes beyond any single dataset.

**Pipeline**
1. **Collect datasets.** Geometric-shape image sets on Kaggle and Hugging Face, plus sketch sets such as Quick, Draw! and TU-Berlin. Check each license before merging.
2. **Standardize format.** One size (for example 64x64 or 128x128), grayscale or binary, consistent background, centered and scale-normalized shapes. Rasterize stroke data first.
3. **Unify labels.** Map class names to one taxonomy (for example "rectangle" vs "square", "oval" vs "ellipse"). Store the mapping in a file and decide how to treat ambiguous classes.
4. **Deduplicate and split.** Remove near-duplicates with perceptual hashing. Split by source image before augmenting. Hold out one dataset for cross-domain testing.
5. **Augment.** Rotation, scale, translation, shear, flips, stroke-width changes, blur, noise, elastic distortion, random backgrounds. Augmentations must not change the class (heavy shear can turn a square into a parallelogram).
6. **Synthesize.** Procedural shapes with code (Pillow, OpenCV or SVG): random size, rotation, color, line style, fill and wobble to mimic hand drawing. Clutter, overlaps and texture backgrounds. Tag synthetic samples in the metadata.
7. **Train.** Small CNN baseline, then ResNet or MobileNet fine-tuning, optionally a small ViT. Class-weighted loss if classes are imbalanced.
8. **Evaluate.** Accuracy, per-class F1 and a confusion matrix. Ablation: real only, real plus augmented, real plus augmented plus synthetic. Test on the held-out dataset and on noisy or hand-drawn inputs.

**Deliverables:** merge and preprocessing scripts; label mapping file and dataset card with licenses; trained weights and evaluation report; small demo (for example a drawing canvas that predicts the shape live).

**Main risks:** ambiguous classes (square vs rectangle, circle vs ellipse); domain gap between clean synthetic shapes and messy hand-drawn ones; augmentations that alter the true label; leakage from duplicates across splits.
