# 7_meta_and_other - P060: Asks what the attribution worksheet fill-in guide means
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P060. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

what is this =[- Fill an entry only when it can be backed up. Values: `claude_opus`, `gemini_neo`, `both`, `team`, `test`.
- Set `attribution_source` to `chat` (the conversation is exported; put its path in `prompt_file`) or
  `recollection` (a team member remembers it, but there is no chat).]

## Response

That is the fill-in guide for the worksheet [results/llm_comparison/attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv). The worksheet lists all 31 failures and 57 changes. The guide explains the four empty columns at the end of each row.

- **`proposed_by`:** who suggested the original step. The values are `claude_opus`, `gemini_neo`, `both`, or `team` if it was your own idea.
- **`caught_by`:** who noticed the problem. This is one of the two models, the `team`, or a `test` that failed.
- **`attribution_source`:** how you know. Use `chat` if you have the conversation, or `recollection` if a team member remembers it but there is no chat.
- **`prompt_file`:** if the source is `chat`, the path to the exported conversation in `prompts/`.

#### What "fill an entry only when it can be backed up" means
Write a model's name only when you have a chat or a clear memory of it. Otherwise, leave the cell empty.

#### Why it matters
These two columns are what the PDF asks for: who recommended something, and how it was checked. Filling in even some rows strengthens the per-stage section (30%) and the two-LLM comparison (15%).

I can delete the guide, or move it into the worksheet itself.

##### Reading the rules
The guide has one strict rule: a value is written only when it can be backed up. A chat export gives `attribution_source` of `chat` and a path. A memory without a chat gives `recollection`. Leaving a cell empty is the correct choice when neither applies, because a guessed value would be worse than a gap.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
