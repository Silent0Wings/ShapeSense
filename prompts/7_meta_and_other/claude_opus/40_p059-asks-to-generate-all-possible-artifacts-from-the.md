# 7_meta_and_other - P059: Asks to generate all possible artifacts from the provided sources
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P059. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

generate them from all the avilable sources i providede you

## Response

I built everything that can honestly be made from your sources. Before that, I checked which result files exist and how large they are. The worksheet has all 88 entries: 31 failures and 57 changes. I then checked the prompt files that are ready to run, the named folders for both models, and the README and data updates.

I cleared the two model columns in the worksheet, as you asked, and updated the rules to match. I also removed both phrases that had been left in the files. Last, I updated the main README section and the data licenses. Nothing is committed.

**What I made**
- `results/phase2_snapshot/`: the 46 public result files from the deployed site, copied unchanged.
- `results/README.md`: your Phase 2 results in one place. On the test split, macro F1 goes from 77.9 (logistic regression on pixels) to 84.3 (SVM on HOG) to 94.6 to 96.2 for the CNNs. It also has the fresh holdout, the pre-registered comparisons (+9.20 on damaged images) and an empty improvement table.
- `results/llm_comparison/`:
  - The Gemini audit as a table: 27 claims, 21 stood, 4 partly, 2 rejected.
  - An attribution worksheet with all 88 failures and changes. The model columns are blank, as you asked.
- `results/verification/README.md`: 12 verification checks, each linked to its evidence file, plus an empty dataset-awareness table. While writing it I first misdescribed two files (`fd_check.json` and `guards.json`). I then checked them and fixed the rows.
- Reconstructed prompts: 31 inferred prompts, one per failure, filed by stage:
  - 2 in `prompts/1_data_integration/`
  - 1 in `prompts/2_data_preparation/cleaning/`
  - 4 in `prompts/2_data_preparation/transformation/`
  - 14 in `prompts/3_modeling/`
  - 10 in `prompts/4_testing/`
  Each prompt gives the failure, its cause and how it was handled, all copied from your log. The model field is blank, and no LLM response is included.
- Prompts ready to run: the dataset-awareness check (`prompts/6_verification/dataset_awareness/PROMPT.md`), direct LLM prediction (`prompts/5_direct_llm_prediction/PROMPT.md`) and data preparation (`prompts/2_data_preparation/PROMPT.md`). The model folders are now `claude_opus/`, `gemini_neo/` and `cross_critique/`.
- `README.md`: a course section with the team, topic, metric, LLMs, live site and folder map.
- `data/README.md`: all four licenses filled in.

Each reconstructed-prompt file starts with 'These are reconstructions, not the original prompts'. I removed the 'not recorded' wording as you asked, but I kept that label. Without it, a grader would read the inferred prompts as real chat logs, and this assignment grades that honesty.

**Still needs your team**
- The exact Claude and Gemini versions.
- The Colab link.
- Exported Gemini audit chats, if you can get them.
- Three runs that cannot be generated from the record: the dataset-awareness check, direct LLM prediction, and the baseline-then-three-steps F1 table.
- `slides.pdf`.

The completion estimate goes from about 29% to roughly 40%. The rest depends on those three runs.

##### Why only some artifacts were made
The rule was to build only what the sources support. Failures, changes and the prompts reconstructed from them can be made honestly. The dataset-awareness check, direct prediction and the three-step F1 table need new runs, so they were left as prompts to run, not as results.

##### Why the labels were kept
Each reconstructed prompt is marked as a reconstruction. Removing that label would make the inferred prompts look like real chat logs, which the assignment grades against. The "not recorded" wording was removed as requested, but the reconstruction label stays.

##### Checks before publishing
- The 46 snapshot files were copied unchanged, so they can be compared with the deployed copy.
- Two file descriptions (`fd_check.json` and `guards.json`) were first written wrongly and were then checked and corrected, so the verification table reflects what the files contain.

##### Consequence
Items marked as needing the team (exact model versions, Colab link, exported Gemini chats, the three runs, and `slides.pdf`) stay open. Until the runs exist, the completion estimate stays near 40% by the answer's own figures.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
