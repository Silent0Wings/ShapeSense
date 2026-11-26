#  prompts: 2_data_preparation/transformation
<a id="f07"></a>

## F07 - Rotation up to ±180° hurt the classes that depend on orientation.

- Iteration: Iteration 2
- LLM: gemini_4_neon + 40297573
- State: Overcome
- CRISP-DM step: Data Preparation · Pipeline stage: 2 · Augmentation

** prompt**

> Rotation augmentation up to 180 degrees seems to hurt squares, rectangles and diamonds. Why, and what rotation range should we search, per class, on validation?

**Answer** 
Square, rectangle and diamond are the classes where orientation carries information. In several sources squares and rectangles are drawn almost always upright: the share of training shapes within ±5° of axis-aligned is 0.924 for kaggle_reevald squares, 0.728 for Quick, Draw! squares and 0.916 for kaggle_reevald rectangles (`docs/crisp_dm/iteration_2/investigation/data_analysis.json`, `orientation`). Rotating by up to ±180° throws that clue away, and a square turned 45° looks like a diamond while keeping the label "square", so the augmentation itself adds label noise. Rotation-invariant classes are not hurt: in the real investigation (`claude_opus/10_real_augmentation-failure-investigation.md`) Opus noted that hexagon and octagon improved under augmentation while the three orientation classes fell.
- **What to search (validation only):** a global range from {0, 5, 10, 15, 20, 30, 45, 90, 180} plus one shared cap for square, rectangle and diamond from {none, 0, 5, 10, 15, 30}, applied per class in the transform (`ROTATIONS`, `ROTATION_CAPS`, `ORIENTATION_CLASSES` in `src/stage4_train/search.py`).
- **How to check:** a rotation-only ablation on A1 with three seeds each. The recorded one gives validation macro F1 89.38 at 0°, 93.62 at ±15° and 90.64 at ±180°, and per-class F1 from ±15° to ±180° of square 93.9 to 90.3, rectangle 87.8 to 82.3, diamond 96.1 to 86.9 (`docs/crisp_dm/iteration_2/search/phase_ablation.json`). Read per-class F1, not only macro F1, and discount runs that stop early: the 0° runs ran only 11 to 13 epochs.
- The search winner was ±20° with a ±10° cap on the three classes, averaging 94.77 validation macro F1 for A1 over three seeds (`docs/crisp_dm/iteration_2/search/winners.json`).

**Documented cause:** In several sources squares and rectangles are nearly always upright, so full rotation removed a clue. A square turned 45° also looks like a diamond.

**Documented outcome:** Searched the range on validation. The winner is ±20°, capped at ±10° for square, rectangle and diamond.

<a id="f08"></a>

## F08 - Augmented shapes came out about 6 px too small.

- Iteration: Iteration 2
- LLM: gemini_4_neon
- State: Overcome
- CRISP-DM step: Data Preparation · Pipeline stage: 2 · Augmentation

** prompt**

> Augmented shapes look smaller than real ones. Compare the framing of augmented images with real images and find the cause.

**Answer** 
Measure the longest side of the ink bounding box on real and augmented copies of the same training images. The investigation did this: real images average 56.42 to 57.81 px per class, augmented ones 50.75 to 51.16 px (`docs/crisp_dm/iteration_2/investigation/data_analysis.json`, `pixel_stats`), and the gap appears for every source in `thin_line_test.json` (for example 57.80 to 51.16 px for mendeley_elkorchi). Because the gap is about 6 px for every class, including circles that rotation does not change, the cause is the transform's re-framing target, not one class's geometry: it re-framed shapes to about 51 px while Stage 1 standardizes them to about 57 px. The fix is to re-frame to the same size Stage 1 produces, `size / (1 + 2 * frame_margin)`, with the margin as a setting (`augment.frame_margin: 0.06` in `configs/pipeline.yaml`, about 57 px in a 64-px frame). This matters because validation and test images are never augmented, so too-small training shapes are a size the model never sees at evaluation. To check it, `test_augmented_shapes_keep_standardized_size` in `tests/stage2/test_outline_survival.py` asserts the mean long side over 100 seeds stays within 3 px of the target times the mean scale jitter. The repo has no per-class size table measured after the fix.

**Documented cause:** The transform re-framed them to 51 px against 57 px in real images.

**Documented outcome:** Corrected the framing margin (augment.frame_margin).

<a id="f09"></a>

## F09 - 1-px strokes broke into pieces after warping.

- Iteration: Iteration 2
- LLM: gemini_4_neon
- State: Overcome
- CRISP-DM step: Data Preparation · Pipeline stage: 2 · Augmentation

** prompt**

> Thin 1-px strokes break into pieces after warping. Why, and how do we keep thin lines connected? How do we measure the fix?

**Answer** 
The transform warps a float ink map with interpolation and then cuts it back to black and white at a fixed level. A 2-3 px stroke still has pixels near full ink after the warp, but a 1-px line at a non-right angle falls between pixel centres, its ink spreads over two neighbours, and both drop below the cut, so the outline turns into dashes. The documented cause is exactly that: the cut after warping was too strict for thin lines. A first fix barely helped (17.2 to 16.3 pieces, `results/phase2_snapshot/iteration_log.json`); the code also lowers the cut in proportion to the shrink, but the records do not say whether that was the first fix, and a shrink-only rule cannot help thin lines rotated at scale 1. What worked is a separate thin-line path: flag an image as thin when no 2x2 block is all ink, and for those images cut at a fraction of the warped peak (`THIN_LINE_LEVEL = 0.2` in `src/stage2_augment/transform.py`), which brought it to 1.0 piece. To measure it, count connected ink components on augmented 1-px references over many seeds (target 1.0), and also check how much ink survives so a fix cannot pass by erasing the line; `test_thin_outline_survives` in `tests/stage2/test_transform_internals.py` covers survival. The script that produced the 17.2 / 16.3 / 1.0 counts is not identified in the repo, and no test counts pieces per stroke.

**Documented cause:** The cut applied after warping was too strict for thin lines.

**Documented outcome:** The first fix barely helped (17.2 down to 16.3 pieces). A separate thin-line path brought it to 1.0 piece.

<a id="f10"></a>

## F10 - Synthetic strokes were thinner than real ones.

- Iteration: Iteration 2
- LLM: opus_medium_5.5 + 40211352 + 40253714
- State: Overcome
- CRISP-DM step: Data Preparation · Pipeline stage: 3 · Synthetic generator

** prompt**

> Compare the stroke width of our synthetic shapes with real images. If they differ, what width should the generator use?

**Answer** 
They differ for every class. Real standardized images have a mean stroke of 2.47 px (hexagon) to 3.30 px (diamond), about 3.0 px averaged over classes, while synthetic images drawn at 2 px measure 1.81 to 2.00 px (`docs/crisp_dm/iteration_2/investigation/data_analysis.json`, `pixel_stats`). A gap that consistent is worth fixing, because stroke width becomes a cheap cue for "synthetic image" instead of shape, and thin synthetic lines are also more fragile under Stage 2 warping. Use 3 px: it is the integer closest to the recorded real value of about 3.1 px and adds no new search dimension (`synth.stroke_px: 3` in `configs/pipeline.yaml`). Sampling a width per image or per class would fit the spread better but adds a range to tune. To confirm the match, re-measure synthetic strokes at 3 px with the same measurement used on the real images; the repo records no such re-measurement and no stroke-width test in `tests/stage3/`.

**Documented cause:** The generator drew 2 px against about 3.1 px in real images.

**Documented outcome:** Set the generator stroke to 3 px.

## Changes, decisions and notes



<a id="c03"></a>

## C03 - Rotation range

- Kind: change (prep)
- LLM: both (mediated, proposed by 40211352)

** prompt**

> Full rotation up to 180 degrees seems to remove the orientation clue that separates square from diamond and rectangle from its rotated forms. What rotation range should we search on validation, and should some classes get a tighter cap?

**Answer** 
Yes, search a global range and a separate, tighter cap for square, rectangle and diamond together, on validation only. The global range should span both ends, {0, 5, 10, 15, 20, 30, 45, 90, 180}, and the cap {none, 0, 5, 10, 15, 30}; the effective rotation for a capped class is the smaller of the two, applied per class in `build_transform` (`src/stage2_augment/transform.py`), with the grid in `src/stage4_train/search.py`. Back the search with a rotation-only ablation (A1, three seeds each): validation macro F1 was 89.38 at 0°, 93.62 at ±15°, 89.91 at ±45°, 90.58 at ±90° and 90.64 at ±180°, and the three orientation classes lost most at ±180° (diamond 96.1 to 86.9, `docs/crisp_dm/iteration_2/search/phase_ablation.json`). The winner was ±20° with a ±10° cap, A1 at 94.77 mean validation macro F1 over three seeds (`docs/crisp_dm/iteration_2/search/winners.json`); no macro F1 for the rotation change on its own is recorded. Note that the later configuration in `configs/pipeline.yaml` keeps ±20° / ±10° for A1 but carries ±15° with a ±15° cap for B, A2 and P, from a later search (see `cross_critique/01_A02_b-and-a2-inherit-augmentation-settings-searc.md`).

**Before:** ±180° for every class

**After:** ±20°, capped at ±10° for square, rectangle and diamond

**Documented reason:** Full rotation removed an orientation clue.

<a id="c04"></a>

## C04 - Other augmentation settings

- Kind: change (prep)
- LLM: both (mediated, proposed by gemini_4_neon)

** prompt**

> Our augmentation ranges (scale, shear, translation, noise and blur probability) were all set by hand. Design a validation-only search for them, with ranges, trial budget and how to pick the winner.

**Answer** 
Run a random search that loads only the train and validation stores and never the test split, as `src/stage4_train/search.py` does. Sample all settings jointly, with ranges that include "off": scale lower bound 0.75 to 1.0 and upper bound up to 1.1, non-uniform scale 0 to 0.2, shear 0 to 20°, translation 0 to 6 px, noise and blur probability 0 to 0.5, plus the rotation range and the orientation cap (`sample_augment`). Budget: `N_AUGMENT = 24` random trials on arm A1 at one seed, plus a small learning-rate and dropout grid. To pick the winner, do not trust the single best single-seed score: keep the `TOP_K = 5` best distinct settings, re-score them more stably (the current code uses cross-validation folds on train and validation), then confirm the chosen setting on seeds 0, 1 and 2 and report the three-seed mean validation macro F1. Search augmentation on A1, the augmentation-only arm, so the result is not confounded with synthetic data. The recorded winner (30 A1 trials in `docs/crisp_dm/iteration_2/search/winners.json`) is scale 0.904 to 1.076, non-uniform scale 0.092, shear 1.4°, translation 0, noise 0.385, blur 0.373, at 94.77 mean validation macro F1. The gain from these settings alone is not recorded, and B and A2 inherited them without their own augmentation search, which the cross-critique A02 confirms and the team disclosed.

**Before:** Set by hand

**After:** Searched on validation: scale 0.904 to 1.076, shear 1.4°, translation 0, noise probability 0.385, blur probability 0.373

**Documented reason:** Every range had been a guess.

<a id="c05"></a>

## C05 - Shape framing after augmentation

- Kind: change (prep)
- LLM: gemini_4_neon (assisted, proposed by 40304911)

** prompt**

> After augmentation our shapes fill about 51 px of the 64-px frame, against about 57 px for real images. Where in the augmentation code does the shape shrink, and how do we expose a framing margin setting and check the fix?

**Answer** 
The shrink happens in the re-framing step of `_augment` in `src/stage2_augment/transform.py`: after the warp, the shape's bounding box is scaled to a target size, and that target did not match what Stage 1 produces, so every class came out about 6 px small (about 51 px against 57 px real, `docs/crisp_dm/iteration_2/investigation/data_analysis.json`). The fit-to-frame loop, which only ever shrinks by `FIT_SHRINK_FACTOR = 0.97` until the ink fits, can shrink rotated shapes further, so it should stay only as a safety net. The fix computes the target as `size / (1 + 2 * frame_margin)` and reads the margin from config, `augment.frame_margin: 0.06` in `configs/pipeline.yaml`, which gives about 57 px in the 64-px frame. Framing must not depend on the label, or size becomes a class cue. To check it, augment reference shapes over many seeds and compare the mean long side with the target; `test_augmented_shapes_keep_standardized_size` in `tests/stage2/test_outline_survival.py` does this over 100 seeds with a 3 px tolerance. Re-running the per-class size table after the fix would be the stronger check, but the repo records none.

**Before:** About 51 px against 57 px real

**After:** Framing margin set by augment.frame_margin

**Documented reason:** Augmented shapes came out too small.

<a id="c06"></a>

## C06 - 1-px stroke handling

- Kind: change (prep)
- LLM: none (40248536)

** prompt**

> 1-px strokes break into about 17 pieces after warping. How do we keep thin strokes connected, and how do we count pieces per stroke to check the fix?

**Answer** 
Give thin strokes their own path through the warp. Detect a 1-px stroke as an image where no 2x2 block is all ink, and for those images cut the warped ink map at a share of its peak rather than at the fixed level, so the line stays joined across the dips between pixels; the code uses `THIN_LINE_LEVEL = 0.2` of the warped maximum (`src/stage2_augment/transform.py`). The thin flag depends only on the stored pixels, so it can be computed once per image. To count pieces, label the 8-connected ink components of each augmented 1-px reference over many seeds and report the mean; a clean outline is 1.0. Also check that most input ink survives, so a fix cannot score 1 piece by erasing the line (`test_thin_outline_survives` in `tests/stage2/test_transform_internals.py`), and that noise only adds ink (`test_noise_only_adds_ink`). The recorded result is 17.2 pieces before, 16.3 after a first fix and 1.0 with the thin-line path (`results/phase2_snapshot/iteration_log.json`). The script behind those counts is not identified in the repo, and no test counts pieces per stroke, so adding one would lock the fix in.

**Before:** 17.2 pieces per stroke

**After:** Separate thin-line path, 1.0 piece

**Documented reason:** Warping broke thin strokes apart.

<a id="c07"></a>

## C07 - Synthetic stroke width

- Kind: change (prep)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Our synthetic generator draws 2-px strokes, but real drawings measure about 3.1 px. What stroke width should the generator use, and how do we measure stroke width on real and synthetic images to confirm the match?

**Answer** 
Use 3 px (`synth.stroke_px: 3` in `configs/pipeline.yaml`). Real per-class mean strokes run from 2.47 to 3.30 px, while 2-px synthetic images measure 1.81 to 2.00 px (`docs/crisp_dm/iteration_2/investigation/data_analysis.json`), so 3 px is the closest single integer and adds nothing to search. The renderer already takes the stroke in output pixels and draws at supersampled resolution before downsampling, so the setting is honoured. To confirm the match, measure stroke width the same way on both sides: per image, estimate the mean outline thickness of the binarized ink (the investigation stored it as `stroke` in `pixel_stats` for real, augmented and synthetic images), using train images only, and compare per-class means. The repo records no re-measurement of synthetic images at 3 px and no stroke-width test in `tests/stage3/`, and the exact measurement method is not documented in `data_analysis.json`, so the match is set by design but not verified.

**Before:** 2 px

**After:** 3 px, against about 3.1 px real

**Documented reason:** The generator did not match real strokes.

<a id="c08"></a>

## C08 - Synthetic generator ranges

- Kind: change (prep)
- LLM: both (mediated, proposed by gemini_4_neon)

** prompt**

> The synthetic generator ranges (size, rotation, jitter, stroke) were set by hand. Should B and A2 get separate generator searches on validation, and how do we keep the search from touching the test split?

**Answer** 
Yes, search them separately. B and A2 mix synthetic images into training in different ways (B at one synthetic fraction, A2 with a clean-real share as well), so the best generator for one need not suit the other. In `src/stage4_train/search.py`, `sample_synth` draws each arm's synthetic fraction (0.1 to 0.5) with the generator ranges from `sample_generator` (radius, centre and vertex jitter, ellipse and rectangle ratios, diamond angle, star inner ratio), with `N_SYNTH = 16` trials per arm, and A2 gets an extra search of its clean and synthetic shares (sum at most 0.8). Both start from the A1 augmentation winner, so only generator and mix settings differ. The test split stays out because the search loads stores through `load_stores`, which returns train and validation only, and the winners are fixed before any test run. Recorded results: B 94.20 and A2 95.17 three-seed mean validation macro F1, from 22 and 18 trials (`docs/crisp_dm/iteration_2/search/winners.json`). No hand-set generator was scored under the same conditions, so the gain from this change alone is not established in the records.

**Before:** Set by hand

**After:** Searched on validation for B and for A2 separately

**Documented reason:** Every range had been a guess.

<a id="c35"></a>

## C35 - Augmentation and generator speed

- Kind: change (prep)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40304911)

** prompt**

> The same stored images are augmented many times, and ink positions and thin-line checks are recomputed every time. What can we cache per stored image, which morphology and array steps can be faster, and how do we test that the output is identical?

**Answer** 
Cache only what depends on the stored pixels and not on the random draw: the ink positions and the 1-px thin flag. In `src/stage2_augment/transform.py` this is `_ink_facts`, wrapped in `functools.lru_cache(maxsize=SHAPE_CACHE_SIZE)` with `SHAPE_CACHE_SIZE = 20_000`, keyed on the image bytes, size and threshold, and returning read-only arrays so no caller can corrupt a cached entry. The bound matters because synthetic images are new every call and only churn through the cache. For speed, the thin check can be four shifted 2x2 slices ANDed together instead of a SciPy erosion, and the 1-px dilation used for outline noise can be done with shifted slices (`_dilate_1px`). Do not cache anything that depends on rotation, scale, blur or noise, and keep the order of random draws unchanged so a seed still gives the same image. To prove identical output, save augmented images for fixed images, labels and seeds before the change and assert byte equality after, and compare the slice-based steps with the SciPy versions on random masks. The worksheet says tests and reruns confirm identical output, but no direct SciPy comparison test and no before/after timing are recorded.

**Before:** Ink positions and thin-line checks recomputed for every image

**After:** Cached per stored image, with faster morphology and array steps

**Documented reason:** The same stored images are augmented many times. Tests and reruns confirm identical output.
