# 3_modeling - Which models to compare for geometric shape recognition
- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-21
- Source: chat pasted by the user, recorded unedited. Two prompts and two replies in one conversation.

## Prompt

> image recognition for geometric shape regcoginition ?=[From the lecture (spoken) "Data science and machine learning here is empirical study. Empirical means we don't know beforehand which of the models can learn better from your data." So "empirically, you are going to choose at least three models", and that "is not a big deal. It is just two lines of code. Plus the import". If you do not know which models exist, give your task and a sample of your data to an LLM, ask it to suggest models, and you may even report that in the project. (transcript, pages 9-10)]

Follow-up prompt:

> my data set is augmented + mixed with synthethic data , and has nnoisy data intetnionaly

## Response

### First reply

For geometric-shape recognition, the best approach depends on whether your shapes are clean/synthetic or noisy/real photos. For a course project, use a feature-based ML pipeline and compare at least three models empirically, exactly as your lecture suggests.

**Recommended setup.** Extract shape features from each cropped object, then train classifiers:

| Model | Why include it | scikit-learn class |
|---|---|---|
| Support Vector Machine | Usually strong on small, well-engineered feature sets | SVC |
| Random Forest | Robust, fast, handles nonlinear feature relationships | RandomForestClassifier |
| K-Nearest Neighbors | Simple baseline; useful for comparison | KNeighborsClassifier |
| MLP neural network | Optional fourth model; learns nonlinear boundaries | MLPClassifier |

MLPClassifier is a supervised multi-layer perceptron and supports multi-class classification through a softmax output. Random Forest and KNN are also standard classification choices.

**Best features for shapes.** Do not feed raw pixels to these models if your images are small and clean. Instead, extract features that describe geometry:
- Number of contour vertices after polygon approximation
- Area, perimeter, and their ratio
- Width, height, aspect ratio
- Circularity: 4πA/P², where A is area and P is perimeter
- Convexity: contour area divided by convex-hull area
- Number of corners detected
- Hu moments, which are shape descriptors invariant to translation, scale, and rotation
- Optional: HOG features if the images are photographs with texture or noise

OpenCV contours are appropriate for shape analysis; thresholding or edge detection before findContours improves accuracy. cv2.approxPolyDP simplifies a contour into fewer vertices, with epsilon controlling approximation accuracy.

**Practical pipeline**

```python
import cv2
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier

def shape_features(mask):
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return np.zeros(8)

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)

    hull = cv2.convexHull(c)
    hull_area = cv2.contourArea(hull)

    epsilon = 0.02 * perimeter
    approx = cv2.approxPolyDP(c, epsilon, True)
    vertices = len(approx)

    x, y, w, h = cv2.boundingRect(c)
    aspect = w / (h + 1e-6)

    circularity = 4 * np.pi * area / (perimeter ** 2 + 1e-6)
    convexity = area / (hull_area + 1e-6)
    extent = area / (w * h + 1e-6)

    return np.array([
        vertices, area, perimeter, aspect,
        circularity, convexity, extent, len(c)
    ], dtype=float)
```

Then compare the models:

```python
models = {
    "SVM": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=10)),
    "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42),
    "KNN": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
    "MLP": make_pipeline(
        StandardScaler(),
        MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
    )
}

for name, model in models.items():
    scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(name, scores.mean(), scores.std())
```

Use cross-validation rather than relying on one train/test split; report mean accuracy and standard deviation. Standardize features for SVM, KNN, and MLP; tree-based models do not require it.

**If shapes are simple.** If your images contain isolated black shapes on a white background (triangles, squares, rectangles, pentagons, circles), OpenCV's contour approximation alone may classify them accurately without machine learning. A common rule is: 3 vertices = triangle, 4 = rectangle/square, 5 = pentagon, and many vertices plus high circularity = circle.

However, for your lecture requirement, still train and compare the three ML models. You can frame it as:

"Although contour-vertex counting is a strong rule-based baseline, we empirically evaluated SVM, Random Forest, and KNN/MLP classifiers on geometric shape features to determine which generalizes best."

**What I'd choose.** For a typical geometric-shape dataset:
- Primary model: SVM with RBF kernel.
- Second model: Random Forest.
- Third model: KNN or MLP.
- Baseline: OpenCV vertex-count rule.

If your images are noisy, rotated, partially occluded, or contain multiple objects, add HOG features and consider a small CNN later. But for a first deliverable, the feature-based SVM/Random Forest/KNN pipeline is simple, explainable, and well aligned with the "try at least three models" instruction.

### Second reply

That makes a CNN an even better choice, not a bad one. Intentional noise and synthetic variation make raw-pixel learning valuable because the CNN can learn robust visual patterns; classical feature-based models may struggle if the noise changes the extracted geometry.

**Why CNN fits your data.** Your augmented, synthetic, noisy dataset likely contains variations in:
- Position and scale
- Rotation
- Blur, Gaussian noise, or salt-and-pepper noise
- Line thickness or incomplete edges
- Background or contrast changes

A CNN learns directly from these pixel patterns, while an SVM/Random Forest using contour features may become unstable if noise breaks contours, creates false vertices, or changes perimeter/area measurements. Data augmentation, including transformations and noise injection, is specifically used to increase diversity and improve robustness.

**Critical evaluation rule.** Apply augmentation and synthetic-noise generation only to the training set. Your validation and test sets should remain clean, or at least use a fixed, reproducible version that is never regenerated after model selection.

This avoids data leakage and gives an honest estimate of generalization. Data augmentation is intended for training; validation/test data should not be altered in the same way.

A good split is:

| Subset | Contents | Purpose |
|---|---|---|
| Training | Original + augmented/synthetic/noisy samples | Model learning |
| Validation | Clean or lightly varied held-out samples | Tune architecture and early stopping |
| Test | Clean, untouched samples | Final reported performance |

Use stratified splitting so every shape class appears proportionally in each subset. Cross-validation is useful for comparing models, but retain a final untouched test set for the result you report.

**Best comparison design.** For the assignment, compare:
1. CNN: raw images.
2. SVM: geometric/HOG features.
3. Random Forest: same features.
4. KNN or MLP: optional fourth model.

Do not compare the CNN trained on augmented noisy data against SVM trained only on clean data. Give every model the same training subset and evaluate all of them on the same held-out test set.

For the CNN, evaluate both:
- Clean test accuracy: "How well does it recognize normal shapes?"
- Noisy test accuracy: "How robust is it under noise?"

That second result is especially useful because your project intentionally includes noise.

**Report wording.** "A CNN was selected because the dataset contains synthetic, augmented, and intentionally noisy geometric-shape images. CNNs operate directly on image pixels and can learn robust spatial features under such variation. To satisfy the requirement for empirical model comparison, the CNN was compared with classical classifiers using identical training and held-out test data."

**Watch for overfitting.** Even with augmentation, check whether validation loss starts rising while training loss keeps decreasing. If so, reduce model capacity, add dropout, use early stopping, or reduce augmentation intensity. Augmentation and dropout are standard methods for reducing overfitting in small or limited image datasets.

In short: your dataset design supports the CNN choice very well. Just make the comparison fair and report clean-test, noisy-test, and confusion-matrix results.

Suggested follow-ups shown under the reply:
- Simulator: test how synthetic data ratios and noise levels affect CNN shape-recognition robustness under occlusion
- Audit your geometric shape dataset: synthetic data ratios, noise injection levels, and validation leak risks
- How should I split the noisy data
- Show me how to check for data leakage
- How to evaluate synthetic data quality

## Validation

Checked against what the project already does:
- **At least three models.** The project compares a CNN with two classical baselines trained in Stage 4 (`src/stage4_train/baselines.py`): logistic regression on raw pixels (validation macro F1 77.7) and a linear SVM on HOG features (82.5), from `results/phase2_snapshot/baselines.json`. The CNN arms score far higher on test (A0 94.6, A2 95.8 macro F1, five seeds). So the CNN, logistic regression and SVM already make three models.
- **Augmentation and synthetic data on the training side only.** Matches the project: augmentation and the synthetic generator feed training batches only, and the validation and test splits are fixed manifests in `configs/splits/`.
- **Clean and noisy test results.** Matches iteration 3: the pre-registered test compares A2 with A0 on damaged copies of the sealed `fresh_holdout_2`, beside the clean result.
- **Hand-made geometric features.** The project uses HOG, not contour features. Hu moments are listed as an open experiment (FS4 in `prompts/2_data_preparation/feature_selection/inferred_prompts.md`) and have not been run.
- **Differs from the project:** the reply suggests stratified random splitting. The project splits by near-duplicate group (pHash), so near-identical images never sit on both sides of a split; plain stratified splitting would leak them.
- **Not checked:** Random Forest, KNN, MLP and the contour-vertex rule were not run in this project.

## Our decision

Keep the CNN as the main model and keep logistic regression and the HOG SVM as the comparison models, which meets the lecture's "at least three models". Keep the group-aware split rather than plain stratified splitting. A contour or Hu-moment model stays an optional experiment.

## Measured effect

None. The reply confirms the existing design; no change was made.
