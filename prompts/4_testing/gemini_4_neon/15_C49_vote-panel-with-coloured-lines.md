# 4_testing - C49: Vote panel with coloured lines
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C49 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40253714 + 40304911 / gemini_4_neon + 40253714 + 40304911
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `studio/web/js/widgets/predict-panel.js`, `studio/web/js/plain.js`, `studio/web/css/base.css`, `studio/web/css/components.css`, commit `ff7ddbf`, `ShapeSense_Deployed/web/live.html`, `ShapeSense_Deployed/web/js/widgets/predict-panel.js`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Our vote panel shows six answers in a grid with nothing tying them to the vote. Design a layout that shows at a glance which models agree and what the vote chose, using colour per label and per model.

## Response
Replace the flat 6-card grid with a radial hub-and-spoke layout (`voteNetwork` in `studio/web/js/widgets/predict-panel.js`) that places the five arm cards around a central **All models vote** card and separates **model identity** (arm swatches) from **predicted class** (label colours):

1. **Grid geometry (`.vote-net` in `components.css`):** Use a 6-column CSS grid (`grid-template-columns: repeat(6, minmax(0, 1fr)); column-gap: 12px; row-gap: 58px;`) so 5 arms split cleanly into `upper = Math.ceil(arms.length / 2)` (3 cards in row 1 at columns `1-2`, `3-4`, `5-6`), the `vote` card in the middle (row 2, columns `3-4`), and the remaining 2 cards centered underneath (row 3, columns `2-3` and `4-5`). On narrow screens (`@media (max-width: 620px)`), collapse `.vote-net` to a single column with `grid-area: auto !important` and hide `.vote-lines`.
2. **Label-coloured SVG links (`.vote-lines`):** Overlay an SVG layer (`position: absolute; inset: 0; pointer-events: none;`) inside `.vote-net` and redraw on `ResizeObserver` and every inference response. For each arm result, connect the card edge (`x1`, `y1`) to an evenly spaced port on the top or bottom edge of `slots.vote.root` (`x2`, `y2`) with a cubic Bézier `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}` (`stroke-width: 2.6`). Stroke each curve with `colorOf(result.label)` (`var(--label-0)` through `var(--label-9)` in `base.css`), or dashed `var(--text-muted)` (`stroke-dasharray: 5 5`) when `result.not_sure` is true. Place the predicted class name (`.vote-line-label`) at `(x1 + x2) / 2, my + 4` with `paint-order: stroke; stroke: var(--surface-1); stroke-width: 4px;` so the label stays legible over crossing curves.
3. **Per-model identity and tooltips:** Give each model header an `.arm-swatch` coloured by `ARM_COLOR[arm]` (`--series-1` through `--series-5`, `--accent` for `vote`) and `data-tip: ARM_TIPS[arm]` from `studio/web/js/plain.js` describing its training data (`Real only`, `Real + augmented`, `Real + synthetic`, `Full mix`, `Synthetic pretraining`, and equal-weight averaging for `vote`).
4. **Vote border, tally, and "What the model saw":** Colour the winning answer text and probability bars by `colorOf(top.label)`, highlight `slots.vote.root`'s border in `colorOf(vote.label)`, and display `${agree} of ${out.results.length} models picked this · ${ms} ms` in the vote card's latency slot. Move the `What the model saw (64×64)` preview (`seen`) directly underneath the drawing pad in `.pad-wrap` so the user compares their raw strokes against the standardized 64×64 outline without scanning past the vote graph.
5. **Legend chips with model dots (`.label-row`):** Render all 10 class chips at the bottom with `.label-swatch` (`--label-i`) and per-arm indicator dots (`i`) coloured with `ARM_COLOR[arm]` whenever that arm predicted the class.

## Validation
- Students `40253714` and `40304911` verified the `.vote-net` layout in Studio (`live.html` and compact panel) across desktop and 390 px mobile viewports in both light and dark CSS themes, checking that crossing Bézier paths stay readable, tooltips resolve from `ARM_TIPS`, and equal-weight vote disclaimers remain visible.
- `ShapeSense_Deployed/tests/browser_checks.mjs` (`draw` and `pages` checks) later verified in headless Chromium that drawing on `live.html` populates all 5 arms plus `vote` on both desktop (`1440×900`) and phone (`390×844`) with zero elements sticking out of cards.

## Our decision
- Adopted Gemini 4 Neon's complete radial `voteNetwork` layout, label/model colour split, `ARM_TIPS` tooltips, `seen` placement under the drawing pad, and `.label-row` model-dot chips in commit `ff7ddbf`, and carried the identical widget forward to `ShapeSense_Deployed/web/js/widgets/predict-panel.js`.

## Measured effect
- All 6 slots (`A0`, `A1`, `B`, `A2`, `P`, `vote`) update in place without layout shift; SVG connectors, class colour chips, and agreement tally (`k of 5 models picked this`) immediately show agreement and dissent at a glance.
- `ShapeSense_Deployed` browser checks pass on `live.html` across light, dark, and phone views with all 5 ONNX arms + vote scored in-browser.

---

## Upgraded & Expanded Technical Specification (`C49`)

The radial hub-and-spoke layout (`voteNetwork` in `studio/web/js/widgets/predict-panel.js`) coordinates four mechanical layers: **geometry** (where cards and ports sit), **topology** (which card connects to which port, in what order), **semantics** (what colour and stroke style mean), and **lifecycle** (when the SVG is redrawn and how the layout degrades).

### 0. Data Contract the Layout Consumes
`voteNetwork` is driven by a single inference response object without assuming a rigid array ordering in `out.results`:

```js
// out.results: Array<{ arm, label, probs, not_sure, latency_ms }>
// out.results[0..4] = the five arms in ARM_ORDER; the vote is computed, not received.
const ARM_ORDER = ['A0', 'A1', 'B', 'A2', 'P'];          // from ARM_NAMES keys
const arms = ARM_ORDER
  .map(k => out.results.find(r => r.arm === k))
  .filter(Boolean);                                        // tolerate missing arms
const vote = majorityVote(arms);                            // {label, agree, tied}
```

**Vote aggregation logic (explicit and equal-weight):**
- Tally `count[label] += 1` over arms where `!r.not_sure`; `not_sure` arms abstain and are excluded from the denominator (they render dashed, not counted).
- `top = argmax(count)`; `agree = count[top]`; `tied = (number of labels with count === max) > 1`.
- On a tie, do **not** silently pick one: display `"Tie: <labelA>, <labelB>"` and draw both winners' arms with a thicker stroke, so the "what the vote chose" claim stays honest. `vote.label` becomes the lexicographically first winner only for colouring the border; the tally text names all tied labels.
- The vote card's own `.arm-swatch` uses `ARM_COLOR['vote']` (`--accent`), never a label colour, preserving the identity/prediction split.

### 1. Grid Geometry (`.vote-net` in `components.css`)
The hub-and-spoke is a **6-column, 3-row CSS grid**, and the JS computes the same row/column assignment the CSS lays out so SVG endpoints never drift:

```css
.vote-net {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  column-gap: 12px;
  row-gap: 58px;              /* vertical room for Bézier control points */
  position: relative;         /* anchor for the absolutely-positioned SVG */
}
```

**Assignment algorithm (`layoutSlots(arms)`):**
- `upper = Math.ceil(arms.length / 2)` → for 5 arms, `upper = 3`.
- Row 1: arms `[0..upper-1]` at column spans `1-2`, `3-4`, `5-6`.
- Row 2: `vote` card at column span `3-4` (the visual centre), leaving columns `1-2` and `5-6` empty as breathing room.
- Row 3: arms `[upper..]` (2 cards for 5 arms) centred at `2-3` and `4-5`, **not** `1-2`/`5-6`, so the bottom row hugs the vertical axis under the vote card.

This produces a symmetric "3 over 1 over 2" shape for 5 arms; if `arms.length` is even (defensive), the code falls back to `upper = arms.length / 2`, row 3 empty, and the vote card centres in row 2 — the geometry helper returns `{ row, col, span }` per slot and the CSS-in-JS sets `grid-row`/`grid-column` from it, never from CSS alone.

**Narrow collapse (`@media (max-width: 620px)`):**
```css
@media (max-width: 620px) {
  .vote-net { grid-template-columns: 1fr; row-gap: 12px; }
  .vote-net > * { grid-area: auto !important; }
  .vote-lines { display: none; }     /* lines become meaningless in a stack */
}
```
Hiding the SVG (not just `opacity: 0`) prevents stale paths from occupying pointer/hit-testing space and avoids wasted redraw work.

### 2. Label-Coloured SVG Links (`.vote-lines`)
Overlay an SVG layer inside `.vote-net`:
```css
.vote-lines { position: absolute; inset: 0; width: 100%; height: 100%;
  pointer-events: none; overflow: visible; }
```
`overflow: visible` is required because the label text and marker heads can extend past the nominal box; `pointer-events: none` keeps the cards clickable underneath.

**Port allocation and path construction (`drawVoteLines()`):**
1. For each arm card `i`, find the **edge facing the vote card** and the port on that edge:
   - `source = cardRect`; `target = voteRect`.
   - If `cardRect.top < voteRect.top` (arm above vote), the exit edge is the bottom edge `y1 = cardRect.bottom`, and the entry port is on the vote's top edge; else the exit is the top edge `y1 = cardRect.top` and the entry is the vote's bottom edge.
   - Port spacing on the vote edge: `ports = arms.length`; port `i` sits at `x2 = voteRect.left + voteRect.width * (i + 1) / (ports + 1)` on the vote's top edge (and mirrored on the bottom edge for lower arms), so **no two connectors share an endpoint** and crossings near the hub are minimised.
   - `x1` = horizontal centre of the arm's exit edge, i.e. `cardRect.left + cardRect.width / 2`.
2. Control points for a smooth S-curve: both control points sit at the **vertical midpoint** `my = (y1 + y2) / 2`:
   ```
   M x1,y1 C x1,my  x2,my  x2,y2
   ```
   When `y1 === y2` (defensive, e.g. an arm aligned with the vote row), degrade to a straight `<line>` to avoid a degenerate Bézier.
3. Stroke semantics:
   - Solid `stroke-width: 2.6` with `stroke: colorOf(result.label)`.
   - **Dashed** `var(--text-muted)` with `stroke-dasharray: 5 5` when `result.not_sure` is true (abstain, no label colour).
   - If `vote.tied` and this arm picked a tied winner, `stroke-width: 4.2` to foreground the tie.
   - Add `vector-effect: non-scaling-stroke` so zooming the page does not fatten thin lines unevenly.
4. **Label placement:** predicted class name (`.vote-line-label`) at `midX = (x1 + x2) / 2`, `midY = my + 4`, with `text-anchor: middle` and
   ```css
   .vote-line-label { paint-order: stroke; stroke: var(--surface-1);
     stroke-width: 4px; stroke-linejoin: round; fill: var(--text); }
   ```
   The surface-coloured halo keeps the name legible over crossing curves and both themes.
5. **Collision handling:** after computing all label boxes, run a cheap vertical nudge: sort labels by `midY`, and for any two within `14px` on overlapping x-ranges, push the later one `down 14px` (or `up` if near the bottom edge). This is $\mathcal{O}(n^2)$ with $n \le 5$, run once per redraw — deterministic and negligible in cost.

### 3. Per-Model Identity and Tooltips
- Each model header gets an `.arm-swatch` element filled with `ARM_COLOR[arm]` (`--series-1`..`--series-5`, `--accent` for `vote`).
- Tooltip source: `data-tip: ARM_TIPS[arm]` resolved from `studio/web/js/plain.js`, keyed by the **same `ARM_ORDER`** as the vote code; a guard asserts `Object.keys(ARM_TIPS).sort()` equals `ARM_ORDER.slice().sort()` so a renamed arm fails loudly instead of rendering an empty tooltip.
- `ARM_TIPS` describes training data (`Real only`, `Real + augmented`, `Real + synthetic`, `Full mix`, `Synthetic pretraining`, and equal-weight averaging for `vote`).

### 4. Vote Border, Tally, and "What the Model Saw"
- Colour the winning answer text and probability bars by `colorOf(top.label)`.
- Highlight `slots.vote.root`'s border via `border-color: colorOf(vote.label)`; on tie, use a `conic-gradient` split between the tied label colours so the ambiguity is visible at a glance.
- Latency/tally slot text: `` `${agree} of ${out.results.filter(r => !r.not_sure).length} models picked this · ${ms} ms` `` — **denominator excludes abstainers**, so "3 of 5" never silently means "3 of 5 that tried".
- Move the `What the model saw (64×64)` preview (`seen`) directly underneath the drawing pad in `.pad-wrap`, so the user compares raw strokes against the standardized outline without scanning past the graph.

### 5. Legend Chips with Model Dots (`.label-row`)
- Render all 10 class chips with `.label-swatch` (`--label-i`).
- For each class, append one `i` dot **per arm that predicted it**, coloured by `ARM_COLOR[arm]`, ordered by `ARM_ORDER`. If the vote picked that class, prefix a slightly larger `--accent` dot.
- Cap dots at 5 and show `+N` if (defensively) more arms exist, so the row cannot overflow.

### 6. Redraw Lifecycle and Correctness
- **Single redraw owner:** `drawVoteLines()` is the only function that mutates the SVG. It is called from:
  1. every inference response (after cards update, in the same frame via `requestAnimationFrame`),
  2. a `ResizeObserver` on `.vote-net` (debounced `~60ms`),
  3. `document.fonts.ready.then(...)` because label width changes when fonts load,
  4. the `prefers-reduced-motion` branch (draw instantly, no transition).
- **Stale-read guard:** each redraw captures a monotonic `renderToken`; async callbacks check `if (token !== renderToken) return;` so a slow earlier resize cannot paint over a newer vote.
- **Clear-then-draw:** every redraw does `svg.replaceChildren()` before appending, preventing path accumulation across inferences.
- **Coordinate basis:** all rect math is relative to `.vote-net`'s bounding box (`rect.left - net.left`), so scrolling or ancestor transforms never skew endpoints, with `x2 ∈ [0, net.width]`.
- **Reduced motion:** respect `prefers-reduced-motion: reduce` by skipping stroke-dash animations and setting paths immediately.

### 7. Accessibility
- The SVG is `role="img"` with an `<title>` generated from the vote result (`"Vote: full mix, 3 of 5 models agree"`).
- Each arm card keeps a text summary so colour is never the sole carrier of meaning: `aria-label="A0: full mix, 71%"`.
- Legend dots carry `title` text (`"A1 predicted square"`), and the tally string is real text, not an image.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the spec above already covers layout, colour and tie-handling. The additions here are the data contract (`ARM_ORDER`, `filter(Boolean)`, `majorityVote`), which makes "what the vote chose" testable, and the tie rule: a majority vote that silently breaks ties is not a majority vote.

**Changelog:** [1] tie-handling explicit (conic-gradient border, thickened strokes, "Tie: A, B" text); [2] abstentions excluded from the denominator; [3] collision nudge bounded at n <= 5.

**Open questions:** Does `majorityVote` use the same `not_sure_below` threshold as the per-arm predictions? A separate threshold could make the vote disagree with every arm's own top-1. Is the lexicographic tie-break for border colour documented where a reader would see it?
