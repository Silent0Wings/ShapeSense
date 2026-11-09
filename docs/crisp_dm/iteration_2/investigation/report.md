# Why augmentation lost in iteration 1: investigation report

Exploratory work on train and validation data only, 2026-11-09. 16 GPU trainings. No test data was read and nothing in the repository was changed. The test result stands; nothing here may be used to re-tune against it. The raw JSON results are in this folder.

## Verdict

No bug in label handling, loss wiring, polarity or batching. A0's lead is a same-source orientation shortcut. The ±180° rotation range removes a cue that reevald and Quick, Draw! encode in orientation, and on a same-source split that cue is legitimately predictive. Two real defects in the transform also cost roughly 1.5 points.

Validation macro-F1, three seeds: A1 with rotation off 93.15, A1 with ±15° rotation 93.17, A0 91.69, A1 as trained 90.03, B 90.47. So augmentation does help once the rotation range is sane.

## Ranked causes

1. **±180° rotation destroys an orientation cue (about 3 points).** reevald squares are 92% axis-aligned, reevald rectangles 92 to 95%, Quick, Draw! squares 73 to 85%; El Korchi squares are randomly oriented. The stored A0 ensemble on rotated validation falls from 93.65 to 80.5 at 15° and 60.9 at 45°, while A1 stays flat at 89 to 91. Without orientation, square, rectangle and diamond must be told apart by aspect ratio and angle, and that boundary is inconsistent across sources.
2. **The transform makes shapes too small (real defect, about 1 to 1.5 points).** Augmented bounding boxes average 51.0 px against 56.0 to 57.8 px for real images. A1 with scale [0.97, 1.08] reached 91.99 and 92.15 against 90.44 and 90.71.
3. **Budget (about 1.5 to 2 points, by design).** A1 reaches 91% clean-train accuracy against 99.9% for A0, and at 60 epochs reaches 92.11 and 92.38. The budget is frozen by Decision 13.
4. **Thin strokes fragment (real defect, no measured cost).** 69% of augmented Quick, Draw! images gain connected components.
5. **Synthetic stroke is 2 px against 3.1 px for real outlines.** Relevant to B vs A1.

## Ruled out

Label attachment (0 mismatches over 179 real images tracked through `make_batch`), the loss, polarity and scaling, the class-safe rule, and rotated squares being mislabelled as diamonds.

Augmentation hurting unseen-source generalization was also ruled out, and the opposite is true. On held-out Hand-Drawn triangles and rectangles: A0 hold-out 47.0, 64.1 and 49.3% accuracy; A1 hold-out 66.4%; B 71.8%; A1 with rotation off 73.2%.

Undetermined: the noise and blur ablation. Both runs stopped early after a validation swing, which also shows early stopping is fragile at learning rate 0.003.

## Question for the project owner

Whether orientation is a cue the deployed model may use. If shapes can arrive at any angle, ±180° rotation is defensible and the iteration 1 result stands as the honest price. Iteration 2 tunes rotation on validation, so it will favour whatever validation rewards.
