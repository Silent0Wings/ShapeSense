# 7_meta_and_other - P067: Checking which worksheet entries still lack a model
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P067. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

which task still missing model

## Response

**78 of the 88 entries still have no model** in `llm_involved`. Only 10 are filled: F04, F06, F07, C03, C04, C08, C11, C12, C17 and C28.

##### Missing entries by stage

| Stage | Failures still missing | Changes still missing |
|---|---|---|
| Data (integration, cleaning) | F01, F05, F13, F18 | C01, C02, C24, C34 |
| Data preparation | F08, F09, F10 | C05, C06, C07, C35 |
| Modeling | F02, F03, F11, F12, F17, F19, F20, F21, F22, F23, F24, F25, F30 | C09, C10, C13, C14, C25, C26, C27, C29, C30, C31, C32, C37, C38, C39, C48, C53 |
| Evaluation / testing | F14 | C15, C16, C20, C21, C22, C23, C36, C42 |
| Deployment / dashboard / report | F15, F16, F26, F27, F28, F29, F31 | C18, C19, C33, C40, C41, C43, C44, C45, C46, C47, C49, C50, C51, C52, C54, C55, C56, C57 |
| **Total** | **28** | **50** |

##### Open question
C40 (the vote-weighting disagreement) has `proposed_by` and `caught_by` set to team, but its model column is empty. Was an LLM involved in settling it, or was it the team alone (`none`)?

##### Which rows matter most for the grade
If you can only fill some of them, start with these:
- **F08, F09, F10, C05, C06, C07:** framing and stroke defects from the same investigation as F07.
- **F01, C01:** dropping the QuickDraw diamonds, your one cleaning step.

##### Why the count fell from 79 to 78
The previous count (P064) had 79 entries with no model. F04 was half-filled then, and it is now counted as attributed. The failure total dropped from 29 to 28 because F07 was filled. The change total stayed at 50 because C03 was filled while C40 moved back into the missing list, since its model column is empty. The record shows these moves, which makes the counts traceable.

- **F24:** the GPU pixel conversion that an outside report recommended and you rejected after measuring it.
- **F14, C15, C23:** the pre-registered tests and the iteration 3 redesign.

##### Why these rows are first
Filling rows that the findings depend on gives the largest gain for the 30% section, because those rows show where the team's own judgment changed the work. Rows for the deployment and dashboard are lower priority.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
