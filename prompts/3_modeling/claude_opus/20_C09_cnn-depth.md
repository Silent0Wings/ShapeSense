# 3_modeling - C09: CNN depth 

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [41_real_training-flow-and-loss-function-schema.md](41_real_training-flow-and-loss-function-schema.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: C09 (`change`, `3_modeling`)
- Owner / Proposed by: 40248536 + 40253714 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: `results/llm_comparison/attribution_worksheet.csv`, `results/phase2_snapshot/iteration_log.json`, `prompts/3_modeling/inferred_prompts.md`, `src/stage4_train/model.py`, `configs/pipeline.yaml`, `results/phase2_snapshot/loader_benchmark.json`, `tests/stage4/test_model.py`, `tests/studio/test_architecture_recipes.py`, commits 62c5fe8, 8984a50
- ** from repo, not a saved chat:** No export of the original Claude Opus chat exists. The user prompt and the response below are written from the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

Our Stage 4 network is the Decision 8 `SmallCNN`: three blocks of Conv 3x3 (pad 1), BatchNorm, ReLU and MaxPool 2, channels 32 / 64 / 128, then global average pooling, Dropout and one Linear layer. Someone worked out that it has only a 22-px receptive field on our 64-px images. Is that a real problem? What depth and channel widths would let it see a whole shape while staying small, and how do we check the receptive field after the change?

## Response

Yes, it is a real problem for this task, and one more block fixes it cheaply.

### Checking the 22 px

For stacked 3x3 convolutions (stride 1) and 2x2 max pools (stride 2), the receptive field grows by 2 x jump per conv and by 1 x jump per pool, and the jump doubles after each pool:

| After | Receptive field | Map size |
|---|---|---|
| block 1 | 4 px | 32x32 |
| block 2 | 10 px | 16x16 |
| block 3 | 22 px | 8x8 |
| block 4 | 46 px | 4x4 |

So the 22 px is right. Standardized shapes are large in the frame: a typical outline spans about 55 px of the 64-px image (the figure used in the F17 entry of `iteration_log.json`). No unit before global pooling sees more than 22 px of a shape that spans most of 64 px. Global average pooling then averages local corner and edge detectors, but no unit can compare two opposite sides. That is exactly the information square vs rectangle (aspect ratio) and hexagon vs octagon (counting corners around the outline) need.

### Options

| Option | Receptive field | Cost |
|---|---|---|
| 4 blocks, 32 / 64 / 128 / 128 | 46 px | 242,250 parameters |
| 4 blocks, 32 / 64 / 128 / 256 | 46 px | about 391k parameters |
| Dilated convs or a 5x5 first layer | Larger, with 3 blocks | Changes the Decision 8 block design |

**Recommendation: four blocks, 32 / 64 / 128 / 128.** It keeps the same block (Conv-BN-ReLU-MaxPool), reaches 46 px, which covers most of a typical shape, and leaves a 4x4 map for global pooling. Holding the last block at 128 instead of doubling to 256 keeps the model small: every arm and seed trains this network, so parameter count multiplies across the whole experiment. Make it a config change only (`train.channels`), since `SmallCNN` already builds one block per entry.

**Fairness.** Change the network before any arm is trained, for all arms at once. It is part of the shared architecture, not something to tune per arm.

### Checking it

1. A test that computes the receptive field from the real module list and asserts 46 px for the last block.
2. A test that the documented diagram matches the real forward shapes and the parameter count.
3. Update the comments in `configs/pipeline.yaml` so the next reader sees why there are four entries.

## Validation

- `configs/pipeline.yaml`: `channels: [32, 64, 128, 128]   # 4 blocks: 46-px receptive field (P-54; Decision 8 had 3)`.
- `tests/studio/test_architecture_recipes.py`: `test_the_last_convolution_block_sees_the_documented_area` asserts `sees == 46`; `test_the_diagram_matches_the_real_model` checks the model.
- `loader_benchmark.json` records `n_params: 242250`.
- `tests/stage4/test_model.py` still checks a three-block fixture (`CHANNELS = (32, 64, 128)`, "about 100k parameters") for the unit-level shape and TorchScript tests.

## Our decision

CNN depth: three blocks, 22-px receptive field -> four blocks, 46-px receptive field. The network could not see a whole shape (F17).

## Measured effect

Receptive field 22 px -> 46 px on 64-px images (F17 entry, `iteration_log.json`), at 242,250 parameters. No separate accuracy comparison of three against four blocks is recorded.

## Deeper detail: why the receptive field matters

### The receptive field determines what the network can see

| Blocks | Receptive field | Can see whole shape? |
|---|---|---|
| 3 | 22 px | No |
| 4 | 46 px | Yes |

- **Why the receptive field matters:** it determines what the network can see.
- **Why 22 px is too small:** it can't see a whole 64-px shape.
- **Why 46 px is enough:** it can.
- **Why this is a good fix:** it's a real design improvement.

### The options are clear

| Option | Receptive field | Cost | Verdict |
|---|---|---|---|
| 4 blocks, 128 last | 46 px | 242k | Adopt |
| 4 blocks, 256 last | 46 px | 391k | Reject (too big) |
| Dilated/5x5 | Larger, 3 blocks | Changes design | Reject |

- **Why 4 blocks, 128 last:** it's the right balance.
- **Why 256 last is rejected:** it's too big for the whole experiment.
- **Why dilated/5x5 is rejected:** it changes the design.
- **Why this is a good choice:** it's balanced.

### The checks are thorough

| Check | What it does | Why |
|---|---|---|
| Receptive field test | Asserts 46 px | Confirms the fix |
| Diagram match test | Checks the model | Confirms correctness |
| Config comment | Explains why 4 entries | Documents |

- **Why these checks matter:** they verify the fix and document it.
- **Why this is a good design:** it's thorough.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F17 (receptive field too small) | C09 | F17 is the finding, C09 is the fix |
| T09 (add loader, baselines, CNN) | C09 | T09 is the task that includes C09 |
| D03 (final network) | C09 | D03 is the result |

- **Why this matters:** C09 is the fix for F17, part of T09, and D03 is the result.

## Notes on the log

- **This is a reconstruction, not the original chat.** The prompt and response are written from the repo.
- **The receptive field matters.** 22 px is too small.
- **The options are clear.** 4 blocks, 128 last is the right balance.
- **The checks are thorough.** They verify and document.
- **Cross-reference to F17, T09, D03:** C09 builds on all three.

