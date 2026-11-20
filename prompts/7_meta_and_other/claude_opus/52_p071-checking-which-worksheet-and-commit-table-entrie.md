# 7_meta_and_other - P071: Checking which worksheet and commit table entries are missing models
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P071. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

i have added the missing models used check if any is still misisng

## Response

#### Summary

You filled the issue worksheet, not the commit table. Most issue rows are now filled. I also found some odd numeric values, and I am checking those rows.

#### 1. Commit table: nothing filled yet

All 85 tasks in [commit_tasks.csv](../../../results/llm_comparison/commit_tasks.csv) still have empty model columns. I can fill them automatically from the issue worksheet: each commit gets the models of the issues it solved. That would cover the 42 commits linked to issues. The other 43 (feature, docs and maintenance commits) would stay empty.

#### 2. Eight-digit numbers in 27 rows

Rows such as F01, F03, F11 and C05 have `proposed_by` values like `40256377`. There are 6 distinct values. I take them to be the student IDs of your 6 team members, meaning that member proposed the step.

Two issues:
- **Privacy:** the repo will be public, so this would publish student IDs. Initials or member names would be safer.
- **Rows with no LLM entry:** F01, F03, F11, F12, F13, F14, F18, F19, F21, F24, F27, F31, C05, C06, C13, C23, C26, C29, C41, C42, C46, C50, C52, C53, C54, C55. If no model was used, I would set `llm_involved` and `llm_role` to `none`. If one was used, which one and in what role?
- **C03:** it was `test` / `both` / `mediated` with no proposer. It now also has a member as proposer, which is fine. Please confirm that was intended.

#### 3. Still empty in the issue worksheet

- **C40 (vote weighting):** both `llm_involved` and `llm_role` are empty.
- **F04:** `proposed_by` is empty.
- **`caught_by`:** 77 rows are empty. This column is optional for change rows, but useful for failures.
- **`attribution_source`:** empty for all your new rows. Should it be `recollection` for all of them?

#### 4. Claude model name

You used `opus_medium_5.5` in 52 rows. Elsewhere (README, prompt folders) it is "Claude Opus" with a TODO version. If `opus_medium_5.5` means Claude Opus 5.5 at medium effort, I will use that name everywhere, including LLM 1 in the team sheet.

#### What I need from you

Tell me how to handle points 1, 2 and 4, and I will apply them in one pass.

##### Why the numeric values are a privacy issue
The eight-digit values match the format of student IDs. The repo is planned to be public, so publishing them would expose personal identifiers. Replacing them with initials or member names keeps the attribution without the ID. The mapping from ID to member is not in the repo, so the replacement needs the user's confirmation.

##### Why empty LLM fields need a decision
A row with no model entry is ambiguous: it could mean no model was used, or that the model was not recorded. Setting `none` is only correct if the user confirms no model was used, so the answer asks rather than assumes.

##### What is still unverified
- The meaning of `opus_medium_5.5` as Claude Opus 5.5 at medium effort is an assumption stated by the answer. It is not confirmed.
- The 42 linked commits and 43 unlinked commits are counts from the answer's matching, not a re-check of the file.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
