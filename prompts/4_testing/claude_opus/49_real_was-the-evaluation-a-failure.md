# 4_testing - Did the Stage 5 evaluation fail?

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: F04
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [F04](../../4_testing/claude_opus/29_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md)

## Prompt (00:57)

> SO THE EVALUATION FAILED ? =[
>
> <pasted_content id="8717">
> Stage 5 · CRISP-DM evaluation
>
> Evaluation
> Each model read the sealed test split exactly once. Everything on this page comes from what Stage 5 saved, so this page never reads the split again.
>
> Verdict
> -0.36
> ✕
> Fail
> B vs A1, macro-F1 points, 95% CI [-1.17, 0.41]
> gain -0.36 < 1.00 points. CI includes 0 ([-1.17, 0.41])
>
> A0 ensemble
> 93.9
> A1 ensemble
> 90.9
> B ensemble
> 90.5
> Test reads
> 13 / 13
> extra: 0
> Expected half-width
> 0.63
> limit 1
> </pasted_content id="8717">
>
> ]

## Response

Yes, but what failed is the hypothesis, not your project. The test asked whether adding synthetic shapes beats augmentation alone, and it doesn't: B scored 0.36 points below A1. The target was a gain of at least 1 point, with a confidence interval that excludes 0. The interval, −1.17 to +0.41, includes 0, so B is no better than A1 and may be about equal.

**The project itself worked:**
- All seven stages passed, and the models score 90 to 94 macro-F1, against 84.3 for the best baseline.
- The test was run cleanly: the rule was fixed in advance, the test split was read exactly as planned, and the check had enough power (expected margin 0.63, limit 1). So this is a real negative result, not an inconclusive one.
- The report treats a fail as a valid outcome. I can't say how it will be graded, because the rubric isn't in the repo, but an honest negative result with this much rigour is usually a strength.

**What the results show:**
- A0, with no augmentation at all, scored highest at 93.9, ahead of A1 (90.9) and B (90.5).
- Most of that gap is in rectangle (A0 93.3, A1 80.2, B 79.3), diamond (99.0, 86.0, 85.4) and square (97.6, 90.3, 89.7).
- B does slightly better than A1 on Quick, Draw! sketches (86.1 vs 85.0% accuracy) and on the unseen Hand-Drawn source (72.7 vs 71.9 macro-F1). The Hand-Drawn figure is one model on 302 images, so it's only a hint.

**Possible reasons, none of them tested:**
- B swaps real images for synthetic ones instead of adding them: 179 real images per batch against A1's 256.
- The clean generated shapes may not look enough like hand-drawn ones.
- Heavy rotation and scaling may blur the line between similar classes such as square and rectangle.
- A0's lead may be partly inflated, because Stage 1 found that a shape's source can give away its class, and an unaugmented model can exploit that.

**Don't change the model or settings now to make it pass.** The test set has already been seen, so any improvement would be tuned to it and would undermine the result.

For the report, I'd present this as the finding: synthetic data as a substitute didn't help here. If you have time for more, the natural follow-up is the deferred `B_equalreal` run, which adds synthetic images on top of the real ones. It would have to be labelled exploratory, separate from this verdict. Do you want me to set that up?

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The verdict came from Stage 5's own saved output: one read of the sealed test split per model, 13 of 13 planned reads, and expected CI half-width 0.63 against a limit of 1.

## Our decision

We kept the failed verdict unchanged (B vs A1 = -0.36 macro F1, 95% CI [-1.17, 0.41]) and investigated on validation only. That decision started iteration 2.

## Measured effect

No change to the model. The recorded result stays -0.36 macro F1 for B vs A1.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`49_real` — The Honest Negative)

### Epistemic Role of the Unaltered Negative Result (`F04`)

In the four-layer evidence architecture of `4_testing`, `49_real` (Iteration 1's `-0.36` macro-F1 failure, 95% CI `[-1.17, 0.41]`) and `50_real` (Iteration 3's `+9.20` pass, 95% CI `[8.89, 9.53]`) are the **same methodological discipline applied twice**: fix the decision rule before unsealing the test split, execute exactly one read (`13/13` reads in Iteration 1), and report the outcome without post-hoc adjustment.

1. **Refusal to Re-Score or Redefine Success Post-Read:** Even though `A1` and `B` already outperformed `A0` on unseen Hand-Drawn shapes (`66.4%` and `71.8%` vs. `53.5%`), the primary pre-registered test was `B vs A1` on the same-source test split. Because `-0.36` missed the `+1.0`-point threshold and its CI straddled zero, the verdict was locked as `fail`.
2. **Validation-Only Diagnostic Decomposition:** By freezing the failed Iteration 1 artifacts and restricting all root-cause probing (`±180°` orientation destruction, `~6 px` scale contraction, `1-px` stroke fragmentation into `17.2` pieces) strictly to the `2,819`-image validation split, the team prevented test-set hill-climbing and established the clean baseline from which Iteration 2 (`F14`) and Iteration 3 (`C23`) were pre-registered.

