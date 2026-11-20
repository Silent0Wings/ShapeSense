# 7_meta_and_other - P087: Explain what attribution_source values mean and which to use
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P087. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

what does What attribution_source should the 75 rows say?
 is about ?

## Response

##### What the field means

`attribution_source` says **how you know** who did what in that row. It is the evidence behind the `owner`, `proposed_by`, `caught_by` and `llm_involved` values. It has two possible values:

|Value|Meaning|Example|
|-|-|-|
|`chat`|The conversation still exists and is linked, so a grader can read the actual prompt and response.|You export the Opus chat where it reviewed the 100 diamond images, save it in `prompts/.../claude_opus/`, and point `prompt_file` at it.|
|`recollection`|A team member remembers it, but there is no saved chat to prove it.|Most of what you told me today, such as Gemini 4 Neon proposing the per-arm search.|

##### Current state

19 rows say `recollection`. Those are the ones you described to me in this conversation. The other 75 are rows you filled in yourself in the editor, and their source cell is empty.

##### Why it matters

The PDF grades how you validated the LLM work. A row marked `recollection` is honest that it comes from memory. An empty cell leaves the grader guessing.

##### What to do with the 75 rows

For each row, the choice is simple:
- **You have the chat** (a Gemini history or a Claude session): set `chat` and link the file in `prompt_file`.
- **You remember it but have no chat:** set `recollection`.

If all 75 are from memory, I can set them to `recollection` in one step. You can then switch individual rows to `chat` as you find and export conversations.

##### Why the empty cells are a problem
An empty `attribution_source` does not say whether the row is from a chat or from memory. A grader cannot tell whether the claim was checked, so the empty value looks like missing evidence even if the user knows the source. Filling it, even with `recollection`, is an honest statement of what the evidence is.

##### Why the two values are kept
The two values match the two kinds of evidence the course can accept: a saved chat, or a team member's memory stated openly. Any other value would need its own definition, which would add to the role problem noted in the previous answer.

##### Consequence
The 75 rows are not yet verified. Setting them to `recollection` is a claim about the source, so it should be made only when the user confirms that they are from memory.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
