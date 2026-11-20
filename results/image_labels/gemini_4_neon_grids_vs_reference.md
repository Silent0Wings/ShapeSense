# Shape grids 1, 3, 5, 7, 9 - Gemini 4 Neon labels checked against reference strips
- LLM: Gemini 4 Neon
- Date: 2026-11-19
- Prompt log: `prompts/5_direct_llm_prediction/gemini_4_neon/01_image-grids-labeling.md`
- CNN performance: `100%` (user-reported in prompt; not printed on reference strips `2.png`, `4.png`, `6.png`, `8.png`, `10.png`)

## Summary across all 5 figures
| Unlabeled image | Reference image | Layout | Tiles | Direct label match | Cross-ref match | Total match |
|---|---|---|---|---|---|---|
| `images/3.png` | `images/4.png` | 5 rows x 6 cols | 30 | 30 / 30 (100%) | - | 30 / 30 (100%) |
| `images/1.png` | `images/2.png` | 1 row x 10 cols | 10 | 10 / 10 (100%) | - | 10 / 10 (100%) |
| `images/5.png` | `images/6.png` | 3 rows x 10 cols | 30 | 30 / 30 (100%) | - | 30 / 30 (100%) |
| `images/7.png` | `images/8.png` | 2 rows x 5 cols (`Real`, `Synthetic`) | 10 | 5 / 5 (`Synthetic`) | 5 / 5 (`Real` via `2.png`) | 10 / 10 (100%) |
| `images/9.png` | `images/10.png` | 10 rows x 10 cols | 100 | 100 / 100 (100%) | - | 100 / 100 (100%) |
| **Total** | | | **180** | **175 / 175 (100%)** | **5 / 5 (100%)** | **180 / 180 (100%)** |

## Per-image comparisons

### 1. `images/3.png` vs `images/4.png` (5 rows x 6 columns, 30 tiles)
| Row | Gemini 4 Neon label | Reference row name (`4.png`) | Matches |
|---|---|---|---|
| 1 | circle | circle | 6 of 6 |
| 2 | ellipse | ellipse | 6 of 6 |
| 3 | square | square | 6 of 6 |
| 4 | rectangle | rectangle | 6 of 6 |
| 5 | diamond | diamond | 6 of 6 |

### 2. `images/1.png` vs `images/2.png` (1 row x 10 columns, 10 tiles)
| Column | Gemini 4 Neon label | Reference name (`2.png`) | Match |
|---|---|---|---|
| 1 | circle | circle | yes |
| 2 | ellipse | ellipse | yes |
| 3 | triangle | triangle | yes |
| 4 | square | square | yes |
| 5 | rectangle | rectangle | yes |
| 6 | pentagon | pentagon | yes |
| 7 | hexagon | hexagon | yes |
| 8 | octagon | octagon | yes |
| 9 | star | star | yes |
| 10 | diamond | diamond | yes |

### 3. `images/5.png` vs `images/6.png` (3 rows x 10 columns, 30 tiles)
| Column | Gemini 4 Neon label (rows 1-3) | Reference column name (`6.png`) | Matches |
|---|---|---|---|
| 1 | circle | circle | 3 of 3 |
| 2 | ellipse | ellipse | 3 of 3 |
| 3 | triangle | triangle | 3 of 3 |
| 4 | square | square | 3 of 3 |
| 5 | rectangle | rectangle | 3 of 3 |
| 6 | pentagon | pentagon | 3 of 3 |
| 7 | hexagon | hexagon | 3 of 3 |
| 8 | octagon | octagon | 3 of 3 |
| 9 | star | star | 3 of 3 |
| 10 | diamond | diamond | 3 of 3 |

### 4. `images/7.png` vs `images/8.png` (2 rows x 5 columns, 10 tiles)
| Row | Column | Gemini 4 Neon label | Reference name (`8.png`) | Match |
|---|---|---|---|---|
| Real | 1 | triangle | *(none printed; `triangle` via `2.png`)* | yes (cross-ref) |
| Real | 2 | square | *(none printed; `square` via `2.png`)* | yes (cross-ref) |
| Real | 3 | pentagon | *(none printed; `pentagon` via `2.png`)* | yes (cross-ref) |
| Real | 4 | star | *(none printed; `star` via `2.png`)* | yes (cross-ref) |
| Real | 5 | diamond | *(none printed; `diamond` via `2.png`)* | yes (cross-ref) |
| Synthetic | 1 | triangle | triangle | yes |
| Synthetic | 2 | square | square | yes |
| Synthetic | 3 | pentagon | pentagon | yes |
| Synthetic | 4 | star | star | yes |
| Synthetic | 5 | diamond | diamond | yes |

### 5. `images/9.png` vs `images/10.png` (10 rows x 10 columns, 100 tiles)
| Row | Gemini 4 Neon label | Reference row name (`10.png`) | Matches |
|---|---|---|---|
| 1 | circle | circle | 10 of 10 |
| 2 | ellipse | ellipse | 10 of 10 |
| 3 | triangle | triangle | 10 of 10 |
| 4 | square | square | 10 of 10 |
| 5 | rectangle | rectangle | 10 of 10 |
| 6 | pentagon | pentagon | 10 of 10 |
| 7 | hexagon | hexagon | 10 of 10 |
| 8 | octagon | octagon | 10 of 10 |
| 9 | star | star | 10 of 10 |
| 10 | diamond | diamond | 10 of 10 |

## Notes
- **Borderline / least-certain tiles:**
  - `1.png` col 4 and `7.png` `Real` col 2 (`square`): ~1.25:1 wider than tall, visually borderline `rectangle` in isolation; distinguished here partly alongside the unmistakable ~1.9:1 vertical dashed `rectangle` (`1.png` col 5) and paired synthetic `square` (`7.png`).
  - `3.png` row 1 (`circle`): bumpy/wavy hand-drawn outline (~1.15-1.2x wide), compared against row 2's flatter `ellipse`.
  - `9.png`: row 1 cols 2, 6, 9-10 (`circle` slightly elongated/borderline `ellipse`); row 3 cols 5-8 (`triangle`, very flat/thin slivers); row 4 cols 5, 6, 8 (`square`, rotated ~45° with 90° corners); row 5 cols 3-4 (`rectangle`, noisy flag/chair shape with protruding stem); row 7 col 7 (`hexagon`, slightly bumpy/rounded); row 8 col 6 (`octagon`, slightly narrow/rounded); row 10 cols 3-6 (`diamond`, jagged/spiky or dashed/dotted thin diamonds).
- **Why grouped grids are easier than isolated 64x64 test tiles:** these QA/studio sheets group identical classes along rows or columns (`3.png`, `5.png`, `9.png`) and follow the canonical 10-class taxonomy order (`1.png`, `5.png`, `9.png`), providing visual context that is absent when classifying single shuffled test tiles one by one.
- **Protocol notes:**
  - The user's prompt included the CNN's reported score (`100%`, unverified from the reference strips); for the official direct-prediction benchmark, CNN scores and predictions must stay out of the LLM prompt.
  - These 5 grids (180 tiles) are not a test set and do not yield a course macro F1 score.
  - The official comparison uses the 200 individual test images listed in `results/direct_llm_prediction/sample_ids.csv` (for which `results/direct_llm_prediction/trained_cnn_predictions.csv` already exists) per `prompts/5_direct_llm_prediction/PROMPT.md`.
