# 7_meta_and_other - P065: Adding llm_involved and llm_role columns for mediated work
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P065. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

also how do i deal with failure that didnt have a model interaction but originiated from a user and the llm acted as mediator such as the robustnesss check

## Response

Keep `proposed_by` for where the idea came from, and add two columns for what the LLM did.

#### The two new columns

- **`llm_involved`:** `claude_opus`, `gemini_4_neon`, `both` or `none`.
- **`llm_role`:** one of these values:
  - `proposed`: the idea came from the LLM.
  - `mediated`: the team's idea, which the LLM turned into a design, weighed options for, or explained.
  - `implemented`: the LLM wrote the code.
  - `critiqued`: the LLM reviewed someone else's work.
  - `none`: no LLM role.

#### Applying it to the robustness check

The robustness check becomes `proposed_by = team`, `llm_involved = gemini_4_neon`, `llm_role = mediated`. This corrects C17 and C28, which I had credited to Gemini as the proposer based on your earlier message.

You edited line 13 and removed "only when it can be backed up". I will leave that edit in place and add only the new column definitions.

#### What I changed

- I added `llm_involved` and `llm_role` to [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv), and changed the robustness rows to match your description.
- I added the column definitions to `results/llm_comparison/README.md` (not in the repository). Your edit removing "only when it can be backed up" is kept.

#### The 9 attributed rows now

| Row | proposed_by | caught_by | llm_involved | llm_role |
|---|---|---|---|---|
| F04 | | test | | |
| F06, C04, C08, C11, C12 (per-arm search) | gemini_4_neon | team | gemini_4_neon | proposed |
| **C17, C28 (robustness check)** | **team** | **team** | **gemini_4_neon** | **mediated** |
| C40 (vote weighting) | team | team | | |

C17 and C28 also carry a note: "Team's idea: find which classes fail under damage. Gemini 4 Neon turned it into the robustness test design."

#### How to use it for other cases

- **Your idea, and an LLM helped design or explain it:** `proposed_by = team`, `llm_role = mediated`.
- **Your idea, and an LLM only wrote the code:** `proposed_by = team`, `llm_role = implemented`.
- **No LLM was involved:** `llm_involved = none`, `llm_role = none`.

#### Two rows to check

- **C40 (vote weighting):** Did an LLM help settle the team's disagreement, for example by setting up the equal vs. weighted comparison? If so, it is also `mediated`.
- **F06 and C04 to C12:** You said earlier that the investigation started from your suspicion that the model was misconfigured. If the idea of a search was yours and Gemini designed it, those rows are `mediated` too. If Gemini suggested the search itself, `proposed` is correct.

For the slides, the "mediated" rows are good material for the 30% section, because they show the team leading and the LLM helping.

##### Why the new columns were needed
The earlier scheme had one `proposed_by` field, which could not show that an idea came from the team but was shaped by an LLM. Adding `llm_involved` and `llm_role` keeps the origin of an idea separate from the LLM's part in it, which matches how the robustness check actually happened.

##### Limits of the rule
- The "mediated" label is a judgment about the LLM's part, so two people could assign it differently. The definitions in the README are meant to make that choice repeatable.
- Earlier rows (C17, C28) were changed from `gemini` to `team` on the basis of a later message from the user. That message is the source, not a repo file.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
