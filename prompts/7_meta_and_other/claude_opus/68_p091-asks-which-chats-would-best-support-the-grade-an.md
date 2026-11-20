# 7_meta_and_other - P091: Asks which chats would best support the grade and where to find them
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P091. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

is there any task you want the prompt repsonse to ?

## Response

Yes. Below are the rows where a real prompt and response would earn the most grade, grouped by how much they support the grade. If you can find the chats, export them.

##### Top priority (30% section and two-LLM comparison)

| Row | Why this one | Where to look |
|---|---|---|
| **F01 / C01**: Opus reviewing 100 images, Gemini proposing the drop | Your best cleaning example, with both LLMs at one stage | Claude session and Gemini history around 2026-11-08 |
| **F06 / F04**: Gemini mediating the data vs. training disagreement and proposing the per-arm search | Shows an LLM settling a team conflict, and it led to the fixes | Gemini history around 2026-11-09 |
| **Gemini audit** (27 claims) | Fills almost all of the two-LLM comparison (15%) | Gemini history. Even the prompt plus 2 or 3 responses help. |
| **D03**: Opus critiquing depth, layers and activation | Modeling-stage cross-check with F17/C09 | Claude session |

##### Good to have

| Row | Why |
|---|---|
| **F24**: the GPU pixel conversion an outside report recommended and you rejected after measuring | The clearest example of not trusting the LLM blindly |
| **C17 / C28**: the robustness check Gemini mediated | Led to your passing result (+9.20 on damaged images) |
| **D04**: Opus advising the move to the GPU machine | Its estimate (1 to 2 h) against the measured result (175 trainings in 3 h 50 min) |
| **S01**: how you searched for and compared datasets | Covers the optional discovery stage, possibly with web search |

##### Do not search for these
They will be produced fresh, so save them as you go:
- The cleaning, transformation and feature-selection runs with both LLMs.
- The dataset-awareness check.
- Direct LLM prediction.

##### How to hand them over
Paste a chat here, or save it as a text file anywhere in `ignore/`, and tell me which row it belongs to. I will then:
1. Remove personal details (email, local paths, keys).
2. Put it in `prompts/<stage>/<model>/NN_title.md` using the template.
3. Link it in `prompt_file` and set `attribution_source = chat`.

Three of your Claude Code sessions are saved locally. If you want, I can search them for F01, D03 and D04 first. I would only read them, and I would show you what I find before anything goes into the repo.

##### Why these rows were ranked
The ranking follows the PDF weights. Rows in the top group touch the 30% per-stage section and the 15% two-LLM comparison, which together carry the most points. The "good to have" rows add evidence but affect fewer criteria. The "do not search" group is excluded because those runs do not exist yet and cannot be recovered from old chats.

##### What is unverified
The locations (for example "around 2026-11-08") are the user's dates as recorded, not checked against the chat files. The answer also does not confirm that the Gemini audit chat still exists in the history.

##### Privacy step
Before any chat enters the public repo, personal details (email, local paths, keys) are removed, as the hand-over steps state.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
