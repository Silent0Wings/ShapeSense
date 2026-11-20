# 7_meta_and_other - P081: Where prompts and LLM responses should be stored in the repository
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P081. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

where should the prompts go ?

## Response

Prompts go in [prompts/](../../../prompts/), organized by stage and then by model. The PDF requires "all prompts and LLM responses, organized by stage and by LLM".

##### Folder layout

```
prompts/
  <stage>/
    opus_medium_5.5 work  -> claude_opus/
    Gemini 4 Neon work    -> gemini_4_neon/
    one model reviewing the other -> cross_critique/
```

The stage folders are:

| Folder | What goes there |
|---|---|
| `0_data_discovery/` | Finding and choosing the datasets (optional) |
| `1_data_integration/` | Merging the 4 sources, splits, catalog |
| `2_data_preparation/cleaning/` | For example, the Opus review of 100 images that found the non-rhombus diamonds (F01) |
| `2_data_preparation/transformation/` | Augmentation, synthetic generator, the per-arm search |
| `2_data_preparation/feature_selection/` | Still to run |
| `3_modeling/` | For example, the Opus architecture critique (D03), the vote (D01), the performance fixes |
| `4_testing/` | Evaluation, robustness check, pre-registered tests |
| `5_direct_llm_prediction/` | The direct-prediction runs (still to do) |
| `6_verification/dataset_awareness/` | The dataset-awareness check (still to do) |

##### File naming and linking

Use one file per conversation. Name it `NN_short-title.md`, for example `01_diamond-image-review.md`, and use the template in [prompts/README.md](../../../prompts/README.md). Each file holds the prompt, the response, the validation, your decision and the measured effect.

Link each file to the worksheet by putting its path in the `prompt_file` column of that entry in [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv). For example, F01 would use `prompts/2_data_preparation/cleaning/claude_opus/01_diamond-image-review.md`. That lets a grader go from an issue to the actual conversation.

##### Why the layout is by stage and then by model
The PDF asks for prompts and responses "organized by stage and by LLM". Putting the stage first and the model second is the only order that satisfies both words without duplicating files. The `cross_critique/` folder covers the case where one model reviews the other, which the two-LLM comparison asks for.

##### Why the raw exports stay out
Chat exports and session logs can contain personal details and large amounts of unrelated text. The repo is public, so only the cleaned version belongs in `prompts/`, and the raw file stays on the user's machine.

##### What is unconfirmed
- The folder names `claude_opus` and `gemini_4_neon` match the renames made earlier, but the record does not show a full check of every file against them.
- The `2_data_preparation/feature_selection/` folder is listed as "still to run", so it stays empty until that work exists.

##### What is already there

- **`PROMPT.md` files:** prompts ready to run for data preparation, direct prediction and dataset awareness.
- **`inferred_prompts.md` files:** the 31 inferred prompts, one per failure. If you find the real chat for one of them, put it in the model folder and keep the reconstructed version as it is.
- **Raw exports:** Gemini chat exports and Claude Code session logs are large and may contain personal details. Put the cleaned-up version in `prompts/`, and keep the raw export out of the public repo.

##### Memory notes

My memory for this repo lives outside the repo, in `<home>/.claude/projects/c--Users-silent-Github-ShapeSense/memory/`. It has 3 files, all last changed on Nov 8:

| File | What it holds |
|---|---|
| `MEMORY.md` | The index. It loads automatically at the start of each session, one line per memory. |
| `no-attribution-commits.md` | Never add a attribution or AI attribution to commits, and always commit through the guard script. |
| `advise-new-training-machine.md` | Before any Stage 4 training run, suggest the new machine (32 GB RAM, RTX 3080, high-core CPU). |

##### Two things to know

- **One memory is out of date.** The commit rule still points to `.commit_guard/safe_commit.py` inside this repo. Your global instructions say the guard moved to `<home>/Github/commit-guard/` on 2026-11-16. Your global instructions take priority anyway, but I can correct the memory file so the two match.
- **Nothing from this session is saved there.** The course work (Team 14, the Opus 5.5 and Gemini 4 Neon names, the worksheet structure, the Dec 18 deadline) lives only in the repo files I created. If you want, I can save a short project memory about the course deliverables, so a future session knows where things stand.

##### Why the stale memory matters
The commit rule in memory points to a guard path inside the repo, but the global instructions say the guard moved on 2026-11-16. A session that follows the outdated path could run a guard that no longer exists. The global instructions take priority, so the risk is confusion rather than a bypass, and the fix is a one-line correction to the memory file.

##### Why nothing from this session is saved yet
Project memory is for facts a future session needs. The course facts (team number, model names, deadline) are already written into the repo files, so a memory copy would only duplicate them. The answer offers a short project note as an option, not a requirement.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
