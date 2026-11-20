# 7_meta_and_other - P055: Checks deployed site docs for remaining sheet values and PDF requirements
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P055. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

i have the other ones , the rest is implicit in the documenation of =["<home>\Github\ShapeSense_Deployed"] as html

## Response

Good, you have the other sheet values. I searched the deployed site's pages (`web/`) and its result files (`snapshot/doc` and `snapshot/docs`). They cover only part of what the PDF asks for.

#### What the site already documents

- The pipeline stages and how each one works.
- Results: metrics, per-class and per-source tables, the iterations, and robustness.
- Verification: QA reviews, seed checks, the shortcut notice, and the noise bands.
- The data sources and licenses.

#### What it does not have

None of the pages or result files mention Claude, Gemini, an LLM or a prompt. So these parts of the PDF are still missing:

| PDF requirement | Weight | On the site? |
|---|---|---|
| Per-stage prompts, LLM responses, validation, your changes | 30% | No |
| Dataset-awareness check (did each LLM already know the data?) | part of 20% | No |
| Comparison of the two LLMs, including one critiquing the other | 15% | No |
| Trained model vs. direct LLM prediction on the same test set | 15% | No |
| Baseline, then cleaning, transformation and feature selection, with F1 deltas | part of 30% | No. Your arms (A0, A1, B, A2, P) compare training mixes, not these three steps. |
| Colab notebook that runs top to bottom | 10% | No |

#### Two other things

1. **The repo is what gets graded.** The PDF asks for `results/`, `prompts/` and so on inside the public GitHub repo, so pointing to the website is not enough. The site's result files in `snapshot/doc/` already passed your forbidden-content scan, so they are safe to copy into `results/`. That fills the folder without exposing anything sealed.
2. **The site is good material elsewhere.** Use it for the verification section, the presentation, and as a link in the README.

I can copy the public result files from `snapshot/doc/` into `results/` and link the site from the README, if you want. That only reads from the deployed copy.

##### Why the table was built this way
The PDF weights are listed next to each requirement so the gaps can be ranked by points. The "On the site?" column answers only whether the site contains the item, not whether the work was done. The baseline row is the closest match, but the site's arms compare training mixes, not the three preparation steps, so it is marked partial.

##### What was checked
- Pages under `web/` and the result files under `snapshot/doc` and `snapshot/docs` were searched for Claude, Gemini, LLM and prompt. None matched, so the "No" entries are based on that search.
- The forbidden-content scan the answer mentions was reported as passed by the earlier record. That was not re-run here.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
