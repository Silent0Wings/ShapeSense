# C46 — Upgraded & Expanded: Animate Button on Augmentation and Synthetic Generator

Below is a substantially expanded reconstruction of C46, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C46: Animate button on Augmentation and Synthetic generator

- **LLM:** Gemini 4 Neon
- **Category:** Two-LLM comparison. Other model's answer: [../claude_opus/42_C46_animate-button-on-augmentation-and-synthetic.md](../claude_opus/42_C46_animate-button-on-augmentation-and-synthetic.md)
- **Date:** 2026-11-10
- **Entry:** C46 (`change`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40211352 / 40211352
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `studio/web/js/widgets/controls.js`, `studio/web/js/widgets/fan-lines.js`, `studio/web/js/pages/stage2.js`, `studio/web/js/pages/stage3.js`, `studio/web/css/components.css`, commit `ff7ddbf`, commit `33858dc`, `ShapeSense_Deployed/web/stage2.html`, `ShapeSense_Deployed/web/stage3.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> I added an Animate button to the Augmentation and Synthetic generator pages. It walks every enabled slider in small random steps, keeps the same random draw, and on Augmentation I draw arrows from the original image to each augmented copy. Can you review it? Is it clear and correct, and what would you change?

**Implicit constraints (made explicit):**
1. **Correctness** — the walk must produce valid parameter combinations at every step, not just at the start.
2. **Interpretability** — the animation must isolate *parameter sensitivity* from *random-draw variance*; if both change per step, the reader learns nothing.
3. **Robustness** — overlapping async requests, background tabs, and manual slider input must not corrupt state.
4. **Clarity** — the arrow diagram must make the one-to-many derivation obvious, not just decorative.
5. **Deployability** — the frozen static site has no live API; the button must not become dead on `ShapeSense_Deployed`.

---

## Response

The core idea — walking every enabled slider in small bounded steps while holding `seed` fixed — is well suited to both `studio/web/js/pages/stage2.js` and `studio/web/js/pages/stage3.js`, because it **isolates parameter sensitivity from random-draw variance**. A few details in `animateButton` (`studio/web/js/widgets/controls.js`) and `fanLines` (`studio/web/js/widgets/fan-lines.js`) determine whether the interaction stays crisp and bug-free.

**Why fixed-seed is the design's load-bearing choice (depth):** if the seed changed per step, the reader would see a different augmentation *and* a different parameter on every tick — two variables moving at once. The animation would look alive but teach nothing about which slider caused which change. Fixing the seed makes the parameter the only varying input, so the visual delta is attributable to the slider walk. Every subsequent review point is in service of preserving that attribution.

### 1. Skip disabled sliders and preserve ordered bounds

- **Stage 2 (`stage2.js`):** `CLASS_RISK` (`nonuniform_scale`, `shear_deg`) is disabled when the selected class is in `d.no_shear` (`circle`, `ellipse`, `square`, `rectangle`, `diamond`).
- **Stage 3 (`stage3.js`):** class-specific sliders (`ellipse_max_axis_ratio`, `rectangle_max_side_ratio`, `diamond_lo`/`diamond_hi`, `star_lo`/`star_hi`) are disabled whenever another class is active.

The tick loop should:
- check `if (input.disabled) continue;` so hidden constraints never drift, and
- invoke `onStep?.(key)` using `keepOrdered` so `scale_lo <= scale_hi` and `radius_lo <= radius_hi` / `diamond_lo <= diamond_hi` / `star_lo <= star_hi` invariants remain valid on every step.

**Why skipping disabled sliders is not just tidiness (complex logic):** a disabled slider represents a constraint the current class *does not have*. Walking it would silently change a value that the user cannot see and cannot verify — and that may be re-enabled later when a different class is selected, producing a config the user never chose. Skipping is what makes the animation's parameter state equal the user's visible parameter state.

**Why `keepOrdered` on every step, not just at the end (depth):** a bounded random walk on `lo` and `hi` independently can cross them mid-walk. Even if the final step is ordered, an intermediate request to `/api/synth` with `diamond_lo > diamond_hi` would either fail or produce a degenerate sample — and the animation's whole purpose is to show *every intermediate step*. Ordering must be an invariant of the walk, not a postcondition of its endpoint.

### 2. Step size, quantization, and wall-bounce

Move by:

```js
direction[key] * Math.max(step, (max - min) * 0.03) * (0.5 + Math.random())
```

- flip `direction[key]` with 20% probability or upon hitting `[min, max]`,
- snap with `Number((min + Math.round((next - min) / step) * step).toFixed(6))`.

**Why the step floor is `max(step, (max - min) * 0.03)` (depth):** a fixed absolute step is too small on wide ranges (slow, imperceptible motion) and too large on narrow ranges (jumpy, skips values). The `3% of range` term scales the step to the slider's own domain; the `step` floor prevents sub-quantum motion on sliders whose range is smaller than 3% of its span. The `(0.5 + Math.random())` multiplier keeps the motion from looking mechanical without letting any single step exceed 1.5× the nominal size.

**Why snapping with `toFixed(6)` matters (edge case):** decimal sliders (`0.01`, `0.05`, `0.1`) accumulate floating-point drift over hundreds of ticks — `0.1 + 0.2` becomes `0.30000000000000004`. Without snapping, the displayed value drifts from the slider's own quantization, and the API receives a value the slider cannot represent. The `toFixed(6)` snap to the slider's `step` grid keeps the animation's values identical to what a user could set by hand.

**Why random flips *and* wall-bounce (depth):** wall-bounce alone would make the walk predictable — every slider traces the same triangle wave. Random flips alone would let a slider drift off one wall and never return. Together they produce a walk that explores the range without becoming a loop, which is what makes the animation informative across many ticks rather than just the first few.

### 3. Concurrency, tab visibility, and manual takeover

Both pages issue async `POST /api/augment` or `POST /api/synth` calls inside `refresh()`.

- **`singleFlight` wrapper.** Prevents out-of-order responses if a 700 ms tick overlaps a slow server call.
- **`if (document.hidden) return;` guard in `tick`.** Avoids background CPU churn.
- **`input` listeners on every slider plus `Reset to config`.** Manual user control immediately calls `stop()` and toggles `aria-pressed="false"`.

**Why `singleFlight` is correctness, not optimization (complex logic):** a 700 ms tick against a server that occasionally takes 1.2 s will, without a guard, deliver responses out of order — the tick at `t=700` arrives after the tick at `t=1400`, and the page renders the older response. The animation would appear to *stutter backward*, which reads as a bug even though every individual response was correct. `singleFlight` makes the rendered state always the most recent *requested* state, which is the only state the reader can interpret.

**Why manual takeover must call `stop()` (edge case):** a user who grabs a slider while the animation is running is asserting control. If the animation continues, the next tick overwrites their input — the user's action appears to have no effect. Stopping on input is the difference between "the animation yields to the user" and "the animation fights the user."

**Why `document.hidden` matters beyond CPU (depth):** a background tab still fires `setInterval`, but `requestAnimationFrame` throttles. Without the guard, ticks accumulate *requests* while the tab is hidden, then all resolve when the tab is foregrounded — the reader sees a burst of stale frames. Guarding on `document.hidden` keeps the visible frame rate equal to the requested frame rate.

### 4. Directed fan lines and row spacing

In `fanLines()` (`studio/web/js/widgets/fan-lines.js`):

- Draw a trunk from the **right edge of `original`** (`x0 = from.right - box.left`) to **horizontal row buses** (`top - 16 - box.top`) with vertical drops and `#fan-head` arrow markers into each `.tile` in `.fan-tiles`.
- Increase **row gap** between `.fan-tiles` rows so the horizontal bus (`top - 16`) sits cleanly in whitespace rather than clipping the previous row's tiles.
- Observe the container with `ResizeObserver`.
- Clear `lines` when `Math.min(...rects.map(r => r.left)) < from.right` so stacked phone layouts do not render broken cross-column paths.

**Why "trunk to bus to drop" rather than "line to each tile" (depth):** a fan of N direct lines from the original to N tiles crosses itself N² times, which reads as a mesh rather than a derivation. A trunk → horizontal bus → vertical drop is the standard org-chart idiom: one origin, one horizontal spine, N unambiguous drops. The reader sees "one original, many copies" without having to trace a single line through a crossing.

**Why `Math.min(...rects.map(r => r.left)) < from.right` is the phone-stacking guard (edge case):** on a phone layout, `.fan-tiles` wraps below the original rather than beside it, so the tiles' left edge is to the *left* of the original's right edge. Drawing lines in that state produces paths that run backward across the original and off-screen. Detecting the stack and clearing `lines` degrades to "no arrows" rather than "broken arrows" — the correct failure mode, because the row-wrapped tiles are already visually readable as a set without the trunk.

**Why `ResizeObserver` and not a window `resize` listener (depth):** the container can resize without the window resizing — a sidebar collapsing, a font loading, a `details` element opening. A window listener misses all of these; `ResizeObserver` catches the container's own geometry changes, which is the geometry the lines are drawn against.

### 5. Static deployment note (`ShapeSense_Deployed`)

For the frozen static site (`stages/stage_7.md` R8), live `/api/augment` and `/api/synth` calls are unavailable; pre-rendered preview frames (`snapshot/previews/augment/` and `snapshot/previews/synth/`) should replace live generation **without leaving dead buttons**.

**Why "without dead buttons" is a real constraint (depth):** the static site is what a reviewer sees first. An Animate button that does nothing on `ShapeSense_Deployed` is worse than no button — it signals "this feature exists and is broken." Pre-rendered frames preserve the demonstration while making the static site's capability honest: the animation plays, the parameters are visibly varying, and the reader learns the same lesson as in Studio, just against a fixed set of frames rather than a live server.

---

## Validation

Student `40211352` and the team exercised `animateButton` and `fanLines` in Studio across all **10 classes** on:
- **Stage 2:** `6`, `12`, `24`, `48` variants.
- **Stage 3:** `24` generated samples.

Verified:
- disabled sliders stay frozen,
- `lo <= hi` bounds hold,
- touching any slider stops animation,
- `ResizeObserver` keeps SVG bus lines aligned across desktop and narrow viewports.

In `ShapeSense_Deployed`, `tests/browser_checks.mjs` (`snapping` and `pages` checks across light, dark, and `390 px` phone views) verified **no SVG clipping or horizontal overflow** and **clean preview stepping** on `stage2.html` and `stage3.html`.

**Why the 10-class × 4-variant × 2-page matrix matters (audit logic):** the disabled-slider rule is class-conditional (`no_shear` on 5 of 10 classes; class-specific sliders on Stage 3). A test on one class would verify one branch; the matrix verifies that every class's disabled set is skipped and every class's ordered-pair invariant holds. The animation's correctness claim is conditional on the class, so the validation must cover the class domain, not a sample.

---

## Our decision

Kept Gemini 4 Neon's design and implementation checks in commit `ff7ddbf` (building on `fanLines` from `33858dc`):

- **`animateButton`** in `studio/web/js/widgets/controls.js` — `interval = 700`, `document.hidden` check, `input.disabled` skip, `onStep: keepOrdered`, stop-on-manual-input.
- **`fanLines`** in `studio/web/js/widgets/fan-lines.js` — increased `.fan-tiles` row spacing and phone-stacking guard.

**Rationale for keeping the design verbatim:** the response's five points are not independent improvements — they are the **minimum set** that preserves the design's central claim (fixed seed isolates parameter sensitivity). Each addresses a specific way that claim could be undermined:
- Point 1 (skip disabled, keep ordered) — a disabled slider would vary an invisible parameter, breaking the attribution.
- Point 2 (step/quantize/bounce) — unquantized drift would make the visible value differ from the walked value.
- Point 3 (singleFlight, hidden, takeover) — out-of-order or overridden state would make the rendered frame not the requested frame.
- Point 4 (trunk→bus→drop, stack guard) — a mesh would obscure the one-to-many claim; a broken cross-column path would misstate it.
- Point 5 (static preview) — a dead button would make the demonstration silent on the deployed site.

Removing any one leaves the design's central claim demonstrable in the happy path but false in a specific edge case.

---

## Measured effect

Both interactive pages (`stage2.html`, `stage3.html`) expose `Animate` / `Stop` (`aria-pressed`) walking all enabled sliders with `seed` fixed (`seed = 7` on Stage 2, `seed = 3` on Stage 3), with:
- **zero overlapping SVG lines**, and
- **zero stale out-of-order renders** during continuous 700 ms stepping.

All **535** Studio/pipeline tests and `ShapeSense_Deployed` browser checks (`pages`, `snapping`) pass across light, dark, and phone views.

**Interpretation (depth):** the measured effect has two distinct claims that should not be conflated:
- *Zero overlapping SVG lines* — a geometry claim, verified by browser checks across viewports.
- *Zero stale out-of-order renders* — a concurrency claim, verified by `singleFlight` and by continuous stepping without stutter.

The second is the harder one to verify and the one that most distinguishes this implementation from a naive `setInterval` + `fetch`. "Zero stale renders during continuous stepping" is the observable consequence of the `singleFlight` guard; without that guard, the same test would show stutter within a few ticks under any realistic server latency.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added **"fixed-seed is the design's load-bearing choice"** (every other point preserves the attribution) | Logical rigor |
| 3 | Added **"why skipping disabled sliders is correctness, not tidiness"** (invisible parameter would drift) | Depth |
| 4 | Added **"why `keepOrdered` on every step, not just at the end"** (intermediate requests must be valid) | Logical rigor |
| 5 | Added **"why the step floor is `max(step, 3% of range)`"** (scales to slider domain; floor prevents sub-quantum motion) | Depth |
| 6 | Added **"why `toFixed(6)` matters"** (floating-point drift on decimal sliders) | Edge-case logic |
| 7 | Added **"why random flips *and* wall-bounce"** (explores without becoming a loop) | Depth |
| 8 | Added **"why `singleFlight` is correctness, not optimization"** (out-of-order responses look like stutter) | Logical rigor |
| 9 | Added **"why manual takeover must call `stop()`"** (animation fights the user otherwise) | Edge-case logic |
| 10 | Added **"why `document.hidden` matters beyond CPU"** (background tab accumulates stale frames) | Depth |
| 11 | Added **"why trunk → bus → drop, not line-to-each"** (mesh vs. org-chart idiom) | Depth |
| 12 | Added **"why the phone-stacking guard clears lines"** (broken arrows worse than no arrows) | Edge-case logic |
| 13 | Added **"why `ResizeObserver` and not `resize`"** (container can resize without window) | Depth |
| 14 | Added **"why 'without dead buttons' is a real constraint"** (dead button signals broken feature) | Deployment logic |
| 15 | Added **"why the 10-class × 4-variant × 2-page matrix matters"** (disabled-slider rule is class-conditional) | Audit logic |
| 16 | Added **alternative-rejection rationale** for keeping the design verbatim (each point preserves the central claim in a specific edge case) | Decision depth |
| 17 | Added **interpretation** distinguishing geometry claim from concurrency claim | Coherence |

**Open questions / assumptions (for the team to confirm):**
- Is `interval = 700` a **measured** choice (e.g., matched to average `/api/augment` latency) or a guess? If server latency exceeds 700 ms, `singleFlight` will skip every other tick, and the animation will step at half the requested rate without the user knowing.
- Does `keepOrdered` **bounce both members of the pair** when one hits a wall, or only the one that hit? Bouncing only one can leave `lo` pushed against `hi` and the pair moving as a unit — visually a slider that appears frozen while its partner moves. The intended behavior is not stated.
- Does the **stop-on-manual-input** also fire on `Reset to config` (a button, not a slider)? The text says "input listeners on every slider plus Reset to config," which suggests yes — worth confirming it is one code path, not two.
- On `ShapeSense_Deployed`, do the pre-rendered frames **step in sync with the slider** (parameter and image advance together), or does the slider move while the frames cycle independently? The demonstration's lesson depends on the synchronization.
- Is there a **visual regression test** for `fanLines` across the 10 classes and 4 variant counts? The browser checks verify clipping and overflow but not that the trunk connects to the correct tile in every configuration — a misrouted arrow would pass `snapping` and `pages` while showing the wrong derivation.

---

## Upgraded & Expanded Technical Analysis (`C46`)

### 1. Bounded Random-Walk Algebra & Paired-Slider Order Invariants
In `studio/web/js/widgets/controls.js::animateButton`, each enabled slider $k$ with domain $[m_k, M_k]$ and quantization step $s_k$ updates every $\Delta t = 700\text{ ms}$ via a reflecting quantized random walk:
1. **Step Magnitude & Stochastic Jitter:**
   $$\delta_k = d_k \cdot \max\big(s_k, \; 0.03(M_k - m_k)\big) \cdot (0.5 + U), \quad U \sim \mathcal{U}(0, 1)$$
   where direction $d_k \in \{-1, +1\}$ flips with probability $p = 0.20$ per tick or deterministically upon hitting the boundary ($x_k + \delta_k \notin [m_k, M_k]$).
2. **IEEE-754 Quantization Snapping:**
   $$x_k^{\text{next}} = \text{Number}\!\left(\left(m_k + \text{round}\!\left(\frac{\text{clamp}(x_k + \delta_k, m_k, M_k) - m_k}{s_k}\right) \cdot s_k\right).\text{toFixed}(6)\right)$$
   Snapping via `toFixed(6)` eliminates base-2 floating-point drift (such as `0.30000000000000004` on `0.01`-step sliders).
3. **Coupled Interval Projection (`onStep: keepOrdered`):** For paired range sliders $(l, u) \in \{(\texttt{scale\_lo}, \texttt{scale\_hi}), (\texttt{radius\_lo}, \texttt{radius\_hi}), (\texttt{diamond\_lo}, \texttt{diamond\_hi}), (\texttt{star\_lo}, \texttt{star\_hi})\}$, invoking `keepOrdered(key)` immediately after updating slider $k$ projects the partner slider onto the half-space $x_l \le x_u$, preventing inverted intervals before `refresh()` reads the form state.

### 2. Concurrency Control (`singleFlight`) and Lifecycle Hygiene
- **Why `singleFlight` Instead of Last-Write-Wins:** When `animateButton` ticks every $700\text{ ms}$ against `POST /api/augment` (or static preview resolution), an overlapping request under naive `fetch()` can resolve out of order (response $t_1$ arriving after response $t_2$), causing the preview tiles and `fanLines` arrows to jump backward relative to the slider thumbs. `singleFlight` serializes execution so at most one request is in flight and only the latest pending state is scheduled next.
- **Background Tab Suppression (`document.hidden`):** Early-returning on `if (document.hidden) return;` inside the `setInterval` callback halts network and canvas churn when the browser tab is backgrounded, while manual `input` events on any slider immediately invoke `stop()` (`aria-pressed="false"`) so user dragging never fights the timer.