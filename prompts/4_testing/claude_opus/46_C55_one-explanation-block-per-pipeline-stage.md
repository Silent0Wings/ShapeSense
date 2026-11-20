# 4_testing - C55: One explanation block per pipeline stage
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/17_C55_one-explanation-block-per-pipeline-stage.md](../gemini_4_neon/17_C55_one-explanation-block-per-pipeline-stage.md)
- Date: 2026-11-10
- Entry: C55 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / 40248536
- LLM role: reviewed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c55, studio/web/js/widgets/stage-brief.js, studio/web/js/pages/stage0.js to stage6.js, studio/web/js/pages/stage3.js, ShapeSense_Deployed/web/stage0.html to stage6.html, commit 7719006

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
Every stage page of the dashboard shows its tools and tables in its own way, and most of them never say what the stage is for. I want each stage to open with the same block: its job, what goes in, what it does, what comes out, the key finding, and the checks that show it worked, all read from stored results, with links to the previous and next stage. Can you review this design and tell me what to change? Gemini is reviewing it too.

## Response
The design is right, and the reason is consistency: a reader new to the project learns the block once on Stage 0 and can then skim six more pages. My review, point by point:

| Slot | Keep? | Note |
|---|---|---|
| Job | Yes | One sentence, no jargon. If it needs two, the stage is doing two things |
| Goes in, What it does, Comes out | Yes | Show as a three-step flow, not three paragraphs; it is the shortest description of a pipeline stage there is |
| Key finding | Yes, with a rule | It must be computed from stored results, never typed. A finding that can drift from the data is worse than none |
| How we know it worked | Yes | Show each check as a badge (passed, failed, or only recorded) read from the stage's stored status, so a failed check is visible, not hidden |
| Previous / Next | Yes | Stage 6 should point on to the live drawing page rather than end |

Changes I would make:
1. **One shared widget.** Implement it once (`stageBrief` plus `stageNav`) and call it from all seven stage pages. Seven hand-built copies would diverge within a week.
2. **Move key results up.** On Data freeze, Training and Evaluation, the main result currently sits under setup tables. Put it right after the block, because the block's key finding will make the reader look for it.
3. **Synthetic generator needs a picture.** Its point is "make shapes that look like real drawings", which no table shows. Put one real training drawing beside one generated shape near the top.
4. **Badge wording.** Distinguish "recorded" from "passed". Some stages store a number without a pass rule, and labelling those as passed would overstate them.

Cautions:
- Keep the block short; if it pushes the page's first interactive tool below the fold on a laptop, trim the sentences, not the slots.
- On the static public site the block must read the same frozen snapshot as the rest of the page.

## Validation
`studio/web/js/widgets/stage-brief.js` exports `stageBrief({ job, input, process, output, finding, checks })`, rendering "Goes in", "What it does", "Comes out", "Key finding" and "How we know it worked", and `stageNav(stage)`, which shows Previous and Next and ends with "Next: Draw and predict" linking to `live.html`. Its `checkBadge` shows `Passed`, `Failed` or `Recorded` (when no pass value is stored). All seven pages `stage0.js` to `stage6.js` import `stageBrief`. `stage3.js` adds the card "Real against generated". Gemini 4 Neon reviewed the same design.

## Our decision
Kept the design by 40248536: every stage opens with the same block, read from stored results, with links to the previous and next stage. Key results moved higher on Data freeze, Training and Evaluation, and Synthetic generator shows a real drawing beside a generated one. Reason recorded: each stage should explain itself clearly to a reader new to the project.

## Measured effect
No separate measurement recorded. The block appears on all 7 stage pages (Stage 0 to Stage 6).

---

## Expanded & Upgraded: Visual-Honesty Cluster Synthesis (`C55`)

### Fail-Closed Badge Semantics & Artifact-Backed Findings

`stageBrief` (`studio/web/js/widgets/stage-brief.js`) applies one shared contract across all seven call sites (`stage0.js`–`stage6.js`). Its deepest design detail is the **three-valued badge semantics**: `Passed` / `Failed` / `Recorded`, where `Recorded` means *"a number was stored, but no pass/fail threshold exists for this metric."* Conflating `Recorded` with `Passed` would overstate verification — the UI analogue of `F26`'s fail-open gate hazard. Computing every stage's key finding from stored artifacts rather than typed prose extends the `C41` traceability chain across the entire dashboard.

