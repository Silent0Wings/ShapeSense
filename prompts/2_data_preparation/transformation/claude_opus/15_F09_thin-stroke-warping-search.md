# 2_data_preparation/transformation - F09: 1-px strokes broke into pieces after warping (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F09 · Question from [failure_search_prompts.md](../../../failure_search_prompts.md#f09) · Record: [F09](../inferred_prompts.md#f09)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented, B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why do 1-px lines break into pieces under affine warping and interpolation, and which methods keep thin strokes connected (warping vector strokes before rasterizing, anti-aliasing, morphological closing, supersampling)? Search image processing and sketch-recognition sources.

## Response

### Well established

- **Interpolate, then threshold at a fixed level, and thin lines vanish.** A patent on pixel-density conversion ([US 5351137](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5351137)) describes exactly this failure. When an interpolated binary image is cut at a fixed 1/2 threshold, a thin line disappears. Its fix is a threshold that depends on the conversion factor, lowered for reduction. A second patent ([US 6707953](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6707953)) reports that lateral thin lines are partly lost after binarizing an enlarged image, and that correcting the thin line before binarizing helps. Patents are not peer-reviewed, but they are primary technical documents for this mechanism.
- **Interpolation choice matters.** OpenCV's [geometric-transform docs](https://docs.opencv.org/4.8.0/da/d54/group__imgproc__transform.html) list nearest, bilinear (the `warpAffine` default), bicubic, area and Lanczos interpolation. Area interpolation is recommended for decimation because it gives moiré-free results. Bilinear interpolation spreads a 1-px line's ink over up to four neighbours when it is rotated or shifted by a fraction of a pixel.
- **Anti-aliased rasterisation keeps sub-pixel lines visible.** Wu's line algorithm ([SIGGRAPH 1991](https://cgg.mff.cuni.cz/~pepca/ref/WU.pdf); [overview](https://en.wikipedia.org/wiki/Xiaolin_Wu%27s_line_algorithm)) draws pairs of pixels that straddle the ideal line, shaded by distance. This is the grey-level version of the ink-spreading effect, and it is correct only if no hard cut follows.
- **Morphological closing bridges small gaps.** In [scikit-image](https://scikit-image.org/docs/stable/api/skimage.morphology), closing is dilation followed by erosion, and it closes up dark gaps between bright features. For dark ink on white, apply it to the inverted image. It also thickens lines and can merge nearby strokes.
- **Sketch datasets keep vector strokes.** Quick, Draw! is distributed as strokes (point lists), and its simplified version is scaled into a 256x256 region ([dataset README](https://github.com/googlecreativelab/quickdraw-dataset)). Kaggle doodle pipelines render the strokes with a chosen line width ([Google AI blog](https://research.google/blog/introducing-the-kaggle-quick-draw-doodle-recognition-challenge/)). That lets a pipeline transform points and rasterise afterwards, so stroke connectivity never depends on interpolation.

### Single reports

- Sketch augmentation work on edge maps ([Efthymiadis et al., arXiv 2202.13164](https://arxiv.org/abs/2202.13164v2)) uses small rotations (±5°) and hysteresis thresholds of 0.5t and 1.5t around an estimated level. Hysteresis keeps weak pixels that connect to strong ones, which is a different way to keep lines connected. I did not confirm from the paper whether it binarizes before or after rotation.

### Reasoning (mine, not from a source)

- **Why 1 px breaks and 3 px does not.** After a rotation by a non-right angle or a fractional shift, a 1-px line's ink at each output pixel is split between neighbours, so the peak can fall to about 0.25-0.5. A fixed cut at 0.5 deletes the pixels that fall below it, and the line becomes dashes. A 3-px stroke keeps a core of pixels near full ink, so it survives.
- **Remedies, ordered by how well they fit raster sources:**
  1. **Warp vectors, then rasterise.** This is ideal, but only Quick, Draw! has strokes. The other three sources are raster images, so it cannot be used across the board.
  2. **Supersample:** upsample 4x, warp, then downsample with area interpolation. This keeps sub-pixel geometry but adds cost.
  3. **Threshold relative to the stroke**, either relative to the warped peak or by hysteresis. This is cheap, and it is what the patents and the ShapeSense fix do.
  4. **Closing** as a last step. It is effective but changes stroke width, which interacts with F10.
- **What to measure:** connected-component count per outline, plus ink retained. A threshold of zero would trivially give one component by flooding the background.

### How it applies to ShapeSense

The thin-line path (detect "no 2x2 all-ink block", then cut at 0.2 of the warped peak) is a peak-relative threshold, the same idea as the factor-dependent threshold in the patent. It is a sound choice for mixed raster sources. The first fix, which lowered the cut in proportion to shrink, could not help a rotation at scale 1, and the patents explain why: the right threshold depends on the transform's effect on the line, not on scale alone. Two cheap safeguards remain: a test that counts components per stroke over many seeds, and an ink-retention check.

## Validation
The record's cause was that the cut applied after warping was too strict for thin lines. The image-processing sources agree with this exact mechanism and with the type of fix: a threshold adapted to the transform or to the stroke's own peak. They add alternatives that are standard but were not used (vector warping, supersampling, closing), and they explain why the first, shrink-only fix barely helped. Nothing contradicts the record. Peer-reviewed evidence for this specific pipeline detail was thin: the clearest primary sources are patents and library docs.

**Correction, 2026-11-20:** git history does not support calling the shrink-scaled cut "the first fix". The cut `BINARY_LEVEL * shrink` was already in the original transform (commit c9f5ce3, 2026-11-08), before F09 was found. The thin-line path (`THIN_LINE_LEVEL`) and a change to the peak-relative cut came later, together in commit 87711f3 (2026-11-09). The records still don't say which change was the first fix (17.2 down to 16.3 pieces), so treat the "shrink-only" explanation above as unconfirmed.

## Our decision
The project added a separate thin-line path with a peak-relative cut, which brought outlines from about 17 pieces to 1.0. The findings suggest adding a component-count test per stroke next to the existing survival test, and recording the script that produced the 17.2 / 16.3 / 1.0 counts. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.
