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
