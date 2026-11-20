# 7_meta_and_other - P112: Asks whether prompts should be per stage or one main file
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P112. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

am i supposed to have prompts per stage or 1 large main md prompt is neough ?

## Response

You need prompts organized per stage. The course PDF asks for "all prompts and LLM responses, organized by stage and by LLM", so a single large file does not meet that requirement. A grader should be able to open `3_modeling/gemini_4_neon/` and see what Gemini was asked and what it answered at the modeling stage.

#### How the current files fit

- **Already per stage:** the `inferred_prompts.md` files and the three `PROMPT.md` files.
- **One file for all stages:** [failure_search_prompts.md](../../../prompts/failure_search_prompts.md). This works as a list of prompts to run. When you run one, save the exchange in its stage's model folder, for example `4_testing/gemini_4_neon/01_synthetic-vs-real-search.md`. The large file then works as an index, not as the record.
- **The worksheet's `prompt_file` column** links each issue to its stage file, which is the per-stage layout the grader expects.

#### Should there be a main file?

A main file is still useful as a table of contents that links to every stage file. [prompts/README.md](../../../prompts/README.md) already does this in part. It should sit on top of the per-stage files, not replace them.

##### Why the PDF wording decides it
The PDF phrase "organized by stage and by LLM" is the requirement, and a single file cannot show per-stage folders for each model. A table of contents helps a reader navigate, but it does not satisfy the requirement on its own.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
