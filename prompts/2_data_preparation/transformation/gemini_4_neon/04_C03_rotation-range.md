## 

# 2_data_preparation/transformation - C03: Rotation range

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Gemini 4 Neon (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../claude_opus/04_C03_rotation-range.md`
- Date: 2026-11-09
- Entry: C03 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40211352 / 40211352
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c03), `results/llm_comparison/attribution_worksheet.csv` (C03), `docs/crisp_dm/iteration_2/search/phase_ablation.json`, `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c

## Prompt

> I want to change the rotation augmentation from ±180° for every class. Full rotation seems to remove the orientation clue that separates square from diamond and rectangle from its rotated forms. How should the config express a tighter limit for some classes, what values should the validation search try, and how do I make sure the cap really reaches the transform?

## Response

Here is a plan in three parts: config, search, verification.

### 1. Config

- Keep `augment.rotate_deg` as the default for all classes.
- Add a per-class override map, for example `rotate_limit_deg`, listing only the classes that need it. An empty map means the old behaviour.
- Validate the map at load time: every key must be a class in the taxonomy, every value must be a number of degrees from 0 to 180. A typo like "diamonds" should fail loudly, not silently leave diamond uncapped.

### 2. Search values

- Global: coarse at the large end, fine at the small end, since the interesting region is probably under 30°. For example 0, 5, 10, 15, 20, 30, 45, 90, 180.
- Cap: none, 0, 5, 10, 15, 30, applied to square, rectangle and diamond together.
- Sample both in the same random trial rather than in two stages, because the best cap depends on the global range.
- Confirm the top candidates with three seeds before picking one.

### 3. Verification

- Unit test the effective angle: with global 180 and cap 10, a square's sampled angle must stay within ±10 and a hexagon's must not.
- Add a studio or notebook view that runs one real training square through the transform with the cap on and off. People reviewing the change will trust a picture faster than a number.
- Log the effective cap per class in the run's saved config, so a result can always be traced back to the setting that produced it.

### Things that can go wrong

- Interaction with shear: a strong shear on a square also produces a rhombus. If the cap helps but diamond is still confused, look at shear next.
- Leakage: the search loop must load only train and val data. Never choose the cap from test-set per-class scores, even "just to check".
- Over-reading small gaps: on our validation size, a fraction of a point between two settings is within seed noise.
- Source effects: if upright squares come mostly from one source, part of what the cap preserves is a source style. Note that in the report rather than claim pure geometry.

## Validation

Caught by test (worksheet). A1 ablation, three seeds each (`phase_ablation.json`): 0° 89.38, ±15° 93.62, ±45° 89.91, ±90° 90.58, ±180° 90.64 validation macro-F1. Square 93.9 -> 90.3, rectangle 87.8 -> 82.3, diamond 96.1 -> 86.9 from ±15° to ±180°.

## Our decision

±180° -> ±20°, capped at ±10° for square, rectangle and diamond (`taxonomy.rotate_limit_deg` in `winners.json`). Grid from `ROTATIONS` and `ROTATION_CAPS` in `search.py`; cap applied in `build_transform`.

## Measured effect

A1 winner: 94.77 mean validation macro-F1 over three seeds. No isolated effect of this change is recorded.

## Deeper detail: why the cap is the right fix

### The config expresses the cap cleanly

| Element | What it does | Why it's clean |
|---|---|---|
| `augment.rotate_deg` | Default for all classes | Simple |
| `rotate_limit_deg` | Per-class override map | Targeted |
| Load-time validation | Fails loudly on typos | Fail-closed |

- **Why the config is clean:** it separates the default from the override.
- **Why load-time validation matters:** it prevents silent failures.
- **Why this is a good design:** it's fail-closed.

### The search is two-dimensional

| Dimension | What it searches | Why |
|---|---|---|
| Global range | 0 to 180° | Finds the best overall |
| Per-class cap | none to 30° for 3 classes | Protects the angle-dependent classes |

- **Why two dimensions:** the global range and the per-class cap are separate.
- **Why sampled together:** the best cap depends on the global range.
- **Why this is a good design:** it's joint.

### The verification is thorough

| Check | What it does | Why |
|---|---|---|
| Unit test effective angle | Confirms the cap reaches the transform | Prevents silent failure |
| Studio/notebook view | Shows the cap visually | Builds trust |
| Log effective cap | Traces result to setting | Auditability |

- **Why these checks matter:** they verify the cap actually works.
- **Why this is a good design:** it's thorough.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F07 (rotation hurts classes) | C03 | F07 is the finding, C03 is the fix |
| S07 (class definitions) | C03 | The class definitions are why the cap is needed |
| C04 (other augmentation) | C03 | Shear is a related risk |
| A01 (noise bands) | C03 | The noise bands are the metric for the fix |

- **Why this matters:** C03 is the fix for F07, building on S07, C04, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The config expresses the cap cleanly.** It separates default from override.
- **The search is two-dimensional.** Global range + per-class cap.
- **The verification is thorough.** Unit test + visual + logging.
- **Cross-reference to F07, S07, C04, A01:** C03 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.