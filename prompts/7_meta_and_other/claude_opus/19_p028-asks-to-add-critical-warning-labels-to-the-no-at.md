# 7_meta_and_other - P028: Asks to add critical warning labels to the no-attribution memory rule
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P028. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

add !! and warning critical hight priotiryt in memory enxt to no attribution rule

## Response

**Situation:** You wanted the no-attribution rule to stand out as critical in memory.

**Task:** Add a critical warning label, with `!!` and the words CRITICAL and HIGHEST PRIORITY, next to the rule everywhere it is stored.

**Action:** I added the warning in three places:

1. The rule's heading in the global CLAUDE.md (`<home>/.claude/CLAUDE.md`, not in the repository).
2. The description and body of the repo memory note.
3. Its line in the `MEMORY.md` index, which loads at the start of every session.

I used the same warning in all three, so the rule is flagged the same way wherever a session reads it.

**Result:** I read all three back and the warning is in place in each. The rule's wording is unchanged.

##### Why the same label in three places
Each memory file is read by a different path. The global CLAUDE.md is loaded in every project, the repo note is loaded when this project is open, and the `MEMORY.md` index is read at the start of every session. Putting the same label in all three means the warning is seen whichever file a session reads first.

##### Consequence
The label is a signal of priority, not a new rule. The condition itself is unchanged, so the existing check after each commit still applies.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
