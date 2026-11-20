# 7_meta_and_other - P106: Asks whether prompts quote the exact log or only summarize it
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P106. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

does it ask for the exact log or a summary of the log ?

## Response

Neither. No prompt asks for a log or includes one. The prompts state the facts in my own words, taken from the summaries in the failure log.

- Search prompts (`failure_search_prompts.md`): each question ends with a one-line 'Our case' summary built from the recorded numbers. For example, F14 gives '+0.06 on test and +0.08 on a fresh holdout'. These questions ask the LLM to research the topic, so a summary is enough.
- Reconstructed prompts (`inferred_prompts.md`): they describe the symptom, for example 'a 108-trial run hung silently after 6 trials, with no error in the log', but do not quote the log itself.
- The template in `prompts/README.md` asks for the exact prompt and the full response, unedited. That is for real chats you save, not for these files.

**Where the exact error text matters**
The exact wording matters most for the engineering failures, because the exact message changes the answer:
- F19: the invalid-handle error.
- F20: the silent hang.
- F22: the GPU error at 66 of 191 trials.
- F23: the worker-pool bugs.
- F25: the GPU looking idle in Task Manager.

For those, I could add a placeholder such as `<paste the exact error and the last 20 log lines>`. Or, if the logs are still in the repo, I could paste the real lines in.

##### Why exact text matters for these five
For an engineering failure, the message decides which fix is right. A paraphrase such as "hung silently" cannot separate a pool bug from a driver issue, so the placeholder marks where the verbatim text belongs rather than letting a summary stand in for it.

##### What was not confirmed
Whether the logs still exist in the repo was not checked in this answer. The placeholder is the safe default until the real lines are found.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
