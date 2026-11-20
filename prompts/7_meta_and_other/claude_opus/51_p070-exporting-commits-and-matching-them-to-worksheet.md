# 7_meta_and_other - P070: Exporting commits and matching them to worksheet issues
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P070. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

your allowed once only this time

## Response

The `ignore/` folder didn't exist, so the shell failed to open the output file before git started, and git never ran. I created the folder and then used the one git run you had allowed.

That run exported 85 commits, and I won't run git again. I then read the commits and matched them to the worksheet by content. For the less obvious matches, I checked the full commit messages. I also added a commit view, where each of the 85 commits is one task, with the worksheet entries it solved or faced. Commits that built something without a logged issue are labeled as such. Eight commits had no stage, so I set those by hand, using what each commit says.

##### Why one git run was used
The user granted a single git run for this export, and the assistant used only that one. The first attempt failed because the `ignore/` folder did not exist, so git never started. That failure is why the folder was created before the one allowed run.

##### How the matching was done
- Each commit was read and matched to worksheet rows by content, not by date alone.
- Less obvious matches were checked against the full commit messages.
- Commits that built something with no logged issue are labelled that way instead of being forced onto a row.

##### Counts and open items
- 75 entries matched a commit that made the change, 9 matched only a commit that logged the issue, and 4 have no commit (F10, C07, C13 and C18). Those four are the unmatched entries to resolve.
- The task-type counts (38, 19, 9, 6, 5, 4, 2 and 2) add up to 85, one per commit.
- T85 is the user's commit of the folder structure from the day of the answer.

#### What changed
Each of the 85 commits is now one task, matched to the issues in the failure and change log.
- **[commit_tasks.md](../../../results/llm_comparison/commit_tasks.md)** is the readable table. Each row has the task (T01 to T85), date, commit, title, type, course stage, and the failure and change IDs it solved or faced.
- **[commit_tasks.csv](../../../results/llm_comparison/commit_tasks.csv)** is the same table, with empty `proposed_by`, `caught_by`, `llm_involved`, `llm_role` and `notes` columns, so you can assign models per task.
- **[attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)** now also links each issue to its commits. 75 entries matched a commit that made the change, and 9 matched only a commit that logged the issue. 4 have no commit: F10 and C07 (synthetic stroke 2 px to 3 px), C13 (5 seeds per arm) and C18 (shipped model A2_2).

#### Task types
| Task type | Commits |
|---|---|
| Solved a logged issue | 38 |
| Built a feature | 19 |
| Documented | 9 |
| Maintenance | 6 |
| Solved an issue not in the log | 5 |
| Faced an issue (recorded, not yet fixed in that commit) | 4 |
| Tested | 2 |
| Other (initial commit, icons) | 2 |

#### The performance work
It shows up as two tasks:
- **T59** (`b3bb15d`): batches built on 7 processes, solving F21 and C30.
- **T62** (`534643d`): optimization without changing results, solving F23, F24, C31, C34, C35 and C36. Its commit message says "Written and reviewed by reading only: not yet run or tested." The later log entries C31 and C39 then measured the speed-up. This is a good example for the validation section: the LLM's code wasn't trusted until it was measured.

#### Still open
- The model columns in `commit_tasks.csv` are empty. One model per commit is probably easier for your team to fill in than one per issue.
- The 4 unmatched entries.
- T85 is your commit of the new folder structure from today.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
