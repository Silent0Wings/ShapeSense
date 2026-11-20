# 4_testing - D02: Deploy the project online: export the five models to ONNX, research the Vercel documentation, and publish a frozen static site with live, interactive inference (draw a shape, all five models and their vote predict it) and an interactive six-part slide presentation ()

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [53_real_vercel-deployment-plan.md](53_real_vercel-deployment-plan.md), [54_real_vercel-deployment-build.md](54_real_vercel-deployment-build.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/19_D02_deploy-the-project-online-export-the-five-mo.md](../gemini_4_neon/19_D02_deploy-the-project-online-export-the-five-mo.md)
- Date: 2026-11-09
- Worksheet entry: D02 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: all members / all members
- Calibration: `winning-decision`
- Grounding sources: ShapeSense/stages/stage_7.md, ShapeSense/src/stage6_report/export.py, ShapeSense/export/README.md, commits 6e633e7 and 6f6f4a4, ShapeSense_Deployed/README.md, ShapeSense_Deployed/site/vercel.json, ShapeSense_Deployed/build/build_site.py, ShapeSense_Deployed/build/check.py, ShapeSense_Deployed/build/inspect_models.py, ShapeSense_Deployed/build/verify_deploy.py, ShapeSense_Deployed/web/js/infer/run.js, ShapeSense_Deployed/web/js/infer/standardize.js, ShapeSense_Deployed/web/js/content/parts.js, ShapeSense_Deployed/tests/browser_checks.mjs, ShapeSense_Deployed/web/live.html, ShapeSense_Deployed/web/part1.html-part6.html, ShapeSense_Deployed/web/index.html
- Follow-up: [`../gemini_4_neon/19_D02_deploy-the-project-online-export-the-five-mo.md`](../gemini_4_neon/19_D02_deploy-the-project-online-export-the-five-mo.md)

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** We want to publish the project online as a frozen static site: export the five models to ONNX, run them in the visitor's browser with ONNX Runtime Web on Vercel, let a visitor draw a shape and see all five models and their vote, and add a slide presentation. Plan it and check browser results against Python.

## Response ()

> **Opus 5.5:** Keep the training repository clean by placing the frozen public build in its own standalone output (`ShapeSense_Deployed` with `site/` as the Vercel root), with zero server code and zero CDN dependencies:
>
> 1. **Static Vercel packaging (`site/vercel.json` & `build/build_site.py`)**:
>    - Configure `framework: null`, `outputDirectory: "dist"`, empty `buildCommand` and `installCommand`, and strict security headers (`Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'`).
>    - Pin `onnxruntime-web` locally into `dist/ort/` (`ort.wasm.min.mjs`, `ort-wasm-simd-threaded.mjs`, `ort-wasm-simd-threaded.wasm`, `numThreads = 1`, `proxy = false`) and bake every file's SHA-256 into `site/dist/frozen.sha256` with a deterministic build (`build_site.py --check`).
>    - Keep all `/api` requests out of the browser (`web/js/api.js` serves frozen JSON snapshots; drawings stay entirely in-browser).
> 2. **All five ONNX models + byte-exact preprocessing parity (`web/js/infer/`)**:
>    - Export all five arms (`A0`, `A1`, `B`, `A2`, `P`) with no external data files (`inspect_models.py --check`) and score all five plus the equal-weight `"All models vote"` in `run.js`.
>    - Port `standardize.py` line by line to `web/js/infer/standardize.js` - matching Pillow's integer alpha compositing and fixed-point resampling, NumPy's median, SciPy's `reflect` median filter, and cross-shaped binary morphology - rather than using a plain canvas resize, which silently breaks predictions.
> 3. **Six-part interactive slide presentation (`part1.html` - `part6.html`, `web/js/content/parts.js`)**:
>    - Give each presenter one part (5-7 slides, one claim, snapshot-backed graphics via `slide-charts.js`, strip of key numbers, max 60-word budget, CRISP-DM phase tags, and an appendix listing the code/docs/tests covered).
> 4. **Automated verification gates (`build/check.py` & `build/verify_deploy.py`)**:
>    - Verify Python-vs-JS parity on preprocessing fixtures, softmax/top-3/vote math, what-if rules, forbidden-content/sealed-path scans, Vercel size limits (60 MB total / 25 MB per file), headless Chromium checks (light/dark/`390×844` phone views, zero outside or `/api` requests, ONNX Runtime Web logits within `1e-4` of Python `onnxruntime`), and byte-for-byte HTTP verification of every file in `frozen.sha256` on the live Vercel URL.

## Why this reading fits

`ShapeSense/stages/stage_7.md` (commit `6f6f4a4`), `ShapeSense/src/stage6_report/export.py` (commit `6e633e7`), and the entire `ShapeSense_Deployed` repository (`README.md`, `site/vercel.json`, `build/build_site.py`, `build/check.py`, `build/verify_deploy.py`, `web/js/infer/standardize.js`, `web/js/infer/run.js`, `web/js/content/parts.js`, and `tests/browser_checks.mjs`) implement this exact architecture and verification pipeline.

## Validation

In `ShapeSense_Deployed`, `build/check.py` verifies: model contract (`inspect_models.py --check`), deterministic rebuild (`build_site.py --check`), Node parity tests (`tests/test_standardize.mjs` on 502 fixtures byte-for-byte, `tests/test_math.mjs` on 1,020 cases, `tests/test_whatif.mjs` on 309 cases, `tests/test_preview.mjs`, and `tests/test_parts.mjs` enforcing slide rules and the 90% inventory floor), explanation consistency (`check_explain.py`), `frozen.sha256`, forbidden-content and size-budget checks, and headless Chromium checks (`tests/browser_checks.mjs`) asserting ONNX Runtime Web logits within `1e-4` of Python `onnxruntime` and zero external or `/api` network calls. Live deployments are checked byte-for-byte against `frozen.sha256` via `build/verify_deploy.py`.

## Our decision

Built `ShapeSense_Deployed` from the frozen snapshot of commit `f3b3bdb`, serving all 5 exported ONNX arms and their equal-weight vote directly in the visitor's browser via ONNX Runtime Web on Vercel (`https://shapesense-ten.vercel.app`) alongside the six-part slide presentation (`part1.html` - `part6.html`), with no backend server and full parity gates.

## Measured effect

Public at `https://shapesense-ten.vercel.app` since `2026-11-11` (six-part presentation live `2026-11-16` under `freezes/2026-11-16-public-4.sha256`, Predict-button freeze live `2026-11-17` under `freezes/2026-11-17-public-5.sha256`), serving byte-for-byte identical files to `frozen.sha256`, passing preprocessing parity across 502 fixtures, browser ONNX logits within `1e-4` of Python, and 93.7% presentation coverage of the 31,736 lines of work.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`D02`)

### The environment-independence theorem

**Claim:** a visitor's browser computes the same prediction as the Python training stack, for every drawing, in every browser, offline, with no server.

This requires three sub-proofs:
1. **Model equivalence:** ONNX export with no external data (`inspect_models.py --check` under Vercel's 60 MB total / 25 MB per-file limits), hashed, and shipped; browser logits within `1e-4` of Python `onnxruntime` (`browser_checks.mjs`).
2. **Preprocessing equivalence:** `standardize.py` ported *line by line* to `standardize.js` — Pillow's integer alpha compositing, fixed-point resampling, NumPy median, SciPy `reflect` median filter, and cross-shaped morphology. A plain HTML canvas resize would silently break predictions by using a different resampling kernel. The **502-fixture parity test** is the proof.
3. **Math equivalence:** softmax / top-3 / equal-weight vote — `test_math.mjs` across `1,020` cases.

### Why "frozen static site" is the right architecture

Zero server code, zero CDN, zero `/api` — the CSP (`default-src 'self'`) enforces it, and `browser_checks.mjs` asserts zero external or `/api` requests. The site is a **pure function of committed bytes**, verified byte-for-byte against `frozen.sha256` on the live Vercel URL (`verify_deploy.py`). This applies the `F16`/`F28`/`C36` bit-identity discipline to the *public deployed artifact*, while the six-part slide deck (`slide-charts.js`, `test_parts.mjs` with a 90% inventory floor) extends the `C41` traceability chain to the presentation layer.

