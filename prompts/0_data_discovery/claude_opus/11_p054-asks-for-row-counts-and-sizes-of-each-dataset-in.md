# 0_data_discovery - P054: Asks for row counts and sizes of each dataset in a folder
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P054. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

how many rows and size per data set read =["<home>\Github\COMP_333_Project"]

## Response

While the file count was running, I checked what the repo currently keeps hidden, and compared it with what the course asks for. The goal was to separate what is hidden on purpose (raw data, checkpoints, private tooling) from what is hidden by accident or is simply missing from the repo, because only the second group needs action before submission.

The comparison has three steps. First, I read the repo's `.gitignore` rules to see which paths are excluded from version control. Second, I matched each excluded or absent path against the course requirements in section 5 of the course PDF. Third, I checked whether each required item already exists in the repo, and if not, what it would take to create it. The PDF text itself is not quoted in this file, so the requirement list below is the one recorded in the table, not a re-read of the PDF in this pass.

**Short answer:** the course doesn't ask you to publish everything that is hidden today. It asks for a public repo with the required items. Some of those are hidden by `.gitignore`, and some don't exist yet. Note that the short answer says "six things", but the table below lists eight rows, so the count should be checked against the PDF before it is quoted to anyone.

#### What the PDF requires vs. where the repo is

| Required (PDF section 5) | Status now | What to do |
|---|---|---|
| **Public** GitHub repo | I can't check this, because I don't run git. | On GitHub, go to Settings, General, Danger Zone, Change visibility, and choose Public. |
| Code | Committed | Nothing. |
| `data/` (the data, **or links** if too large) | `data_set/` is ignored. I made [data/README.md](../../../data/README.md) with links. | Links are allowed, so the raw data can stay hidden. The 35 MB unified dataset is small enough to publish if you want to. |
| `prompts/` (**all** prompts and LLM responses, by stage and by LLM) | **Missing.** The folders are empty. | This is the biggest gap. See the section below. |
| `results/` (improvement table, comparisons) | **Hidden.** `artifacts/*` is ignored, so every metric file stays local. | Copy the final tables (CSV or JSON) into `results/`. Don't un-ignore all of `artifacts/`. |
| `notebooks/` (copy of the Colab notebook) | Missing | Build the Colab notebook, then save a copy here. |
| `slides.pdf` | Missing | Do this at the end. |
| README with members, topic, LLMs, Colab link | Members exist. The LLMs and the Colab link are missing. | Add them. |

#### What is hidden, and whether the course needs it

- **Raw images (`data_set/`):** not needed, because links are enough. The datasets are public anyway.
- **Stage outputs (`artifacts/`):** the results are needed, so publish the summary tables and not the whole folder. [stages/stage_7.md:132](../../../stages/stage_7.md#L132) warns that the folder holds sealed test predictions and paths.
- **Model checkpoints (`*.pt`) and `phase2_report.pdf`:** not required.
- **The sealed test/holdout rule (R15):** this is your team's own rule for the public dashboard, not a course rule. Iteration 3 is closed, so publishing aggregate test results (macro F1, per-class tables) is fine. Section 3 of the PDF *does* require sending test images to both LLMs for direct prediction. Do that only after the final model is frozen, so that it can't affect any choices.
- **`.commit_guard/`, local notes and backups:** private tooling that the course doesn't require. Keep them hidden.

#### The prompts problem (30% of the grade)

The PDF wants every prompt and response, organized by stage and by LLM.
- **Claude:** only 3 Claude Code sessions are saved locally for this repo (about 35 MB), so most of the build history is gone.
- **Gemini:** export your chats from Gemini's activity history.
- **Before publishing,** remove personal details from both: emails, local paths and keys.

Old logs alone won't cover the Section 1 requirements. Those need a baseline before any data preparation, then cleaning, transformation and feature selection, each with both LLMs. You will have to run those stages now and save the prompts as you go. Don't write prompts afterwards to make the logs look complete.

#### Order of work
1. Fill in the team sheet (due Nov 23) and make the repo public.
2. Run each stage with both LLMs and save the logs into `prompts/`.
3. Build the Colab notebook: baseline, then the three preparation steps, then the final model, then direct LLM prediction on the same test set.
4. Put the tables in `results/`, the notebook copy in `notebooks/`, update the README, and add `slides.pdf`.

#### Rows and size per dataset (your earlier question)

The final counts were measured in `COMP_333_Project/data_set`:

| Source | Raw files downloaded | Raw size | Rows in unified dataset |
|---|---|---|---|
| Google QuickDraw | 7 NDJSON files (500 drawings each) | about 1 MB | 3,000 |
| Kaggle reevald | 20,000 JPG | 174 MB | 5,000 |
| Mendeley El Korchi | 90,000 PNG | 391 MB | 7,000 |
| GitHub hand-drawn | 27,292 PNG | 163 MB | 3,000 |
| **Total (4 sources)** | **137,299 files** | **about 729 MB** | **18,000 rows, about 35 MB** |
| Kaggle dinesh (license "Unknown", excluded) | 30,000 | 134 MB | 0 |

Two counts need explaining:
- **GitHub hand-drawn:** the folder has 47,333 files, of which 27,312 are images. 27,292 of those images are the dataset images in `user.*/images`, which is the number given in [docs/source.md](../../../docs/source.md). The other files are the repo's code, docs and extras.
- **QuickDraw:** the unified folder in `COMP_333_Project` holds 3,500 QuickDraw images and 18,500 images in total. The final pipeline in the deployed snapshot uses 3,000, for 18,000 in total, so the table shows the final numbers.

For the sheet, you could add the raw size to your dataset-size cell:

```
18,000 rows (64x64 grayscale PNG images, indexed in a SQLite catalog with a CSV export), 35 MB (selected from 137,299 raw files, about 729 MB)
```

How I checked these numbers: I cross-checked the table against [docs/source.md](../../../docs/source.md), which lists the same raw counts and sizes (7 NDJSON files of 500 drawings, 20,000 JPG, 90,000 PNG, 27,292 PNG, and 30,000 excluded Kaggle dinesh files). The arithmetic is consistent: the four raw counts add to 137,299 files, the four raw sizes add to about 729 MB (1 + 174 + 391 + 163), and the unified row counts add to 18,000 (3,000 + 5,000 + 7,000 + 3,000). I did not re-count files on disk in this pass, so the figures are as measured earlier and recorded in the source map.

The sheet suggestion is a choice of wording, not a requirement. It gives the reader both the delivered size (35 MB) and the raw size it was selected from (about 729 MB), so the selection step is visible. Before using it, confirm that the 35 MB figure matches the current `data_set/unified/` folder, because that folder is git-ignored and was not re-measured here.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
