# ShapeSense export bundle

This folder is a self-contained copy of the best trained shape classifier.
It classifies a fresh image of any size and colour into one of the 10 shape
classes in `labels.json`. Nothing outside `export/` is needed to run it.

## Contents

| File | Kind | Purpose |
|---|---|---|
| `model.onnx` | generated | Trained CNN (ONNX, opset 17). Input `image` float32 `(N, 1, 64, 64)`, output `logits` `(N, 10)`. |
| `standardize.py` | generated | Verbatim copy of the training preprocessing (`src/stage1_freeze/standardize.py`). |
| `labels.json` | generated | Class names in model index order. |
| `model_card.json` | generated | Which run was exported, its validation macro-F1, and the input spec. |
| `predict.py` | maintained | `preprocess`, `predict_proba`, `predict`, `model_available`. Imports only numpy, Pillow, onnxruntime and `standardize.py`. |
| `README.md` | maintained | This file. |

Generated files are written by the Stage 6 export (`src/stage6_report/export.py`,
`build_bundle`). Do not edit them by hand. Regenerate them by rerunning the
export.

## Usage

Run from the repository root:

```python
from PIL import Image
from export import predict

img = Image.open("drawing.png")          # any size, RGB or RGBA
print(predict.predict(img))              # e.g. "hexagon"
print(predict.predict_proba(predict.preprocess(img)))   # {"circle": 0.04, ...}
```

`predict.preprocess(img)` returns the 64 x 64 uint8 image the model sees. It
raises `predict.Rejected` for a blank or contrast-free image, such as a single
dot.

The deployment demo (`python run_pipeline.py --demo`, which runs `demo/app.py`)
uses only this folder. It draws on a canvas, calls `predict_proba`, and shows
the top-3 classes and the 64 x 64 image.

If `model.onnx` is missing, `predict.model_available()` returns `False`, and
`predict_proba` raises `FileNotFoundError`. Run the Stage 6 export first.

## Preprocessing (train/serve consistency)

Every input goes through `standardize.py`, the same file that prepared the
training images. The steps are:

1. Alpha flattening: RGBA is composited onto white.
2. Foreground mask: the background colour is estimated from the border, and
   ink is any pixel far enough from it. Dark-on-light and light-on-dark both work.
3. Outlier gate: blank images and images too small to carry shape information
   are rejected.
4. Crop and letterbox: the shape is cropped to its bounding box with a margin,
   padded to a square (aspect ratio is kept), and resized to 64 x 64.
5. Outline redraw: every closed shape (solid, thick ring or hollow star) is
   redrawn as the same 2-px black outline on white. Open or dashed strokes keep
   their original strokes.

The model input is `uint8 / 255`, so white background is 1.0 and ink is 0.0.

Do not replace this with a plain `resize()`. A plain resize gives thick grey
strokes that the model never saw during training.

## Model selection

The exported model is the run with the highest validation macro-F1 among the
configured runs. The test split is never used for the choice. Ties go to the
earlier run in `configs/pipeline.yaml`. The selected run is recorded in
`model_card.json`.

The primary test measures same-source generalization: the images come from
the same sources as the training images. Accuracy numbers belong to the report,
which reads them from the Stage 5 artifacts. This README does not restate
them.

## Data and model credits

The training images come from four sources. Names, creators and links are from
the Phase 1 bibliography.

- **Quick, Draw!** — Google Creative Lab, *The Quick, Draw! Dataset*. License:
  CC BY 4.0. <https://github.com/googlecreativelab/quickdraw-dataset>
- **Geometric Shapes Mathematics** — reevald, Kaggle. License: CC0, public domain.
  <https://www.kaggle.com/datasets/reevald/geometric-shapes-mathematics>
- **2D geometric shapes dataset** — A. El Korchi, Mendeley Data, DOI
  10.17632/wzr2yv7r53.1. License: CC BY 4.0.
  <https://data.mendeley.com/datasets/wzr2yv7r53/1>
- **Hand-Drawn Shapes Dataset** — frobertpixto, GitHub. License: CC BY 4.0 (data),
  MIT (code).
  <https://github.com/frobertpixto/hand-drawn-shapes-dataset>

The Phase 1 report also lists other sources. They are not used for training and
are not part of this bundle.

Dataset preparation:

- **Standardization:** all images are converted to 64 x 64, single channel,
  uint8, with a 2-px black outline on white (see Preprocessing above).
- **Filtering:** all Quick, Draw! diamonds are excluded by rule, because most
  are not rhombi (CRISP-DM iteration 1). The count is in the Stage 1 status
  artifact and is not restated here.
- **Splitting:** images are split 70 / 15 / 15 into train, validation and
  test. Near-duplicate groups (perceptual hash, Hamming distance at most 2)
  never straddle two splits.

## Redistribution

This bundle redistributes **model weights** (`model.onnx`) and **code**
(`predict.py`, `standardize.py`, and the export and demo code). It contains
**no training images** and **no derived outlines** from the training data.

The license for the team's own code and model weights is a **team decision that
has not been made yet**. No license has been chosen for this bundle, so do not
treat it as licensed for reuse until the team decides. The source-dataset
licenses above apply to the data they cover.
