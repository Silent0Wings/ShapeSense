# 7_meta_and_other - P104: Asks whether prompts link to commit tasks; explains what is missing
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P104. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

do you link the prompt to a task ?

## Response

I checked what the repo calls a "task" before answering.

**Short answer: not yet.** Each prompt links to its entry (F, C, D or N), but not to a task (T01-T90 in `results/llm_comparison/commit_tasks.csv`).

##### What is linked now
- **Worksheet to prompt:** all 94 rows in `results/llm_comparison/attribution_worksheet.csv` have a `prompt_file` pointing to their reconstructed prompt.
- **Search prompt to entry:** each question in `prompts/failure_search_prompts.md` names its failure and links to that failure's reconstructed entry.

##### What is missing
Nothing links a prompt to the commit task that solved or faced it. `commit_tasks.csv` has no prompt column.

##### What linking would give
- `commit_tasks.csv` already lists, for each task, the entries it solved or faced. So 90 of the 94 entries can be linked to their tasks automatically. For example, F01 and C01 go to T06 and T12, and F14 goes to T40.
- Four entries have no task: F10, C07, C13 and C18. I would mark those as "no task recorded" rather than guess one.
- Each prompt entry would get a `Tasks: T06, T12` line.
- `commit_tasks.csv` would get a `prompt_files` column, and possibly `commit_tasks.md` too. Links would then run both ways: issue to prompt to commit.

Should I go ahead?

##### Why a link needs a rule
A prompt links to an entry, and an entry links to a task, so a link to a task is only correct if it follows the commit-to-issue matching already recorded in `commit_tasks.csv`. That keeps the new links traceable to a source instead of to a guess.

##### Why four entries stay unlinked
F10, C07, C13 and C18 have no task in the commit table. Marking them "no task recorded" is more honest than picking a nearby task, and it leaves the gap visible to a grader.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
