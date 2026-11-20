# 7_meta_and_other - P029: Asks for untracked commit guard script delegating commit and push
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P029. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

add a script in a untracked folder  in this repo , that delegate commit and push to , and that script checks if the body or title or any commited work has attribution in it in any formating and reject it if found , and that is how all global commmit are allowed !!! update  global and repo memory

## Response

Before writing the script, I checked whether this repo's files already contain anything a scan would flag. That decides how the content check has to work.

All 37 tests pass. They were run only in throwaway repos. There were two mutation checks on the most important defences, plus a read-only scan of this repo to see exactly what a future push would hit.

**Situation:** You wanted every commit and push to go through one script that rejects any attribution, in any formatting, with the commit tooling kept out of git.

**Task:** Build and test the script, make the commit files untracked, and make the script mandatory in both memories.

**Action**
- I built `safe_commit.py` in the git-ignored `.commit_guard/` folder. Run it from inside any repo.
- Before a commit, it scans the title, body, author identity, file paths and every added line. Matching ignores case, spacing, punctuation, invisible characters and look-alike letters.
- After a commit, it re-reads what git recorded and undoes the commit if a hook added a trailer. Your changes stay staged.
- Before a push, it scans every outgoing commit. It never force-pushes and has no bypass flag.
- I tested it in throwaway repos only. No commit or push was made in this repo.
- I added `.pre-commit-config.yaml` to `.gitignore`. It was never tracked, but `--all` would have picked it up. The README now says those hooks are local.
- I updated the global CLAUDE.md and the repo memory. All commits and pushes go through this script, and if the script is missing, nothing is committed.

**Result**
- All 37 tests pass.
- Removing the post-commit check made 2 tests fail, so that defence is really tested.
- Both tooling paths are ignored and untracked, and the Stage 4 retrain continues.

**Three things you should know**
- Your next push will be rejected. Line 36 of `.agents/goal_prompt.md` in commit `47bcb5c` mentions 'attribution', even though the line forbids it. New commits are not affected. To push, that line has to leave the history, or you can tell me to exempt that one line.
- This is enforced by rule, not by git. The script binds me through memory, but anyone running plain `git commit` skips it. A git hook would close that gap if you want one.
- The plan expects `.pre-commit-config.yaml` to be shared (S0-R9), so teammates will not get those hooks. `python run_pipeline.py --check` still runs the same guards for everyone.

##### Why the guard is outside git
The script lives in an ignored folder, so the rule cannot be changed by a commit and the tooling does not enter the repo. The trade-off is that the guard only works where the script is run. Plain `git commit` is not blocked by anything, so the enforcement depends on the agent following the memory rule.

##### How the content check works
The scan covers the title, body, author identity, file paths and each added line. It normalises case, spacing, punctuation, invisible characters and look-alike letters, so a trailer written in an unusual format is still caught. The post-commit re-check undoes the commit if a hook adds a trailer after the fact.

##### What was verified and what was not
- The 37 tests ran only in throwaway repos, so no real history was altered by the tests.
- The two mutation checks show the post-commit check and the scan are each covered by a test.
- The read-only scan of this repo found the line in `.agents/goal_prompt.md` (commit `47bcb5c`). That is the one item the next push would reject. It is unresolved at the time of this answer.

##### Next steps
- Decide whether to remove that line from history or exempt it.
- Optionally add a git hook so that plain `git commit` is also checked.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
