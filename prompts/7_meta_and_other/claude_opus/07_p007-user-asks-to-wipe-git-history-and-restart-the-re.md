# 7_meta_and_other - P007: User asks to wipe git history and restart the repo
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-07
- Source: Claude Code session notes, pair P007. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

can we nuke the entire git of this repo since it remember old stuff ?

## Response

#### What I did

Your global git identity is set, so deleting `.git` does not lose it. I went ahead and deleted the old git history and started the repo over.

#### Result

- The repo now has exactly one commit, `47bcb5c Initial commit`, on `main`.
- You are the author, and nothing in `.git` mentions a attribution.
- The old branches and all 28 earlier commits are gone for good.
- Your files were not touched, and nothing was pushed.

#### Files the new commit picked up

The commit includes every file that `.gitignore` does not exclude. That brought in two folders you might not want tracked:

- **`.agents/`** (2 files), which holds `goal_prompt.md` and the `text-humanizer` skill.
- **`ignore/`** (10 files). Despite the name, `.gitignore` does not exclude it.

`phase1_report.pdf` and the 26 files in `figures/` went in too. If any of these should not be tracked, I can add them to `.gitignore` and amend the commit.

#### Goal prompt

I read the seven stage briefs so the goal prompt covers what they add beyond `implementation.md`, then folded them in: R-number coverage, Done-when lists, Pitfalls and Mission expected outcomes. The prompt is written for an AI agent running as the lead orchestrator over many sessions, starting from a fresh session.

The goal prompt is at [.agents/goal_build_implementation.md](../../../.agents/goal_build_implementation.md). It follows the layout of your example, uses your `.agents/` prompts, and covers all seven stage briefs. Paste its contents to start a run.

**How the briefs are covered:**
- **Coverage matrix first.** The agent's first job is `ignore/plan/10_coverage_matrix.md`. It has one row for every Must requirement (all 88 R-numbers across Stages 0-6), every Should, every Done-when box and every deliverable path. The run cannot finish while any row is unmapped.
- **Missions become tests.** Each Mission's "Expected outcome" is turned into a named test. For example, the 77 synthetic + 179 real batch, McNemar chi-squared 4.51, and the bounding-box vs min-area-rectangle check on rotated rectangles. Mission code snippets are treated as sketches, so the agent fixes their TODOs and unit mix-ups instead of copying them.
- **Pitfalls in the audit.** After each sub-agent finishes, the audit walks that brief's Pitfalls list item by item.
- **Done-when boxes stay unticked** in the briefs, because the stage owner owns them. The agent records them as met in the matrix instead.
- **Brief vs plan conflicts.** `implementation.md` wins, and each conflict gets logged as a new P-NN row. For example, Stage 5 says `#criterion` but the config key is `success_criterion`.

**Choices you may want to change:**
- **No git at all.** Your `.agents/` prompts all forbid it, so wherever a brief says "commit" or "in a PR", the agent parks that step for you.
- **Overrides of your parallel-execution prompt,** taken from your example: up to 35 sub-agents at once instead of 10 in total, and `fable` for hard problems such as the Stage 4 loader or step-budget design and the Stage 5 statistics.
- **Stage 0 is mostly the orchestrator's own work,** because it touches the shared files. That includes adding the missing config keys in one reviewed step, using values copied verbatim from the Decisions.
- **Left for you:** the gemstone review, the git commits, the second-machine hash check, the owners, the rubric, the license, and the 60-drawing live sketch check. The agent prepares each of these and keeps working on everything else.

#### Which files to give the agent

Use only `goal_build_implementation.md`. Leave out the other two:

- **Do not add `goal_prompt.md`.** It is the older version and it conflicts with the new one. It allows local git branches and commits, keeps a separate `PROGRESS.md` ledger, and stops to ask before long training. The new file has no git at all, uses `ignore/todo.md` plus the coverage matrix, and runs without asking. Giving the agent both gives it contradictory rules.
- **Do not add `implementation.md`.** The goal file already points at it with `@implementation.md`, along with all seven stage briefs, and tells the agent to read them first.

Either of these works:

```
/goal Execute the goal defined in @.agents/goal_build_implementation.md exactly as written.
```

Or open `goal_build_implementation.md`, copy everything (it already starts with `/goal`), and paste it in. Pasting is the safest choice: the full text becomes the goal itself, so it does not depend on the agent opening the file.

You could also rename `.agents/goal_prompt.md` (for example to `goal_prompt.old.md`), so no future session picks it up by mistake.

##### Why the older prompt is a risk
Two goal files with different git rules would give the agent contradictory instructions. The new file removes git from the loop, so keeping the old file in `.agents/` is the main source of confusion. Renaming it is a reversible step, and the content is kept.

##### What was not verified
The answer does not show a test run of the goal file. Whether the agent follows it as written can only be confirmed by running a session.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
