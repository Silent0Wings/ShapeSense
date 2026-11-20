# 5_direct_llm_prediction - Studio shape grids labeling (5 figures, 180 tiles)
- LLM: Gemini 4 Neon
- Category: Pipeline vs. direct LLM prediction
- Date: 2026-11-19

## Prompt
> [Gemini's answers go in its own folder, and the CNN's numbers should stay out of Gemini's prompt.
>
> **Where Gemini's answers go:**
> - Each reply is saved as `prompts/5_direct_llm_prediction/gemini_4_neon/NN_short-title.md`, using the template in [prompts/README.md](prompts/README.md): LLM, date, exact prompt, full response, validation, decision, measured effect. The folder already exists with a `.gitkeep`.
> - The parsed answers go in `results/direct_llm_prediction/gemini_predictions.csv`, with the columns `image_id,true_label,predicted_label`.
>
> **Why the CNN's performance should not go in ahead of time:** the protocol says to run this only after the final model is frozen, so no test result can shape the comparison. If Gemini sees the CNN's score, or any CNN predictions, its answers stop being a fair direct prediction. Record the CNN's score in the results table after Gemini has answered, not in the prompt.
>
> **Also:** the CNN's score on these 200 images has not been computed yet. The Phase 2 numbers in `results/README.md` are for the full test split, so they are not the same measurement.
>
> I can create the empty Gemini file with the template header and the prompt text, if you want it ready before the run.label the iamges @[c:\Users\silent\Github\ShapeSense\results\image_labels\images\3.png]  @[c:\Users\silent\Github\ShapeSense\results\image_labels\images\1.png] @[c:\Users\silent\Github\ShapeSense\results\image_labels\images\5.png] @[c:\Users\silent\Github\ShapeSense\results\image_labels\images\7.png] @[c:\Users\silent\Github\ShapeSense\results\image_labels\images\9.png] ] store them in a file the performace of my cnn on these was 100%

*(Note: the five PNG files `3.png`, `1.png`, `5.png`, `7.png`, and `9.png` were attached directly with the prompt.)*

## Response
Labels for all five attached shape figures (180 tiles total), listed in the order provided (`3.png`, `1.png`, `5.png`, `7.png`, `9.png`):

1. **`results/image_labels/images/3.png`** (5 rows x 6 columns = 30 tiles, by row):
   - Row 1 (cols 1-6): `circle` (6 of 6) — bumpy/wavy hand-drawn outline (~1.15-1.2x wide), still clearly `circle` vs. Row 2's flat ellipse
   - Row 2 (cols 1-6): `ellipse` (6 of 6)
   - Row 3 (cols 1-6): `square` (6 of 6) — dashed/jagged ~1:1 quadrilateral
   - Row 4 (cols 1-6): `rectangle` (6 of 6) — vertical quadrilateral (~1.3:1 height:width)
   - Row 5 (cols 1-6): `diamond` (6 of 6) — pinched/spade-like vertical 4-pointed diamond

2. **`results/image_labels/images/1.png`** (1 row x 10 columns = 10 tiles, left to right):
   - 1: `circle`
   - 2: `ellipse`
   - 3: `triangle`
   - 4: `square` *(least certain: ~1.25:1 wider than tall, visually borderline `rectangle` in isolation; classified `square` alongside the unmistakable ~1.9:1 vertical dashed `rectangle` in col 5 and the paired synthetic `square` in `7.png`)*
   - 5: `rectangle`
   - 6: `pentagon`
   - 7: `hexagon` *(open incomplete outline with ~120° angles)*
   - 8: `octagon` *(irregular/dented 8-sided polygon)*
   - 9: `star`
   - 10: `diamond`

3. **`results/image_labels/images/5.png`** (3 rows x 10 columns = 30 tiles, by column):
   - Col 1 (rows 1-3): `circle`
   - Col 2 (rows 1-3): `ellipse`
   - Col 3 (rows 1-3): `triangle`
   - Col 4 (rows 1-3): `square`
   - Col 5 (rows 1-3): `rectangle`
   - Col 6 (rows 1-3): `pentagon`
   - Col 7 (rows 1-3): `hexagon`
   - Col 8 (rows 1-3): `octagon`
   - Col 9 (rows 1-3): `star`
   - Col 10 (rows 1-3): `diamond`

4. **`results/image_labels/images/7.png`** (2 rows x 5 columns = 10 tiles):
   - Row 1 (`Real`, cols 1-5): `triangle`, `square` *(same ~1.25:1 quadrilateral as `1.png` col 4, paired above synthetic `square`)*, `pentagon`, `star`, `diamond`
   - Row 2 (`Synthetic`, cols 1-5): `triangle`, `square`, `pentagon`, `star`, `diamond`

5. **`results/image_labels/images/9.png`** (10 rows x 10 columns = 100 tiles, alternating `original`/`augmented` pairs, by row):
   - Row 1 (cols 1-10): `circle` (10 of 10; cols 2, 6, 9-10 slightly elongated/borderline `ellipse`)
   - Row 2 (cols 1-10): `ellipse` (10 of 10)
   - Row 3 (cols 1-10): `triangle` (10 of 10; cols 5-8 very flat/thin sliver triangles; cols 9-10 concave-sided)
   - Row 4 (cols 1-10): `square` (10 of 10; cols 5, 6, 8 rotated ~45° with 90° corners)
   - Row 5 (cols 1-10): `rectangle` (10 of 10; cols 3-4 noisy flag/chair shape with protruding stem; cols 5-6 notched end; cols 7-8 slanted parallelogram-like)
   - Row 6 (cols 1-10): `pentagon` (10 of 10)
   - Row 7 (cols 1-10): `hexagon` (10 of 10; col 7 slightly bumpy/rounded)
   - Row 8 (cols 1-10): `octagon` (10 of 10; col 6 slightly narrow/rounded)
   - Row 9 (cols 1-10): `star` (10 of 10)
   - Row 10 (cols 1-10): `diamond` (10 of 10; cols 3-4 jagged/spiky thin diamond; cols 5-6 dashed/dotted)

## Validation
Checked against the paired labeled reference images in `results/image_labels/images/`:
- `3.png` vs `4.png`: 30 / 30 (100%)
- `1.png` vs `2.png`: 10 / 10 (100%)
- `5.png` vs `6.png`: 30 / 30 (100%)
- `7.png` vs `8.png`: 5 / 5 (100%) on the named `Synthetic` row; 10 / 10 (100%) including the `Real` row cross-referenced via `2.png`
- `9.png` vs `10.png`: 100 / 100 (100%)
- Overall: **180 / 180 (100%)** agreement with reference class names (175 / 175 printed directly on the paired reference images + 5 / 5 in the `7.png` `Real` row cross-referenced via `2.png`).

The user-reported `"the performace of my cnn on these was 100%"` is recorded as **user-reported and unverified from the images** (the paired reference strips show ground-truth class names, not CNN predictions). Per `prompts/5_direct_llm_prediction/PROMPT.md`, CNN performance must be omitted from the prompt in the official 200-image test run.

## Our decision
Keep as an exploratory grid-labeling record alongside `results/image_labels/gemini_4_neon_grids_vs_reference.md`. Do **not** populate `results/direct_llm_prediction/gemini_4_neon_predictions.csv` (or `gemini_predictions.csv`) from these 5 sheets, because grouped/ordered QA grids are easier than isolated 64x64 tiles and do not correspond to the 200 test IDs in `results/direct_llm_prediction/sample_ids.csv`.

## Measured effect
Exploratory direct visual check: 180 / 180 (100%) agreement with reference class labels (user-reported CNN score on these grids: 100%, unverified from the strips). Does not produce the official 200-image test-set macro F1 score (still pending per `prompts/5_direct_llm_prediction/PROMPT.md`).

---

## Reviewer addendum (cross-batch review, not part of the blind prediction record)

**Depth only close reading reveals:** the 100% is not comparable to the 94% on the blind 200-tile set. The grids are grouped, so a row or column is one class and the layout leaks the label. The file's own line that the grid results must not populate the predictions file is the key guard.

**Changelog:** [1] 180 tiles in the layouts 30, 10, 30, 10 and 100, which matches the arithmetic; [2] grouped layout leaks the label; [3] the user-reported CNN 100% is kept out of the measured record.

**Open questions:** The recorded prompt contains the user's CNN 100% claim. The file's own rule says CNN results must not be shared with Gemini before the run. If this run is recorded as a direct prediction, the claim in the prompt breaks that rule, even though the grids are not the official 200-image test set.
