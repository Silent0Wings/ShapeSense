# 7_meta_and_other - P096: Asks for a per-requirement breakdown of what is still missing
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P096. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

give me a more detialed break down on whic are stil misising ?

## Response

Here is every requirement in the PDF, checked against what is in the repo now. Status key: done, partial, or missing.

#### Section 1: Build the pipeline with an LLM, stage by stage (30%)

| Requirement | Status | What's missing |
|---|---|---|
| 0. Data discovery (optional) | Partial | S01 to S07 recorded and reconstructed. Owner and model columns are empty. |
| 1. Data integration | Partial | 5 entries plus reconstructed prompts. No real chat. |
| 2a. Cleaning | Partial | F01 and C01, with 2 reconstructed exchanges. **The Gemini contradiction on C01 is unresolved.** No F1 delta against a raw baseline. |
| 2b. Transformation | Partial | 11 entries (rotation, framing, strokes, search). No F1 delta against a raw baseline. |
| 2c. Feature selection | Missing | **No step exists.** It needs a decision (cropping, resolution, HOG features and so on), a run and an F1 delta. |
| 3. Modeling | Partial | 31+ entries, plus D01, D03 and D04. The real D04 prompt was found in a session but hasn't been extracted yet. |
| 4. Testing | Partial | 13 entries plus the pre-registrations. No real chat. |
| Per stage: "what you asked the LLM" | Partial | All prompts are reconstructions. **0 real chats saved.** |
| Per stage: "what the LLM recommended" | Partial | Only F01 and C01 have a recommendation, and it is reconstructed. Other rows only have the outcome. |
| Per stage: "how you validated it" | Done | Failure log, change log, audit verdicts, verification README. |
| Per stage: "what you changed, and why" | Done | 57 changes, each with before, after and why. |
| Per stage: "measured effect" | Partial | Phase 2 deltas exist (arms, search, +9.20 robustness), but not per preparation step. |
| **Baseline before any data preparation** | Missing | **Not trained.** The Phase 2 baselines used prepared 64x64 images. |
| **Improvement table** (cleaning, transformation, feature selection: baseline, new, delta) | Missing | The table in [results/README.md](../../../results/README.md) is all TODO. |

#### Section 2: Compare two LLMs (15%)

| Requirement | Status | What's missing |
|---|---|---|
| Names and versions stated | Partial | `opus_medium_5.5` in the CSVs, but "Claude Opus (TODO exact version)" in the README and prompt folders. **Use one name everywhere.** |
| Compare recommendations at each stage | Partial | Attribution per row exists. There is no side-by-side comparison per stage, and feature selection has nothing. |
| Did working with both help? One critiques the other? | Partial | Gemini audit (27 claims, 21 stood, 11 fixed), D03 and F17/C09. **The audit chats aren't exported.** |

#### Section 3: Pipeline vs. direct LLM prediction (15%)

| Requirement | Status | What's missing |
|---|---|---|
| Give the LLM the data and get predictions | Missing | The protocol is ready in [prompts/5_direct_llm_prediction/PROMPT.md](../../../prompts/5_direct_llm_prediction/PROMPT.md). **Not run.** |
| Same held-out test set, same metric | Missing | No `sample_ids.csv`, no predictions, no score. |
| Explain the difference | Missing | Depends on the run. |

#### Section 4: Verification (20%)

| Requirement | Status | What's missing |
|---|---|---|
| Describe the verification process | Done | [results/verification/README.md](../../../results/verification/README.md), 12 checks with evidence. |
| Check whether each LLM knew the dataset | Missing | Prompts are ready. **Not run.** The table is all TODO. |

#### Section 5: Deliverables (10% repo/Colab, 10% presentation)

| Requirement | Status | What's missing |
|---|---|---|
| Public GitHub repo | Unknown | Visibility is unknown, so check the GitHub settings. **Student IDs in the CSVs would be published.** |
| `README.md`: members, topic, LLMs, Colab link | Partial | Colab link is TODO, and the Claude version is TODO. |
| `data/` | Done | Links and licenses. |
| `prompts/` by stage and by LLM | Partial | Structure done, reconstructions done, real chats missing. There are duplicate `01_` files in `cleaning/`. |
| `notebooks/` copy of the Colab notebook | Missing | Empty. |
| `results/` improvement table and comparisons | Partial | Phase 2 results, stage map, audit and worksheets are done. The improvement table and direct prediction are missing. |
| `slides.pdf` | Missing | Not made yet. |
| Colab: final pipeline only, runs top to bottom | Missing | **Doesn't exist.** The pipeline needs a CUDA GPU and 35 MB of data from Drive or links. |
| Colab: one section per stage, F1 after each preparation step | Missing | Not started. |
| Colab: baseline, final model and direct LLM on the same test set | Missing | Not started. |
| Colab shared with the instructor and TAs | Missing | Not shared. |
| Slides: about 8 slides, 10 min, 2 or more presenters, with repo and Colab links | Missing | The site deck can be reused, but the PDF must follow the course layout. |
| Team sheet (due **Nov 23**) | Unknown | Did you submit it? |

#### Housekeeping in the CSVs

| Item | Status |
|---|---|
| `attribution_source` empty | 75 rows |
| `proposed_by` empty | F04, N01, N02, D02, D03 |
| Owner and model empty | S01 to S07 |
| LLM empty | N01, N02 |
| No commit found | F10, C07, C13, C18 |
| Role values undefined | `assisted`, `reviewed` and `inspected` have no legend, since the README was deleted |
| Mixed list formats | ` + ` in the worksheet, commas in the commit table |
| `commit_tasks.csv` | No `owner` column |
| `llm_tools` (web search) | Column not added yet |

#### Shortest path to done
1. **Nov 23:** team sheet.
2. **Next:** the dataset-awareness check, under an hour.
3. Then the **Colab notebook:** raw baseline, cleaning (the diamonds), transformation (augmentation), and feature selection, each with both LLMs logged.
4. Then **direct LLM prediction** on the same test images.
5. Then **slides.pdf**, the README links, and making the repo public.
6. Alongside all of these, the CSV housekeeping and any real chat exports you find.

##### Why this breakdown is organised by PDF section
Each row matches a requirement in the course PDF, so a gap can be traced to the rubric line it affects. The status key (done, partial, missing) is applied to what the repo contains now, not to what was planned.

##### Gaps the breakdown exposes
- **Feature selection** has no step at all, so it is marked missing, not partial.
- **The baseline before data preparation** has not been trained. The Phase 2 baselines used prepared images, so they cannot stand in for it.
- **Visibility of the repo** is unknown, and the answer notes that student IDs in the CSVs would be published if it is public.

##### Limits of the check
The statuses are based on the files named in the table. The answer does not re-read the Colab notebook (which does not exist yet) or confirm the team sheet submission (marked unknown).

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
