# 7_meta_and_other - P121: Asks whether duplicate prompts are identical LLM answers
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P121. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

are they diplicate but exactly the same pormpt anser by llm ?

## Response

##### Short answer

No. None of the 14 duplicates is the same exact prompt answered twice.

##### The 14 pairs inside `claude_opus/`

The prompts in each pair share only 3% to 48% of their wording, and the answers differ too. Both are imagined Opus exchanges about the same failure or change, written separately by two sessions. They are duplicates by topic, not by text, so one of each pair should go.

##### The 13 entries with both an Opus and a Gemini file

Only 3 of them (F07, C08 and D02) use the exact same prompt, answered once by each model. Those 3 are proper two-LLM comparisons.

The other 10 ask the same question in different words, so they do not count as a fair comparison yet.

##### Current state

You interrupted the earlier "do it" request, which was going to use a opus agent. Nothing is running and nothing has changed.

##### Proposed next step

With your go-ahead, I would:
1. add the category lines,
2. align the 10 mismatched pairs to one prompt,
3. remove the 14 duplicates.

A opus agent would handle the mechanical part. This should start only once the other session has stopped writing.

Should I go ahead with it now?

##### Why the wait is required
The mechanical changes (adding category lines, aligning prompts, removing duplicates) touch files the other session may still write. Running them now could overwrite that session's work or be overwritten by it, so the answer waits for the other session to stop.

##### What the duplicate finding means
The duplicates are two Opus imagined exchanges on one topic, not two models' answers. That is why the answer treats them as one conversation written twice, which a grader would read as invented.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
