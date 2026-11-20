# 3_modeling - C48: Architecture and training diagrams 
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C48 (`change`, `3_modeling`)
- Owner / Proposed by: 40253714 + 40256377 / opus_medium_5.5 + 40253714 + 40256377
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md#c48, studio/data/architecture.py, studio/web/js/widgets/architecture.js, studio/web/js/pages/stage4.js, tests/studio/test_architecture_recipes.py, configs/pipeline.yaml, configs/models/A2.yaml, ShapeSense_Deployed/web/stage4.html, commits ff7ddbf, b39a942

> ** from repo, not a saved chat:** No export of the original Claude Opus chat exists. The user prompt and the response below are written from the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
On the Training page the network is just a table of layers, and how each model was trained is only in `configs/pipeline.yaml`. Readers do not get that all five models use the same network and differ only in their training images. How could we show the network, how a training run works, and what each model saw per batch, without the diagrams drifting from the real code?

## Response
The message the page has to land is one sentence: one network, five training diets. A layer table cannot say that. I would build three linked views on the Training page, all fed from one data builder that reads the config and the run list, never from numbers typed into JavaScript.

**1. The shared network.** Generate the list of operations from the config (`image_size`, image channels and `train.channels`): per block a 3x3 convolution with padding 1, BatchNorm, ReLU and a 2x2 max pool, then global average pooling, dropout and a linear layer. Draw each block as a stack of slabs, one slab per operation, shrinking as the image shrinks, and highlight the selected slab. Add Play, Previous and Next, and small worked examples where the reader can try a filter, a max pool and a global average pool on a tiny grid. For each operation show its output shape, its parameters and how much of the image it sees.

**2. How a training run works.** A clickable flow from the stored image index and the batch plan, through the pool of CPU workers that prepare batches (`prep_workers: 7` in the config), to the update step and the validation checkpoint. This answers "what does the machine actually do" in one picture.

**3. What each model saw.** One stacked bar per model showing a batch of 256 split into real unchanged, real augmented and synthetic images, computed by the same functions the trainer uses. P gets two bars, one for its synthetic pretraining epochs and one for the rest.

| Option | Readable | Stays correct |
|---|---|---|
| Keep the table, add prose | Partly | Only if prose is updated |
| Hand-drawn SVG | Yes | No, drifts with every config change |
| Generated from config and run list, with tests | Yes | Yes, tests fail if it drifts |

Recommendation: the third. Back it with tests against the real code: the sum of the diagram's parameters equals the PyTorch model's count, each block's output shape matches a forward pass, the last pool's receptive field matches the documented value, and the batch bars match the trainer's batch composition for every arm.

Cautions: keep the views on the Training page so the home page stays short, and label pretraining by epochs read from the config, not a typed number.

## Validation
`tests/studio/test_architecture_recipes.py` has four tests: the recipes match the real batch composition, only the pretraining arm has a pretraining phase, the diagram matches the real model, and the last convolution block sees the documented area (`pools[-1]["sees"] == 46`). `studio/data/architecture.py` provides `network()`, `recipes()` and `layers()`. `studio/web/js/widgets/architecture.js` exports `networkExplorer` (with Play and the "Try it: max pooling" and "Try it: global average pooling" examples), `systemExplorer`, `recipeBars` and `trainingFlow`, all mounted in `stage4.js` under cards such as "The network every model shares". Published on `ShapeSense_Deployed/web/stage4.html`.

## Our decision
Adopted: an interactive diagram of every operation in the shared network with worked pooling examples, a clickable view of the batch-preparation pool and training loop, and what each model saw per batch, read from the config and run list. Each slab in a block stands for one operation, and the selected one is highlighted. Built by 40253714 and 40256377.

## Measured effect
No separate measurement recorded. The diagram reads the shared network as recorded in `configs/models/A2.yaml`: block channels `[32, 64, 128, 128]`, 242,250 learned parameters, batch size 256, 49 steps per epoch, 60 epochs.

---

## Config-Driven Interactive Architecture & Training Visualization (`C48`)

### Metadata & Lineage

* **Entry ID / Type:** `C48` (`change`, `3_modeling`)
* **Date:** `2026-11-10`
* **Owner / Proposed By:** `40253714 + 40256377` / `opus_medium_5.5 + 40253714 + 40256377` (`proposed`)
* **Primary Artifacts:** `studio/data/architecture.py`, `studio/web/js/widgets/architecture.js`, `studio/web/js/pages/stage4.js`, `tests/studio/test_architecture_recipes.py`, `ShapeSense_Deployed/web/stage4.html`, commits `ff7ddbf`, `b39a942`

### Single-Source-of-Truth Visualization Engineering

To communicate the core experimental invariant—**"one shared CNN architecture, five distinct training diets"**—without static SVGs drifting from pipeline code, `studio/data/architecture.py` (`network()`, `recipes()`, `layers()`) dynamically computes all structural metadata directly from `configs/pipeline.yaml` and the trainer's batch composition functions:

1. **`networkExplorer` (Interactive Operation-Level Tensor Inspector):**
   * Renders each convolutional block as a proportional stack of operation slabs (`Conv 3x3 pad 1` $\rightarrow$ `BatchNorm2d` $\rightarrow$ `ReLU` $\rightarrow$ `MaxPool2d(2)`), followed by `AdaptiveAvgPool2d(1)`, `Dropout`, and `Linear`.
   * Dynamically computes exact output tensor dimensions, trainable parameter counts (`242,250` total), and cumulative receptive field (`46 × 46` px at Block 4 pool) alongside interactive numerical sandboxes (*Try it: max pooling* and *Try it: global average pooling*).
2. **`systemExplorer` & `trainingFlow` (Execution Topology):**
   * Visualizes the end-to-end runtime dataflow from indexed datasets and deterministic batch plans through the 7-worker CPU preparation pool (`prep_workers: 7`) into GPU gradient updates and epoch checkpoints.
3. **`recipeBars` (256-Image Batch Composition):**
   * Computes stacked batch distributions directly from the trainer's sampler for `A0`, `A1`, `B`, `A2`, and dual-phase bars for `P` (synthetic pretraining epochs vs. clean real fine-tuning epochs).

*Contract Enforcement (`tests/studio/test_architecture_recipes.py`):* Four automated tests assert parameter-count parity with the instantiated `PyTorch` module, forward-pass shape equivalence, receptive-field exactness (`pools[-1]["sees"] == 46`), and batch-mix parity across all arms.

