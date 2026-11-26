## Expanded entry

# 2_data_preparation/transformation - T07: Add class-safe augmentation and QA sheet



- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T07 (`built`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40253714 / 40253714
- LLM role: assisted
- Grounding sources: `results/llm_comparison/commit_tasks.csv` (T07), `stages/stage_2.md`, `src/stage2_augment/transform.py`, `src/stage2_augment/qa.py`, `src/stage2_augment/run.py`, `configs/taxonomy.yaml`, `tests/stage2/test_transform_internals.py`, commit c9f5ce3

## Prompt

> I am building Stage 2: `transform(img, label, rng)` for 64x64 black-on-white outlines, applied on the fly during training. The brief says shear and non-uniform scale must be off for circle, ellipse, square, rectangle and diamond, the list must come from `configs/taxonomy.yaml`, and all randomness must come from `rng`. I also need a QA sheet so a person can check that no augmentation changes the class. How should I structure this?

## Response

The main risk in this stage is a silent label flip: the function returns a valid image, the label stays the same, and the image now shows a different class. Shear turns a square into a parallelogram or a diamond, and non-uniform scale turns a circle into an ellipse. So "class-safe" should be enforced by construction, then checked by tests and by eye.

### Structure

- `build_transform(config)` reads `config["augment"]` and `config["taxonomy"]` once and returns the function. Build the no-shear set from `no_shear_no_nonuniform_scale` by class name, so editing the YAML changes behaviour with no code edit (Stage 2 "Done when").
- Inside, for disabled labels set the shear and stretch ranges to 0, but still draw them from `rng`. Keeping the draw order fixed for every label means one seed always gives the same image (R5).
- Warp a float ink map, then re-threshold so the output is only 0 or 255. Bilinear interpolation leaves grey pixels, which the brief lists as a pitfall.
- Keep the shape inside the frame: shrink and re-render until the outer 1-px ring is empty, with a bounded number of steps.
- Raise `ValueError` for unknown labels and wrongly shaped images.

### QA sheet

One row per class, original and augmented images side by side with different frame colours, so a reviewer compares each pair directly. Use matplotlib's Agg canvas, not pyplot, so no global backend state leaks into tests.

### Tests worth writing

- For disabled classes, the linear part is a pure rotation (mock the draw, check the matrix).
- A rotated rectangle keeps its side ratio, and disabled classes stay on their side of the taxonomy margins.
- The disable list is read from config: change it in a test config, and behaviour changes.
- No use of the global `random` or `np.random` state.
- Thin outlines survive noise and blur.

### Cautions

- Rotation is not class-safe for every class in this dataset. A 45° square is still a square by the taxonomy, but a model may lean on orientation to separate square from diamond. Keep the rotation range a setting, so it can be searched.
- Augment training images only. Validation and test stay untouched.
- The QA sheet is a human check, not a test. Record its verdict in `status.json`.

## Validation

- Commit c9f5ce3, status built (`results/llm_comparison/commit_tasks.csv`). The code and tests described are the versions in the repo now, which also include later iteration 2 changes.
- Tests present: `test_disabled_linear_part_is_pure_rotation`, `test_rotated_rectangle_ratio_preserved`, `test_disabled_classes_stay_on_their_side_of_the_margin`, `test_disable_list_read_from_config`, `test_no_global_rng`, `test_thin_outline_survives` (`tests/stage2/test_transform_internals.py`).
- `src/stage2_augment/qa.py` draws 5 original/augmented pairs per class row (`QA_COLS = 10`), while `stages/stage_2.md` describes "10 augmented samples per class". The sheet itself is not kept in the repo.

## Our decision

The team member built the stage, with Gemini assisting. Rotation stayed a setting. It was later capped per class (C03).

## Measured effect

No measured effect is recorded for this task. Rotation later turned out to hurt orientation-dependent classes (F07), which the class-safe rules alone did not prevent.

## Deeper detail: why class-safe by construction matters

### The main risk is a silent label flip

| Risk | What it does | Why it's silent |
|---|---|---|
| Shear on square | Turns it into parallelogram/diamond | Label stays same |
| Non-uniform scale on circle | Turns it into ellipse | Label stays same |

- **Why silent label flip is the main risk:** it's the worst kind of bug.
- **Why class-safe by construction matters:** it prevents the flip.
- **Why this is a good design:** it's fail-safe.

### The structure is config-driven

| Element | What it does | Why |
|---|---|---|
| `build_transform(config)` | Reads config once | Returns the function |
| `no_shear_no_nonuniform_scale` | From taxonomy.yaml | Config-driven |
| Fixed draw order | Same seed = same image | Deterministic (R5) |
| Re-threshold | 0 or 255 only | No grey pixels |
| Fit loop | Keeps shape in frame | Bounded steps |

- **Why config-driven matters:** editing YAML changes behaviour without code edit.
- **Why this is a good design:** it's flexible and safe.

### The tests are thorough

| Test | What it checks | Why |
|---|---|---|
| Pure rotation for disabled | Linear part is rotation only | Confirms the disable |
| Rectangle ratio preserved | Rotation keeps the ratio | Confirms correctness |
| Margin respected | Disabled classes stay in bounds | Confirms safety |
| Config-driven disable | Changing config changes behaviour | Confirms flexibility |
| No global rng | No global state | Confirms determinism |
| Thin outline survives | Noise/blur don't break it | Confirms robustness |

- **Why these tests matter:** they cover the main risks.
- **Why this is a good design:** it's thorough.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | T07 | The taxonomy is from S07 |
| R5 (seed determinism) | T07 | The fixed draw order is from R5 |
| F07 (rotation hurts classes) | T07 | Rotation stayed a setting, later capped |
| C03 (rotation cap) | T07 | C03 is the later fix |

- **Why this matters:** T07 is the foundation for the class-safe augmentation, building on S07, R5, F07, and C03.

## Notes on the log


- **Class-safe by construction matters.** It prevents silent label flips.
- **The structure is config-driven.** Editing YAML changes behaviour.
- **The tests are thorough.** They cover the main risks.
- **Cross-reference to S07, R5, F07, C03:** T07 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.