# 2_data_preparation/transformation - Stage 2 and 3 plans: augmentation and synthetic generator

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-07
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner briefs for Stage 2 (augmentation) and Stage 3 (synthetic generator) and one implementation plan for each.

## Response (saved output, verbatim)

### `stages/stage_2.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
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
````

### `stages/stage_3.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 3 — Synthetic generator

> Owner brief. Everything here is about Stage 3 only. The full project
> plan is `../implementation.md`; shared rules live there under
> *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 3` · **Code folder:** `src/stage3_synth/`
- **Depends on:** the format spec only — nothing from Stage 1 ·
  **Parallel with:** Stage 2
- **Blocks:** Stage 4 arm B
- **Effort:** ~1.5 days

## Focus

Build **one function**, `generate(label, rng)`, that draws a brand-new
shape image of the requested class from scratch, in exactly the same
64×64 black-outline-on-white format as the real data. Stage 4 uses it
to fill ~30% of every training batch for arm B. The generator is what
the whole project is testing: if B doesn't beat A1, the generator adds
little.

## Goals

1. Render all 10 classes with randomized size, position, rotation and
   stroke width.
2. Never produce an ambiguous image — enforce explicit margins between
   the confusable pairs.
3. Be fast enough to supply 30% of a batch without slowing training.
4. Log the parameter ranges so the report can state them.

## Out of scope

- Augmenting real images (Stage 2). Augmentation is applied *after*
  generation by Stage 4, not inside `generate`.
- Saving images to disk — synthetic data is never stored.
- Deciding the 70/30 mix (Stage 4's loader, from `configs/pipeline.yaml`).

## Inputs

| Input | Where |
|---|---|
| 10-class taxonomy, definitions and ambiguity margins | `configs/taxonomy.yaml`, report Table 2 (`tab:labels`) |
| Format spec: 64×64, single channel, black outline on white, centred | report section C |
| Parameter ranges | `configs/pipeline.yaml#synth` |

## Requirements

**Must**
- R1. Public signature exactly `generate(label: int, rng) -> uint8[64,64]`.
- R2. Output matches the standardized format (64×64, uint8, white
  background, ~2-px black outline, shape centred).
- R3. Margins: ellipse axis ratio ≥ 1.2; rectangle side ratio ≥ 1.2;
  diamond interior angles at least 10° off 90°; circle axes equal;
  square sides equal with right angles. These values are already in
  `configs/taxonomy.yaml#ambiguity_margins` — read them.
- R4. All randomness from `rng` (reproducible per seed).
- R5. Nothing written to disk during training.
- R6. No import of `stage2_augment` or any other stage.
- R7. Margins come from `configs/taxonomy.yaml`, parameter ranges from
  `configs/pipeline.yaml#synth`. No literals in code.
- R8. Hit an **absolute** throughput target: **≥ 2,000 images/s
  single-threaded** on the training machine. At batch 256 and a 30%
  share that is 77 images in under 40 ms, comfortably inside one CPU
  training step. Stage 4's D3 loader benchmark re-checks this against
  the real step time — but you do not wait for it, because Stage 4's B
  arm waits for you.

**Should**
- Rotation: any angle for every class (the taxonomy allows it).
- Star: alternate outer/inner radius with a clear ratio (e.g. inner ≤
  0.6 × outer) so it never looks like a decagon.

## Deliverables

- `stage3_synth.generate` (public) and its config.
- `artifacts/stage3/param_ranges.json` — actual min/max used per parameter.
- `artifacts/stage3/qa/qa_sheet.png` — 10 samples per class.
- `artifacts/stage3/status.json` — QA verdict, throughput, margins in force.

## Done when

- [ ] QA sheet passes (no ambiguous or off-class renders).
- [ ] Margin checks are enforced in code and covered by contract tests.
- [ ] Measured throughput ≥ 2,000 images/s single-threaded.
- [ ] Parameter ranges are logged.

## Interfaces you provide

`generate` is the second (and last) cross-stage import allowed
(`stage4_train → stage3_synth.generate`). Freeze the signature at the Stage
1/2/3 hand-off.

## Pitfalls

- **Ellipse with ratio 1.05** — looks like a circle; teaches the model
  the wrong boundary.
- **Diamond with 88° angles** — that's basically a square.
- **Filled shapes** — real data is outline-only; a fill becomes a
  "this is synthetic" shortcut.
- **Anti-aliasing grey** — threshold to pure black/white like the real
  pipeline, or the model learns "grey edges = synthetic".
- **Always centred, same size** — real sketches are messier; too-clean
  renders widen the domain gap.

## Glossary

- **Synthetic data**: training images produced by a program rather than
  collected. Example: a hexagon drawn by `ImageDraw.polygon`.
- **Procedural rendering**: drawing from parameters (centre, radius,
  angle) each time. Example: hexagon vertices at
  `(cx + r·cos(θ + k·60°), cy + r·sin(θ + k·60°))`.
- **Parameter randomization**: sampling parameters from ranges so no two
  renders are equal. Example: `r = rng.uniform(14, 28)`.
- **Ambiguity margin**: a forced gap between confusable classes.
  Example: an ellipse must have axis ratio ≥ 1.2.
- **Domain gap**: the visible difference between synthetic and real
  images. Example: perfectly straight synthetic lines vs wobbly sketches.
- **Throughput**: how many images the generator makes per second.
  Example: 5,000 img/s produces a batch's 77 synthetic images in 15 ms,
  well inside one CPU training step.
- **Pillow ImageDraw**: Python drawing API for lines, ellipses and
  polygons on an image. Example: `d.ellipse(box, outline=0, width=2)`.

## Missions

### M1 Which renders break the margins? (recognition)
Prompt: each line is a set of render parameters. Which ones violate a
Stage 3 requirement?

1. ellipse, axes 20 × 18
2. rectangle, sides 30 × 20
3. diamond, angles 85° / 95°
4. square, filled black
5. star, outer 24, inner 20

Expected outcome: 1 violates R3 (ratio 1.11 < 1.2). 2 is fine (1.5).
3 violates R3 (too close to 90°). 4 violates R2 (filled, not outline).
5 violates the star "should" (inner/outer 0.83 — reads as a decagon).

### M2 Render one class with its margin (application)
Prompt: implement the ellipse renderer so the margin can never be
broken, whatever the RNG returns.

```python
from PIL import Image, ImageDraw
import numpy as np

def render_ellipse(rng, cfg, margins):
    img = Image.new("L", (64, 64), 255)
    a = rng.uniform(cfg["min_axis"], cfg["max_axis"])
    ratio = ...                 # TODO: sample in [margins["ellipse_min_axis_ratio"], cfg["ellipse_max_ratio"]]
    b = a / ratio
    angle = rng.uniform(0, 180)
    # TODO: draw on a larger canvas, rotate, crop/resize to 64x64, threshold to 0/255
    return np.asarray(img, dtype=np.uint8)
```
Expected outcome: over 1,000 seeds, the fitted axis ratio of every
output is ≥ 1.2 (within 0.02 measuring error); pixel values are only 0
and 255.

### M3 Full generator + proof (synthesis)
Prompt: route all 10 labels through `generate`, write a contract test
per margin, and measure throughput.

```python
RENDERERS = {0: render_circle, 1: render_ellipse, 2: render_triangle, ...}

def generate(label, rng):
    return RENDERERS[label](rng, CFG, MARGINS)

def test_margins():
    for seed in range(300):
        rng = np.random.default_rng(seed)
        assert axis_ratio(generate(1, rng)) >= 1.2      # ellipse
        assert side_ratio(generate(4, rng)) >= 1.2      # rectangle
        assert abs(min_angle(generate(9, rng)) - 90) >= 10   # diamond
```
Expected outcome: all margin tests pass; `status.json` records
throughput (e.g. `"throughput_img_s": 6200`, against the 2,000 target),
`param_ranges.json` is written, and the QA sheet shows 10 clean rows.

When you finish M3, run `quiz-topic` on "synthetic shape generation".
````

### `24_s2_transform.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E24 evidence line

# Plan 24: S2 class-safe transform + QA

**Stage:** `stages/stage_2.md` R1–R7, Should 1–2, Done-when D1–D3, Missions M1–M3 · **Plan refs:** `implementation.md` § Stage 2; Decision 11
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E24) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Arms A1/B need label-preserving on-the-fly augmentation.

## 2. Root Cause & Investigation
`src/stage2_augment/run.py` is a stub; the protocol gains `rng` in E12.

## 3. Architecture & Modular Design Strategy
Pure NumPy/SciPy: `transform(img, label, rng)` builds an affine (rotation, uniform scale and — only for labels not in `no_shear_no_nonuniform_scale` — shear and non-uniform scale), fits the result inside the frame, warps, **re-thresholds to {0,255}**, applies noise/blur that keep 2-px outlines, returns uint8 64×64. `build_transform(config)`; module-level `transform` uses the committed config. Registers `"augment"`. QA sheet 10 × 10.

## 4. Proposed Changes by File
- `src/stage2_augment/transform.py`, `qa.py`, `run.py`, `__init__.py`.
- `tests/contracts/test_transform.py`, `tests/stage2/test_transform_internals.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: shape/dtype/binary, determinism, all labels; `::test_disabled_classes_keep_fitted_ratio` (min-area-rectangle ratio, 200 seeds, rotated rectangles); `::test_enabled_class_can_shear`; `::test_disable_list_read_from_config`; `::test_thin_outline_survives`; `::test_shape_stays_in_frame`.
- **Figure review**: open `qa_sheet.png`.
- **Break verification**: ignore the disable list → ratio test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Rotating a square 45° is legal; bbox checks would wrongly fail — use a min-area rectangle.
````

### `25_s3_generator.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E25 evidence line

# Plan 25: S3 generate + margins + QA + throughput

**Stage:** `stages/stage_3.md` R1–R8, Should 1–2, Done-when D1–D4, Missions M1–M3 · **Plan refs:** `implementation.md` § Stage 3; Decision 11
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E25) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Arm B needs a procedural renderer in the standardized format whose ambiguous pairs can never be confused.

## 2. Root Cause & Investigation
`src/stage3_synth/run.py` is a stub.

## 3. Architecture & Modular Design Strategy
Pure geometry builders per class parameterized from `config.synth` and `taxonomy.ambiguity_margins`; Pillow `ImageDraw` outline (no fill), any rotation, centre jitter, binary output. `param_ranges.json` logs realized min/max. Throughput measured single-threaded. Registers `"synthetic"`.

## 4. Proposed Changes by File
- `src/stage3_synth/shapes.py`, `render.py`, `generate.py`, `qa.py`, `run.py`, `__init__.py`.
- `tests/contracts/test_generate.py`, `tests/stage3/test_shapes.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: contract shape/dtype/binary, determinism, all labels; margin tests for ellipse, rectangle, diamond (1,000 seeds); star inner ratio; outline not filled; margins read from taxonomy.
- **Figure review**: open `qa_sheet.png`.
- **Break verification**: sample ellipse ratio from 1.0 → margin test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Margins enforced on geometric parameters; measured checks allow 0.02 slack at 64 px.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each plan's status line records 'verified in tree' (todo E24, E25).

## Our decision

Augmentation is class-safe and applied after the split, to training data only. The generator draws all ten classes.

## Measured effect

Iteration 1 later showed this augmentation hurt (F04, F07 to F09). See the exchange on why augmentation lost.
