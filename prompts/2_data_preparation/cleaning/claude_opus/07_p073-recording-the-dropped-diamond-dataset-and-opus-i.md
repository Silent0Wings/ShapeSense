# 2_data_preparation - P073: Recording the dropped diamond dataset and Opus image review
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P073. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

also do we have a enry about drop the diaonmond dataa set due to it not conforming to the geometric requriment ? and that we use opus 5.5 to randomly read 100 images ocr style and find fault with them , and suggested that some of the data set has non geometric representation of a diamoon [non rhombi ] doddle style with styling and extra features which helped us identify an issue with our model low performance on feature diaomon ,

## Response

##### Short answer

Yes. The diamond drop is already recorded in two places: **F01** (the failure) and **C01** (the change). Neither entry mentioned the Opus image review, so I checked what the iteration 1 record says about that review before updating them. The check matters because the worksheet should only say a review happened if the repo supports it. The iteration 1 numbers are in [iteration_1_quickdraw_diamonds.json](../../../../docs/crisp_dm/iteration_1_quickdraw_diamonds.json). The saved prompt and response for the Opus review are not in the repo (see P093 below), so the review is recorded from memory, not from a saved transcript.

I updated both diamond entries in [attribution_worksheet.csv](../../../../results/llm_comparison/attribution_worksheet.csv) and kept the proposers you had already set. The table below shows the values now in the worksheet. Because the proposers were left as you set them, the record of who proposed each step is unchanged.

|Entry|proposed_by|caught_by|llm_involved|llm_role|
|-|-|-|-|-|
|**F01** Most QuickDraw diamonds were not rhombi|40256377 (your entry, kept)|opus_medium_5.5|opus_medium_5.5|**inspected** (new value)|
|**C01** All 500 QuickDraw diamonds dropped|gemini_4_neon (your entry, kept)|opus_medium_5.5|both|proposed|

##### What the F01 entry records

1. **The symptom:** diamond scores were low on validation. Diamond F1 was 80.4 for A0, and QuickDraw diamond recall was 59% for A1. Both numbers come from [iteration_1_quickdraw_diamonds.json](../../../../docs/crisp_dm/iteration_1_quickdraw_diamonds.json). They are single runs: the 80.4 is seed 0 of arm A0 (seed 2 gives 90.1), and the 59% is seed 0 of arm A1 (seed 2 gives 51.3%). In the A0 seed 0 run, 71 of 76 QuickDraw diamonds were predicted as diamond. In the A1 seed 0 run, 16 of 76 went to triangle. The problem looks specific to the QuickDraw source, not to the whole class, which fits a source-specific rule. Four runs are too few to prove that.
2. **The LLM check:** Opus 5.5 read 100 random images one at a time. It found QuickDraw "diamonds" that were styled doodles with extra features such as gems, cones and shields, not rhombi. The request was for a random sample of 100 images, read in an OCR-style pass, as your prompt describes. No saved transcript confirms the exact procedure, so this detail is as reported.
3. **The fix:** all 500 were dropped because they did not meet the geometric definition. The split was then re-frozen at 12,405 / 2,819 / 2,776. The drop is a rule, not a per-image decision. [pipeline.yaml](../../../../configs/pipeline.yaml) lists `exclude_source_labels: [[quickdraw, diamond]]`, added as an amendment to Decision 1 on 2026-11-08. The exclusion runs before the split, so the test set is never filtered afterward. The config's comment gives the reason: Quick, Draw! "diamonds" are mostly gemstone, cone and shield doodles, not rhombi. The separate gemstone filter is still off (`filter_gemstones: false`), and the config says it stays a dry run until `configs/gemstone_ids.csv` is filled in by the reviewers.

Both rows are marked `recollection`, because the review is described from memory and no saved chat backs it up. The consequence is that anyone reading the worksheet can see the review's details cannot be checked from the repo. If the slides cite it, they should say so. If a saved chat turns up later, the rows can change to `chat`.

##### Why I added the role "inspected"

Opus reviewed the data. It did not propose a design or critique one, so neither "proposed" nor "critiqued" describes what it did. The README that held the role list has been deleted, so the value "inspected" is not defined anywhere in the repo yet. Without a definition, a reader cannot tell "inspected" apart from "checked a fix", and the values would be hard to compare across rows. It should be documented before the worksheet is shared.

##### Use in the slides

This is the strongest example of cleaning with an LLM in the project:
- Opus found the problem.
- Gemini proposed the fix.
- The team checked the fix against the per-source numbers.

It supports Section 1 (validation and human judgment) and Section 2 (both LLMs at the same stage). Before using it, note that the iteration 1 file holds only before-exclusion numbers. The repo has no post-exclusion result, so the claim that the team checked the fix against per-source numbers is not yet backed by a record of the result.

##### Still missing

- 26 worksheet rows have no model assigned.
- All 85 commit tasks are still empty.

Next step: assign models to the 26 rows and fill in the 85 commit tasks before the worksheet is used in the report.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
