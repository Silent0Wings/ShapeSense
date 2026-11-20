# 4_testing - docs: add pipeline banner image to README
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T14, commit ba563ff (type: documented)
- Course stage: deployment (not a course stage) (filed here: deployment and support work goes under 4_testing)
- Worksheet entries: none (commit_tasks.csv T14 lists the proposal as opus_medium_5.5 + 40256377)
- Source: **real exchange.** Saved Claude Code session of 2026-11-08 (session transcript, user message at 09:17, Claude Opus 5.5). The reply below is the final text message of that turn. The intermediate tool calls (listing `assets/banners`, reading the README and `banner4x3.jpg`, and the README edit) are not repeated here.

## Prompt

> add the banner to readme

## Response

I added the banner at the top of [README.md](../../../README.md), centred above the title at 640 px wide.

You had two banners, so I used `banner4x3.jpg`, the wider one, which suits the top of a README. To use the square one, change the filename to `banner1x1.jpg` in the first lines of the README.

Nothing is committed yet: the README change and the `assets/` folder are still uncommitted. The images are about 2.2 MB and 0.5 MB, plus a 1.8 MB icon. Tell me when you want them committed and I'll run it through the guard.

## Validation

In the session the banner image was opened and the README head was read before the edit. The edit tool reported that the README was updated. The commit itself (ba563ff) is recorded in `results/llm_comparison/commit_tasks.csv` (row T14). No rendering check is recorded.

## Our decision

The 4x3 banner was used because it is the wider one and suits the top of the README. The square banner stayed as an option. The commit was made later as ba563ff, per commit_tasks.csv row T14.

## Measured effect

None. This is a documentation change with no effect on results.
