# ShapeSense Studio

An interactive dashboard for the finished pipeline. The home page shows the CRISP-DM cycle, each stage has its own page with a live example, and the live page scores a shape you draw.

It runs on your computer only (`127.0.0.1`), loads no external files, and uses the real pipeline code for every preview.

## Run it

Double-click `scripts\run_studio.bat`, or from Windows PowerShell at the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m studio.tools.export_arms   # once, exports every arm for comparison
python -m studio
```

Open <http://127.0.0.1:8765>. It needs a finished pipeline (`python run_pipeline.py`) and the virtual environment from the main `README.md`. FastAPI and uvicorn come with Gradio, so there is nothing extra to install.

## Pages

| Page | CRISP-DM step | Try this |
|---|---|---|
| Home | The whole cycle | Open a step, or draw a shape |
| Business understanding | Business Understanding | Change the success rule in the what-if panel |
| Iteration 1 and 2 results | Evaluation | Read each frozen verdict |
| Failure timeline | Every step | Open a failure for its own page and visual |
| Changes by CRISP-DM step | Every step | See what changed, before and after |
| Robustness check | Evaluation | Compare arms on damaged validation images |
| Stage 0 | Foundations | Browse the hash cache by stage |
| Stage 1 | Data Understanding, Preparation | Browse classes, near-duplicates, the diamond evidence |
| Stage 2 | Data Preparation | Pick a class, compare original and augmented, move the sliders |
| Stage 3 | Data Preparation | Resample the generator, inspect drawn parameters |
| Stage 4 | Modeling | Scrub the training curves, compare runs |
| Stage 5 | Evaluation | Hover or select confusion-matrix cells |
| Stage 6 | Deployment | Open the report and the bundle details |
| Draw and predict | Deployment | Compare every arm on your own drawing, and save a wrong prediction |

## How it stays honest

- **The test split stays sealed.** The server never opens the test manifest or the old `test/` image folder. Browsing is limited to train and val, chosen through the manifests. `tests/studio/test_no_test_split_read.py` watches every file opened while each endpoint is called.
- **Evaluation shows stored results only.** Confusion counts and error images come from what Stage 5 saved, and images are limited to the three confusable pairs the report shows.
- **Nothing frozen changes.** The studio writes only to `studio/out/` and to `studio/feedback/` for saved drawings. `.importlinter` limits what it can import, and it does not touch `src/`, `configs/` or any stage's artifacts.
- **The what-if panel is a what-if.** It re-applies the rule to stored results and saves nothing.
- **Live results are informal.** The live arms are single best-validation seeds, while the verdicts use multi-seed ensembles.

## Layout

| Folder | Job |
|---|---|
| `server/` | Routes, request limits, local-only rules |
| `ops/` | Live calls to the real Stage 2 and Stage 3 code |
| `data/` | Read allow-listed results and build page bundles |
| `inference/` | Decode a drawing, standardize it, score it with ONNX |
| `tools/` | One-shot ONNX export of every arm (the only part that needs PyTorch) |
| `web/` | Static pages, styles and JavaScript, with no build step |

`allowlist.py` is the complete list of files the studio can read.

## Tests

```powershell
python -m pytest tests/studio -q
```
