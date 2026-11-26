## 

# 2_data_preparation/transformation - C35: Augmentation and generator speed



- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C35 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40304911 / opus_medium_5.5 + 40304911
- LLM role: proposed
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv` (C35), `prompts/2_data_preparation/transformation/inferred_prompts.md` (C35), `src/stage2_augment/transform.py`, `tests/stage2/test_transform_internals.py`, `tests/stage2/test_outline_survival.py`, `stages/stage_3.md` (R8), commit 534643d

## Prompt

> Training with augmentation on is slow on the CPU side. The same stored images are augmented many times per run, and as far as I can tell `_augment` recomputes the ink positions and the thin-line check for every call. What can we cache per stored image, which morphology and array steps can be made faster, and how do we prove the output does not change?

## Response

The key observation is in your prompt: two of the per-call steps depend only on the stored image, not on the random draw. Those can be cached. Everything that uses `rng` must stay per call.

### 1. Cache the image facts

Ink pixel positions and the "is this a 1-px stroke" flag are pure functions of the pixels and the ink threshold. Wrap them in one function keyed on `(img.tobytes(), size, threshold)` with `functools.lru_cache`. Two details matter:

- Return read-only arrays (`setflags(write=False)`). A cached array that a caller mutates would corrupt every later call for that image, and that bug would not show up in a single test.
- Bound the cache. Synthetic images are new every call, so they will churn through it. A size in the tens of thousands keeps the real training images resident without unbounded memory. For synthetic images the cache gives nothing, so their speed rests on the generator itself, which has its own target (Stage 3 R8: at least 2,000 images/s single-threaded).

### 2. Cheaper thin-line check

A stroke is thin when no 2x2 block is all ink. That is the same as asking whether a 2x2 binary erosion leaves anything, but you can compute it with four shifted slices ANDed together, with no SciPy call.

### 3. Cheaper dilation for outline noise

The 1-px growth used to pick noise pixels near the outline is a full 3x3 dilation. Two passes of shifted slices, one along rows and one along columns, give exactly the same mask as a 3x3 structuring element.

### What not to touch

The draw order from `rng` must stay fixed, or the same seed gives a different image (Stage 2 R5). Do not cache anything that depends on rotation, scale, blur or noise.

### How to prove identical output

- Before the change, save augmented outputs for a fixed set of images, labels and seeds. After the change, assert they are byte-identical. Equal statistics are not enough.
- Add unit checks that the slice-based thin check and dilation equal the SciPy versions on random masks, including masks touching the frame edge.
- Record a before and after timing on the same machine, otherwise the speed-up is a claim.

### Caution

Identical output means this change needs no retraining and cannot shift any metric. If any metric moves after it, treat that as a bug.

## Validation

- `src/stage2_augment/transform.py` now has `_ink_facts` cached with `SHAPE_CACHE_SIZE = 20_000`, returning read-only positions, a thin check built from four 2x2 slices, and `_dilate_1px` built from shifted slices.
- The worksheet notes "Tests and reruns confirm identical output" (`results/llm_comparison/attribution_worksheet.csv`). The existing tests in `tests/stage2/` check seeds, framing and thin-outline survival. None of them compares `_ink_facts` or `_dilate_1px` with a SciPy reference directly.
- No before and after timing is recorded in the repo.

## Our decision

Caching and the slice-based steps were kept (commit 534643d). The random draw order was not changed.

## Measured effect

No accuracy metric is expected or recorded. Output identity is reported by tests and reruns. No speed-up figure is recorded.

## Deeper detail: why caching works

### The cache is keyed on image facts

| What's cached | Why it's cacheable | Why it's safe |
|---|---|---|
| Ink pixel positions | Pure function of pixels + threshold | Read-only arrays prevent mutation |
| Thin-line flag | Pure function of pixels + threshold | Same |

- **Why the cache is keyed on image facts:** they don't depend on the random draw.
- **Why read-only arrays matter:** a mutated cached array would corrupt later calls.
- **Why the cache is bounded:** synthetic images churn through it, so unbounded memory is a risk.

### The slice-based steps are faster

| Step | Old approach | New approach | Why faster |
|---|---|---|---|
| Thin-line check | SciPy 2x2 erosion | Four shifted slices ANDed | No SciPy call |
| 1-px dilation | Full 3x3 dilation | Two passes of shifted slices | Same mask, less work |

- **Why the slice-based steps are faster:** they avoid SciPy calls.
- **Why they're equivalent:** they produce the same mask.
- **Why this is a good design:** it's faster without changing output.

### The random draw order must stay fixed

- **Why the draw order must stay fixed:** the same seed must give the same image (Stage 2 R5).
- **Why nothing that depends on rng can be cached:** it would break the seed determinism.
- **Why this is a good design:** it's consistent with the determinism requirement.

### How to prove identical output

1. Save augmented outputs before the change.
2. Assert byte-identical after the change.
3. Add unit checks against SciPy reference.
4. Record before/after timing.

- **Why byte-identical is the bar:** equal statistics are not enough.
- **Why the unit checks matter:** they catch edge cases (masks touching the frame edge).
- **Why the timing matters:** otherwise the speed-up is just a claim.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| Stage 2 R5 (seed determinism) | C35 | The draw order must stay fixed |
| Stage 3 R8 (generator speed) | C35 | The generator has its own speed target |
| F09 (broken 1-px strokes) | C35 | The thin-line check is related |
| T35 (transform fix) | C35 | C35 is part of T35's three groups |

- **Why this matters:** C35 is a performance fix that preserves output identity, building on Stage 2 R5, Stage 3 R8, F09, and T35.

## Notes on the log


- **Caching works because the facts are pure functions.** They don't depend on the random draw.
- **The slice-based steps are faster without changing output.** They're equivalent.
- **The random draw order must stay fixed.** It's a determinism requirement.
- **Byte-identical is the bar for proof.** Equal statistics are not enough.
- **Cross-reference to Stage 2 R5, Stage 3 R8, F09, T35:** C35 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.