# Direct LLM prediction

Goal (PDF section 3): give each LLM the data with the target, let it predict the test images directly, and
compare with the trained model **on the same images and the same metric (macro F1)**.

## Protocol

1. Run this only after the final model is frozen, so no test result can change a modeling choice.
2. Take a fixed sample of the test split: 20 images per class, 200 in total, drawn with seed 0. Save the list of
   image IDs to `results/direct_llm_prediction/sample_ids.csv`. If you can afford the whole test split
   (2,776 images) through the API, use that instead.
3. Score the trained model (`A2_0` final exported ONNX) on exactly the same image IDs.
4. Give each LLM 5 labeled training images per class as examples (50 in total, `results/direct_llm_prediction/fewshot_example_ids.csv`), then the test images shuffled behind blind IDs (`T001`–`T200`, hiding source/class filenames) in batches of 20.
5. Save every request and reply in `claude_opus/` or `gemini_4_neon/`, and the parsed answers in
   `results/direct_llm_prediction/<llm>_predictions.csv` (`image_id,true_label,predicted_label`).

## Prompt

> You are classifying 64x64 grayscale images of 2D shapes into exactly one of these 10 classes:
> circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond.
> First, here are 50 labeled examples (5 per class). <examples>
> Now classify each of the following 20 images. Answer only with lines in the form `image_id,label`, using one
> of the 10 class names, with no other text. <images>

## Report

| Model | Images | Macro F1 |
|---|---|---|
| Trained CNN (final model, `A2_0`) | 200 | 97.50 |
| Claude Opus, direct (`claude-opus-5-5-medium`) | 200 | 92.55 |
| Gemini 4 Neon, direct (`gemini-4-neon-medium`) | 200 | 93.97 |

### Explaining the gap and class confusions

- **Trained CNN (`A2_0`: `97.50` Macro F1, `195/200`) vs. Direct VLMs (`Claude Opus 5.5`: `92.55` Macro F1, `185/200`; `Gemini 4 Neon`: `93.97` Macro F1, `188/200`):** The frozen `A2_0` CNN (`ShapeSense_Deployed/snapshot/models/A2/model.onnx`, `96.25` Macro F1 across all `2,776` test images) was trained directly on `12,405` real standardized shapes plus Stage 2 augmentations and Stage 3 synthetic renders (`synthetic_fraction: 0.3`). Both direct VLMs received only 50 labeled training thumbnails (`fewshot_examples.png`) and classified shuffled blind `64x64` contact sheets with zero weight updates.
- **Claude Opus 5.5 top confusions:** `circle -> ellipse` (4), `hexagon -> octagon` (4), `ellipse -> circle` (1), `ellipse -> hexagon` (1), `square -> rectangle` (1), `rectangle -> ellipse` (1), `pentagon -> hexagon` (1), `octagon -> hexagon` (1). Per-source accuracy ranged from `77.78%` to `98.86%`.
- **Gemini 4 Neon top confusions:** `circle -> ellipse` (4), `hexagon -> octagon` (4), `ellipse -> circle` (1), `square -> rectangle` (1), `rectangle -> diamond` (1), `octagon -> hexagon` (1). Per-source accuracy ranged from `77.78%` to `100.00%`.
- **Trained CNN (`A2_0`) errors (`5/200`):** `hexagon -> octagon` (2), `ellipse -> triangle` (1), `rectangle -> diamond` (1), `octagon -> hexagon` (1).
- **Why those errors happen:** At `64x64` grayscale resolution, vision models without Stage 1–4 task calibration struggle most on subtle geometric thresholds (`pentagon`/`hexagon`/`octagon` vertex counting on thick/jittered polygons, rotated `45°` right-angle squares vs. non-90° rhombi (`square` vs. `diamond`), and slight aspect ratios (`circle` vs. `ellipse`, `square` vs. `rectangle`)), as well as broken/gapped thin strokes in `github_handdrawn` and `quickdraw`. Full per-class tables, per-source tables, and concrete misclassified tile IDs are recorded in [cross_critique/01_direct-prediction-error-comparison.md](cross_critique/01_direct-prediction-error-comparison.md) and [results/direct_llm_prediction/README.md](../../results/direct_llm_prediction/README.md).
