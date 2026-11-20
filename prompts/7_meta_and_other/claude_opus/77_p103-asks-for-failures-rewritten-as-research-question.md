# 7_meta_and_other - P103: Asks for failures rewritten as research questions for an LLM to search
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P103. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

no i didnt ask you to do a prompt search i asked yout to restart some failure we had as a prmopt asking a llm to conduct a search . such as when does syntehthic data + real data loses to a model trained on only real data and why ?

## Response

Understood. You want each failure rewritten as a research question for an LLM to look up, for example "when does synthetic + real lose to real only, and why?". I had misread the request and searched the web for prompt templates. I replaced that file with one search prompt per failure, and deleted the wrong one.

#### Result

All 31 failures on the timeline are now research questions an LLM should search, in the style of your example. They are in [prompts/failure_search_prompts.md](../../../prompts/failure_search_prompts.md).

#### Situation, task and action

**Situation:** I had misread your request and searched the web for prompt templates. You wanted each failure turned into a question an LLM goes and researches.

**Task:** Rewrite each failure as a general "when does this happen, and why?" question for an LLM to search.

**Action:**
- I wrote one research question per failure. Each asks what is known in general, names papers, docs or bug trackers worth checking where I know them, and ends with "Our case: ..." and the project's own numbers. Two examples:
  - **F14:** When does a model trained on real + augmented + synthetic data fail to beat one trained on real data alone, and why? It also asks for studies where synthetic data did not help on familiar images but did help on unseen sources or damaged images.
  - **F04:** When does real + synthetic fail to beat augmented real images, and when does augmentation lose to no augmentation at all?
- The file opens with a block to send before any question. It tells the LLM to search, cite a link for every claim, separate solid findings from single reports or its own reasoning, and relate the answer to ShapeSense.
- Failures are in timeline order, and each one links to its reconstructed entry. That lets you compare what the LLM's search finds with the cause you actually found.
- I deleted the earlier `failure_why_prompts.md` and changed the line in [prompts/README.md](../../../prompts/README.md) to point to the new file.

**Result:** The file has 31 questions, one per failure, and none is missing. It uses plain hyphens only. The reconstructed files and the worksheet are unchanged. None of the questions has been run yet.

##### Why the request was misread, and what fixed it
The first attempt searched the web for prompt templates, which was not what the user asked for. The user's example (a question about when synthetic plus real data loses to real data alone) shows the wanted style: a research question an LLM answers by looking things up. The wrong file was deleted and replaced, so the repo holds one correct version.

##### Why each question ends with "Our case"
The general question is kept separate from the project's own numbers, so an LLM's answer can be compared with the recorded cause without mixing the two. The "Our case" line carries the project facts.

##### What is unverified
The named papers, docs and bug trackers are the assistant's own picks where it knows them. None has been checked by a search in this turn, so they need checking before use.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
