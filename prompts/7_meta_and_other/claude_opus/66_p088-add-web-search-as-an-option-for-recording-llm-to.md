# 7_meta_and_other - P088: Add web search as an option for recording LLM tool use
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P088. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

can i add llm web search as a option

## Response

Yes, but it fits better in a column other than `attribution_source`. That column answers "how do we know who did it" (chat or memory). Web search is a **tool the LLM used**, and it applies to rows with either kind of evidence. For example, the Gemini audit used web search, and you remember that rather than having the chat.

#### Two clean options

| Option | How it looks | Best when |
|---|---|---|
| **New column `llm_tools`** (recommended) | `web_search`, or empty for none | You want to show which rows relied on search. Many rows could have it next to any role. |
| **New `llm_role` value `researched`** | `llm_role = researched` | The LLM's whole job in that row was looking things up, for example researching the Vercel docs for D02. |

I recommend the column, because it keeps the role and the tool separate. A row can then say `llm_role = critiqued, llm_tools = web_search`, which describes the Gemini audit exactly.

#### Why it helps the course

- **Verification (20%):** Answers that came from web search did not come from the model's own knowledge. This matters for the dataset-awareness check, where search must be off.
- **Two-LLM comparison (15%):** You can report how many of Gemini's contributions used search compared with Opus's.

#### Proposed next step

Shall I add the `llm_tools` column to both CSVs and pre-fill `web_search` on the rows we know used it? Those are the Gemini audit rows and D02 (Vercel research). You would add the rest.

##### Why a separate column
Search changes what the model knew, so it matters for the verification section. A separate column records it per row without changing the role, which keeps `llm_role` a single meaning and lets a row say both who did the work and which tool they used.

##### Why it matters for the dataset-awareness check
That check is meant to show what a model knew without help. Rows marked `web_search` are excluded from that claim, so the column lets the grader see which answers were influenced by outside lookup.

##### What is still to decide
The proposed column is recommended, not yet applied. The user chooses between the column and the new role value, and the pre-filled `web_search` values for the Gemini audit rows and D02 are the answer's own assumption until confirmed.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
