## 

# 2_data_preparation/transformation - C08: Synthetic generator ranges
`33_real_iteration-2-plan-tuning-and-a2.md`
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: `../gemini_4_neon/07_C08_synthetic-generator-ranges.md`
- Date: 2026-11-09
- Entry: C08 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c08), `results/llm_comparison/attribution_worksheet.csv` (C08), `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, commits 87711f3 and 5acfb7c


## Prompt

> The synthetic generator's ranges (shape size, centre and vertex jitter, ellipse and rectangle aspect ratios, diamond angle, star inner ratio) were set by hand, and the per-arm search suggests the wide variation of the synthetic data is part of the error. Should arm B and arm A2 each get their own generator search on validation, and how do we keep that search away from the test split?

## Response

Yes, I'd search them separately, and I'd say why in the report, because it looks like extra work otherwise.

### Why separate searches

B and A2 use synthetic images for different jobs. In B, synthetic shapes are mixed into the real training set as extra variety, so the generator should probably stay close to what real images look like. In A2, synthetic data sits next to a clean share and real images, and the best generator may be broader. One shared setting would be a compromise that is optimal for neither, and it would make the B vs A2 comparison partly a comparison of a generator tuned for the other arm.

### What to search per arm

| Knob | Suggested range |
|---|---|
| Synthetic fraction | 0.1 to 0.5 |
| Radius, low / high | 12 to 20 px / 22 to 30 px |
| Centre jitter | 0 to 8 px |
| Vertex jitter | 0 to 2 px |
| Ellipse max axis ratio | 1.5 to 4 |
| Rectangle max side ratio | 1.5 to 4 |
| Diamond acute angle, low / high | 40 to 60° / 60 to 80° |
| Star inner ratio, low / high | 0.35 to 0.45 / 0.5 to 0.6 |

For A2, also sample the clean and synthetic shares together, with their sum bounded so real images keep a meaningful share.

### Keep the augmentation fixed

Start both arms from the augmentation winner found for A1. Otherwise the generator search and the augmentation search compete for the same budget and the result is hard to attribute.

### Class-dependent risks

- The ellipse ratio, rectangle ratio and diamond angle define class boundaries. A rectangle ratio near 1 is a square; a diamond angle near 90° is a square too. The lower bounds above stay away from those edges, and I would not widen them.
- Check per-class F1 on the winners for ellipse, rectangle, diamond and square specifically.

### Test split

The generator itself never reads data, but the search does: it should load only train and val stores, and validation must contain only real images, never synthetic ones. Freeze both winners before any test evaluation.

### Interpretation

If the two arms end up with very different generator settings, that is a finding, not a bug, but it is also a reminder that the B vs A2 gap includes tuning differences.

## Validation

Searched on validation, separately for B and A2. In `src/stage4_train/search.py`, `sample_synth` draws the arm's synthetic fraction (0.1 to 0.5) plus `sample_generator` (ranges as in the table above), and `sample_shares` draws the A2 clean and synthetic shares with their sum at most 0.8. `N_SYNTH` is 16. `winners.json` records 22 trials for B and 18 for A2.

## Our decision

Hand-set ranges -> one searched generator per arm. B winner: radius 19.7 to 24.8 px, centre jitter 3.7, vertex jitter 1.6, ellipse ratio 3.7, rectangle ratio 1.78, diamond angle 55.1 to 60.9°, synthetic fraction 0.278. A2 winner: radius 12.5 to 27.1 px, centre jitter 5.3, vertex jitter 0.4, ellipse ratio 2.46, rectangle ratio 3.99, diamond angle 54.9 to 65.6°, clean fraction 0.411, synthetic fraction 0.198. Both keep the A1 augmentation values.

## Measured effect

Three-seed mean validation macro-F1: B 94.20, A2 95.17 (`winners.json`). No macro-F1 for the hand-set generator under the same conditions is recorded, so the gain from this change alone is unknown.

## Deeper detail: why separate searches matter

### B and A2 use synthetic differently

| Arm | Synthetic role | Generator should be |
|---|---|---|
| B | Extra variety in real training set | Close to real images |
| A2 | Alongside clean + real | Broader |

- **Why separate searches:** B and A2 use synthetic for different jobs, so the optimal generator differs.
- **Why a shared setting would be a compromise:** it would be optimal for neither.
- **Why this is a good design:** it's arm-aware.

### The ranges are class-safe

| Knob | Range | Why it's class-safe |
|---|---|---|
| Ellipse ratio | 1.5-4 | Avoids square (ratio 1) |
| Rectangle ratio | 1.5-4 | Avoids square (ratio 1) |
| Diamond angle | 40-80° | Avoids square (90°) |

- **Why the ranges are class-safe:** they avoid the boundaries that would confuse classes (per S07).
- **Why this is a good design:** it's consistent with the class-aware approach.

### The search is validation-only

- **Why validation-only:** the test split must not choose any setting.
- **Why validation has only real images:** synthetic images in validation would leak.
- **Why this is a good design:** it's consistent with the fail-closed pattern.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | C08 | The class-safe ranges are from S07 |
| T35 (transform fix) | C08 | C08 is part of T35's three groups |
| C04 (other augmentation) | C08 | C04 is the augmentation; C08 is the generator |
| A01 (noise bands) | C08 | The noise bands are the metric for the search |

- **Why this matters:** C08 is the fix for the generator ranges, building on S07, T35, C04, and A01.

## Notes on the log


- **Separate searches for B and A2.** They use synthetic differently.
- **The ranges are class-safe.** They avoid class-changing boundaries.
- **The search is validation-only.** The test split is protected.
- **Cross-reference to S07, T35, C04, A01:** C08 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.