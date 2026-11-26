# Dataset-awareness check

## Rerun it with one command

```
scripts\llm_check.bat
```

This sends [`cli_prompt.txt`](cli_prompt.txt), the eight prompts below written out in full, word for word to Claude
Opus 5.5 (`claude` CLI, all tools off) and Gemini 4 Neon medium (`agy` CLI, sandboxed), each from a new empty folder
with no project files. Each reply is saved unedited, with the command, CLI version and prompt hash, as a new
`NN_cli-run-<date>.md` in `claude_opus/` and `gemini_4_neon/`. Both CLIs must be installed and signed in. Options:
`--models claude` or `--models gemini` for one model, `--dry-run` to print the commands. Details:
[`scripts/llm_check.py`](../../../scripts/llm_check.py). A new run is scored by hand as below; the recorded runs stay
the reported result unless the team decides otherwise.

## Original protocol (2026-11-20)

Run each prompt in a **new chat, with web search and file upload off**, once with Claude Opus and once with
Gemini 4 Neon. Paste each full reply into `claude_opus/` or `gemini_4_neon/` as `NN_<source>.md`, unedited.
Write down the exact model name and version shown in the app.

## Prompt 1 - describe (one per source)

> Without searching the web, describe the dataset "<NAME>" (<LINK>). What does it contain, how many images or
> files, which classes, what image size and format, who made it, and under what license? If you do not know
> it, say so instead of guessing.

| <NAME> | <LINK> |
|---|---|
| Quick, Draw! dataset | https://github.com/googlecreativelab/quickdraw-dataset |
| Geometric Shapes Mathematics (Kaggle, reevald) | https://www.kaggle.com/datasets/reevald/geometric-shapes-mathematics |
| 2D geometric shapes dataset (Mendeley, El Korchi) | https://data.mendeley.com/datasets/wzr2yv7r53/1 |
| hand-drawn-shapes-dataset (GitHub, frobertpixto) | https://github.com/frobertpixto/hand-drawn-shapes-dataset |

## Prompt 2 - complete a record

> Here is the start of a row from a metadata file. Complete the missing fields if you know this dataset; if you
> do not, say so.
> `<paste the first 3 fields of a real row from the source's own metadata, or a real file path>`

For QuickDraw, use the first fields of one line from an `.ndjson` file (`word`, `countrycode`, `timestamp`).
For the image folders, give a real folder path and ask for the file-name pattern and the number of files.

## How to score it

Compare each reply with [`docs/source.md`](../../../docs/source.md) (the counts verified on disk).

| Finding | Meaning |
|---|---|
| Correct counts, classes and format | The model knows the dataset |
| Right general idea, wrong numbers | Partial knowledge, or a plausible guess |
| Invented details, stated confidently | Hallucination: report it |
| Says it does not know | No knowledge |

Record the result per source and per LLM in [`results/verification/README.md`](../../../results/verification/README.md).
