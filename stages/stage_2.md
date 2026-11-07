# Stage 2 — Augmentation pipeline

> Owner brief. Everything here is about Stage 2 only. The full project
> plan is `../implementation.md`; shared rules live there under
> *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 2` · **Code folder:** `src/stage2_augment/`
- **Depends on:** format spec for development; Stage 1 train manifest for
  final QA · **Parallel with:** Stage 3 · **Starts:** day 1
- **Blocks:** Stage 4 arms A1 and B
- **Effort:** ~1 day

## Focus

Build **one function**, `transform(img, label, rng)`, that randomly
varies a training image **without ever changing what shape it is**.
Stage 4 calls it on the fly for every training batch of arms A1 and B.
The hard part is not the transforms — it is making sure none of them
turns a square into a rectangle or a near-round ellipse into a circle.

## Goals

1. Implement the five augmentations from the Phase 1 report: rotation,
   scale, shear, noise, blur.
2. Disable shear and non-uniform scaling for circle, ellipse, square,
   rectangle and diamond — **through config, not `if` statements
   scattered in code**. The list already exists as
   `configs/taxonomy.yaml#no_shear_no_nonuniform_scale`; read it, do not
   retype it.
3. Prove visually and by test that labels survive augmentation.

## Out of scope

- Generating new shapes (Stage 3).
- Choosing which images get augmented or how batches are mixed
  (Stage 4's loader decides).
- Touching validation or test images — augmentation is train-only.

## Inputs

| Input | Where |
|---|---|
| Train manifest | `common.load_split("train")` |
| Augmentation ranges | `configs/pipeline.yaml#augment` |
| Per-class disable list, class names and indices | `configs/taxonomy.yaml` |

## Requirements

**Must**
- R1. Public signature exactly
  `transform(img: uint8[64,64], label: int, rng) -> uint8[64,64]`.
- R2. Output is 64×64 single-channel uint8, black outline on white.
- R3. The label never changes (the function does not return a label).
- R4. Shear and non-uniform scale are off for classes listed in
  `configs/taxonomy.yaml#no_shear_no_nonuniform_scale` — circle, ellipse,
  square, rectangle, diamond.
- R5. All randomness comes from the `rng` argument, so a seed reproduces
  the exact augmented image. Note that the committed
  `src/common/interfaces.py` declares `TransformFn` **without** `rng`;
  Stage 0 fixes the protocol, and your signature is the one above.
- R6. Nothing is written to disk during training (on-the-fly only).
- R7. No import of `stage3_synth` or any other stage (import-linter enforces).

**Should**
- Keep the shape inside the frame after rotation/scale (no clipped
  corners that hide a vertex).
- Noise and blur must not erase thin 2-px outlines.

## Deliverables

- `stage2_augment.transform` (public), plus the config it reads.
- `artifacts/stage2/qa/qa_sheet.png` — 10 augmented samples per class.
- `artifacts/stage2/status.json` — rules in force, QA verdict.

## Done when

- [ ] QA sheet shows zero label-changing artifacts.
- [ ] Disable rules are read from `configs/taxonomy.yaml` (changing the
      list changes behaviour with no code edit).
- [ ] `transform` contract tests pass.

## Interfaces you provide

`transform` is one of only two cross-stage imports allowed in the whole
project (`stage4_train → stage2_augment.transform`). Freeze its signature at
the Stage 1/2/3 hand-off and don't change it afterwards.

## Pitfalls

- **Shear on a square** produces a parallelogram — no longer any of the
  10 classes, or worse, a diamond.
- **Non-uniform scale on a circle** produces an ellipse — a silent
  label flip.
- **Rotating a square by 45°** is fine: it is still a square (the
  taxonomy says "any rotation"). Don't over-restrict.
- **Interpolation grey** — rotation creates grey pixels; re-threshold or
  the image no longer looks like the black-on-white standard.
- **Using the global `random` module** breaks reproducibility (R5).

## Glossary

- **Data augmentation**: making new training examples by randomly
  changing existing ones. Example: rotating a triangle by 17°.
- **On-the-fly**: applied when the batch is built, never saved. Example:
  epoch 1 and epoch 2 see different rotations of the same image.
- **Label-preserving transform**: a change after which the true class is
  still the same. Example: rotation for every class in this taxonomy.
- **Affine transform**: rotation, scaling, shear and translation, the
  transforms that keep straight lines straight. Example:
  `A.Affine(rotate=(-30, 30))`.
- **Shear**: slanting an image so right angles stop being right. Example:
  a square sheared by 15° becomes a parallelogram.
- **Non-uniform scaling**: stretching x and y by different amounts.
  Example: a circle scaled 1.3× wide becomes an ellipse.
- **Seeded RNG**: a random generator started from a known number, so
  results repeat. Example: `rng = np.random.default_rng(42)`.
- **QA sheet**: a grid image of samples for a human to inspect. Example:
  10 columns × 10 class rows of augmented images.

## Missions

### M1 Safe or label-flipping? (recognition)
Prompt: for each pair, say whether the transform is safe and why.

1. square + rotate 45°
2. circle + scale x=1.0, y=1.3
3. hexagon + shear 10°
4. rectangle + shear 10°
5. star + Gaussian blur σ=0.5

Expected outcome: 1 safe (squares allow any rotation). 2 flips to
ellipse. 3 safe-ish (hexagon stays 6 vertices; not on the disable list).
4 unsafe — right angles break, may read as diamond/parallelogram.
5 safe if the outline survives.

### M2 Config-driven per-class rules (application)
Prompt: build two pipelines and pick one by class, using only the
config to decide.

```python
import albumentations as A, numpy as np

CFG = load_config("configs/pipeline.yaml")["augment"]   # {"rotate": 30, ...}
DISABLED = load_config("configs/taxonomy.yaml")["no_shear_no_nonuniform_scale"]

full = A.Compose([
    A.Affine(rotate=(-CFG["rotate"], CFG["rotate"]),
             scale={"x": (0.85, 1.15), "y": (0.85, 1.15)},
             shear=(-CFG["shear"], CFG["shear"]), fill=255, p=1.0),
    A.GaussNoise(p=0.3), A.GaussianBlur(blur_limit=(3, 3), p=0.3),
])
safe = ...   # TODO: same, but uniform scale and no shear

def transform(img, label, rng):
    ...       # TODO: choose pipeline from DISABLED; seed from rng
```
Expected outcome: for a circle, 1,000 calls never change the aspect
ratio of the bounding box by more than ~2%; for a hexagon, shear is
visible. Calling with the same seed twice returns identical arrays.

### M3 Prove it: contract test + QA sheet (synthesis)
Prompt: write the test that would catch a label flip, and the QA sheet
that lets a human confirm it.

```python
def fitted_ratio(img):
    """Long/short side of the min-area rectangle around the ink.

    NOT the bounding box: rotation is legal for every class, and a
    rectangle rotated 45 degrees has a near-square bounding box. A
    bbox-based assertion fails on correct behaviour.
    """
    ...

def test_transform_keeps_shape_class():
    for label in DISABLED_CLASSES:
        img = render_reference(label)            # a clean sample
        for seed in range(200):
            out = transform(img, label, np.random.default_rng(seed))
            assert out.shape == (64, 64) and out.dtype == np.uint8
            assert fitted_ratio(out) == pytest.approx(fitted_ratio(img), rel=0.05)
```
Expected outcome: the test passes, **including for rotated rectangles
and ellipses**; temporarily remove `square` from the disable list and it
fails. `qa_sheet.png` shows 10 rows × 10 samples and `status.json`
records `qa: passed`.

When you finish M3, run `quiz-topic` on "class-safe augmentation".
