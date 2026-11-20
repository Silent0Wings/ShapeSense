# 7_meta_and_other - P095: Asks how far along the project is against the grading table
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P095. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

estiamte how done are we ?

## Response

**Situation:** Team 14, COMP 333 final project, due **Dec 18, 9:00 am** (29 days left). Today's session was spent on the documentation side.

**Task:** Estimate how far the project is along the PDF's grading table.

**Action: what changed today**
- Built the required repo layout and the results.
- Wrote the 101-entry attribution worksheet with owners, models and roles.
- Matched 90 commits and the deployment work to tasks.
- Wrote reconstructed prompts for every stage.
- Mapped the course stages to CRISP-DM.
- Wrote up the Gemini audit and the verification evidence.

**Result: about 41%, up from about 29% this morning.**

| Criterion (weight) | Done | Points | Main gap |
|---|---|---|---|
| Per-stage LLM use, validation, judgment (30) | about 50% | **15** | No baseline-then-three-steps F1 table, no feature selection, and every prompt is still a reconstruction (0 real chats) |
| Verification and dataset-awareness check (20) | about 50% | **10** | Verification is written up; the awareness check has not been run |
| Two-LLM comparison (15) | about 55% | **8** | Attribution per stage exists; no real exchanges; the new preparation steps do not yet have both LLMs |
| Pipeline vs. direct LLM prediction (15) | about 5% | **1** | Only the prompt and protocol exist |
| Repo and Colab completeness (10) | about 45% | **4.5** | No Colab notebook, no notebook copy, no `slides.pdf`; repo visibility unknown |
| Presentation (10) | about 25% | **2.5** | The interactive site deck exists, but there is no 8-slide PDF in the required layout |
| **Total** | | **about 41 / 100** | |

**What is left is mostly running things, not documenting them.** In order of points per effort:
1. Dataset-awareness check (+6 to 8): under an hour with both LLMs, web search off.
2. Direct LLM prediction (+12): 200 test images through each LLM, scored with macro F1 against the CNN.
3. Colab: baseline, then cleaning, transformation and feature selection, with both LLMs logged (+15 to 20). This is the biggest remaining piece, and it fills the empty improvement table.
4. Slides PDF (+6): mostly reuse of the site and the material already in `results/`.
5. Real chat exports (+3 to 5): even 2 or 3 genuine ones lift the per-stage section.

With items 1 to 4 done, the project would land at roughly **85 to 90%**.

##### How the 41% was estimated
Each row takes a judgment of how much is covered, multiplied by the criterion weight, as in the earlier estimate of 29.5. The percentages are planning judgments, not measured scores. The jump from about 29% to about 41% comes from the documentation work listed under "what changed today" and the mapping of commits to tasks.

##### Why the projected 85 to 90% is conditional
The projection assumes items 1 to 4 succeed as described. Items 1 and 2 are runs that have not happened, and the Colab item carries the largest weight, so the projection could fall short if any of them fails or takes longer.

##### Deadline context
The answer uses the Dec 18, 9:00 am due date. The earlier record also gives December 18 as the deadline. The answer says 29 days left, but counting from 2026-11-20 gives 28 days, so the figure is slightly off.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
