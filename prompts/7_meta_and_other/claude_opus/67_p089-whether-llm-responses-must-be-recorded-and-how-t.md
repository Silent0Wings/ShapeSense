# 7_meta_and_other - P089: Whether LLM responses must be recorded, and how to record them
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P089. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

do i also need to record the llm answer ?

## Response

Yes. The PDF says the repository must hold "all prompts **and LLM responses**". For each stage you also report "what the LLM recommended or produced". The answer does not go in the CSV. It goes in the prompt files, and the CSV links to it through `prompt_file`.

#### What to record, depending on what you have

| You have | What to record |
|---|---|
| **The real chat** (Gemini history, Claude session) | The full response, unedited, in `prompts/<stage>/<model>/NN_title.md`. Use the template in [prompts/README.md](../../../prompts/README.md): prompt, **response**, validation, decision, effect. Then set `attribution_source = chat`. |
| **Only memory of it** | No verbatim answer, because writing one now would be invented. Instead, add a short **summary of what the LLM recommended**, labeled as a summary from memory. For example: "Gemini 4 Neon recommended tuning each arm separately, training hundreds of models (summary from recollection, not the original response)." |
| **New work from now on** (feature selection, the dataset-awareness check, direct prediction) | Save the full response every time, as you go. These are the easy points. |

#### The reconstructed files

Each entry already has "Documented outcome", which is what was done. It has no "what the LLM said". You could add a **"Recommended (summary)"** line to the entries where you remember the advice. The diamond review (F01), the per-arm search (F06) and the architecture critique (D03) are good candidates.

Even a handful of real exported chats is worth more than many summaries. So it is worth looking through your Gemini activity history and the 3 saved Claude Code sessions for the big decisions first.

##### Why summaries are labelled
A summary written from memory is weaker than a verbatim response, and the grader can only trust it if the label says so. The rule is to write no verbatim text that was not recorded, and to mark every summary as a recollection. That keeps the record honest about what was actually saved.

##### Why new work is the cheapest fix
Runs that have not happened yet can be saved in full as they are produced. Recovering old responses depends on finding the chats, which may not exist, so saving new runs in full is the easiest route to the points.

##### Consequence
The CSV stays a pointer. The evidence sits in the prompt files, so each row can be checked by following `prompt_file` to the response.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
