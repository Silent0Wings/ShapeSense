# 4_testing - D02: Deploy the project online: export the five models to ONNX, research the Vercel documentation, and publish a frozen static site with live, interactive inference (draw a shape, all five models and their vote predict it) and an interactive six-part slide presentation
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/48_D02_deploy-the-project-online-export-the-five-mo.md](../claude_opus/48_D02_deploy-the-project-online-export-the-five-mo.md)
- Date: 2026-11-09
- Entry: D02 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: all members / all members
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `stages/stage_7.md`, `export/README.md`, `src/stage6_report/export.py`, `studio/tools/export_arms.py`, `ShapeSense_Deployed/README.md`, `ShapeSense_Deployed/build/build_site.py`, `ShapeSense_Deployed/build/check.py`, `ShapeSense_Deployed/web/js/infer/standardize.js`, `ShapeSense_Deployed/web/js/infer/run.js`, `ShapeSense_Deployed/web/js/content/parts.js`, `ShapeSense_Deployed/tests/browser_checks.mjs`, commits `6e633e7`, `6f6f4a4`, `f3b3bdb`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
We want to publish the project online as a frozen static site: export the five models to ONNX, run them in the visitor's browser with ONNX Runtime Web on Vercel, let a visitor draw a shape and see all five models and their vote, and add a slide presentation. Plan it and check browser results against Python.

## Response
Structure the deployment as a separate, self-contained static repository (`ShapeSense_Deployed`) gated by `stages/stage_7.md` (G1-G4 and requirements R1-R18), so the research pipeline in `ShapeSense` stays untouched:

1. **Multi-arm ONNX export (`studio/tools/export_arms.py`, `src/stage6_report/export.py`):** Select each arm's (`A0`, `A1`, `B`, `A2`, `P`) best-validation checkpoint using validation macro-F1 only (never test), export via `export_onnx` (opset 17, input `image` float32 `(N, 1, 64, 64)`, output `logits` `(N, 10)`), and record run names, validation scores, and SHA-256 hashes in `manifest.json`.
2. **Deterministic frozen snapshot & Vercel isolation (`ShapeSense_Deployed`):**
   - `tools/snapshot.py` captures read-only page JSONs, pre-rendered Stage 2/3 previews, figures, reports, and the 5 ONNX models from an approved clean commit (`f3b3bdb`), writing `snapshot/manifest.json`.
   - `build/build_site.py` assembles `site/dist/` (the Vercel root under `site/vercel.json`) with sorted listings, `\n` line endings, and pinned `onnxruntime-web` WASM files (`ort.wasm.min.mjs`, `ort-wasm-simd-threaded.mjs`, `ort-wasm-simd-threaded.wasm`) copied from `node_modules` - zero CDN or `/api` calls - and writes `site/dist/frozen.sha256` plus `js/frozen.js` (commit + snapshot date banner on every page).
   - Remove or pre-render Python-dependent controls (`R8`): no live `/api/feedback` saving, and Stage 2/3 sliders snap to saved `snapshot/previews/`.
3. **Byte-exact browser preprocessing & ONNX Runtime Web inference:**
   - Port `src/stage1_freeze/standardize.py` to pure ES module `web/js/infer/standardize.js` (reproducing Pillow's integer `AlphaComposite.c` and fixed-point `Resample.c`, `np.median`, `scipy.ndimage.median_filter` `'reflect'`, cross morphology, bounding-box crop/letterbox, and 2-px outline redraw) instead of shipping Pyodide, keeping the total bundle well under Vercel limits.
   - Port softmax, top-3, `not_sure_below`, and equal-weight probability averaging to `web/js/infer/math.js`.
   - Load all 5 `.onnx` models in `web/js/infer/run.js` via `ort.InferenceSession.create(..., { executionProviders: ['wasm'], graphOptimizationLevel: 'all' })` (`numThreads = 1`, `proxy = false` so cross-origin isolation headers are unnecessary), feeding `uint8 / 255` float32 tensors so visitor drawings never leave the browser.
4. **Six-part interactive slide presentation (`part1.html` - `part6.html`):** Define all slide content in `web/js/content/parts.js` (5-7 slides per part, one claim, one graphic via `slide-charts.js`, key-number strip, ≤ 60-word budget for claim + bullets, CRISP-DM phase tags, handoff, and file inventory appendix covering ≥ 90% of project lines via `tools/inventory.py` and `tests/test_parts.mjs`).
5. **End-to-end verification gate (`build/check.py` and `tests/browser_checks.mjs`):** Before and after `vercel deploy --prebuilt --prod`, enforce:
   - Model contract (`inspect_models.py --check`), reproducible build (`build_site.py --check`), and `frozen.sha256` integrity.
   - Node parity suites (`test_standardize.mjs` byte-exact on 502 fixtures, `test_math.mjs` on 1,020 cases, `test_whatif.mjs` on 309 cases, `test_preview.mjs`, `test_parts.mjs`).
   - Forbidden-content scan (`R15`/`R16`: zero sealed split paths/files, local paths, user details, or secrets) and size budget (`≤ 60 MB` total, `≤ 25 MB` per file).
   - Headless Chromium checks across light, dark, and 390×844 phone views verifying zero console/network errors, zero external or `/api` calls, ONNX Runtime Web logits within `1e-4` of Python `onnxruntime` across all 5 arms + vote (`fixtures/model/logits.json`), and live canvas prediction on desktop and phone.

## Validation
- `python build/check.py` in `ShapeSense_Deployed` ran the full verification suite: model contract, reproducible build, Node parity tests (502 preprocessing fixtures byte-exact, 1,020 math cases, 309 what-if cases, saved previews, slide rules covering 93.7% of 31,736 lines), `build/check_explain.py`, `frozen.sha256`, forbidden-content scan, size budget, and Playwright headless Chromium checks (`tests/browser_checks.mjs`) across all pages in light, dark, and phone views plus `1e-4` ONNX logit parity against Python.
- After `vercel deploy --prebuilt --prod`, `python build/verify_deploy.py https://shapesense-ten.vercel.app` and `node tests/browser_checks.mjs --base https://shapesense-ten.vercel.app` verified byte-for-byte parity on the live URL.

## Our decision
- Executed the full plan across `ShapeSense` (`6e633e7`, `6f6f4a4`, `f3b3bdb`) and `ShapeSense_Deployed`: satisfied Gates G1-G4 (MIT code license, CC BY 4.0 weights license, written user approval on `f3b3bdb`), chose pure-JS `standardize.js` over Pyodide for instant load and zero external dependencies, and shipped the frozen site, six-part presentation, and live `Predict` button panel.

## Measured effect
- Live at `https://shapesense-ten.vercel.app` (initial public release `2026-11-11` from commit `f3b3bdb`, six-part slide presentation live `2026-11-16` / `freezes/2026-11-16-public-4.sha256`, `Predict` button freeze live `2026-11-17` / `freezes/2026-11-17-public-5.sha256`).
- All 5 ONNX models (`A0`, `A1`, `B`, `A2`, `P`) and equal-weight vote execute 100% client-side in ONNX Runtime Web with logits within `1e-4` of Python `onnxruntime`, preprocessing byte-identical on 502 fixtures, zero `/api` or third-party network calls, and 93.7% of 31,736 source lines indexed across the six presentation parts.

---

## Upgraded & Expanded Technical Analysis (`D02`)

### 1. Byte-Exact Browser Preprocessing & Multi-Arm ONNX Parity Gate
- **Validation-Only Model Selection:** Each arm (`A0`, `A1`, `B`, `A2`, `P`) selects its exported checkpoint by **validation macro-F1 only** (never test, matching `C18`), exported at ONNX opset 17 (`input: float32 (N, 1, 64, 64)`, `output: logits (N, 10)`).
- **Reproducing Python C-Extension Numerics in Pure JS (`web/js/infer/standardize.js`):**
  - Achieving $|\text{logits}_{\text{browser}} - \text{logits}_{\text{python}}|_\infty \le 10^{-4}$ requires matching the exact `uint8` pixel grid fed into `(N, 1, 64, 64)` tensor division (`uint8 / 255.0`). Even a 1-pixel rounding discrepancy during resampling shifts convolutional activations by $>10^{-2}$.
  - `standardize.js` ports Pillow's integer `AlphaComposite.c`, fixed-point bicubic/bilinear `Resample.c`, `np.median`, `scipy.ndimage.median_filter(..., mode='reflect')`, cross-structuring-element morphology, bounding-box crop/letterbox, and 2-px outline redraw to pure JavaScript — avoiding a $>15\text{ MB}$ Pyodide download while matching Python **byte-for-byte across all 502 test fixtures** (`test_standardize.mjs`, plus `1,020` math cases in `test_math.mjs` and `309` what-if cases in `test_whatif.mjs`).
- **WASM Threading & Header Simplicity:** Configuring `ort.env.wasm.numThreads = 1` and `proxy = false` eliminates `SharedArrayBuffer` requirements, allowing Vercel to serve `site/dist/` without restrictive `Cross-Origin-Opener-Policy` / `Cross-Origin-Embedder-Policy` headers while keeping single-image 5-arm inference fast in-browser.

### 2. Hermetic Static Snapshot Isolation & Six-Part Presentation Coverage
- **Deterministic Build & `R8` Static Pre-Rendering:** `tools/snapshot.py` captures from clean commit `f3b3bdb` into `snapshot/manifest.json`; `build/build_site.py` emits `site/dist/` with sorted directory listings, normalized `\n` line endings, local `node_modules` WASM binaries (zero CDN or `/api` calls), and `site/dist/frozen.sha256`. Interactive Stage 2/3 sliders snap to pre-rendered `snapshot/previews/` frames and live `/api/feedback` writes are omitted (`stages/stage_7.md` R8).
- **93.7% Line-Level Presentation Inventory:** `tools/inventory.py` and `tests/test_parts.mjs` enforce that the six presentation parts (`part1.html`–`part6.html`, 5–7 slides/part, $\le 60$-word claim+bullet budget per slide) index $\ge 90\%$ of all repository lines, achieving **93.7% coverage across 31,736 source lines**.
- **Pre- and Post-Deploy Verification (`build/check.py` & `verify_deploy.py`):** Runs model contract checks, reproducible build verification, Node parity suites, forbidden-content scans (zero sealed split paths or secrets), bundle budget checks ($\le 60\text{ MB}$ total, $\le 25\text{ MB}$/file), and Playwright Chromium checks across light, dark, and `390×844` phone viewports both locally and against `https://shapesense-ten.vercel.app`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** pure-JS `standardize.js` over Pyodide is justified by a chain. Pyodide adds roughly 10 MB, needs a CDN or vendored WASM, and brings a second Python whose Pillow and scipy versions must match training. The 502-fixture byte-exact test is what makes the port trustworthy.

**Changelog:** [1] Pyodide-vs-JS chain of reasons; [2] 502 fixtures as the trust anchor; [3] `numThreads = 1` is an explicit trade (multi-threading needs COOP/COEP headers); [4] the frozen-site limitation (no unseen shapes) is stated.

**Open questions:** Is "93.7% of lines" lines indexed, or lines appearing in a slide? Which categories are excluded? Does `frozen.sha256` cover the ONNX models or only the site bundle?
