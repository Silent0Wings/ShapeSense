# 2_data_preparation/transformation - Why augmentation lost in iteration 1

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: F07, F08, F09, C03, C05, C06
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [F07](../../../2_data_preparation/transformation/claude_opus/02_F07_rotation-up-to-180-hurt-the-classes-that-dep.md), [C03](../../../2_data_preparation/transformation/claude_opus/04_C03_rotation-range.md)

## Prompt 1 (00:59)

> INVESTIGATE WHY IS IT THAT AUGMENTATION FAILED , BECAUSE IN ALL LOGICAL SCENARIOS AUGMENTATION SHOULD HELP , THIS MEANS SMTH WRONG HAPPENDE THAT WE DIDNT ACCOUNT FOR , DATA CORRUPTION BAD LOSS FUNCITON OF INCOMPATIBLE FEATURES SPAWN FABLE SUB AGENT [
>
> <pasted_content id="8717">
> Possible reasons, none of them tested:
>
> B swaps real images for synthetic ones instead of adding them: 179 real images per batch against A1's 256.
> The clean generated shapes may not look enough like hand-drawn ones.
> Heavy rotation and scaling may blur the line between similar classes such as square and rectangle.
> A0's lead may be partly inflated, because Stage 1 found that a shape's source can give away its class, and an unaugmented model can exploit that.
> </pasted_content id="8717">
>
> ]

## Response 1

I'm sending this to a Fable agent now. I've told it to treat this as an open question, testing for real bugs (data corruption, a bad loss, incompatible features) and for genuine causes alike. It works only on train and validation data, in the scratchpad, so the sealed test split and the verdict stay untouched.

The drawing pad now matches the theme: dark paper with white ink in dark mode, white paper with black ink in light mode. It switches instantly with the theme button, even with a drawing already on it. Refresh the page to get it (`4bd50eb`).

I checked the actual pixels in Chrome. In both themes the image sent to the models is still black on white, and a drawn circle still comes back as "circle" from all three models. The small "What the model saw" preview stays black on white on purpose, since that's the real model input.

The Fable agent is still investigating why augmentation lost. I'll report its findings as soon as it finishes.

## Prompt 2 (01:19)

> WELL THIS CLARIFY ALOT =[
>
> <pasted_content id="8717">
> rectangle
> 93.3
> 80.2
> 79.3
> diamond*
> 99.0
> 86.0
> 85.4
> square
> 97.6
> 90.3
> 89.7
> octagon
> 87.2
> 90.8
> 91.3
> </pasted_content id="8717">
>
> ] ARE GEOMETRICALY CLOSE , AGRESSIVE AUGMENEATION WILL DEFINITLY BLUR THE LINE BETWEEN THEM AND MAKE A AUGMENTED OR SYNTHETIC

## Response 2

You're very likely right about those three classes, and the early evidence agrees. But octagon, which you included, moves the opposite way, and that sharpens the explanation.

| Class | A0 | A1 | B | Effect of augmentation |
|---|---|---|---|---|
| Rectangle | 93.3 | 80.2 | 79.3 | Much worse |
| Diamond | 99.0 | 86.0 | 85.4 | Much worse |
| Square | 97.6 | 90.3 | 89.7 | Worse |
| Octagon | 87.2 | 90.8 | 91.3 | **Better** |
| Hexagon | 88.3 | 89.7 | 90.5 | **Better** |

Hexagon and octagon are geometrically close too, yet augmentation helped them. So being close isn't the whole story. It seems to matter what separates the classes:

- **Corner count (hexagon, octagon):** rotating a shape doesn't change how many corners it has, so more variety teaches the model the right thing.
- **Orientation or proportions (square, diamond, rectangle):** rotate a square 45° and it looks much like a diamond. The ±180° rotation may remove a cue that A0 was free to use. That cue would be real in this data if, for example, diamonds usually appear upright, but the agent still has to measure that.

The early result fits this: with rotation off, A1 seed 0 recovered its diamond F1 from 84.6 to 95.5. That's still only one run, though.

Shear and non-uniform stretch were already switched off for these classes because they would change the label. That points to rotation, or to the scaling and re-framing, rather than those two.

If this holds, there's no data corruption or loss bug behind it. The augmentation design would simply be wrong for these classes: every rotation is geometrically valid, but the range was set by hand at ±180° and never tested. B is also slightly lower on these three classes, but it uses the same augmentation, so this doesn't tell us much about the synthetic shapes themselves.

The agent is still testing this directly, including a reduced ±15° rotation and whether A0's lead survives on an unseen source. That last check matters most, because if A0 falls behind there, its lead was partly memorizing dataset style, and augmentation was doing its job after all. I'll bring you the full results when it finishes.

## Prompt 3 (10:02)

> does this now show up as a new iteraation of our crips stages as a falure =[Why augmentation lost in iteration 1: it wasn't data corruption or a bad loss function. Rotating up to ±180° removed an orientation clue the classes rely on. The augmentation code also made shapes about 6 px too small and broke thin strokes.
> ] because we need to docment all the falure we faced and how we overcame them

## Response 3

Let me check what the log and dashboard actually say about this before answering.

All 431 tests pass, and only Stage 6 reran, so there was no retraining and no new test reads. Now I'll check how the tables look in the PDF and on the home page.

The 17 rows and links all render. The traceback is just my check script reading SVG text the wrong way, which I'll fix. Next I'm reading the evidence and endpoint shapes for the visuals.

I caught a mistake of mine while gathering evidence. The source-classifier figure I wrote into the ledger may be described wrongly, so I'll check the original note before building on it.

The icons, rotate, scale, undo and save all work, and every failure page loads without errors. I'll delete the one test drawing my check saved and look at how the pages actually render.

The visuals and the icon buttons render well. While the stress test and the audit check finish, I'll build the dashboard page that compares the two validation sets.

The page is in place and the stress test is about halfway through the models. I'm waiting on that run and the audit check before reporting either.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The investigation ran on validation only, so the sealed test split was not read again. Its three causes were each checked on their own: rotation range (F07), framing margin, about 51 px against 57 px real (F08), and thin-stroke breakage, 17.2 pieces per stroke (F09).

## Our decision

We rejected the first guesses (data corruption, a bad loss function) once the evidence pointed at the augmentation settings. Rotation was cut from ±180° to ±20°, capped at ±10° for square, rectangle and diamond (C03). The framing margin was corrected (C05), and thin lines got a separate path, giving 1.0 piece per stroke (C06). We also kept the user's point that square, rectangle and diamond are geometrically close, which the per-class table supported.

## Measured effect

The fixes went into iteration 2. On the reused test split A2 vs A0 was +0.06 macro F1, and +0.08 on the fresh holdout, with both CIs including 0 (F14). So the fixes removed the damage but did not create a clean-test gain.
