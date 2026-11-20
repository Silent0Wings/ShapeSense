# 7_meta_and_other - P036: Banner image placement in README and which banner to use
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P036. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[Image: original 2400x1792, displayed at 2000x1493. Multiply coordinates by 1.20 to map to original image.]

## Response

I added the banner at the top of [README.md](../../../README.md), centred above the title at 640 px wide.

##### Which banner
You had two banners. I used `banner4x3.jpg`, the wider one, because it suits the top of a README. To use the square one instead, change the filename to `banner1x1.jpg` in the first lines of the README.

##### Current state
Nothing is committed yet. The README change and the `assets/` folder are still uncommitted. The images are about 2.2 MB and 0.5 MB, plus a 1.8 MB icon.

Tell me when you want them committed, and I will run the commit through the guard.

##### Why the wider banner
A 4x3 image fits the width of the README header and reads well at the 640 px size used here. The square banner would take more vertical space above the title. The choice is a layout decision, and switching is a one-line change to the filename.

##### Consequence
The README now opens with an image. The image sizes (about 2.2 MB and 0.5 MB, plus a 1.8 MB icon) are relevant if the repo size matters, which the answer does not assess.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
