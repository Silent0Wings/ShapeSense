# 3_modeling - Schema of the training flow and loss function

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C09, C29
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [C09](../../3_modeling/claude_opus/20_C09_cnn-depth.md)

## Prompt (10:15)

> describe a schema for our trianing flow what we use to train what loss funciton and other

## Response

I'll read the training code and configs in the repo, then write up the flow with the actual model, loss and settings it uses.

The core loop is clear. I still need the class list, how each arm's settings get applied, the baselines and the iteration 2 search.

This is the training flow as the code and [configs/pipeline.yaml](configs/pipeline.yaml) define it. I read the code but did not run a training job.

## Flow

```
data_set/unified + configs/splits/{train,val}.csv     (test is refused by ImageStore)
        │  uint8 64×64 grayscale, black outline on white, held in memory
        ▼
BatchStream: 256 images per step, 49 steps per epoch
  real images (class-balanced, with replacement)
  + augmentation (Stage 2, by arm)
  + synthetic shapes (Stage 3, by arm)
  → float32 (N,1,64,64) in [0,1], no mean/std normalization
        ▼
SmallCNN → 10 logits
        ▼
Cross-entropy → AdamW step → cosine LR step (per batch)
        ▼
After each epoch: score validation → macro-F1
  best so far: keep the weights
  5 epochs with no improvement: stop (max 30 epochs)
        ▼
artifacts/stage4/<arm>_<seed>/
  model.pt (TorchScript, best epoch), val_probs.npz, train_log.csv, val_curve.png, run.json
```

## Model
Each of the 4 blocks is Conv 3×3 (padding 1), BatchNorm, ReLU, then MaxPool 2.

| Layer | Output shape |
|---|---|
| Input | 1×64×64 |
| Block 1 | 32×32×32 |
| Block 2 | 64×16×16 |
| Block 3 | 128×8×8 |
| Block 4 | 128×4×4 |
| Global average pool | 128 |
| Dropout, Linear | 10 logits |

The model has about 242k parameters and a 46-pixel receptive field. The 10 classes are circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star and diamond.

## Training settings

| Setting | Value |
|---|---|
| Loss | Softmax cross-entropy, with no label smoothing or class weights |
| Class imbalance | Handled by balanced sampling |
| Optimizer | AdamW, weight decay 0.0001 |
| Learning rate | 0.003 |
| Dropout | 0.2 (0.4 for A0) |
| LR schedule | Cosine annealing over 1,470 steps (30 × 49), with no restarts or warmup |
| Batch size | 256 |
| Step budget | 49 per epoch, frozen from `ceil(12405 / 256)`, same for every arm |
| Model selection | Highest validation macro-F1, ties keep the earlier epoch |
| Seeds | 0 to 4 per arm, so 20 CNN runs in total |
| Hardware | CUDA, 2 runs in parallel, deterministic mode on |

Gradient clipping and mixed precision are not used. An early-stopped run never reaches the end of the cosine schedule.

## Arms
All arms use the same architecture, optimizer, schedule and step budget. Only the batch contents and the tuned settings differ.

| Arm | Clean real | Augmented real | Synthetic (augmented) |
|---|---|---|---|
| A0 (control) | 256 | 0 | 0 |
| A1 | 0 | 256 | 0 |
| B | 0 | 185 | 71 |
| A2 | 105 | 100 | 51 |

The tuned augmentation for A1, B and A2 is:
- Rotation up to ±20°, capped at ±10° for square, rectangle and diamond.
- Scale from 0.904 to 1.076.
- Noise with probability 0.385 and blur with probability 0.373.
- Shear and non-uniform scaling, which are skipped for circle, ellipse, square, rectangle and diamond.

## Order of a Stage 4 run
1. Train the baselines: logistic regression on pixels and a linear SVM on HOG features, with 600 real images per class.
2. Run the loader benchmark.
3. Load the tuned settings. Iteration 2 takes them from `src/stage4_train/search.py`, which uses validation data only.
4. Train the arm × seed sweep. Finished runs are reused only if their recipe hash matches.
5. Compute seed disagreement, and check that the test split was never read.

The leave-one-source-out runs only happen if Stage 1's shortcut check fired.

## Stale text to avoid copying into the report
- [model.py:31](src/stage4_train/model.py#L31) still says 3 blocks, but the config uses 4.
- [run.py:62](src/stage4_train/run.py#L62) and the `batch_composition` docstring in [sampling.py](src/stage4_train/sampling.py) still describe a 30% synthetic share (179 + 77). B actually uses 27.8% and A2 uses 19.8%.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Opus 5.5 read the code and configs/pipeline.yaml and ran no training. The schema was checked against the config.

## Our decision

Used as the reference description of training in the report and the dashboard (C48).

## Measured effect

A description only, with no macro F1 change.

---

## End-to-End Stage 4 Execution & Optimization Specification (`C09`, `C29`)

### Metadata & Lineage

* **Entries:** `C09` (*4-block `SmallCNN` depth upgrade*), `C29` (*Training budget evolution*)
* **Date:** `2026-11-09` (10:15 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)

### Formal Stage 4 Computational Graph & Hyperparameter Contract

1. **Input Ingestion & Normalization:** `ImageStore` loads standardized `uint8` `64 × 64` grayscale tensors (black ink on white background) into RAM from `configs/splits/{train,val}.csv` while explicitly refusing `"test"`. `BatchStream` yields `float32` tensors of shape `(256, 1, 64, 64)` scaled to `[0.0, 1.0]` **without dataset mean/std standardization**.
2. **Architecture (`SmallCNN`, `242,250` params, `46 px` RF):** Four sequential `Conv2d(3×3, pad=1) → BatchNorm2d → ReLU → MaxPool2d(2)` stages (`1×64×64 → 32×32×32 → 64×16×16 → 128×8×8 → 128×4×4`), followed by `AdaptiveAvgPool2d(1) → Dropout(p) → Linear(128, 10)`.
3. **Objective & Optimization:** Unweighted softmax cross-entropy loss (no label smoothing; class imbalance is neutralized upstream via uniform class-balanced sampling), optimized with **AdamW** (`lr = 0.003`, `weight_decay = 1e-4`), single-cycle **cosine annealing** over `49 steps/epoch` (`ceil(12405 / 256)`), `dropout = 0.2` (`0.4` for `A0` in Iteration 2), deterministic CUDA kernels enabled, and **zero mixed precision or gradient clipping**.
4. **Class-Safe Augmentation Policy (`A1`, `B`, `A2`):** Uniform rotation $\pm 20^\circ$ (restricted to $\pm 10^\circ$ for rotationally ambiguous `square`, `rectangle`, `diamond`), isotropic scale `[0.904, 1.076]`, Gaussian noise ($p = 0.385$), blur ($p = 0.373$), and affine shear / anisotropic scaling **strictly disabled** for symmetry-sensitive classes (`circle`, `ellipse`, `square`, `rectangle`, `diamond`).
5. **Documentation Hygiene Audit:** Flagged two stale code comments (`model.py:31` still citing 3 blocks; `run.py:62` and `sampling.py` docstrings citing `30%` / `77` synthetic images instead of Iteration 2's tuned `27.8%` / `71` for `B` and `19.8%` / `51` for `A2`) so report authors would not transcribe obsolete constants.

