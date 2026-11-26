##  — Data preparation: cleaning, transformation, feature selection

**Run each prompt with both Claude Opus and Gemini 4 Neon, then give each model the other's answer with the critique prompt. Save every exchange in the step's `claude_opus/`, `gemini_4_neon/` and `cross_critique/` folders.**

## Baseline (before any data preparation)

> Train the model on the merged raw images, only resized to 64x64 so they fit into one tensor. No deduplication, no relabeling, no grayscale conversion, no augmentation. Record its macro F1 on the test split. Every step below is compared with this number.

**Why a baseline matters :**
- The baseline is the reference point for every subsequent step. Without it, you can't tell if a cleaning/transformation/feature-selection step helped or hurt.
- **Why only resize to 64x64:** this is the minimum change needed to fit into one tensor. No other processing is applied, so the baseline captures the "raw" performance.
- **Why macro F1:** it's the right metric for a multi-class problem with uneven class support (which this dataset has, per A01).
- **Why test split:** it's the held-out evaluation set, which is the only unbiased measure.

## Cleaning prompt

> We are building an image classifier for 10 shape classes from 4 public sources (QuickDraw drawings, Kaggle printed shapes, Mendeley rendered shapes, GitHub hand-drawn shapes). Here is a summary of the merged raw data:
> <counts per source and class, image sizes and modes, a sample sheet of images>.
> What cleaning steps do you recommend (duplicates, corrupt or blank images, mislabeled images, classes that do not match our definitions)? For each step, say how to detect the problem and how we can check the fix.

**Why this prompt is well-designed :**
- It asks for **both** the problem (duplicates, corrupt, blank, mislabeled, out-of-taxonomy) and **how to detect and fix** each one. This is a complete specification.
- It provides the data summary (counts, sizes, modes, sample sheet), which is necessary for a grounded answer.
- It's specific to the 4 sources and 10 classes, which is the actual dataset.

**What cleaning steps would be recommended (augmented, based on the repo):**
1. **Duplicates:** detect via `md5` (exact) and `phash` (near-duplicate, Hamming <= 2). Fix by deduplicating (keep one per group).
2. **Corrupt or blank images:** detect via `standardize()` rejection gates (`MIN_FG_FRACTION`, `MIN_SHAPE_PX`, `MIN_INK_64`). Fix by rejecting (logged to `rejects.csv`).
3. **Mislabeled images:** detect via manual audit (e.g., QuickDraw `diamond` doodles that are gems, not rhombi). Fix by excluding (`exclude_source_labels: [[quickdraw, diamond]]`).
4. **Classes that don't match definitions:** detect via the taxonomy (`configs/taxonomy.yaml`) and the `LABEL_MAP`. Fix by dropping out-of-taxonomy labels (`kite`, `trapezoid`, `parallelogram`, `Heptagon`, `Nonagon`, `other`).

## Transformation prompt

> After cleaning, the images still differ in size, color mode, background and stroke width. What transformations do you recommend (resizing, grayscale, inversion, normalization, centering, augmentation)? For each one, say why it should help a small CNN and which shape classes it could harm (for example, rotation and square vs. diamond).

**Why this prompt is well-designed :**
- It asks for **both** the transformation and **why it helps / which classes it harms**. This is a complete specification.
- It's specific to the residual differences (size, color mode, background, stroke width), which is the actual state after cleaning.
- It gives a concrete example (rotation and square vs diamond), which shows the kind of reasoning expected.

**What transformations would be recommended (augmented, based on the repo):**
1. **Resizing:** to 64x64, aspect-preserving (letterbox). Helps a small CNN (uniform input size). Harms: none if aspect-preserving.
2. **Grayscale:** convert to single-channel. Helps a small CNN (fewer parameters). Harms: none for shape classification.
3. **Inversion:** normalize polarity (black ink on white vs white ink on black). Helps consistency. Harms: none.
4. **Normalization:** defer to Stage 4 load time (`[0, 1]` float). Helps training stability. Harms: none.
5. **Centering:** aspect-preserving crop + letterbox (`_to_square`, `MARGIN = 0.08`). Helps consistency. Harms: none.
6. **Augmentation:** rotation, translation, uniform scaling are safe. Shear and non-uniform scaling are dangerous (change geometric class, per S07). Harms: square -> diamond under shear, circle -> ellipse under non-uniform scale.

## Feature selection prompt

> Our input is a 64x64 grayscale image fed to a CNN. What does feature selection mean for this setup, and what would you try (input resolution, cropping to the shape's bounding box, removing background, or hand-made features such as HOG or Hu moments with a classical model)? How do we measure whether it helped?

**Why this prompt is well-designed :**
- It asks for **both** what feature selection means for a CNN and **what to try** (resolution, cropping, background removal, hand-made features). This is a complete specification.
- It's specific to the 64x64 grayscale CNN input, which is the actual setup.
- It asks how to measure whether it helped, which is the right question.

**What feature selection would mean (augmented, based on the repo):**
- For a CNN, feature selection is less about hand-picking features and more about **input representation** (resolution, cropping, background) and **architecture** (which layers, how many filters).
- **Input resolution:** 64x64 is a reasonable choice for a small CNN. Higher resolution (e.g., 128x128) might help but costs more compute.
- **Cropping to bounding box:** could help by removing irrelevant background, but risks losing context.
- **Removing background:** already done by `standardize.py` (white background, black ink).
- **Hand-made features (HOG, Hu moments):** could be used with a classical model (SVM, random forest) as a comparison, but not as CNN input.
- **How to measure:** compare macro F1 on the test split with and without each change.

## Critique prompt (cross_critique/)

> Another assistant recommended the following for the <step> step of our pipeline: <paste>. Check it for errors, risks of data leakage between train and test, and steps that would not help. Say which points you agree with, which you reject, and why.

**Why this prompt is well-designed :**
- It asks for **errors, leakage risks, and steps that wouldn't help**. This is a complete critique specification.
- It asks for **agree/reject and why**, which is the right format for a cross-critique.
- It's generic (works for any step), which is good for reuse.

**What the critique would check (augmented, based on the repo):**
- **Errors:** factual mistakes (e.g., wrong formula, wrong class count).
- **Leakage risks:** anything that would let test information leak into train (e.g., fitting a scaler on test data).
- **Steps that wouldn't help:** redundant or harmful steps (e.g., destructive skeletonization, per I06).

## Record after each step

| Step | Baseline | New | Delta | Kept from Claude | Kept from Gemini | Rejected, and why |
|---|---|---|---|---|---|---|
| Cleaning | | | | | | |
| Transformation | | | | | | |
| Feature selection | | | | | | |

**Why this table is well-designed :**
- It captures **baseline, new, delta** (the quantitative result), **kept from each LLM** (the qualitative decision), and **rejected and why** (the audit trail).
- **Why this is good practice:** it makes the decision auditable and reproducible.
- **Why "kept from Claude" and "kept from Gemini" are separate:** it shows which LLM contributed what, which is the whole point of the two-LLM comparison.

## Deeper detail: why this three-step structure matters

### Cleaning -> Transformation -> Feature selection is the right order

| Step | What it does | Why it comes here |
|---|---|---|
| Cleaning | Remove duplicates, corrupt, blank, mislabeled, out-of-taxonomy | Must happen first, so downstream steps see clean data |
| Transformation | Resize, grayscale, invert, normalize, center, augment | Must happen after cleaning, so transformations aren't applied to bad data |
| Feature selection | Choose input representation and architecture | Must happen after transformation, so the input is well-defined |

- **Why this order matters:** each step depends on the previous one. Cleaning must come first, then transformation, then feature selection.
- **Why this is good pipeline design:** it's a clear, logical progression.

### The baseline is the anchor

- **Without a baseline, you can't tell if a step helped.** This is the most important methodological point.
- **Why macro F1:** it's the right metric for uneven class support.
- **Why test split:** it's the only unbiased measure.

### The cross-critique is the two-LLM comparison

- **Each LLM critiques the other.** This is exactly the "one LLM critiques the other" pattern the PDF rubric asks for.
- **Why this matters:** it catches errors and risks that a single LLM might miss.
- **Why the critique prompt is generic:** it works for any step, which makes it reusable.

## Notes on the log

- **This is the template for the data preparation stage.** It defines the prompts, the cross-critique pattern, and the record-keeping table.
- **The baseline is the anchor.** Without it, you can't tell if a step helped.
- **The three-step order (cleaning -> transformation -> feature selection) is logical.** Each step depends on the previous one.
- **The cross-critique is the two-LLM comparison.** Each LLM critiques the other.
- **The record table is auditable.** It captures baseline, new, delta, kept from each LLM, and rejected and why.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.