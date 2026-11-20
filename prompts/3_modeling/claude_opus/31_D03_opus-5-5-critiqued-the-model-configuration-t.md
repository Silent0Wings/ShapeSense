# 3_modeling - D03: Opus 5.5 critiqued the model configuration: the network depth, the choice of layers and the activation function 

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/20_D03_opus-5-5-critiqued-the-model.md](../gemini_4_neon/20_D03_opus-5-5-critiqued-the-model.md)
- Date: 2026-11-08
- Worksheet entry: D03 (`decision`, `3_modeling`)
- Owner / Proposed by: 40297573 / 40297573
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: `src/stage4_train/model.py`, `configs/pipeline.yaml`, `studio/data/architecture.py`, `docs/crisp_dm/iteration_log.json` (`F17`), `results/phase2_snapshot/loader_benchmark.json`, `tests/stage4/test_model.py`, `tests/studio/test_architecture_recipes.py`, `ShapeSense_Deployed/web/stage4.html`, commits `62c5fe8` & `8984a50`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Critique our Stage 4 `SmallCNN` configuration for 64x64 grayscale shapes: 3 blocks of `Conv 3x3 -> BatchNorm -> ReLU -> MaxPool 2` with channels `[32, 64, 128]`, global average pooling, dropout, and a single linear layer. What would you change and why?

## Response ()

> **Opus 5.5:** The layer block, activation, and head design are sound, but **3 blocks is too shallow for 64x64 global shape geometry**:
>
> - **Network depth (main weakness)**: Three `Conv 3x3 (pad 1) -> MaxPool 2` blocks shrink `64x64` to `8x8` with only a **22-px receptive field**. Since standardized shapes span roughly `55` px, no neuron before global average pooling can see an entire shape at once-making global aspect ratios (`square` vs `rectangle`) and full symmetry harder to separate. Add a **4th conv block** so the final max-pool reaches a **46-px receptive field** on a `4x4` map.
> - **Channel widths**: For the 4th block, standard VGG-style doubling suggests **`[32, 64, 128, 256]`** (~391k parameters) to keep representational capacity scaling as spatial resolution halves to `4x4`, though capping the 4th block at `128` is a reasonable lighter fallback if you want to keep parameters closer to ~240k.
> - **Block layers & activation**: Keep `Conv 3x3 (pad 1) -> BatchNorm2d -> ReLU -> MaxPool2d(2)`. ReLU with BatchNorm trains reliably under AdamW + cosine decay on sparse black-on-white strokes without needing GELU/SiLU complexity.
> - **Head**: Keep `AdaptiveAvgPool2d(1)` -> `Dropout` -> `Linear(C, 10)`. Flattening `4x4` into a dense MLP would blow up parameters and add shift sensitivity before global pooling.
>
> | Component | Critique | Recommendation |
> |---|---|---|
> | Depth | 3 blocks see only `22` px of a ~`55`-px shape | **Move to 4 blocks (`46`-px receptive field)** |
> | Block channels | Doubling across 4 stages gives `[32, 64, 128, 256]` | Start with `[32, 64, 128, 256]` (or cap block 4 at `128`) |
> | Layer stack & activation | `Conv 3x3 -> BN -> ReLU -> MaxPool 2` is clean and fast | **Keep unchanged** |
> | Classification head | GAP + Dropout + Linear keeps classifier lightweight | **Keep unchanged** |

## Why this reading fits

Opus 5.5's critique pinpoints the exact receptive-field bottleneck documented later in `F17` (`22` px vs `46` px on ~`55`-px shapes in a `64x64` frame) and correctly validates `Conv-BN-ReLU-MaxPool` plus GAP/Dropout/Linear. Its initial VGG-style instinct to double Block 4 to `256` channels (`[32, 64, 128, 256]`) was realistic for a first pass, and the team refined that width down to `128` (`[32, 64, 128, 128]`, `242,250` parameters) to stay lightweight across 5 arms x 5 seeds plus hold-out runs.

## Validation

Updating `configs/pipeline.yaml#train.channels` to `[32, 64, 128, 128]` was verified by `tests/studio/test_architecture_recipes.py` (`test_the_last_convolution_block_sees_the_documented_area` confirms `sees == 46` and `test_the_diagram_matches_the_real_model` confirms forward shapes and `242,250` parameters) and recorded in `phase2_report.tex` (commit `8984a50`). (Note: `tests/stage4/test_model.py` retains the local `CHANNELS = (32, 64, 128)` fixture from `62c5fe8` for unit-level TorchScript checks.)

## Our decision

Moved from 3 blocks (`[32, 64, 128]`, ~94k parameters, `22`-px receptive field) to **4 blocks with channels `[32, 64, 128, 128]`** (`242,250` parameters, `46`-px receptive field), keeping `Conv 3x3 (pad 1) -> BatchNorm -> ReLU -> MaxPool 2`, global average pooling, `Dropout`, and one `Linear` layer (`src/stage4_train/model.py`, `configs/pipeline.yaml`).

## Measured effect

The 4-block `[32, 64, 128, 128]` `SmallCNN` expanded the pre-GAP receptive field from `22` px to `46` px (`F17`, `C09`) at `242,250` parameters, trained smoothly on a single RTX 3080 (`2,218` img/s measured on heaviest stream `B` in `loader_benchmark.json`), and reached `98.3` clean macro-F1 on `fresh_holdout_2` and `82.84` 23-level damaged mean macro-F1 for `A2` (`+9.20` points over `A0`, 95% CI `[8.89, 9.53]`).

---

## Receptive-Field Geometry & `SmallCNN` Depth Upgrade (`D03`)

### Metadata & Lineage

* **Entry ID / Type:** `D03` (`decision`, `3_modeling` — Two-LLM comparison with `gemini_4_neon`)
* **Date:** `2026-11-08`
* **Owner / Proposed By:** `40297573` / `40297573` (`calibration: close-to-reality`, 30% tier)
* **Linked Entries:** `F17`, `C09`
* **Primary Artifacts:** `src/stage4_train/model.py`, `configs/pipeline.yaml`, `studio/data/architecture.py`, `tests/studio/test_architecture_recipes.py`, commits `62c5fe8`, `8984a50`

### Receptive-Field Calculation & Architectural Trade-Offs

Standardized input shapes span `~55 px` inside a `64 × 64` grayscale canvas. Evaluating the receptive field $r_l$ across sequential `Conv 3x3 (stride 1, pad 1)` $\rightarrow$ `MaxPool 2x2 (stride 2)` stages ($r_l = r_{l-1} + (k_l - 1) \cdot j_{l-1}$, where jump $j_l = 2^l$):

| Stage / Block | Output Spatial Map | Cumulative Jump ($j_l$) | Receptive Field After `Conv 3x3` | Receptive Field After `MaxPool 2x2` | Coverage of `~55 px` Shape |
| --- | --- | --- | --- | --- | --- |
| **Block 1** (`32` ch) | `32 × 32` | `2` | `3 × 3` px | `4 × 4` px | Local stroke edge |
| **Block 2** (`64` ch) | `16 × 16` | `4` | `8 × 8` px | `10 × 10` px | Corner / vertex junction |
| **Block 3** (`128` ch) | `8 × 8` | `8` | `18 × 18` px | **`22 × 22` px** | **Only `40%` of shape span** (Iter 1 bottleneck) |
| **Block 4** (`128` ch) | `4 × 4` | `16` | `38 × 38` px | **`46 × 46` px** | **`84%` global span** (enables aspect-ratio & symmetry discrimination) |

#### Design Synthesis

* **Why 3 Blocks Failed Global Geometry (`22 px` RF):** Before `AdaptiveAvgPool2d(1)` collapsed spatial dimensions, no convolutional neuron in the 3-block `[32, 64, 128]` (`~94k` params) network could simultaneously observe opposite edges of a `~55 px` shape, impairing global aspect-ratio (`square` vs. `rectangle`) and rotational symmetry discrimination.
* **Channel Capping (`[32, 64, 128, 128]` vs. `[32, 64, 128, 256]`):** Adding Block 4 expanded the pre-GAP receptive field to **`46 × 46` px**. Rather than VGG-style doubling to `256` channels (`~391k` params), the team capped Block 4 at `128` channels (`242,250` parameters), preserving high throughput (`2,218 img/s` on RTX 3080 for stream `B`) across 25+ multi-seed runs while achieving `98.3` macro-F1 on clean `fresh_holdout_2` and `+9.20` macro-F1 over `A0` on 23-level damaged images.

