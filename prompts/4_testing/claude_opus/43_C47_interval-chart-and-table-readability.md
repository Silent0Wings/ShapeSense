# 4_testing - C47: Interval chart and table readability
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C47 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / opus_medium_5.5 + 40211352
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c47, studio/web/js/svg/charts.js, studio/web/js/pages/stage5.js, studio/web/js/pages/experiments.js, docs/crisp_dm/README.md, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/experiments.html, commit ff7ddbf

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
On the Evaluation page, the confidence interval chart only shows a tooltip if you hit the tiny dot or the thin whisker, and each row's numbers float above its dot, so on a wide screen you lose track of which label goes with which interval. The table of earlier evaluation sets below it has no tooltips at all. How do we make each row easy to follow and explain itself on hover?

## Response
There are two separate problems: the eye cannot follow a row from label to mark, and the hover target is a few pixels wide. Fix both in the chart components so every page that uses them benefits.

**Chart rows (`ciChart`, and the dot charts in `valueBars`)**
1. **Row shading.** Shade every other row lightly, full width. It is the cheapest way to keep a long row together.
2. **Leader guide.** Draw a faint dotted line from the end of the label to the start of the interval (or the dot), so the label points at its mark.
3. **Value column.** Move the estimate and its range out of the plot into a right-aligned column with tabular figures and a header, instead of text floating above the dot. Numbers then line up and never collide with whiskers.
4. **Whole-row hover.** Lay a transparent rectangle over the full row and attach the tooltip to it. Hovering the label, the guide, the interval or the number all give the same explanation.

**Earlier-sets table**
Give every column a tooltip that answers the reader's real question:
- *Data*: whether the row is the never-read holdout or the test split already read in earlier iterations.
- *95% CI*: whether the range stays above zero, stays below zero, or includes zero, in plain words.
- *Result*: whether the success rule applies and was met, and that a reused set is weaker evidence; otherwise "reported for context".

This matters for the content, not only the looks: `docs/crisp_dm/README.md` reports A2 vs A0 at +0.64, CI [0.19, 1.07] on clean images and +0.52, CI [-0.24, 1.22] on the reused test split. A reader who cannot see at a glance that the second range includes zero will misread the table.

| Option | Pro | Con |
|---|---|---|
| Bigger dots and whiskers | Easy | Still a small target; numbers still float |
| Shading, guides, value column, row hover | Rows readable and every part explains itself | Slightly wider chart |

Recommendation: the second, applied to the shared components so the Experiments page dot charts get it too.

## Validation
In `studio/web/js/svg/charts.js`, `ciChart` and `valueBars` shade even rows (`var(--surface-2)`, opacity .55), draw a `stroke-dasharray: 1 5` guide from the label to the mark, print values right-aligned with `font-variant-numeric: tabular-nums`, and attach `hover(band, tip)` to a full-row band. In `stage5.js`, the earlier-sets table gives `Data`, `95% CI` (`rangeTip`) and `Result` (`resultTip`) their own tooltips. `experiments.js` uses `valueBars` for its dot charts. The pages are published as `ShapeSense_Deployed/web/stage5.html` and `experiments.html`.

## Our decision
Adopted: rows are shaded with a guide from label to dot and a value column, the whole row shows a tooltip, and every cell of the earlier-sets table explains itself. The Experiments page dot charts got the same shading and guides. Reason recorded: rows were hard to follow across the chart, and labels and values gave no feedback on hover.

## Measured effect
No separate measurement recorded.

---

## Expanded & Upgraded: Visual-Honesty Cluster Synthesis (`C47`)

### Row Legibility and Contaminated-Comparison Tooltips

Shading even rows (`var(--surface-2)`), drawing a dotted leader guide (`stroke-dasharray: 1 5`), moving numbers into a tabular-figure value column, and attaching a full-row hover band solve two distinct hazards:
1. **Perceptual tracking:** prevents the eye from misassociating a comparison label with the wrong interval whisker across wide viewports.
2. **Statistical interpretation of earlier sets:** in the earlier-sets table (`stage5.js`), the reused-test CI `[-0.24, 1.22]` **includes zero**, which a reader must see immediately or they will misread a null/contaminated result as a positive gain. The tooltips on `Data`, `95% CI` (`rangeTip`), and `Result` (`resultTip`) act as a **correctness layer for contaminated comparisons**, implementing the cluster theorem alongside `C45`, `C52`, `C54`, and `C55`.

