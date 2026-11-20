# 7_meta_and_other - P047: Create course folder structure using the deployed site as reference
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P047. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

be aware that this has the full documentation =[<home>\Github\ShapeSense_Deployed] read only access there

## Response

I created the folders the course PDF asks for. They are empty apart from placeholder READMEs, and I didn't commit anything.

#### What I found in the deployed copy
[ShapeSense_Deployed](../../../../ShapeSense_Deployed) is the frozen static site, which I read in read-only mode. Its `snapshot/doc/` folder has useful result files for the verification section: metrics, per-class results, the iteration logs and the QA reviews. It has no LLM prompts or responses anywhere, so `prompts/` starts empty.

#### What's new
- [data/README.md](../../../data/README.md): download links for the four sources. The images stay in `data_set/`, which git already ignores. Three license fields are marked TODO, and the details are in [docs/source.md](../../../docs/source.md).
- [notebooks/README.md](../../../notebooks/README.md): says where the copy of the final Colab notebook goes, with the Colab link marked as TODO.
- [prompts/](../../../prompts/): one folder per stage, each with `llm1/`, `llm2/` and `cross_critique/`. The stage folders are `0_data_discovery`, `1_data_integration`, `2_data_preparation/{cleaning, transformation, feature_selection}`, `3_modeling`, `4_testing`, `5_direct_llm_prediction` and `6_verification/dataset_awareness`. [prompts/README.md](../../../prompts/README.md) has a template for each exchange: the prompt, the response, how you validated it, your decision, and the change in F1.
- [results/README.md](../../../results/README.md): the improvement table with macro F1 as the metric, with empty cells, plus `llm_comparison/`, `direct_llm_prediction/` and `verification/`.

Git doesn't keep empty folders, so each empty leaf folder holds a `.gitkeep` file.

##### Why the structure was copied from the deployed site
The course PDF asks for specific folders inside the public repo, and the deployed copy already documents the pipeline. Using it as the reference kept the new folders aligned with the verified results, rather than inventing a layout. The deployed copy was opened read-only, so nothing there changed.

##### What was checked
- The deployed site's `snapshot/doc/` folder holds metrics, per-class results, iteration logs and QA reviews, which is why `results/` was given a table layout.
- The deployed copy contains no LLM prompts or responses, so `prompts/` was created empty rather than filled from that source.
- Nothing was committed, so the folder structure is still local at the time of this answer.

##### Consequence
The structure is in place, but the open items above (the llm1 and llm2 names, `slides.pdf`, and the main README update) are still required before the repo meets the PDF.

#### Still to do
- Rename `llm1` and `llm2` in [prompts/README.md](../../../prompts/README.md) once the team picks the two models.
- Add `slides.pdf` at the end.
- Update the main README with the members, the LLMs and the Colab link.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
