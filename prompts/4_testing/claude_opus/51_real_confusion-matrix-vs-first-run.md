# 4_testing - Is the current confusion matrix worse than the first run?

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-11 (times are local, UTC-5)
- Owner: 40256377
- Source: **exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (00:54)

> isnt current confusion matrix worst than the first run ?

## Response 1

I'll compare the stored results from the first run and the current one, and check whether both were scored on the same images.

Both runs' confusion figures exist. I'll compare the first run's A0 with the current A0 and A2.

No, the current models are better overall. The first run's best model got 2,621 of 2,776 test images right. Today's A2 gets 2,679, and today's A0 gets 2,665. Both runs were scored on the same 2,776-image test split: every row in the two figures has the same total (375 circles, 149 ellipses and so on), so the comparison is direct.

Two cells did get worse, and they're probably what caught your eye:

| Confusion | First run (A0) | Now (A0) | Now (A2) |
|---|---|---|---|
| Correct overall | 2,621 (94.4%) | 2,665 (96.0%) | 2,679 (96.5%) |
| Hexagon called octagon | 42 | 19 | 20 |
| Octagon called hexagon | 3 | 14 | 15 |
| Circle called ellipse | 3 | 5 | **18** |
| Triangle called ellipse or circle | 19 | 4 | 6 |
| Rectangle called triangle | 12 | 12 | 3 |

- **Hexagon and octagon.** The first run mostly called hexagons octagons, which made one dark off-diagonal cell. The current models split their mistakes between both directions. The total fell from 45 to 33–35, but the error now shows up as two light cells instead of one dark one, which can look messier.
- **Circle called ellipse (A2 only).** This went from 3 to 18 and is the one real regression. A2 trades a few circles for ellipses: it gets 12 more ellipses right and 12 fewer circles.
- **Everything else improved or stayed the same.** Triangle, rectangle, ellipse and hexagon all have more correct answers.

Two things to keep in mind:
- **This test split has been read in every iteration, so these numbers describe the models and shouldn't be used to tune them.** Iteration 3's pass came from a separate sealed holdout of damaged images, where A2 beat A0 by 9.20 points.
- **Clean-image gains are small.** The figures above are on clean images, where the gap between models is small by design, about +0.5 to +0.6 points for A2 over A0.

If the circle-to-ellipse drift matters for the public site, it would need a new pre-registered iteration with fresh sealed data, because tuning against this test split isn't allowed. Otherwise there's nothing to fix.

## Prompt 2 (00:55)

> in dasboard where do i find a2 confusion matrix ?

## Response 2

The A2 confusion matrix is on the **5 · Evaluation** page, in the left-hand navigation (`stage5.html`).

1. Scroll to the card titled **"Confusion matrices (soft-vote ensembles)"**.
2. Use the arm picker at the top of that card. It opens on A2, the shipped model, so you may already be looking at it. The other buttons switch to A0, A1, B and P.
3. Select a cell to see its count and share. For A2 only, cells in the three confusable pairs also show the stored misclassified images.

This is an interactive version of the same 2,776-image test matrix as the PNG figure I compared earlier.

The **Iteration 1** and **Iteration 2** pages show only the older runs' matrices, as static images. A2 didn't exist in iteration 1, and its iteration 2 version is from before the retraining.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Both runs were scored on the same 2,776-image test split. Row totals are identical in both figures.

## Our decision

We questioned the result. The answer showed overall improvement with two worse cells, and no change was needed.

## Measured effect

Correct test images: 2,621 for the first run's best model, against 2,679 for the current A2 and 2,665 for the current A0.

---

##  Analysis: Resisting the Visual-Salience Trap in Confusion Matrices (`51_real`)

### Why this exchange matters

The user suspects a regression (`"isn't the current matrix worse?"`). A naive answer would compare only the dark off-diagonal cells. The rigorous answer requires:
1. **Confirming invariant marginal distributions:** Both runs were scored on the exact same `2,776`-image test split with identical row totals (`375` circles, `149` ellipses, etc.), licensing direct cell-by-cell comparison.
2. **Separating error dispersal from error growth (`Hexagon` $\leftrightarrow$ `Octagon`):** In Iteration 1, errors concentrated asymmetrically (`42` `Hexagon` $\rightarrow$ `Octagon` vs. `3` `Octagon` $\rightarrow$ `Hexagon`, total `45`), producing one visually salient dark cell. In Iteration 3, total errors fell to `33–35`, split symmetrically (`19/14` for `A0`, `20/15` for `A2`) across two lighter cells.
3. **Isolating the one genuine boundary shift (`Circle` $\rightarrow$ `Ellipse` on `A2`):** `Circle` called `Ellipse` rose from `3` (`5` on `A0`) to **`18`** on `A2`, reflecting a precision-recall trade-off (`+12` more `Ellipse`s correct in exchange for `-12` `Circle`s).
4. **Enforcing the test-reuse boundary:** Because the `2,776`-image test split was read across every iteration, tuning against `Circle` $\rightarrow$ `Ellipse` drift on that split is prohibited without pre-registering a new iteration and fresh sealed holdout.

### Cross-Session Lineage

* **Related sessions:** [52_real_is-the-project-done-and-final-audit.md](52_real_is-the-project-done-and-final-audit.md) (final audit confirming 157 sealed reads), [55_real_dashboard-with-onnx-inference.md](55_real_dashboard-with-onnx-inference.md) (interactive Studio confusion matrix on `stage5.html`).

