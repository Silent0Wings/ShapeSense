# 7_meta_and_other - P110: Clarifies files may cite a session by date and topic, not ID
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P110. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

just not the code of the session

## Response

Understood: the files can say that a session happened, but not give its ID. I saved that rule to memory so it carries over to future sessions.

#### Saved to memory
I saved the rule to memory. Any file I write can cite a source as Claude Code session, 2026-11-08, plus the topic. It must never include the session ID.

#### Why the rule is useful
A date and topic still let a reader find the source session, while keeping the internal identifier out of a public repo. The rule covers every future file, not just this one.

#### What to do next
1. Apply the rule to any new file that cites a session.
2. Accept the tradeoff: a date and topic are less exact than an ID, so finding the exact source may take more searching.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
