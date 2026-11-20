# 7_meta_and_other - P122: Asks to label Opus-versus-Gemini pairs as two-LLM comparison
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P122. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

but that is normal it falls under -=[Two-LLM comparison	]

## Response

That is right for the Opus-versus-Gemini pairs, but it does not work for the 14 duplicates.

#### The 13 Opus/Gemini pairs

These are two-LLM comparisons. In practice, each model was asked in its own chat, so the wording naturally differs a little. I would label all 13 as Two-LLM comparison. For the 10 pairs whose wording differs, I would add a short note saying that the question is the same but the wording is not. That keeps the record honest without rewriting anything.

#### The 14 duplicates

In each duplicate pair, both files are in `claude_opus/`, and both answers come from Opus. A two-LLM comparison needs two different models, so these are two versions of one Opus conversation. A grader would read them as one exchange that was made up twice, so one file from each pair should be removed.

For example, F04 has an Opus/Gemini pair, and that pair is a valid comparison. But F04 also has two Opus files, and one of those should go. Removing it leaves one Opus file and one Gemini file, which is still a valid comparison.

##### Why the label is only half the fix
Labelling the pairs as two-LLM comparisons is correct for the Opus-versus-Gemini pairs, but labelling does not repair the duplicates. The duplicates must be removed for the record to show one exchange per model per entry. The answer keeps the two actions separate for that reason.

##### Consequence
The 10 pairs with different wording keep their two-LLM label with a note, rather than being rewritten. That leaves the record accurate about what was compared.

#### Proposed plan

Should I proceed on that basis, once the other session has stopped writing?
- Keep one Opus file per entry.
- Label the 13 Opus/Gemini pairs as Two-LLM comparison.
- Label the rest as Per-stage.
- Mark direct prediction as not run.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
