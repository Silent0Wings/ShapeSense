# 7_meta_and_other - P114: Asks to add recommended summaries and extract saved Claude sessions for big decisions
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P114. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[The  files: each entry already has "Documented outcome", which is what was done. It has no "what the LLM said". You could add a "Recommended (summary)" line to the entries where you remember the advice. The diamond review (F01), the per-arm search (F06) and the architecture critique (D03) are good candidates.

Even a handful of real exported chats is worth more than many summaries. So it's worth looking through your Gemini activity history and the 3 saved Claude Code sessions for the big decisions first.]

## Response

I did two things: I added a "Recommended (summary)" line to the entries where the advice is known, and I searched the saved Claude Code sessions for the big decisions. I could not open your Gemini activity history from here, so that part needs your export.

##### Situation
The reconstructed files said what was done but not what the LLM advised. Every chat in the prompts folder was a reconstruction. You also asked which parts of the data-discovery checklist the repo actually covers.

##### Task
Add the advice summaries, find real chats for the big decisions, and check the checklist against the code.

##### Action
- **Real chats.** The session of 2026-11-08 contains two of the big decisions word for word. I saved them using the template, keeping your typed answers to the multiple-choice questions. I only shortened local paths and changed en dashes to hyphens, and each file says so.
  - `prompts/2_data_preparation/cleaning/claude_opus/03_f01-quickdraw-diamond-review.md` holds the whole F01 exchange: your "gemstones look like doodles" message with the review sheets; Opus's three options, recommending A (drop all); your "it depends, can the models learn it?"; the validation check it ran (Quick, Draw! diamond recall 59%, 16 of 76 called triangle); and your final "drop them, and record it as part of the cycle".
  - `prompts/3_modeling/claude_opus/16_d04-move-training-to-gpu-machine.md` holds D04: the GPU question, Opus's speed-only advice and its warning not to mix machines, plus the ellipse and machine choice (F02).
  - The worksheet's `prompt_file` for F01, C01 and D04 now points to these real files.
- **Recommended (summary) lines.**
  - F01 was written from the real chat.
  - F06 was written from the worksheet note (the team split, and Gemini's two-day per-arm search).
  - D03 says only that the depth change is recorded. The rest of the architecture critique is not in any saved session, so I did not invent it.
- **Gemini activity history.** I cannot open it from here. If you export the big-decision chats, I will clean them up and file them the same way.

##### Result: data discovery checklist against the repo

| Done (evidence in the repo) | Not done |
|---|---|
| Sources and licenses (`docs/source.md`, Stage 1 builder) | A second annotator and agreement score (no kappa anywhere) |
| Counts per class and source (`catalog.py`, class/source chart) | t-SNE or UMAP of embeddings |
| Image properties: color modes, transparent backgrounds, standardized to 64x64 (`standardize.py`) | Per-channel mean and std, image-size or aspect-ratio histograms |
| Bad images rejected: no contrast, blank, too small, broken by resizing (`audit_dataset.py`) | EXIF or capture metadata (does not apply to these sources) |
| Exact and near-duplicates: file hashes, pHash groups kept inside one split | A coverage grid (class x condition) |
| Visual label check: the diamond review sheets (F01) | Reviewing the highest-loss images as a discovery step |
| Source leakage: the source-shortcut check (F05), leave-one-source-out runs | |
| Quick baselines: logistic regression on pixels and a linear SVM on HOG features (`baselines.py`) | |
| A confusion matrix (Stage 5 figures) | |
| A realistic held-out evaluation: sealed test split, two fresh holdouts, damaged copies | |

##### Notes on the folders
- `0_data_discovery/claude_opus` is correctly empty. No Opus chat exists for Phase 1 data discovery.
- You said Phase 1 was mostly Gemini 4 Neon with web search, so it belongs in `gemini_4_neon/` once exported.
- Many of the checks above were done later in Stage 1, so they are recorded under `1_data_integration` and `cleaning`.
- The README table now undercounts Opus files by two. Cleaning should be 3, not 2, modeling 16, not 15, and the total 49, not 47. I did not edit it because another process was still editing the file. You can change it by hand, or I can fix it once that process stops.

##### Why the chats were quoted word for word
A real exchange is evidence only if it is unedited. The answer kept the user's typed answers and changed only local paths and dashes, and each file says so. That is the difference between a record and a summary.

##### Why the summaries were limited
The "Recommended (summary)" lines are written only where the advice is known from a source. D03 records only the depth change, because the rest of the critique is not in any saved session. Inventing the rest would put unrecorded advice into the evidence.

##### What was checked
- The checklist was matched against files named in the answer (for example `docs/source.md`, `catalog.py`, `baselines.py`). The answer does not re-run those scripts.
- The 16 `3_modeling` count and the 49 total in the answer are the counts after the split, and the README still shows the older numbers.

##### Consequence
The README table is out of date until the user or the assistant edits it. Until then, the Opus file counts are inconsistent across the repo.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
