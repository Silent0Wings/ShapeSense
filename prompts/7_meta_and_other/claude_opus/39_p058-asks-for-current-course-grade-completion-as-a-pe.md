# 7_meta_and_other - P058: Asks for current course grade completion as a percentage
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P058. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

@artifacts/comp333-course-project.pdf  grade current to completion as %

## Response

**Overall completion: about 29%.** This measures how much of each rubric item is done, not a prediction of the grade.

##### How the estimate works

Each rubric criterion has a weight. For each one I estimated the share that is done, then multiplied it by the weight to get points. The sum is about 29.5 out of 100.

| Criterion (weight) | Done | Points | What exists / what's missing |
|---|---|---|---|
| Per-stage LLM use, validation, human judgment (30) | about 35% | **10.5 / 30** | Done: 31 failures, 57 changes (before, after, why), 3 iterations. Missing: no saved prompts or responses, no record of which LLM proposed what, no table of baseline, then cleaning, transformation and feature selection with deltas. |
| Verification and dataset-awareness check (20) | about 45% | **9 / 20** | Done: strong verification, including a sealed holdout, CI, seeds, QA reviews, parity checks and noise bands. Missing: no dataset-awareness check for either LLM. |
| Two-LLM comparison (15) | about 40% | **6 / 15** | Done: Gemini audit with 27 claims, 21 stood and 11 fixes. Missing: chats not saved, critique went one way only, not done at every stage, data preparation barely covered. |
| Pipeline vs. direct LLM prediction (15) | 0% | **0 / 15** | Not started. |
| Repo and Colab completeness (10) | about 20% | **2 / 10** | Done: code and the folder structure I set up. Missing: repo may not be public, `prompts/` and `results/` are empty, no Colab notebook, no notebook copy, no `slides.pdf`, README is missing the LLMs and the Colab link. |
| Presentation (10) | about 20% | **2 / 10** | Done: the six-part site presentation can be reused. Missing: no 8-slide, 10-minute deck in the required layout. Slides 2, 4, 5, 6 and 8 need content that does not exist yet. |
| **Total** | | **about 29.5 / 100** | |

##### How the estimate was made
The percentages are judgments of how much of each criterion is covered by existing material. They are not measured scores. Each row multiplies that judgment by the criterion's weight, and the rows sum to the total. Treat the total as a planning figure, not a grade.

##### Where the points are

The items below are ordered by how many points they would gain.

1. **Baseline and three-step F1 table, run in Colab, with prompts saved:** worth up to about 25 points across the 30% criterion, Colab and presentation.
2. **Direct LLM prediction on the test set, with both LLMs:** 15 points for one script plus the API or chat runs.
3. **Dataset-awareness check, with web search off:** about 8 points for under an hour of prompting.
4. **Export the Gemini audit chats and add `proposed_by` and `caught_by` to the failure and change entries:** about 8 points, mostly paperwork.
5. **Slides, README, `results/` copied from the snapshot, repo made public:** about 8 points.

Items 3 to 5 are quick and together worth about 24 points. Items 1 and 2 are the bulk of the remaining work. The deadline is December 18.

##### How the ranking was chosen
Items are ordered by points gained per unit of work. Items 3 to 5 are documentation or short prompting tasks, while items 1 and 2 need full runs. The point values are the answer's own estimates and were not checked against the rubric weights beyond the table above.

##### What this means for planning
Doing items 3 to 5 first gives the most points soonest. Items 1 and 2 cannot be shortened by paperwork, so they should start early enough to finish before the December 18 deadline.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
