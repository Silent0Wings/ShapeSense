## Expanded entry

# 2_data_preparation/transformation - T08: Add synthetic shape generator with enforced margins

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Gemini 4 Neon (simulated reconstruction)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T08 (`built`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40211352 + 40256377 / gemini_4_neon + 40211352 + 40256377
- LLM role: proposed
- Grounding sources: `results/llm_comparison/commit_tasks.csv` (T08), `stages/stage_3.md`, `configs/taxonomy.yaml` (`ambiguity_margins`), `src/stage3_synth/generate.py`, `src/stage3_synth/shapes.py`, `src/stage3_synth/render.py`, `src/stage3_synth/measure.py`, `tests/stage3/test_shapes.py`, `docs/crisp_dm/iteration_2/investigation/data_analysis.json`, commit 6e3be2f

## Prompt

> We need a Stage 3 generator, `generate(label, rng)`, that draws the 10 classes as 64x64 black outlines on white for arm B. The brief asks for margins between confusable classes: ellipse axis ratio at least 1.2, rectangle side ratio at least 1.2, diamond angles at least 10° off 90°. It also asks for a "~2-px" outline and at least 2,000 images per second on one thread. How would you design it so the margins can never be broken?

## Response

I would split the generator into three layers, so each one can be tested on its own.

### 1. Parameters (`sample_params`)

Sample shape parameters per class from ranges in `configs/pipeline.yaml#synth`, with the margins read from `configs/taxonomy.yaml#ambiguity_margins`. Enforce margins at sampling time:

- Ellipse and rectangle ratios are drawn from `[margin, max]`, never below.
- Diamond angles are clamped so `|angle - 90| >= margin`.
- Circle axes are equal. Square sides are equal with right angles.
- Vertex jitter is off for square, rectangle and diamond, so their margins hold exactly.

A `check_params` function should list any violation, so tests can feed it deliberately bad values (Mission M1).

### 2. Geometry (`vertices`)

Turn parameters into polygon vertices in pixel space. Circles and ellipses need enough points to look smooth, at least 64. Place the shape with a margin from the frame edge by shifting, not clipping, so no vertex is cut off.

### 3. Rendering (`render_outline`)

Draw a closed line at a supersampled resolution, then downsample and threshold to pure 0 and 255. Two pitfalls:

- Pillow's wide `polygon(width=)` fills concave shapes such as the star. Use a closed `line` instead.
- Round joints add a pie slice at every vertex, which is slow on 64-point circles. Square caps at real corners only are cheaper.

### Margins in the image, not only in the numbers

A thick outline on a small ellipse makes its visible ratio look closer to 1 than the sampled ratio. Add a small cushion above the taxonomy margin, and measure the ratio on the rendered image with a PCA-based `axis_ratio` helper.

### Throughput

Build the generator once from config, avoid per-call config reads, and benchmark in a test so the 2,000 images/s target is checked, not assumed.

### Cautions

- The "~2-px" in the brief should be checked against real standardized images. If the real stroke differs, the generator adds a style cue that separates synthetic from real.
- Margins remove ambiguity from synthetic images only. Real images near the boundary still exist, so do not judge the margins on test results.

## Validation

- Commit 6e3be2f, status built (`results/llm_comparison/commit_tasks.csv`). The code described is the version in the repo now.
- `src/stage3_synth/shapes.py` has `sample_params`, `vertices`, `check_params`, `RATIO_RENDER_CUSHION = 0.05` and no jitter for square, rectangle and diamond. `render.py` uses a closed line and square corner caps. `measure.py` has `axis_ratio` and `min_interior_angle_deg`.
- Tests in `tests/stage3/test_shapes.py` cover the ellipse, rectangle and diamond margins, circle axes, square sides, the star inner ratio, unfilled outlines, margins read from taxonomy, and M1 violations. No throughput result is kept in the repo.

## Our decision

Built as proposed, with a 2-px stroke from the brief.

## Measured effect

No metric is recorded for this task. The stroke caution proved right: in iteration 2, synthetic strokes measured 1.81 to 2.00 px against 2.47 to 3.30 px real per class (`data_analysis.json`), and the stroke was raised to 3 px (F10, C07).

## Deeper detail: why the three-layer split matters

### The three layers are testable separately

| Layer | What it does | Why it's testable |
|---|---|---|
| `sample_params` | Samples + enforces margins | Margins checked at sampling |
| `vertices` | Params -> pixel space | Geometry checked |
| `render_outline` | Draws + downsamples | Rendering checked |

- **Why three layers:** each is testable on its own.
- **Why margins at sampling time:** they can never be broken.
- **Why this is a good design:** it's modular.

### The margins are enforced, not just sampled

| Margin | How enforced | Why |
|---|---|---|
| Ellipse ratio | `[margin, max]` | Never below |
| Rectangle ratio | `[margin, max]` | Never below |
| Diamond angle | Clamped `|angle - 90| >= margin` | Never too close |
| Circle axes | Equal | By definition |
| Square sides | Equal + right angles | By definition |
| Vertex jitter | Off for 3 classes | Margins hold exactly |

- **Why enforced matters:** it's not just a preference.
- **Why `check_params` matters:** it catches violations.
- **Why this is a good design:** it's fail-safe.

### The rendering has two pitfalls

| Pitfall | What it does | Fix |
|---|---|---|
| `polygon(width=)` fills concave | Star gets filled | Use closed `line` |
| Round joints slow | Pie slice per vertex | Square caps at real corners |

- **Why these pitfalls matter:** they break correctness and speed.
- **Why this is a good design:** it's aware of the pitfalls.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | T08 | The taxonomy margins are from S07 |
| F10 (stroke width) | T08 | The stroke caution proved right |
| C07 (stroke width fix) | T08 | C07 is the later fix |
| A01 (noise bands) | T08 | The noise bands are the metric for the generator |

- **Why this matters:** T08 is the foundation for the synthetic generator, building on S07, F10, C07, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The three-layer split matters.** Each is testable separately.
- **The margins are enforced, not just sampled.** They can never be broken.
- **The rendering has two pitfalls.** They're aware of them.
- **Cross-reference to S07, F10, C07, A01:** T08 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.