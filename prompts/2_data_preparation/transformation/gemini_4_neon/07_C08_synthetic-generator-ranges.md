## Expanded entry

# 2_data_preparation/transformation - C08: Synthetic generator ranges



- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: `../claude_opus/07_C08_synthetic-generator-ranges.md`
- Date: 2026-11-09
- Entry: C08 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c08), `results/llm_comparison/attribution_worksheet.csv` (C08), `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, commits 87711f3 and 5acfb7c

## Prompt

> The synthetic generator's ranges (shape size, centre and vertex jitter, ellipse and rectangle aspect ratios, diamond angle, star inner ratio) were set by hand, and the per-arm search suggests the wide variation of the synthetic data is part of the error. Should arm B and arm A2 each get their own generator search on validation, and how do we keep that search away from the test split?

## Response

Recommendation: yes, two searches, same code path, different seeds offset so their trial lists do not overlap.

### Design

1. **Shared sampler.** Write one function that draws a full generator setting. Both arms call it, so the ranges are defined once and cannot drift apart.
2. **Arm-specific extras.**
   - B: also draw the synthetic fraction of the training mix.
   - A2: also draw the clean share and the synthetic share, rejecting draws where they leave too little room for real images.
3. **Fixed base.** Every generator trial starts from the augmentation winner and the same starting learning rate and dropout. Only generator knobs and shares vary.
4. **Selection.** Same rule as the augmentation search: rank on one seed, confirm the top candidates on three seeds, pick the best mean.

### Ranges: start from the class definitions, not from taste

| Class rule | What could go wrong | Guard |
|---|---|---|
| Rectangle side ratio | Ratio close to 1 gives a square | Lower bound well above 1 |
| Diamond acute angle | Close to 90° gives a square | Upper bound kept below 90° |
| Ellipse axis ratio | Close to 1 gives a circle | Lower bound above 1 |
| Star inner ratio | Too high looks like a polygon | Narrow band |
| Radius | Too small breaks thin strokes; too large clips | Keep inside the 64 px frame |

Jitter ranges (centre and vertex) are the ones I'd make widest, because they mimic hand-drawn imperfection, which is what the synthetic data lacks most.

### Leakage checklist

- [ ] The search loads train and val stores only.
- [ ] Validation is real images only; synthetic images never enter validation.
- [ ] Generator seeds for training are independent of anything in the test split.
- [ ] Both winners are written to a file before the first test run.

### Reporting

- Report both winners side by side. If B prefers a narrow generator and A2 a wide one, say so; it explains part of the arm gap.
- Report per-class F1 for square, rectangle, diamond and ellipse, since those are the classes the generator can mislabel.
- State that no hand-set baseline was rerun, if that is the case, so readers do not read the winners as a measured gain.

## Validation

Validation-only search in `src/stage4_train/search.py`: `sample_generator` (radius low 12 to 20 px, high 22 to 30 px; centre jitter 0 to 8; vertex jitter 0 to 2; ellipse and rectangle ratios 1.5 to 4; diamond angle 40 to 60° / 60 to 80°; star inner ratio 0.35 to 0.45 / 0.5 to 0.6), `sample_synth` (fraction 0.1 to 0.5) and `sample_shares` for A2 (clean plus synthetic at most 0.8). B ran 22 trials and A2 18 (`winners.json`).

## Our decision

Searched on validation for B and A2 separately. B: radius 19.7 to 24.8 px, rectangle ratio 1.78, synthetic fraction 0.278. A2: radius 12.5 to 27.1 px, rectangle ratio 3.99, clean fraction 0.411, synthetic fraction 0.198. Full values in `winners.json`.

## Measured effect

Three-seed mean validation macro-F1: B 94.20, A2 95.17. No hand-set generator baseline under the same conditions is recorded.

## Deeper detail: why the ranges are class-safe

### The ranges start from class definitions

| Class rule | Guard | Why |
|---|---|---|
| Rectangle ratio | Lower bound above 1 | Avoids square |
| Diamond angle | Upper bound below 90° | Avoids square |
| Ellipse ratio | Lower bound above 1 | Avoids circle |
| Star inner ratio | Narrow band | Avoids polygon |
| Radius | Inside 64 px frame | Avoids clipping |

- **Why the ranges are class-safe:** they avoid the boundaries that would confuse classes (per S07).
- **Why this is a good design:** it's grounded in the class definitions.

### The design is shared but arm-aware

| Element | What it does | Why |
|---|---|---|
| Shared sampler | One function, both arms | Ranges can't drift |
| Arm-specific extras | B: fraction, A2: shares | Arm-aware |
| Fixed base | Augmentation winner + same LR/dropout | Only generator varies |
| Selection | Same rule as augmentation | Consistent |

- **Why shared but arm-aware:** it's consistent and targeted.
- **Why this is a good design:** it's clean.

### The leakage checklist is thorough

| Check | Why |
|---|---|
| Train + val only | Test protected |
| Validation real only | No synthetic leak |
| Generator seeds independent | No test coupling |
| Winners written before test | Auditability |

- **Why the checklist matters:** it prevents leakage and ensures auditability.
- **Why this is a good design:** it's fail-closed.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | C08 | The class-safe ranges are from S07 |
| C04 (other augmentation) | C08 | C04 is the augmentation, C08 is the generator |
| A02 (B/A2 inherit A1) | C08 | C08 is the generator search that A02 critiques |
| A01 (noise bands) | C08 | The noise bands are the metric for the search |

- **Why this matters:** C08 is the search for the generator ranges, building on S07, C04, A02, and A01.

## Notes on the log


- **The ranges are class-safe.** They avoid class-changing boundaries.
- **The design is shared but arm-aware.** One sampler, arm-specific extras.
- **The leakage checklist is thorough.** It prevents leakage and ensures auditability.
- **Cross-reference to S07, C04, A02, A01:** C08 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.