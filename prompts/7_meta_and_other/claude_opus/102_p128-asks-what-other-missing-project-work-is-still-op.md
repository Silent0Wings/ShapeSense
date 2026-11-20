# 7_meta_and_other - P128: Asks what other missing project work is still open
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P128. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

what other misisng work is left

## Response

#### Summary

Here is what is still open, grouped by the checklist sections. Items marked (me) are ones I can do from the repo. The rest need you or an account.

#### Due soon

- **Team sheet, due Nov 23 (4 days from today):** not known whether it was submitted. You need to check.
- **Repo visibility:** unknown. The student IDs in the CSVs would be published if the repo goes public, so remove or anonymise them first.

#### Section 1: pipeline

- **Raw baseline:** not trained. Needs a GPU run with the cleaning rule off. (you)
- **Improvement table** in `results/README.md`: all TODO, and it depends on the baseline. (you, then me)
- **Feature selection:** no step yet. Needs a decision, a run and an F1 delta. (you decide, then run)
- **Real chat exports:** none saved. Reconstructed entries do not replace them. (you)
- **Gemini contradiction on C01:** unresolved. (you)
- **Per-step F1 deltas** for cleaning and transformation: these depend on the baseline.
- **D04 prompt:** the real one is in a session that has not been extracted yet. (you export, me file)
- **Data discovery owner and model columns** for S01 to S07: empty.

#### Section 2: LLM comparison

- **One name for the Claude version:** `opus_medium_5.5` in the CSVs, "TODO exact version" in the README. (me, once you confirm the exact version)
- **Side-by-side comparison per stage:** not written. (me)
- **Gemini audit chats:** not exported. (you)

#### Section 3: direct LLM prediction

- **Sample list:** done (200 images, seed 0).
- **Predictions, macro F1 and explanation:** not run. Needs both LLM accounts and the frozen model. (you run, me score)

#### Section 4: verification

- **Dataset-awareness check:** prompts are ready, not run. The table is TODO. (you run, me record)

#### Section 5: deliverables

- **`notebooks/` copy:** skeleton written, not run. Needs a GPU to verify.
- **Colab notebook:** not verified to run top to bottom. The Colab link is TODO. It is not shared with the instructor and TAs. (you)
- **`slides.pdf`:** missing. About 8 slides, 10 minutes, 2 or more presenters. (me for the outline, you for the presenters)
- **README:** the Colab link and Claude version are TODO. (me, once you give the links)
- **Duplicate `01_` files** in `prompts/2_data_preparation/cleaning/`. (me, after checking which one is the real one)

#### CSV housekeeping

- **`attribution_source`:** 75 rows empty.
- **`proposed_by`:** F04, N01, N02, D02, D03 empty.
- **LLM column:** N01, N02 empty.
- **No commit found:** F10, C07, C13, C18.
- **Role values** `assisted`, `reviewed`, `inspected`: no legend, since the README was deleted. (me, if you give the meanings)
- **Mixed list formats:** ` + ` in the worksheet, commas in the commit table. (me)
- **`commit_tasks.csv`:** no `owner` column. (me)
- **`llm_tools` column:** not added. (me)

#### Done this session

- Direct-prediction sample: 200 images.
- Colab notebook skeleton, not run.
- CRISP-DM step and stage lines on all 31 failure entries.
- Feature-selection note saying there are no entries yet.

##### Why this list is ordered by ownership
Each item is tagged (me) or (you), so the next step is clear: items the assistant can do from the repo are separated from items that need the user, an account, or a GPU run. Due dates come first because the team sheet has a fixed deadline.

##### Points to confirm
- The "4 days from today" count for the Nov 23 team sheet was stated in the answer. The pair date is 2026-11-20, and from that date to Nov 23 is 3 days, so the count is off by one.
- The labels "(me)" and "(you)" are the answer's own assignments, not an agreed split.

#### Most useful next step

Confirm the team sheet, then give me the Colab link, your exact Claude version and the role-value meanings. I can then do the README links, the CSV fixes and the slides outline.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
