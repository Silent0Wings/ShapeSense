# 7_meta_and_other - P068: Mapping deployed-site CRISP-DM material to repo and course stages
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P068. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

from the deployed folder there are many other stages we didnt brein in such as the crips steps

## Response

I checked what the deployed site has that is not yet in this repo, then wrote a map that ties the three ways of organizing the work together.

##### What I added

**[results/stage_map.md](../../../results/stage_map.md)** (new) links the three organizing schemes:

- The course's 5 stages, the CRISP-DM phases, and your stages 0 to 6, with the repo files and live page for each. I checked that every linked path exists.
- 19 key findings, one set per stage, copied from the conclusions on the live stage pages.
- Gaps: feature selection has no step, and the Phase 2 baselines were trained on prepared 64x64 images, so they do not count as the course baseline.

Much of the CRISP-DM and pipeline-stage material was already in this repo (`docs/crisp_dm/` and `stages/`), but nothing linked it to the course's 5 stages. The map fixes that. Last, I added a link to the map from the results README.

**[attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)** has three new columns: `course_stage`, `crisp_dm_phase` and `shapesense_stage`. All 88 rows are tagged. Counts by stage:

| Course stage | Failures | Changes |
|---|---|---|
| 1. Data integration | 2 | 3 |
| 2. Cleaning | 1 | 1 |
| 2. Transformation | 4 | 7 |
| 2. Feature selection | 0 | 0 |
| 3. Modeling | 13 | 18 |
| 4. Testing | 3 | 10 |
| Deployment (not a course stage) | 8 | 18 |

##### One mismatch to resolve

The worksheet puts 7 failures (F15, F16 and F26 to F31) under deployment. The reconstructed-prompt file filed them under `4_testing` earlier. The worksheet labels are the more accurate ones. I can move those 7 entries so the files match, if you want.

##### What the numbers mean for the grade

Your record is heavy on modeling and deployment, which the PDF counts least. It is light on data preparation (13 entries) and has nothing for feature selection, which the PDF weighs most. So the new cleaning, transformation and feature-selection runs are where the remaining time should go.

##### Why a separate map was written
The course uses five stages, CRISP-DM uses its own phases, and the repo uses stages 0 to 6. Each scheme is correct on its own terms, but a grader reads the course's terms. The map links the three so each repo file can be found from the course stage it supports.

##### What was checked
- Every linked path in the map was confirmed to exist, as the answer states.
- The findings were copied from the conclusions on the live stage pages, not re-derived.
- The stage counts in the table were computed from the new `course_stage` column of all 88 rows, which the answer says are all tagged.

##### Consequence
The gaps are stated as gaps: feature selection has no step, and the Phase 2 baselines use prepared 64x64 images, so they cannot serve as the course baseline. Those need new runs, not new documentation.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
