# 4_testing - C54: Screen review fixes
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C54 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40304911 / 40304911
- LLM role: assisted
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c54, studio/web/js/plain.js, studio/web/js/pages/home.js, studio/web/js/svg/charts.js, studio/web/css/components.css, docs/crisp_dm/README.md, results/README.md, commit 9d24f95

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
I went through every screen of the dashboard and wrote down what bothered me: a headline that oversells the result, model names that are hard to read, a very long home page, chart labels that collide, and controls that are fiddly on a phone. Can you help me sort these by importance and suggest a concrete fix for each, starting with whatever could mislead a reader?

## Response
Your list is right; I would order it by harm. Something that misleads comes before something that is merely hard to read.

| Priority | Problem | Fix |
|---|---|---|
| 1 | The main headline gives the A2 vs A0 gain without saying it was measured on damaged images | Say "on damaged images" in the sentence and add the clean-image result after it |
| 2 | The Business page blends the iterations, so a reader cannot tell which question each verdict answered | Separate the iterations, each with its own question, comparison and image condition |
| 3 | Home page is very long | Replace the full iteration and failure lists with short summaries that link to their own pages; fold each finding after its first sentence |
| 4 | Faint model names and batch text | Use the primary text colour for model names and dark text on bright series colours |
| 5 | Colliding chart labels | Turn wide column labels upright and anchor first and last line labels inward |
| 6 | Small phone touch targets | Raise sliders and other controls to a comfortable height under a phone breakpoint |

On item 1, the numbers make the case. `docs/crisp_dm/README.md` records the Iteration 3 verdict as +9.20 macro-F1 points, 95% CI [8.89, 9.53], on damaged images, while clean images show only +0.64, CI [0.19, 1.07]. A headline that says "+9.20" alone invites a reader to believe the model is nine points better in general. The same file says it plainly: "The gain is in surviving damage, not in clean accuracy." The fix belongs in the shared sentence builder (`finding()` in `plain.js`) so every page that states a verdict gets it, not in one page's text.

For items 3 and 5, prefer changes that keep information over changes that drop it: summaries with links rather than deleting the lists, rotated labels rather than truncated ones. A truncated class name on a heatmap is a new way to mislead.

For item 6, check at the phone breakpoint the CSS already uses (620 px) and test on a real phone-sized viewport, since slider thumbs are the worst offender.

Cautions:
- After the headline change, search for other places that state the 9.20 figure without its condition.
- Contrast fixes on series colours must work in both light and dark themes.

## Validation
`studio/web/js/plain.js` now has `finding(verdict, { damaged })`, which adds " on damaged images" and appends `cleanSentence(verdict.clean)`. `studio/web/js/pages/home.js` uses `iterationSummary` and `failureSummary` instead of full lists. `studio/web/js/svg/charts.js` rotates wide labels with `rotate(-90 ...)`. `studio/web/css/components.css` sets `input[type="range"] { min-height: 44px; }` inside `@media (max-width: 620px)`. `results/README.md` lists the damaged-image result as +9.20 [8.89, 9.53].

## Our decision
Applied by 40304911: the headline says the gain is on damaged images and gives the clean result, the Business page separates the iterations, the home page is about half as long, findings fold after their first sentence, model names and batch text pass contrast, chart labels no longer collide, and phone touch targets are larger. Reason recorded: readers should be able to trust and read the results on every screen.

## Measured effect
The home page is recorded as "about half as long" (`iteration_log.json`). No other measurement recorded.

---

## Expanded & Upgraded: Visual-Honesty Cluster Synthesis (`C54`)

### Harm-Ordered UI Triage & Conditioned Headline Reporting

The screen review prioritized fixes by **epistemic harm**, not implementation effort. The headline fix (`"+9.20 on damaged images, +0.64 clean"`) was ranked #1 because an unconditioned `"+9.20"` **misleads** — inviting the reader to believe a general clean-data gain that Iteration 2 (`F14`) explicitly falsified. Placing the fix in the shared `finding(verdict, { damaged })` builder (`studio/web/js/plain.js`) ensures every page inherits the conditioned statement automatically: **a number without its condition is a false statement.**

