# 7_meta_and_other - P124: Asks to build checklist items from the course requirements
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P124. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

buidl these =[

<pasted_content id="18fa">
Here is every requirement in the PDF, checked against what's in the repo now. ✅ done, 🟡 partial, ❌ missing.

#### Section 1: Build the pipeline with an LLM, stage by stage (30%)

| Requirement | Status | What's missing |
|---|---|---|
| 0. Data discovery (optional) | 🟡 | S01 to S07 recorded and . Owner and model columns empty. |
| 1. Data integration | 🟡 | 5 entries plus  prompts. No real chat. |
| 2a. Cleaning | 🟡 | F01/C01 with 2  exchanges. **Gemini contradiction on C01 unresolved.** No F1 delta against a raw baseline. |
| 2b. Transformation | 🟡 | 11 entries (rotation, framing, strokes, search). No F1 delta against a raw baseline. |
| 2c. Feature selection | ❌ | **No step exists.** Needs a decision (cropping, resolution, HOG features...), a run and an F1 delta. |
| 3. Modeling | 🟡 | 31+ entries, D01, D03, D04. Real D04 prompt found in session `[session ID removed]` but not extracted yet. |
| 4. Testing | 🟡 | 13 entries plus the pre-registrations. No real chat. |
| Per stage: "what you asked the LLM" | 🟡 | All prompts are reconstructions. **0 real chats saved.** |
| Per stage: "what the LLM recommended" | 🟡 | Only F01/C01 have a recommendation, and it's . Other rows have only the outcome. |
| Per stage: "how you validated it" | ✅ | Failure log, change log, audit verdicts, verification README. |
| Per stage: "what you changed, and why" | ✅ | 57 changes with before, after and why. |
| Per stage: "measured effect" | 🟡 | Phase 2 deltas exist (arms, search, +9.20 robustness), but not per preparation step. |
| **Baseline before any data preparation** | ❌ | **Not trained.** The Phase 2 baselines used prepared 64x64 images. |
| **Improvement table** (cleaning, transformation, feature selection: baseline, new, delta) | ❌ | [results/README.md](../../../results/README.md) table is all TODO. |

#### Section 2: Compare two LLMs (15%)

| Requirement | Status | What's missing |
|---|---|---|
| Names and versions stated | 🟡 | `opus_medium_5.5` in the CSVs, but "Claude Opus (TODO exact version)" in the README and prompt folders. **Use one name everywhere.** |
| Compare recommendations at each stage | 🟡 | Attribution per row exists. No side-by-side comparison per stage. Feature selection has nothing. |
| Did working with both help? / one critiques the other | 🟡 | Gemini audit (27 claims, 21 stood, 11 fixed), D03 and F17/C09. **The audit chats aren't exported.** |

#### Section 3: Pipeline vs. direct LLM prediction (15%)

| Requirement | Status | What's missing |
|---|---|---|
| Give the LLM the data and get predictions | ❌ | Protocol ready in [prompts/5_direct_llm_prediction/PROMPT.md](../../../prompts/5_direct_llm_prediction/PROMPT.md). **Not run.** |
| Same held-out test set, same metric | ❌ | No `sample_ids.csv`, no predictions, no score. |
| Explain the difference | ❌ | Depends on the run. |

#### Section 4: Verification (20%)

| Requirement | Status | What's missing |
|---|---|---|
| Describe the verification process | ✅ | [results/verification/README.md](../../../results/verification/README.md), 12 checks with evidence. |
| Check whether each LLM knew the dataset | ❌ | Prompts ready. **Not run.** Table all TODO. |

#### Section 5: Deliverables (10% repo/Colab, 10% presentation)

| Requirement | Status | What's missing |
|---|---|---|
| Public GitHub repo | ❓ | Visibility unknown, check GitHub Settings. **Student IDs in the CSVs would be published.** |
| `README.md`: members, topic, LLMs, Colab link | 🟡 | Colab link TODO, Claude version TODO. |
| `data/` | ✅ | Links and licenses. |
| `prompts/` by stage and by LLM | 🟡 | Structure ✅, reconstructions ✅, real chats ❌. Duplicate `01_` files in `cleaning/`. |
| `notebooks/` copy of the Colab notebook | ❌ | Empty. |
| `results/` improvement table and comparisons | 🟡 | Phase 2 results ✅, stage map ✅, audit ✅, worksheets ✅. Improvement table ❌, direct prediction ❌. |
| `slides.pdf` | ❌ | Missing. |
| Colab: final pipeline only, runs top to bottom | ❌ | **Doesn't exist.** The pipeline needs a CUDA GPU and 35 MB of data from Drive or links. |
| Colab: one section per stage, F1 after each preparation step | ❌ | |
| Colab: baseline, final model and direct LLM on the same test set | ❌ | |
| Colab shared with the instructor and TAs | ❌ | |
| Slides: about 8 slides, 10 min, 2 or more presenters, with repo and Colab links | ❌ | The site deck can be reused, but the PDF must follow the course layout. |
| Team sheet (due **Nov 23**) | ❓ | Did you submit it? |

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
2. **Next:** dataset-awareness check, under an hour.
3. Then the **Colab notebook:** raw baseline, cleaning (the diamonds), transformation (augmentation), feature selection, each with both LLMs logged.
4. Then **direct LLM prediction** on the same test images.
5. Then **slides.pdf**, the README links, and making the repo public.
6. Alongside all of these, the CSV housekeeping and any real chat exports you find.
</pasted_content id="18fa">

]
based on =["<home>\Github\ShapeSense_Deployed"-> state of the repo
"<home>\Github\ShapeSense"-> html and files ]

## Response

##### Situation
You asked me to build the checklist items from the course requirements. The checklist covers the main ShapeSense repo at `<home>\Github\ShapeSense`. I read `<home>\Github\ShapeSense_Deployed` for the deployed state but changed nothing there.

##### Task
Build what can be built from files alone, and state plainly what cannot.

##### Action
I first checked the requirements against the repo. Many items need GPU runs or accounts I do not have. The buildable items were the direct-prediction sample list and a Colab notebook. I checked the pipeline entry point and the test split's label distribution before writing anything.
- **Direct-prediction sample:** I wrote `results/direct_llm_prediction/sample_ids.csv` with 200 test images, 20 per class, drawn with seed 0 from `configs/splits/test.csv`. It matches the protocol in `prompts/5_direct_llm_prediction/PROMPT.md`.
- **Colab notebook:** I wrote `notebooks/shapesense_pipeline.ipynb`, with 23 cells and valid JSON. It has a GPU check, an install step, a data mount, `--check`, then stages 1 to 6 through `run_pipeline.py`, a results cell, and the direct-prediction sample load. The notebook is a skeleton that runs the real entry points and claims no results.
- **Label correction:** I first labelled the stages from memory, which was wrong. After reading the stage modules, I corrected them: stage 2 is augmentation (the transformation step), not cleaning, and stage 1 builds the frozen dataset with the diamond exclusion.

##### Result
- Neither the notebook nor the sample has been run. The notebook needs a CUDA GPU and the raw `data_set/` folder, and neither is available here.
- The GitHub clone URL and the Drive path are `TODO` placeholders that you need to fill in.
- I did not change the CSVs. The empty attribution and owner fields need your decisions.

##### Why these two items were the buildable ones
Most checklist items need a GPU run, a web account or a human decision, so they cannot be finished from files. The sample list and the notebook skeleton are the two items that can be built now, and the answer keeps them separate from any claimed result.

##### How the sample was drawn
The 200 images are 20 per class, drawn with seed 0 from the sealed test split's manifest (`configs/splits/test.csv`). Using a fixed seed makes the draw repeatable. The answer says it matches the protocol in the direct-prediction PROMPT file, which was not re-read here.

##### Why the label correction matters
The first labels for the stages were written from memory and were wrong. After the stage modules were read, stage 2 was corrected to augmentation (the transformation step), and stage 1 was confirmed to build the frozen dataset with the diamond exclusion. Labels that came from memory would have misdescribed the pipeline in the notebook.

##### What the notebook does and does not claim
The notebook runs the real entry points and includes a results cell, but it claims no results. It needs a CUDA GPU and the raw data folder, which are not available in this environment, so it has not been executed.

##### Open items
- The GitHub clone URL and the Drive path are `TODO` placeholders the user must fill in.
- The sample and the notebook must be run on a machine with the GPU and data before they count as evidence.

##### Still missing and blocked
- **Raw baseline and improvement table:** needs a training run on uncleaned data. Not run.
- **Feature selection:** needs a decision, a run and an F1 delta.
- **Direct LLM predictions and dataset-awareness check:** need calls to your Claude and Gemini accounts. Not run.
- **Real chat exports:** these are in your accounts, not the repo.
- **slides.pdf, Colab link, team sheet, repo visibility:** these need your input.

##### Next step
If you give me the Drive path and the Colab link, I can finish the notebook's paths and the README links. Tell me if you also want the slides outline written.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
