# Prompts and LLM responses

One folder per pipeline stage, and inside each one folder per LLM:

- `claude_opus/`: Claude Opus 5.5, medium effort (`opus_medium_5.5` in the worksheet)
- `gemini_4_neon/`: Gemini 4 Neon
- `cross_critique/`: one LLM reviewing the other's output

Save each exchange as `NN_short-title.md` using this template:

```markdown
# <stage> - <short title>
- LLM: <name and version>
- Date: YYYY-MM-DD

## Prompt
<exact prompt, unedited>

## Response
<full response, unedited>

## Validation
<how we checked it: tests, metric, manual inspection>

## Our decision
<what we kept, what we changed, and why>

## Measured effect
<macro F1 before -> after, delta>
```

Stage folders: `0_data_discovery` (optional), `1_data_integration`,
`2_data_preparation/{cleaning,transformation,feature_selection}`, `3_modeling`,
`4_testing`, `5_direct_llm_prediction`, `6_verification/dataset_awareness`.

**Claude Code session pairs.** Files named `NN_pNNN-<title>.md` in the `claude_opus/` folders are retained prompt-and-answer pairs from the Claude Code sessions of 2026-11-08 to 2026-11-20, one file per prompt, in the template above. Their answers were rewritten by subagents for more detail and are not the original model output; each file says so in its header.

[failure_search_prompts.md](failure_search_prompts.md) restates each of the 31 failures on the Failure
timeline as a research question for an LLM to search, for example: when does real + synthetic training lose
to real data alone, and why?


Files named `NN_real_<title>.md` are **exchanges**, exported verbatim from saved Claude Code sessions (Claude Opus 5.5, owner 40256377, 2026-11-08 to 2026-11-11). Files named `NN_evidence_<title>.md` cover the work before 2026-11-08, whose chats were not saved: each quotes the LLM's saved output (plans, research notes, scripts, logs) verbatim, and its prompt is either verbatim (session log or the user's todo entry) or marked **inferred**. Gemini 4 Neon wrote plans 01 to 05; Claude Opus 5.5 wrote the research notes and the later plans. 
## Stage Table of Contents (CRISP-DM → Course Stage)

Every prompt and LLM response lives inside its stage folder, mapped across CRISP-DM phases and ShapeSense stages in [stage_map.md](../results/stage_map.md). Cross-stage indexes and summaries: [gemini_audit.md](../results/llm_comparison/gemini_audit.md) and [attribution_worksheet.csv](../results/llm_comparison/attribution_worksheet.csv) (`prompt_file`).

| Course stage | CRISP-DM / ShapeSense mapping | Prompts| `claude_opus/` | `gemini_4_neon/` | `cross_critique/` |
|---|---|---|---:|---:|---:|
| `0_data_discovery` | Business / Data understanding (Phase 1) | [inferred_prompts.md](0_data_discovery/inferred_prompts.md) | [5 files](0_data_discovery/claude_opus/) | [3 files](0_data_discovery/gemini_4_neon/) | [2 files](0_data_discovery/cross_critique/) |
| `1_data_integration` | Data understanding / Data preparation (Stage 1) | [inferred_prompts.md](1_data_integration/inferred_prompts.md) | [12 files](1_data_integration/claude_opus/) | [7 files](1_data_integration/gemini_4_neon/) | [4 files](1_data_integration/cross_critique/) |
| `2_data_preparation/cleaning` | Data preparation (Stage 1, Iteration 1) | [inferred_prompts.md](2_data_preparation/cleaning/inferred_prompts.md) | [4 files](2_data_preparation/cleaning/claude_opus/) | [2 files](2_data_preparation/cleaning/gemini_4_neon/) | [1 file](2_data_preparation/cleaning/cross_critique/) |
| `2_data_preparation/transformation` | Data preparation (Stages 2-3) | [inferred_prompts.md](2_data_preparation/transformation/inferred_prompts.md) | [15 files](2_data_preparation/transformation/claude_opus/) | [9 files](2_data_preparation/transformation/gemini_4_neon/) | [2 files](2_data_preparation/transformation/cross_critique/) |
| `2_data_preparation/feature_selection` | Data preparation (48 px resolution) | [inferred_prompts.md](2_data_preparation/feature_selection/inferred_prompts.md) | [2 files](2_data_preparation/feature_selection/claude_opus/) | [2 files](2_data_preparation/feature_selection/gemini_4_neon/) | [1 file](2_data_preparation/feature_selection/cross_critique/) |
| `3_modeling` | Modeling (Stage 4) | [inferred_prompts.md](3_modeling/inferred_prompts.md) | [51 files](3_modeling/claude_opus/) | [20 files](3_modeling/gemini_4_neon/) | [14 files](3_modeling/cross_critique/) |
| `4_testing` | Evaluation (Stage 5) + Deployment (Stages 6-7) & infra | [inferred_prompts.md](4_testing/inferred_prompts.md) | [34 files](4_testing/claude_opus/) | [18 files](4_testing/gemini_4_neon/) | [13 files](4_testing/cross_critique/) |
| `5_direct_llm_prediction` | Course requirement (200-image benchmark) | [PROMPT.md](5_direct_llm_prediction/PROMPT.md) | [13 files](5_direct_llm_prediction/claude_opus/) | [12 files](5_direct_llm_prediction/gemini_4_neon/) | [1 file](5_direct_llm_prediction/cross_critique/) |
| `6_verification/dataset_awareness` | Course requirement (complete) | [PROMPT.md](6_verification/dataset_awareness/PROMPT.md) | [4 files](6_verification/dataset_awareness/claude_opus/) | [4 files](6_verification/dataset_awareness/gemini_4_neon/) | [1 file](6_verification/dataset_awareness/cross_critique/) |
| **Total** | | | **140** | **77** | **39** |

## Prompt categories

Every file in a model folder has a `- Category:` line under its LLM line, naming the course requirement it covers:

| Category | Rule |
|---|---|
| Per-stage LLM use, validation and human judgment | One LLM at one stage. The Validation and Our decision sections record how we checked it and what we decided |
| Two-LLM comparison | The same prompt, word for word, answered by Claude Opus 5.5 and Gemini 4 Neon. Each file links to the other model's answer. Files in `cross_critique/` also belong here |
| Pipeline vs. direct LLM prediction | The runs in `5_direct_llm_prediction/` (200-image blind benchmark complete) and `6_verification/dataset_awareness/` (Claude and Gemini blind dataset-awareness checks complete) |
