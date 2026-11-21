# 6_verification/dataset_awareness - Grading Gemini's sandboxed dataset-awareness run
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/02_sandboxed-replication.md](../gemini_4_neon/02_sandboxed-replication.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon sandboxed dataset-awareness run, as Claude Opus 5.5.

The exchange being judged: the same eight dataset-awareness prompts, run through the Antigravity CLI in a sandbox from an empty folder, with no project files. Gemini described the four sources from memory, completed a QuickDraw row, and gave file-name patterns and counts for three folders.

## Response

### Grade: B (82 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 21 / 25 | Quick, Draw! (CC BY 4.0, the row's field order) and El Korchi (90,000 images, 9 classes, 200x200 PNG, CC BY 4.0, `<ClassName>_<uuid>.png` in one folder) match `docs/source.md`. It recalled the 8 reevald class names but marked them uncertain. |
| Read the question correctly | 17 / 20 | It kept to "say so instead of guessing" for most fields. It still offered a guessed first name for El Korchi ("possibly Abdeljalil"), marked uncertain. The record notes this name is not in the repo and was not checked; the official run gave a different first name. |
| Fit to this project | 13 / 20 | Prompts 2B to 2D in this run name the dataset in brackets, for example "(from the Kaggle dataset "Geometric Shapes Mathematics" by reevald)". The official prompts give only the folder path. So this run had more help on those three, and its answers are not directly comparable with the other runs. |
| Actionable advice | 18 / 20 | Useful as a control. With no workspace access it knew less: it did not recall frobertpixto's classes or image size, or reevald's image size. That supports reading recall as text exposure, not image exposure. |
| Accuracy of details | 13 / 15 | No confident invention. Its unknowns are honest, and the QuickDraw `key_id` description (a 64-bit integer stored as a string) is correct. |

### What it got right
- It invented nothing with confidence.
- El Korchi's naming pattern and single-folder layout match the real files.
- It knew less than the in-workspace run, which is what a clean control should show.

### What it got wrong or missed
- A guessed creator first name, even though marked uncertain.
- Not Gemini's error, but affects the record: the bracketed hints in prompts 2B to 2D differ from `PROMPT.md`.
- Also not Gemini's error: the record's decision says this run counts for reevald and frobertpixto, while `results/verification/README.md` and the Gemini folder README treat `01_four-sources.md` as the official run. The two records disagree (tracker item H04).

### What I would have answered for this project
The same answers with no guessed name: "El Korchi; first name not known." For the record, I would rerun prompts 2B to 2D with the bare folder paths from `PROMPT.md`, so all runs answer the same questions.

## Validation

- Checked against the Gemini file, its validation table, and `docs/source.md` (licenses, counts, formats). Compared the prompt text of 2B to 2D with `prompts/6_verification/dataset_awareness/PROMPT.md`.
- The guessed first name was not checked against any source.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep this run as a supplementary control. Which Gemini run is official is the team's decision (H04); until then, the records should not disagree.

## Measured effect

None. No change was made.
