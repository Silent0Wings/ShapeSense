# 7_meta_and_other - P086: Check worksheet CSV health and list missing fields
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P086. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

any issues with the health of the csv what does it have missing ?

## Response

Most fields are filled in now. The `prompt_file` check flagged every row, so I am looking at what is in that column.

##### Structure: both CSVs are sound
- No broken or uneven rows, no duplicate IDs, and clean UTF-8.
- All 94 `prompt_file` links point to a file that exists. Every `#anchor` matches an `<a id>` in its target file.
- You added the C, D and N entries to the reconstructed files with anchors, and those also resolve.
- The label saying these are reconstructions is still at the top of each file.

##### Still missing in [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv) (94 entries)

| Gap | Entries |
|---|---|
| `proposed_by` empty (an owner is set) | F04, N01, N02, D02, D03 |
| `llm_involved` and `llm_role` empty | N01, N02 |
| No commit found | F10, C07 (synthetic stroke 2 px to 3 px), C13 (5 seeds), C18 (shipped model A2_2) |
| `attribution_source` empty | 75 entries, every row you filled in yourself. Only 19 say `recollection`. |
| `caught_by` empty | 80 entries. Optional for changes, but useful for the 33 failures. |

##### Consistency problems
1. **Undefined role values.** You used `assisted` (12 rows) and `reviewed` (2 rows), and I added `inspected`. The README that defined the roles has been deleted, so no role is defined anywhere in the repo now. A grader cannot tell `assisted` from `implemented`, or `reviewed` from `critiqued`.
2. **Two list formats.** The worksheet joins multiple values with ` + ` (for example `gemini_4_neon + 40248536`). The commit table uses commas (for example `team, test` and `proposed, mediated`). Pick one, so the files can be filtered and counted.
3. **Every prompt link points to a reconstruction.** All 94 `prompt_file` entries point to `inferred_prompts.md`. No real exported chat is linked yet, so the per-stage evidence, which is 30% of the grade, is currently all inferred. Linking even a few real Opus or Gemini chats would strengthen it a lot.
4. **Student IDs in a public repo.** The `owner` and `proposed_by` columns would publish 6 student IDs. First names or initials avoid that.

##### In [commit_tasks.csv](../../../results/llm_comparison/commit_tasks.csv) (90 tasks)
- There is no `owner` column. Owners exist only in the worksheet.
- `proposed_by` is empty for T32 and T86 to T90. The deployed-site tasks should probably be `all members`, the same as D02.

##### Fixes I can make right away
- Write a short legend file with the allowed values and what each role means, including `assisted`, `reviewed` and `inspected`.
- Use one list format in both files.
- Add an `owner` column to the commit table, filled from the issues each task solved, with T86 to T90 set to `all members`.

##### Questions that need your answers
- What `attribution_source` should the 75 rows say?
- How should N01 and N02 be attributed?
- Should IDs or names be used for people?

##### Why these checks were run
A CSV can look complete and still be unusable for a grader: broken rows, duplicate IDs, or links to files that do not exist would each break the attribution. The structure checks rule those out first, so the remaining gaps are only about content.

##### Why the role values are a problem
A grader needs each role to mean one thing. The roles `assisted` and `reviewed` were used without a definition, and the README that defined the roles was deleted. Until a legend restores the definitions, the same label could be read two ways, which would weaken the 30% section.

##### What is most important for the grade
The per-stage evidence is currently all inferred, because every `prompt_file` points to the reconstructed file. Linking even a few real chats would change the evidence from inferred to recorded, which matters more than filling the remaining empty cells.

##### Consequence
Several fixes can be made right away (legend, one list format, owner column for commits). The four questions need the user's answers before those values can be set.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
