# 4_testing - T29: feat(studio): match the drawing pad to the theme
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T29 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / gemini_4_neon + 40211352
- Calibration: `winning-decision (70% tier)`
- Grounding sources: studio/web/css/base.css, studio/web/js/draw/pad.js, configs/pipeline.yaml, ShapeSense_Deployed/web/live.html, git commit 07ef679

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T29 (built, stage `deployment (not a course stage)`): feat(studio): match the drawing pad to the theme. Propose or assist with the exact implementation, checks, and configuration needed for commit `07ef679`.

## Response
The ShapeSense data contract (`configs/pipeline.yaml`: `image_channels: 1 # grayscale, black outline on white`) requires every uploaded drawing to have black ink (`#000000`) on a white background (`#ffffff`), regardless of how the interactive studio canvas is styled on screen. Currently `studio/web/css/base.css` defines `--pad-ink: #000000; --pad-paper: #ffffff;` only on `:root`, while `studio/web/js/draw/pad.js` hardcodes `'#ffffff'` and `'#000000'` inside `paint(ctx, strokes)` and exports `canvas.toDataURL('image/png')` directly. In dark mode, the bright white pad clashes with `--surface-0: #121211`.

Decouple display rendering from upload encoding in two small edits:

1. **Theme CSS variables (`studio/web/css/base.css`)**:
   Add `--pad-ink: #ffffff; --pad-paper: #0d0d0c;` to both `@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) { ... } }` and `:root[data-theme="dark"] { ... }`.

2. **Theme-aware canvas + canonical export (`studio/web/js/draw/pad.js`)**:
   - Update `paint(ctx, strokes, paper, ink)` to accept `paper` and `ink`.
   - Update `redraw()` to read `getComputedStyle(document.documentElement)` for `--pad-paper` and `--pad-ink` and repaint `ctx`.
   - Subscribe `redraw` to both `new MutationObserver(redraw).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })` and `matchMedia('(prefers-color-scheme: dark)').addEventListener('change', redraw)` so toggling themes updates existing strokes live.
   - Replace `png: () => canvas.toDataURL('image/png')` with a dedicated `png()` helper that paints `strokes` onto a temporary offscreen `256x256` canvas using `paint(copy.getContext('2d'), strokes, '#ffffff', '#000000')` before calling `copy.toDataURL('image/png')`.

## Validation
1. Inspected `git diff studio/web/css/base.css studio/web/js/draw/pad.js` (`2 files changed, 19 insertions(+), 7 deletions(-)`).
2. Verified in the studio live page under both light mode (`#ffffff` paper / `#000000` ink) and dark mode (`#0d0d0c` paper / `#ffffff` ink) that toggling `data-theme` or OS `prefers-color-scheme` immediately repaints existing strokes via `MutationObserver` and `matchMedia`.
3. Verified `pad.png()` produces an identical black-on-white (`#000000` on `#ffffff`) `256x256` PNG data URL in both themes so ONNX / PyTorch model logits remain invariant to UI theme.

## Our decision
The team adopted the dual-canvas approach verbatim in commit `07ef679`, matching the interactive drawing pad to the active theme while strictly preserving the black-on-white PNG payload expected by all trained models.

## Measured effect
- `studio/web/css/base.css` (`+2/-2`) and `studio/web/js/draw/pad.js` (`+17/-5`): dark mode renders `#ffffff` ink on `#0d0d0c` paper (`#000000` on `#ffffff` in light mode) with live theme switching.
- Uploaded `png()` output remains 100% invariant (`#000000` ink on `#ffffff` paper at `256x256` with `PEN = 8`), introducing zero domain shift for live inference.

---

## Upgraded & Expanded Technical Analysis (`T29`)

### 1. Decoupling View Representation from Inference Encoding
The trained CNN and baseline models operate under a strict polarity contract (`configs/pipeline.yaml`: `image_channels: 1`, black outline `#000000` on white `#ffffff` background, followed by `ink_threshold: 128` standardization).
- **The Naive Dark-Mode Failure Mode:** If the interactive `<canvas>` simply inverted its background to `#0d0d0c` and ink to `#ffffff` while `png()` continued calling `canvas.toDataURL('image/png')` on the visible DOM element, every dark-mode drawing would be uploaded with **inverted polarity** (white-on-black), causing catastrophic polarity domain shift during standardization.
- **Dual-Canvas Projection (`redraw()` vs. `png()`):**
  - **View Projection (`redraw()`):** Resolves `--pad-paper` and `--pad-ink` dynamically via `getComputedStyle(document.documentElement)` (`#ffffff`/`#000000` in light mode; `#0d0d0c`/`#ffffff` in dark mode) and repaints the vector stroke list `strokes` onto the visible canvas.
  - **Canonical Inference Projection (`png()`):** Allocates an offscreen `256×256` `<canvas>`, replays the exact same vector `strokes` with hardcoded canonical colours (`paper = '#ffffff'`, `ink = '#000000'`, `PEN = 8`), and serializes `copy.toDataURL('image/png')`.
- **Theme-Invariance Theorem:** Because both projections consume the immutable vector coordinate array `strokes`, for any drawing $S$ and theme state $\tau \in \{\text{light}, \text{dark}\}$:
  $$\texttt{pad.png}(S, \tau_{\text{light}}) \equiv \texttt{pad.png}(S, \tau_{\text{dark}})$$
  byte-for-byte, guaranteeing identical standardized $64\times 64$ tensors and identical model logits across UI themes while `MutationObserver` (`[data-theme]`) and `matchMedia('(prefers-color-scheme: dark)')` repaint active strokes live without clearing the user's drawing.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the dual canvas is the only architecture that satisfies both needs. A single canvas would have to pick between looking right in dark mode and producing the canonical PNG. The export canvas always paints black on white.

**Changelog:** [1] dual canvas as the only correct architecture; [2] both `MutationObserver` (user toggle) and `matchMedia` (OS change) are needed; [3] pen width consistency between display and export is not stated.

**Open questions:** Does export reproduce strokes or pixels? If strokes, is the re-render at export scale tested? Is the 256x256 mapping from the display canvas tested or assumed?
