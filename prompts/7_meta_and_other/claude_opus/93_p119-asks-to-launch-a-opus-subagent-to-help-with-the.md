# 7_meta_and_other - P119: Asks to launch a opus subagent to help with the task
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P119. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

do it  launch opus sub agent to help

## Response

The prompt asks me to launch an Opus sub-agent to help, but the record has no answer, no task description and no result, so I cannot say what was launched or what it did.

#### Information missing
To launch the sub-agent, I need to know:

- The task it should carry out.
- Which files or folders it should read or change.
- What result you expect back, and whether it should only report or also make edits.

#### Why the brief matters
A sub-agent starts with no context of its own, so the brief is its only instruction. Without the task, the files it may touch, and whether it should report or edit, it could change files that other work depends on. The three questions above prevent that.

#### What to do next
1. Give me the task, the files in scope, and the expected result.
2. I launch the Opus sub-agent with that brief. Risk: an edit-capable brief can change files other work depends on, so decide report-only or edit first.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
