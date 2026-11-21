# 3_modeling - Why the CNN labels an image with two triangles as "triangle"
- LLM: Gemini 4 Neon (assumed: the paste does not name the model; it was recorded in the same request series as file 21)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-21
- Source: chat pasted by the user, recorded unedited. Three prompts and three replies in one conversation.

## Prompt

> why is my cnn detecting non geometric shaoes such as 2 triangles in 1 iamge as triagnle but it was only trained on 1 triangle image >

Follow-up prompts:

> is this a limitation ? that is acceptable ?

> so nothing woul have fixed that aprt no mattree how much snthethic or augemtnation i add ?

## Response

### First reply

Your CNN is behaving normally: it was trained to output the single most likely label, not to detect and count instances. If an image contains two triangles, it still contains many triangle-like features (diagonal edges, corners, straight segments), so a binary/one-class "triangle" classifier can legitimately predict triangle. CNNs learn local feature patterns, not a human-style definition such as "exactly one closed three-sided polygon."

**Why it happens**
- Classification vs. detection: A classifier answers "is this image triangle-like?" It does not answer "how many triangles are in this image?" Two triangles therefore remain a positive example of the class.
- Translation invariance: Convolutional filters scan the whole image, so a triangle feature can be detected anywhere; having it twice only strengthens the evidence.
- Overgeneralization from one training image: With only one triangle image, the model has likely memorized that image's edge orientation, scale, position, line thickness, and background. It may then fire on anything with similar diagonal edges or corners.
- No negative examples: If every training image was labeled triangle, the network may have learned a weak "triangle-ishness" score rather than a precise geometric rule. CNNs can learn quite different, non-human features depending on the data and loss.
- CNNs are not inherently shape-biased: Their behavior depends heavily on training data, augmentation, initialization, and architecture; a model can rely on texture, local edges, or other cues rather than global shape.

**What "trained on 1 triangle image" means.** One image is not enough to teach the concept triangle. It teaches the model one particular pixel pattern, perhaps with small augmentations. It cannot reliably distinguish:

| Input | Desired behavior | Likely classifier behavior |
|---|---|---|
| One triangle | triangle | triangle |
| Two triangles | two triangles / count = 2 | triangle |
| A triangle-like non-geometric shape | not triangle | Often triangle |
| A rotated/scaled triangle | triangle | May work only if augmented |
| A noisy or partial triangle | triangle or not triangle | Unpredictable |

**How to fix it.** Choose the task you actually want:

1. Single-shape classification. If the goal is "does this image contain at least one triangle?", current behavior is not necessarily wrong.
   - Train with both triangle and non-triangle images.
   - Include non-triangles with lines, corners, arrows, circles, squares, and partial shapes.
   - Use many varied triangle examples: different sizes, rotations, positions, thicknesses, colors, backgrounds, and numbers of triangles.
   - Apply augmentation: random rotation, scaling, translation, brightness/contrast changes, and small perspective transforms.
2. Count triangles. Use an object-detection or segmentation model, not a plain image classifier.
   - Object detection: YOLO, Faster R-CNN, or DETR-style models return boxes/classes, so two triangles yield two detections.
   - Instance segmentation: Mask R-CNN or similar returns a mask per triangle; count connected components or detected instances.
   - Classical CV first: For clean synthetic images, use edge detection plus contour analysis (for example, OpenCV findContours + polygon approximation). This is often more reliable and interpretable than a CNN for exact geometry.
3. Enforce geometry. If the shapes are clean line drawings, do not rely solely on a CNN:
   - Binarize the image.
   - Detect contours or line segments.
   - Approximate each contour with a polygon.
   - Count vertices/sides; a closed 3-vertex polygon is a triangle.
   - Count qualifying contours.

   This directly answers "how many triangles?" and avoids the classifier's ambiguity.

**Quick diagnostic.** Run these checks:
- Feed an image with zero triangles but diagonal lines/corners. If it predicts triangle, the model learned weak local cues.
- Feed the same triangle shifted, rotated, scaled, or on a different background. If predictions change, it memorized placement/appearance rather than shape.
- Inspect the softmax probability. triangle: 0.51 versus triangle: 0.99 means very different confidence, even if the argmax label is the same.
- Add a none / background class and retrain. A one-class setup has no meaningful way to say "this is not a triangle."

In short: your model is detecting triangle-like evidence, not counting closed triangular objects. For counting, switch to detection/segmentation or contour-based geometry; for robust classification, add diverse positive and negative examples.

### Second reply

Yes, it is a limitation of using image classification for a task that needs object counting. It is acceptable only if your intended output is "does this image contain a triangle?"; it is not acceptable if you need "how many triangles are in this image?"

**Why it is expected.** A standard CNN classifier produces one prediction for the entire image, such as triangle or not triangle. It is not designed to locate individual objects or return a variable count, so two triangles can correctly map to the single class label triangle.

| Task | Output | Two triangles |
|---|---|---|
| Image classification | One image-level label | triangle |
| Object detection | A bounding box + class per object | Two boxes, count = 2 |
| Instance segmentation | A pixel mask per object | Two masks, count = 2 |
| Semantic segmentation | Class per pixel | Triangle pixels, but not separate instances |

Object detection explicitly returns one or more boxes and labels, while instance segmentation separates each individual object instance; both are appropriate when counting matters.

**When it is acceptable.** It is acceptable if your application only needs presence detection:
- "Is there a triangle somewhere in this image?"
- "Is this image triangle-like?"
- "Does this drawing contain any triangular region?"

In that framing, predicting triangle for two triangles is not a bug; it is the correct classification output.

**When it is not acceptable.** It is a real limitation if you need any of these:
- Exact count: "There are 2 triangles."
- Location: "One triangle is top-left, one is bottom-right."
- Separation: distinguish two adjacent or overlapping triangles.
- Rejection: say "this has diagonal lines but is not a triangle."
- Geometric validation: verify exactly three straight sides and a closed contour.

A classifier cannot reliably provide those outputs because its architecture and training objective do not represent individual instances.

**Best fix for your case.** For synthetic/clean geometric shapes, use contour-based geometry first:

```python
contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

triangle_count = 0
for contour in contours:
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    if len(approx) == 3 and cv2.isContourConvex(approx):
        triangle_count += 1
```

This can count separate triangles directly and is more predictable than a CNN for exact shapes.

If images are noisy, hand-drawn, rotated, occluded, or contain many shape types, train an object detector such as Faster R-CNN or YOLO. It returns per-object boxes and confidence scores, so you can count detections after confidence and overlap filtering.

**Practical recommendation**
- Need only "triangle present?" Keep the classifier, but add non-triangle negatives and diverse triangle images.
- Need "how many?" Use contour analysis for clean synthetic shapes, or object detection/instance segmentation for real-world images.
- Need both presence and count? Use detection; derive count as len(valid_detections).
- Need exact outlines? Use instance segmentation or contour extraction.

So: your observation is a task-model mismatch, not necessarily a training failure. A single-label CNN is doing what it was designed to do; you need a different output representation if counting is part of the requirement.

### Third reply

No, more augmentation or synthetic data alone would not fix the counting part if your labels remained triangle for every image. But it can fix it if you change the labels/task: generate multi-triangle images and supervise the model with the count, or switch to detection/segmentation.

**The distinction.** Augmentation changes the appearance of examples; it does not change the supervisory signal. If both one-triangle and two-triangle images are labeled triangle, the model is being correctly trained to answer "is there triangle evidence?" rather than "how many triangles?"

| Setup | Can more synthetic data fix it? |
|---|---|
| One-triangle images only, label triangle | No |
| One- and two-triangle images, both labeled triangle | No |
| One- and two-triangle images, labels 1 and 2 | Yes, for count classification |
| Images with bounding-box labels for every triangle | Yes, for detection/counting |
| Images with a separate mask per triangle | Yes, for instance segmentation/counting |

Image classification assigns a label to the whole image and does not represent where objects are or how many instances exist; detection gives each object its own box, enabling a count.

**What would fix it**

Option A: Count classification. Keep a CNN, but make the output a count:

```text
0 = no triangle
1 = one triangle
2 = two triangles
3+ = three or more triangles
```

Generate synthetic images with known counts and label them accordingly. This can work well if triangles are usually separate and the maximum count is small.

Option B: Object detection. Label each triangle with a bounding box. The model returns one detection per triangle, and you compute:

```python
count = len(valid_detections)
```

This is the standard approach when you need both count and approximate location.

Option C: Contour geometry. For clean synthetic shapes, skip learned counting:

```python
count = sum(
    len(cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)) == 3
    for c in contours
)
```

This is often the most reliable and cheapest solution for exact line drawings.

**Important caveat.** Even with count labels, augmentation must preserve the count. For example, random cropping can cut a triangle out of frame; random erasing, heavy blur, or aggressive perspective transforms can make a triangle unrecognizable. If the augmented image no longer contains two visible triangles but keeps the label 2, the labels become wrong and training will suffer.

So the precise answer is:
- No, unlimited augmentation cannot teach a model a concept it was never labeled to learn.
- Yes, synthetic data can solve it if you generate varied 0/1/2/3-triangle scenes and provide count, box, or instance-mask supervision.
- Best choice: contour analysis for clean synthetic shapes; detection or count-classification if you need robustness to varied/noisy inputs.

Suggested follow-ups shown under the reply:
- how do I structure count classification labels
- what architecture changes are needed for count classification
- how to transition from classification to object detection
- can contour analysis handle overlapping shapes
- what if my shapes vary wildly in size and position

## Validation

Checked against the project:
- **The behaviour is expected.** The model is a single-label classifier over 10 classes (`configs/taxonomy.yaml`), trained on images that each show one shape. An image with two triangles is outside the training distribution, and the model still has to pick one of the 10 labels, so "triangle" is the natural answer.
- **The prompt's "trained on 1 triangle image" means one triangle per image**, not a single training image. The reply's points about memorising a single image do not apply; the project trains on thousands of triangle images from several sources.
- **There is no reject class.** `docs/phase1_report_plan.md` records an 11th `other` class as a recommendation awaiting approval; the taxonomy was not changed.
- **The only guard is low confidence.** The demo shows "not sure" when the top probability is below 0.5 (`NOT_SURE_THRESHOLD` in `demo/logic.py`), and the studio marks `not_sure` the same way (`studio/inference/predict.py`). A confident wrong answer on an out-of-scope drawing is not caught.
- **Not run in this project:** count labels, object detection, instance segmentation and contour counting.

## Our decision

Record it as a known limitation: the model answers "which one of the 10 shapes is this?" for a drawing of one shape. It does not count shapes and cannot reject drawings that are not one of the 10 classes. More augmentation or synthetic data would not change that, because the labels never describe counts or "none of these". Counting or rejection would need a different task: count labels, a detector, or an `other` class.

## Measured effect

None. No change was made; the limitation should be stated in the report and slides.
