# 4_testing - Dashboard with one page per stage and live ONNX inference

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C19
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [C19](../../4_testing/claude_opus/39_C19_live-models-in-the-studio.md)

## Prompt (23:24)

> ok create a extensive dashboard , that shows each sstage as seperate page , with the main page showing the cucle we use cthe crisp dm steps , + a interactive inferncce solution by exporting the model to onxx and having a way to draw a shape and infere , + for each stage show interactive example of the work , for examplpe how does augmenttaion look like , picming a class and seing the orginal vs augmentd 
> =======
> [
>
> <pasted_content id="8717">
> ## Advanced prompt
>
> ````markdown
> # TASK: Interactive CRISP-DM Dashboard for Shape Recognition
>
> ## Operating rules
> - Operate ONLY inside the target folder: `<TARGET_FOLDER_PATH>`. Do not read or write outside it.
> - NEVER run git commands (no commit, push, add, branch, stash, or reset), and never suggest that you did.
> - Before coding, scan the folder for `TODO`, `FIXME`, stubs, and placeholder comments. List them and resolve or report each one.
> - Do not leave new TODOs, stubs, or fake or mock data behind. Every page must run end to end.
>
> ## Goal
> Build a local, offline, interactive dashboard for a hand-drawn shape-recognition project. It follows the six CRISP-DM stages, and each stage is its own page. The home page shows the CRISP-DM cycle. The dashboard ends with live in-browser inference from an exported ONNX model.
>
> ## Stack (simplest approach)
> - Training (Python): PyTorch, a small CNN, a 28x28 or 32x32 grayscale input.
> - Export: `torch.onnx.export` to `model/shape_cnn.onnx`, then verify it with `onnxruntime` against PyTorch outputs (max abs diff < 1e-4).
> - Dashboard: static HTML, ES modules, and vanilla JS or Preact. No build step if possible.
> - Inference: `onnxruntime-web` (WASM) running in the browser. No server is needed for prediction.
> - Charts: Chart.js or Plotly. Cycle diagram: inline SVG.
> - Everything runs locally, with vendored libraries and no CDN calls at runtime.
>
> ## Dataset
> - Classes: circle, square, triangle, star, line, and others that are easy to add (put the list in `config/classes.json`).
> - Source: a procedural generator (`data/generate_shapes.py`) with random size, position, stroke width, rotation, and jitter. Optionally accept Quick, Draw! ndjson.
> - Export a small JSON or PNG sample set for the dashboard (`dashboard/assets/samples/`).
>
> ## Folder structure (nested by focus, one task per file)
> ```
> <TARGET_FOLDER_PATH>/
>   config/                  classes.json, hyperparams.json
>   ml/
>     data/                  generate_shapes.py, dataset.py
>     augmentation/          augment_ops.py   (one op per function)
>     training/              model.py, train.py, metrics.py
>     export/                export_onnx.py, verify_onnx.py
>   artifacts/
>     model/                 shape_cnn.onnx
>     metrics/               history.json, confusion.json, per_class.json, errors.json
>     samples/               class_samples.json
>   dashboard/
>     index.html             home page with the CRISP-DM cycle
>     pages/                 01_business.html ... 06_deployment.html
>     js/
>       core/                router.js, state.js, theme.js
>       components/          cycle_diagram.js, canvas_pad.js, chart_wrap.js, class_picker.js
>       stages/              business.js, data_understanding.js, data_prep.js,
>                            modeling.js, evaluation.js, deployment.js
>       inference/           onnx_session.js, preprocess.js, postprocess.js
>     css/                   base.css, layout.css, components.css
>     vendor/                onnxruntime-web, chart lib
> ```
> Add new `.js`, `.py`, or `.cpp/.h` files rather than growing existing ones. Each file does one job. Stage modules import shared components and never import each other.
>
> ## Pages
>
> **Home (index.html)**
> - An SVG CRISP-DM cycle with six clickable nodes: Business Understanding, Data Understanding, Data Preparation, Modeling, Evaluation, Deployment. Arrows show the iterative loop, with Data and Business linked in both directions.
> - Each node shows a one-line status and opens its page.
> - A "Try it now" card embeds a mini draw-and-predict pad.
>
> **1. Business Understanding**
> - Objective, success criteria (for example accuracy >= 95%, latency < 50 ms in browser), and constraints.
> - Interactive: a editable target-metric panel that is checked against the real results from the Evaluation page.
>
> **2. Data Understanding**
> - Class distribution chart, pixel-mean heatmap per class, and sample grid.
> - Interactive: pick a class and see random samples (a "shuffle" button), the mean image, and the per-class variance.
>
> **3. Data Preparation**
> - Interactive: pick a class, then view the original beside the augmented version.
> - Sliders and toggles for rotation, scale, translation, noise, stroke thickness, flip, and elastic distortion.
> - A "randomize" button, plus a grid of N augmented variants.
> - Show the pipeline order and the train, validation, and test split with counts.
> - Augmentation code runs in JS for the live preview and matches `augment_ops.py`.
>
> **4. Modeling**
> - Architecture diagram, parameter count, and hyperparameters.
> - Training curves (loss and accuracy) with an epoch scrubber.
> - Interactive: change the epoch and see the predictions on fixed samples at that epoch, if checkpoints are saved.
>
> **5. Evaluation**
> - Confusion matrix (hover to see the counts, click a cell to list the misclassified samples), per-class precision, recall, and F1.
> - Interactive: click an error to see the image, the true label, the predicted label, and the probabilities.
> - Compare against the success criteria from page 1.
>
> **6. Deployment (live inference)**
> - A drawing canvas with mouse, touch, and stylus input, pressure-aware stroke width, clear, and undo.
> - Preprocessing: crop to bounding box, pad to square, resize, normalize. This must match training exactly (single shared spec in `config/`).
> - Run `onnxruntime-web` on every stroke end, with an optional live mode while drawing.
> - Show top-k probabilities as bars and the latency in ms.
> - Show the preprocessed 28x28 input next to the canvas so the user can see what the model sees.
> - A "wrong prediction?" button saves the drawing locally (download JSON) as feedback for the next CRISP-DM iteration.
>
> ## Guardrails
> - Modular: no file over ~200 lines. Split by responsibility.
> - Decoupled: preprocessing, inference, and UI are separate modules with explicit interfaces.
> - Separation of concerns: ML code never touches the DOM, and UI code never contains model logic.
> - Single source of truth for class labels and the preprocessing spec.
> - Fail visibly: if the ONNX file is missing, show a clear message and tell the user which script to run.
>
> ## Deliverables and order
> 1. Short plan listing the files to create and any TODOs found.
> 2. `ml/` scripts, then run them to produce `artifacts/`.
> 3. Dashboard shell (router, theme, cycle page).
> 4. One stage page at a time, each tested in the browser.
> 5. A README with exact Windows commands: `python -m venv`, `pip install`, run each script, and serve with `python -m http.server`.
> 6. Acceptance checklist:
>    - [ ] ONNX output matches PyTorch.
>    - [ ] Drawing a circle and a square gives the correct top-1.
>    - [ ] The augmentation preview works for every class.
>    - [ ] No CDN requests.
>    - [ ] No leftover TODOs or stubs.
>    - [ ] No git commands were used.
> ````
>
> ## What I changed
> - **Structure:** The prompt now maps each CRISP-DM stage to a page, with a concrete interactive element for each.
> - **Rules:** It adds your standing rules: the target-folder path, no git, a TODO/stub scan, and nested folders named by focus.
> - **Modularity:** Guardrails enforce one task per file, UI separated from ML, and new files over one big file.
> - **Deployment:** The preprocessing spec is shared between training and the browser, because a mismatch there is the most common cause of bad drawn-shape predictions.
> - **Offline:** It uses `onnxruntime-web` with vendored libraries, so there is no server-side inference and no cloud dependency.
> - **Verification:** There is an ONNX parity check and a final acceptance checklist.
>
> If you want a Babylon.js or 3D feature layer, or a `skill.md` version of this prompt, tell me which.
> </pasted_content id="8717">
>
> ]

## Response

I'll start by checking what the existing dashboard, demo and export already provide, and which real data each stage page can draw on. I'm in plan mode, so nothing changes yet.

Both searches are running in the background. I'll design the plan once their results are in.

First search is back. The key finding is that the import rules stop the dashboard calling Stage 2, Stage 3 or the export directly. I'm waiting on the second search before designing around that.

Before designing further, four decisions are yours, because your pasted prompt conflicts with how this project is actually built.

The planning agent is running. When it finishes, I'll write up the plan for your approval.

Plan mode is off, so I'll build this now as a new, separate `studio/` package. The design keeps every frozen pipeline file and the sealed test split untouched.

Three things came out of the design that you should know:
- About 14% of train and val images physically sit in the old `test/` folder, so I'll leave those out of the browsing pages.
- Stage 5's saved error file holds all of B's mistakes, so I'll show only the three confusable pairs you agreed to.
- The CI level can't be changed in the what-if panel, because that would need a new test computation.

First I'm reading the exact code it has to call.

The real code is confirmed and FastAPI is already installed, so `requirements.txt` stays untouched. I'm taking the validated chart colours from the visualization guide before writing any chart code.

Backend first: settings, the strict file allow-list, the wrappers around the real Stage 2 and 3 code, and inference.

Now the server, security layer and page data, plus the import rule that keeps the test split and frozen stages out of reach.

The A1 and B models exported and all 6 import rules hold. My smoke script just wrote to the wrong temp path, so I'm running it from the scratchpad.

Shared parts are done. Before writing each page, I'm checking the exact shape of the few JSON files whose structure I haven't confirmed.

All structures confirmed. Now the ten pages.

Zero errors in Chrome now. For final verification I'm stopping the test server, running the entire project test suite and confirming no frozen file changed, then committing.

The dashboard is built, tested and committed locally through the guard (`cf83c4c`, `e3c0165`), with no attribution and nothing pushed. I tested it with a mouse in real Chrome. Touch and stylus use the same input code, but I couldn't try them on an actual device.

**To open it**, from the repo root:
```powershell
.\.venv\Scripts\Activate.ps1
python -m studio
```
Then go to http://127.0.0.1:8765. It's a new, separate package, and your existing dashboard and demo are unchanged.

**What's in it:**
- **Home:** the clickable CRISP-DM cycle, stage status lights and a mini draw pad.
- **A page for each stage (0 to 6), plus a Business page:**
  - Stage 2: pick a class, compare original and augmented, and move the sliders. Stage 3 works the same way for the generator.
  - Stage 1: browse real images and near-duplicates.
  - Stage 4: scrub the training curves.
  - Stage 5: click confusion-matrix cells.
  - Business: a what-if panel for the success rule.
- **Draw and predict:** draw with undo and clear, see the real 64×64 input, and compare A0, A1 and B as ONNX models. You can also save a wrong prediction as JSON.

**How it was checked:**
- All 399 project tests pass.
- A sweep of every endpoint opened nothing from the sealed test split, and the access log is still at 13 lines.
- All seven stages still show passed, with no change to `src/` or `configs/`.
- In Chrome there were no errors and no external requests, and it also held up at phone width and in dark mode.

**Where it differs from the pasted prompt** (the first two are what you chose):
- It runs a small local server, so previews use the real pipeline code rather than JavaScript copies.
- It uses your real 64×64 models and 10 classes, not a new 28×28 model.
- Stroke width is a fixed 8 px, not pressure-aware, to match how the demo feeds the model.
- The epoch slider only moves through the training log, because only each run's best epoch was saved.

**What you'll see when using it:**
- A drawn square can come back "rectangle" from A1 and B while A0 says "square". That's real model behaviour and matches their weakness on rectangle/square in the results.
- About 14% of train and val images aren't browsable, because they sit in the old `test/` folder.
- A fresh clone needs `python -m studio.tools.export_arms` once to get the A1 and B models.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Tested with a mouse in real Chrome. Touch and stylus were not tested on a device.

## Our decision

All arms are exported for live comparison on the same drawing (C19).

## Measured effect

Reporting only, with no macro F1 change.

---

## Upgraded & Expanded Analysis: Local Studio Architecture & Multi-Arm ONNX Inference (`55_real`)

### Architectural Role in the Testing & Deployment Lineage

Session `55_real` bridges the pipeline's internal evaluation artifacts (`Stage 5` / `Stage 6`) and the public static site (`ShapeSense_Deployed` in [53_real](53_real_vercel-deployment-plan.md) and [54_real](54_real_vercel-deployment-build.md)):
1. **Uniform Multi-Arm ONNX Export (`C19`):** Exports the best-validation checkpoint for every trained arm (`A0`, `A1`, `B`, `A2`, and later `P`) into `studio/out/arms/<arm>/model.onnx` with a single `manifest.json`, eliminating the legacy `export/model.onnx` special case that would have conflated `A0` with the shipped `A2` model.
2. **Read-Only Artifact Isolation:** The Studio server reads frozen/saved pipeline artifacts and serves side-by-side live drawing predictions across all arms without touching `configs/splits/test.csv` or `fresh_holdout_2` (`artifacts/test_access.log` remains invariant).
3. **Interactive Visual Diagnostics:** Provides the interactive per-arm confusion matrix (`stage5.html`, referenced in [51_real](51_real_confusion-matrix-vs-first-run.md)), class-safe augmentation sliders (`stage2.html`), and CRISP-DM failure/change timelines (`failures.html`, `changes.html`) that were subsequently frozen into `ShapeSense_Deployed`.

