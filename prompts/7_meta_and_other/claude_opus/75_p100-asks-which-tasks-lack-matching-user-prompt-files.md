# 7_meta_and_other - P100: Asks which tasks lack matching user prompt files
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P100. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

which ones are misising their user prompts ?

## Response

##### Answer

Only one Opus or Gemini task has no matching prompt file: **T23** (`52f6e64`, "chore(config): note the GPU Decision 7 winner in a comment").

##### How the matching works

The Gemini and Opus tasks that do have a prompt file are matched in one of two ways: by the T-number in the filename, or by the commit hash in the file text.

##### What I did not check

I did not check these locations:
- the `inferred_prompts.md` stage files,
- the `cross_critique` folders,
- the `gemini_4_neon` folders that hold only `.gitkeep`.

Those locations may cover other tasks, but none of them is a prompt file for a specific task.

##### Why T23 is the only gap
T23 is the commit that noted the GPU Decision 7 winner. It is the only Opus or Gemini task whose matching prompt file was not found by either method (T-number or commit hash). The answer does not say whether a prompt file for T23 is needed, so this is a gap to confirm, not a confirmed missing record.

##### Why the match method matters
Matching by T-number or by commit hash is a repeatable rule, so a reader can reproduce the result. Matching by topic would be less reliable and was not used.

##### What remains unchecked
The inferred stage files, the cross-critique folders and the empty Gemini folders were not searched. The answer's conclusion covers only the two match methods it used.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
