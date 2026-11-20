# Direct LLM prediction - Gemini 4 Neon

Blind direct visual classification run completed on **2026-11-19** using `gemini-4-neon-medium` against the 50 seed-0 labeled training examples (`results/direct_llm_prediction/fewshot_example_ids.csv`) and the 200 seed-0 held-out test images (`results/direct_llm_prediction/sample_ids.csv`).

- **Score:** **93.97 Macro F1** (`188/200`, `94.00%` accuracy) vs. `97.50` Macro F1 for trained CNN `A2_0`
- **Predictions CSV:** [`results/direct_llm_prediction/gemini_4_neon_predictions.csv`](../../../results/direct_llm_prediction/gemini_4_neon_predictions.csv)
- **Blind ID mapping:** [`results/direct_llm_prediction/blind_id_map.csv`](../../../results/direct_llm_prediction/blind_id_map.csv)
- **Error comparison:** [`01_direct-prediction-error-comparison.md`](../cross_critique/01_direct-prediction-error-comparison.md)

## Batch Exchanges (10 batches × 20 images)

- [Batch 01 (T001-T020)](01_batch-01.md)
- [Batch 02 (T021-T040)](02_batch-02.md)
- [Batch 03 (T041-T060)](03_batch-03.md)
- [Batch 04 (T061-T080)](04_batch-04.md)
- [Batch 05 (T081-T100)](05_batch-05.md)
- [Batch 06 (T101-T120)](06_batch-06.md)
- [Batch 07 (T121-T140)](07_batch-07.md)
- [Batch 08 (T141-T160)](08_batch-08.md)
- [Batch 09 (T161-T180)](09_batch-09.md)
- [Batch 10 (T181-T200)](10_batch-10.md)

---

## Studio / QA shape grids labeling (5 figures, 180 tiles)

- **Saved prompt & response exchange:** [`01_image-grids-labeling.md`](01_image-grids-labeling.md)
- **Detailed comparison against reference strips (`2.png`, `4.png`, `6.png`, `8.png`, `10.png`):** [`../../../results/image_labels/gemini_4_neon_grids_vs_reference.md`](../../../results/image_labels/gemini_4_neon_grids_vs_reference.md)
- **CNN performance on these grids:** `100%` *(user-reported in the prompt; not printed on the reference strips `2.png`, `4.png`, `6.png`, `8.png`, `10.png`)*

### Summary across all 5 figures
| Unlabeled image | Reference image | Layout | Tiles | Direct label match | Cross-ref match | Total match |
|---|---|---|---|---|---|---|
| `images/3.png` | `images/4.png` | 5 rows x 6 cols | 30 | 30 / 30 (100%) | - | 30 / 30 (100%) |
| `images/1.png` | `images/2.png` | 1 row x 10 cols | 10 | 10 / 10 (100%) | - | 10 / 10 (100%) |
| `images/5.png` | `images/6.png` | 3 rows x 10 cols | 30 | 30 / 30 (100%) | - | 30 / 30 (100%) |
| `images/7.png` | `images/8.png` | 2 rows x 5 cols (`Real`, `Synthetic`) | 10 | 5 / 5 (`Synthetic`) | 5 / 5 (`Real` via `2.png`) | 10 / 10 (100%) |
| `images/9.png` | `images/10.png` | 10 rows x 10 cols | 100 | 100 / 100 (100%) | - | 100 / 100 (100%) |
| **Total** | | | **180** | **175 / 175 (100%)** | **5 / 5 (100%)** | **180 / 180 (100%)** |

### Per-image labels
1. **`results/image_labels/images/3.png`** (5 rows x 6 columns = 30 tiles, by row):
   - Row 1 (cols 1-6): `circle` (6 of 6; bumpy/wavy hand-drawn outline ~1.15-1.2x wide, distinct from Row 2's flat ellipse)
   - Row 2 (cols 1-6): `ellipse` (6 of 6)
   - Row 3 (cols 1-6): `square` (6 of 6; dashed/jagged ~1:1 quadrilateral)
   - Row 4 (cols 1-6): `rectangle` (6 of 6; vertical quadrilateral ~1.3:1 height:width)
   - Row 5 (cols 1-6): `diamond` (6 of 6; pinched/spade-like vertical 4-pointed diamond)

2. **`results/image_labels/images/1.png`** (1 row x 10 columns = 10 tiles, left to right):
   - 1: `circle`, 2: `ellipse`, 3: `triangle`, 4: `square` *(least certain: ~1.25:1 wider than tall, visually borderline `rectangle` in isolation; classified `square` alongside the unmistakable ~1.9:1 vertical dashed `rectangle` in col 5 and the paired synthetic `square` in `7.png`)*, 5: `rectangle`, 6: `pentagon`, 7: `hexagon` *(open incomplete outline with ~120° angles)*, 8: `octagon` *(irregular/dented 8-sided polygon)*, 9: `star`, 10: `diamond`

3. **`results/image_labels/images/5.png`** (3 rows x 10 columns = 30 tiles, by column):
   - Col 1 (rows 1-3): `circle`, Col 2: `ellipse`, Col 3: `triangle`, Col 4: `square`, Col 5: `rectangle`, Col 6: `pentagon`, Col 7: `hexagon`, Col 8: `octagon`, Col 9: `star`, Col 10: `diamond` (3 of 3 per column)

4. **`results/image_labels/images/7.png`** (2 rows x 5 columns = 10 tiles):
   - Row 1 (`Real`, cols 1-5): `triangle`, `square` *(same ~1.25:1 quadrilateral as `1.png` col 4, paired above synthetic `square`)*, `pentagon`, `star`, `diamond`
   - Row 2 (`Synthetic`, cols 1-5): `triangle`, `square`, `pentagon`, `star`, `diamond`

5. **`results/image_labels/images/9.png`** (10 rows x 10 columns = 100 tiles, alternating `original`/`augmented` pairs, by row):
   - Row 1: `circle` (10 of 10; cols 2, 6, 9-10 slightly elongated/borderline `ellipse`)
   - Row 2: `ellipse` (10 of 10)
   - Row 3: `triangle` (10 of 10; cols 5-8 very flat/thin sliver triangles; cols 9-10 concave-sided)
   - Row 4: `square` (10 of 10; cols 5, 6, 8 rotated ~45° with 90° corners)
   - Row 5: `rectangle` (10 of 10; cols 3-4 noisy flag/chair shape with protruding stem; cols 5-6 notched end; cols 7-8 slanted parallelogram-like)
   - Row 6: `pentagon` (10 of 10)
   - Row 7: `hexagon` (10 of 10; col 7 slightly bumpy/rounded)
   - Row 8: `octagon` (10 of 10; col 6 slightly narrow/rounded)
   - Row 9: `star` (10 of 10)
   - Row 10: `diamond` (10 of 10; cols 3-4 jagged/spiky thin diamond; cols 5-6 dashed/dotted)
