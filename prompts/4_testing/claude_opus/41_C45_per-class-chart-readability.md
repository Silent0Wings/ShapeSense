# 4_testing - C45: Per-class chart readability
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C45 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40297573 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c45, studio/web/js/svg/charts.js, studio/web/js/pages/stage5.js, studio/web/js/pages/stage4.js, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/stage4.html, commit ff7ddbf

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
On the Evaluation page's per-class F1 chart, the five arms often score within a fraction of a point of each other, so their dots sit on top of each other and you only see one colour. Since P was added, the fifth score column also runs off the right edge. Someone suggested a log scale to pull the dots apart. Should we do that, or is there a better layout that keeps distances honest?

## Response
I would not use a log scale. The scores sit high on a 0 to 100 range, and a log axis stretches only one end of it: equal gaps in F1 would get different widths depending on where they fall, so a reader comparing "A2 is 1 point above A0" in two rows would see two different distances. A reverse-log trick has the same problem in the other direction. The axis should stay linear; the collision is a layout problem, not a scale problem.

| Option | Separates dots | Distances honest | Cost |
|---|---|---|---|
| Log scale | Partly, one end only | No | Misleading reading |
| Bigger chart, same layout | Only if gaps are wide | Yes | Still collides at sub-point gaps |
| Zoomed linear axis | Better | Yes, if the start is stated | Needs a note that the axis does not start at zero |
| Lanes on a linear axis | Always | Yes | Taller rows where dots collide |

Recommendation: lanes plus a zoomed linear axis.

1. **Lanes.** Sort a row's dots by x. A dot that would land within a minimum gap of an already placed dot in the same lane moves to the next lane, alternating above and below the line (0, -1, 1, -2, 2, ...). Only rows that need lanes grow taller. Vertical position then carries no meaning, so say so in a note under the chart, and only show the note when some row actually used a lane.
2. **Columns that fit.** Give each arm its own value column on the right and compute the SVG width from the last column, with a sensible minimum, instead of a fixed width. Tighten column spacing when there are more than three series.
3. **Winner marking.** Put the best score in each row on a small pill in that arm's colour, with bold dark text, so the row's answer reads without hunting for dots.
4. **Zoom.** On Evaluation, start the axis at the lowest score rounded down to a multiple of 5 and end at 100. Reuse the same component for the validation-by-seed chart on Training, zoomed to that chart's own minimum and maximum.
5. **Hover.** Make the whole row a transparent hover band listing every arm's exact value.

Cautions: keep the range bar between the lowest and highest dot on the real axis position, so lanes never fake a spread, and keep the numbers in tabular figures so columns line up.

## Validation
`studio/web/js/svg/charts.js` contains `dodge` (lanes `[0, -1, 1, -2, 2, -3, 3]`, default gap 17) and `scoreRows` (lane height 15, width `Math.max(780, last column + 14)`, best value on a coloured `rect`, row hover band). The note "Only left and right position carries the score." appears only when `layout.some((r) => r.lanes.some(Boolean))`. `stage5.js` calls `scoreRows` with domain `[Math.floor(lo / 5) * 5, 100]`, and `stage4.js` uses it for "Validation macro-F1 by seed and arm" with the domain rounded to the observed scores. The same pages are published as `ShapeSense_Deployed/web/stage5.html` and `stage4.html`.

## Our decision
Kept the linear axis and spread close dots into lanes. "A log scale would stretch only one end of the axis and distort distances, while lanes keep the axis honest." The chart widens to fit every column, the seed chart uses the same layout with its axis zoomed to the scores, and each row's winning score sits on a pill in that model's colour.

## Measured effect
No separate measurement recorded. The chart now holds all five arm columns (`A0`, `A1`, `B`, `A2`, `P`) inside its computed width.

---

## Expanded & Upgraded: Visual-Honesty Cluster Synthesis (`C45`, `C47`, `C52`, `C54`, `C55`)

### The Visual-Honesty Principle (`C45`)

A **log axis is a monotone but non-linear map**, so equal F1 gaps get unequal pixel widths — violating `"distance on screen ∝ distance in score."` Lanes preserve the linear axis and separate colliding dots by moving them *perpendicular*, with an explicit note `"Only left and right position carries the score."` shown *only when lanes are used*. That conditional note is a key subtlety: a permanent disclaimer trains readers to ignore it; a conditional one fires only when the vertical offset exists.

### The Cluster Theorem (`C45`–`C55`)

Every display element that shows a number must:
1. **Show its condition** (`C54`: `"+9.20 on damaged images, +0.64 clean"`).
2. **Preserve distance** (`C45`: linear axis with perpendicular lanes, never a log scale).
3. **Explain whether an interval includes zero** (`C47`: full-row hover + earlier-sets table tooltips showing `[-0.24, 1.22]` includes zero).
4. **Teach the vocabulary before the taxonomy** (`C52`: three image kinds before the five models, with data-derived batch bars).
5. **Distinguish `Passed` / `Recorded` / `Failed` and derive from artifacts, never hand-typing** (`C55`: shared `stageBrief` across all 7 stages).

