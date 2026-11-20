# 7_meta_and_other - P056: Points out failures and iterations are the human-judgment record under other names
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P056. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

no not stated as llm it was statded as failures and iterations

## Response

You are right. Your human-judgment record is in the repo under other names, and it is substantial. In `snapshot/doc/iteration_log.json`, it looks like this:

| Your record | Count | Maps to this PDF item |
|---|---|---|
| `iterations` (trigger, route, decision) | 3 | Per stage: what you changed based on your own judgment, and why |
| `failures` (failure, cause, how handled, state) | 31 | Per stage: how you validated it |
| `changes` (before, after, why) | 57 | What you changed, and why, plus measured effect where there are numbers |
| `audit` (claim, verdict, action) | 27 | Close to the two-LLM critique, if one model reviewed the other's work |

For example, F01 dropped the 500 QuickDraw drawings labeled as diamonds that were not rhombi. It is a real cleaning step with a before and after (18,500 images down to 18,000).

##### What is still missing: attribution
The PDF grades how you worked with the LLMs, so each entry needs three more facts:
1. **Which LLM proposed the original step:** Claude or Gemini.
2. **Who caught the problem:** the team, the other LLM, or a test.
3. **The prompt and response behind it,** saved in `prompts/<stage>/<llm>/`.

Add a `proposed_by`, `caught_by` and `prompt_file` field to the failures and changes. Once that is done, most of the 30% section is already covered by work you have done. If Gemini did the audit, it also covers most of the two-LLM comparison (15%).

##### Still not covered by the old record
- The dataset-awareness check for both LLMs (part of the 20%).
- Direct LLM prediction compared with your model on the same test set (15%).
- The baseline-then-three-steps F1 table, with the macro F1 change after each step.
- The Colab notebook.

All four are new runs, not documentation.

##### Why the record is not enough
Documenting what was already done cannot produce the missing evidence. Direct LLM prediction, the dataset-awareness check and the notebook each need a new run whose output is saved, so their percentages stay at zero until that happens.

##### Recommended order
1. Attribute the existing failures and changes (proposed_by, caught_by, prompt_file), since that is cheap and covers much of the 30% section.
2. Run the baseline-then-three-steps table, which feeds the verification section.
3. Run the direct LLM prediction and dataset-awareness checks, then the notebook.

##### Open question
Who did the audit of the 27 claims: Claude, Gemini or the team? The answer decides whether the two-LLM comparison is partly covered already.

##### Why this is the blocking question
The 27 audit claims are the one record that could support the two-LLM comparison. Without knowing who made the audit, the comparison cannot be credited to either model, so the question is answered from the record rather than assumed.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
