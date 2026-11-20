# 4_testing - C46: Animate button on Augmentation and Synthetic generator
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/14_C46_animate-button-on-augmentation-and-synthetic.md](../gemini_4_neon/14_C46_animate-button-on-augmentation-and-synthetic.md)
- Date: 2026-11-10
- Entry: C46 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / 40211352
- LLM role: reviewed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c46, studio/web/js/widgets/controls.js, studio/web/js/widgets/fan-lines.js, studio/web/js/pages/stage2.js, studio/web/js/pages/stage3.js, studio/server/schemas.py, ShapeSense_Deployed/web/js/widgets/controls.js, commit ff7ddbf

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
I added an Animate button to the Augmentation and Synthetic generator pages. It walks every enabled slider in small random steps, keeps the same random draw, and on Augmentation I draw arrows from the original image to each augmented copy. Can you review it? Is it clear and correct, and what would you change?

## Response
The idea is sound, and the one choice that matters most is already right: keeping the same random draw (`seed`) while the sliders move. Then every change on screen comes from the settings, not from a new draw, which is exactly what the page wants to teach. A few points to check before it ships:

| Area | What I see | Suggestion |
|---|---|---|
| Which sliders move | `animateButton` skips `input.disabled`, so class-restricted controls stay put | Keep it |
| Step size | Each step is `max(step, 3% of the range)` times a random factor between 0.5 and 1.5, snapped to the slider's `step` | Fine; bounce off `min`/`max` so it never sticks at an edge |
| Ordered ranges | `scale_lo`/`scale_hi` on Augmentation and the lo/hi pairs on Synthetic can cross during a walk | Pass an `onStep` that keeps each pair ordered; the server rejects a crossed pair (`schemas.py`: "scale_lo must not exceed scale_hi") |
| Request rate | One preview request per tick | Keep the 700 ms interval and avoid stale responses overwriting newer ones |
| Stopping | Runs until stopped | Stop as soon as the user drags any slider, skip ticks while the tab is hidden, and switch the label between Animate and Stop with `aria-pressed` |
| Arrows | Lines from the original to each copy show where the copies came from | Add space between tile rows so lines do not cross tiles, redraw on resize, and hide them from screen readers |

Two things I would not add: a speed slider (one more control to explain) and per-slider animation toggles (the point is to see everything respond together).

On the static public site the previews come from saved snapshots rather than live Python, so check that the button does not leave a dead control there.

## Validation
`studio/web/js/widgets/controls.js` defines `animateButton({ sliders, onStep, refresh, interval = 700 })`: it skips disabled inputs, returns early when `document.hidden`, toggles `aria-pressed` and the Animate/Stop label, and stops on any manual `input` event. `studio/web/js/widgets/fan-lines.js` draws directed lines with an arrow marker, `aria-hidden="true"`, and repaints through a `ResizeObserver`. `stage2.js` and `stage3.js` both call `animateButton` with `onStep: keepOrdered`; `stage2.js` mounts `fanLines()`. The widget is also present in `ShapeSense_Deployed/web/js/widgets/controls.js`. Gemini 4 Neon reviewed the same feature.

## Our decision
Kept as designed by 40211352. Animate walks every enabled slider in small random steps with the same random draw, until stopped, and on Augmentation directed lines run from the original image to every augmented copy, with more space between rows. Reason recorded: "It shows how the images respond to the settings."

## Measured effect
No separate measurement recorded.

---

## Expanded & Upgraded: Interactive Parameter Exploration & Controlled Variance (`C46`)

### Isolating Parameter Effect from Stochastic Draw Variance

The core pedagogical invariant of `animateButton` (`studio/web/js/widgets/controls.js`) is **seed invariance during parameter perturbation**: by holding the random seed constant while walking enabled sliders in small bounded steps (`max(step, 3% of range)` with `onStep: keepOrdered`), every visual change across the augmented or synthetic tiles is causally attributable to the slider parameters rather than a new random draw. Skipping `input.disabled` preserves class-safe geometric rules (`no_shear_no_nonuniform_scale`), while `document.hidden` early-return, `aria-pressed` state toggling, and immediate cancellation on manual `input` events keep interaction deterministic and accessible.

