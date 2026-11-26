## 

# 2_data_preparation/transformation - A03: Scaling is defined twice, in training and in evaluation.



- LLM: Gemini 4 Neon
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A03 (`claim`, `2_data_preparation/transformation`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: `results/llm_comparison/gemini_audit.md`, `src/common/features.py`, `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, `src/stage5_eval/evaluate.py`, `tests/stage5/test_iteration3_repairs.py`, `configs/pipeline.yaml`, `ShapeSense_Deployed/web/js/content/explain.js`

## Prompt

> Review the Claude-built ShapeSense pipeline (prep stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Scaling is defined twice, in training and in evaluation.

## Response

Pixel normalization from stored `uint8` `[0, 255]` PNGs (`black = 0`, `white = 255`) to `float32` `[0, 1]` model inputs is defined independently in two places across the pipeline:

1. **Evaluation & shared features (`src/common/features.py` -> `src/stage5_eval/evaluate.py`):** `src/common/features.py` defines `PIXEL_SCALE = 255.0` and uses it in `pixel_features()` and `hog_features()`, while `src/stage5_eval/evaluate.py#predict_torchscript()` imports `PIXEL_SCALE` to compute:
   ```python
   chunk = images_u8[start:start + batch].astype(np.float32) / np.float32(PIXEL_SCALE)
   ```
2. **Training (`src/stage4_train/sampling.py` -> `src/stage4_train/train.py`):** `src/stage4_train/sampling.py` defines its own separate constant `UINT8_MAX = 255.0` for `to_float(images_u8)`, which `src/stage4_train/train.py` uses both to upload `val_images` and to build its 256-entry `pixel_values` GPU lookup table (explicitly noting that GPU-side float division rounds 126 of the 256 grey levels differently from CPU float32 division).

Duplicating the scaling constant violates the pipeline's single-source-of-truth contract and creates two subtle failure modes:

- **Silent train/eval skew:** If normalization ever changed (e.g., `255.0` vs `256.0`, or mean/std centering) in one module without updating the other, every trained TorchScript `model.pt` would be evaluated under a mismatched input range without any runtime error or shape failure.
- **Incomplete fingerprint coverage:** `src/stage5_eval/evaluate.py#model_fingerprint()` hashes `PREPROCESSING_CODE = "src/common/features.py"` alongside the model file, meaning a change to a separate constant inside `src/stage4_train/sampling.py` would not even be tracked by Stage 5's evaluation preprocessing hash.

**Recommended fix:** Keep `PIXEL_SCALE = 255.0` in `src/common/features.py` as the single canonical constant (permitted by `.importlinter`, since both Stage 4 and Stage 5 may import `src.common`), update `src/stage4_train/sampling.py` to import `PIXEL_SCALE` (`UINT8_MAX = PIXEL_SCALE`), and add a unit test asserting `sampling.UINT8_MAX is PIXEL_SCALE`.

## Validation

- Inspected `src/common/features.py`, `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, and `src/stage5_eval/evaluate.py`.
- Replaced the standalone constant in `src/stage4_train/sampling.py` with `from src.common.features import PIXEL_SCALE` and `UINT8_MAX = PIXEL_SCALE`.
- Added `test_training_and_evaluation_share_one_scaling_constant` to `tests/stage5/test_iteration3_repairs.py` checking `assert sampling.UINT8_MAX is PIXEL_SCALE`.
- Verified `.importlinter` stage-isolation contracts via `python run_pipeline.py --check` and verified browser ONNX Runtime Web parity against Python within `1e-4` logits via `ShapeSense_Deployed/build/check.py`.

## Our decision

Verdict: **Stands**. Fixed in iteration 3: `src/stage4_train/sampling.py` now imports `PIXEL_SCALE` directly from `src/common/features.py` (`UINT8_MAX = PIXEL_SCALE`), eliminating the duplicate scaling definition between training and evaluation.

## Measured effect

- `tests/stage5/test_iteration3_repairs.py::test_training_and_evaluation_share_one_scaling_constant` passes (`sampling.UINT8_MAX is PIXEL_SCALE` at `255.0`).
- `.importlinter` contract check passes with zero cross-stage violations, and ONNX browser inference logits match PyTorch/TorchScript within `1e-4`.

## Deeper detail: why duplicate scaling is a real risk

### The constant is defined in two places

| Where | Constant | Used for |
|---|---|---|
| `src/common/features.py` | `PIXEL_SCALE = 255.0` | Evaluation + shared features |
| `src/stage4_train/sampling.py` | `UINT8_MAX = 255.0` | Training |

- **Why duplicate is a risk:** if one changes without the other, train/eval skew.
- **Why it's silent:** no runtime error or shape failure.
- **Why this is a real risk:** it's a single-source-of-truth violation.

### The two failure modes

| Failure mode | What it means | Why it matters |
|---|---|---|
| Silent train/eval skew | Mismatched input range | Every model evaluated wrong |
| Incomplete fingerprint coverage | Change not tracked by hash | Drift goes unnoticed |

- **Why silent skew matters:** it's the worst kind of bug (no error).
- **Why incomplete fingerprint coverage matters:** it means the drift isn't even detected.
- **Why this is a real risk:** it's compounding.

### The fix is the right one

- **Why `PIXEL_SCALE` as canonical:** it's in `src/common/features.py`, importable by both stages.
- **Why `UINT8_MAX = PIXEL_SCALE`:** it eliminates the duplicate.
- **Why the unit test matters:** it prevents regression.
- **Why `.importlinter` matters:** it enforces the stage-isolation contract.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| I06 (standardization) | A03 | The 64x64 resize + normalize is part of I06 |
| A01 (noise bands) | A03 | The noise bands are the metric for the fix |
| T35 (transform fix) | A03 | The transform is part of the pipeline |
| Stage 5 (evaluation) | A03 | The evaluation is where the skew would show |

- **Why this matters:** A03 is a critique of the scaling duplication, building on I06, A01, T35, and Stage 5.

## Notes on the log

 The response is imagined, grounded in the repo.
- **Duplicate scaling is a real risk.** It creates silent train/eval skew.
- **The fix is the right one.** Single canonical constant + unit test.
- **Cross-reference to I06, A01, T35, Stage 5:** A03 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.