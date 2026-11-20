# 7_meta_and_other - P006: User restates no-attribution commit rule; goal prompt drafted
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-07
- Source: Claude Code session notes, pair P006. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

allowed to use commit on this repo , but if and onlyif you dont include attribution in the commit if not dont fucking do shit you dumb fuck

## Response

Understood. I will commit in this repo only when the message has no attribution or AI credit line. If I cannot meet that condition, I will not commit at all. I have added that rule to the memory note, so it now reads: commit without attribution, or do not commit.

##### Why the rule is a hard gate
The condition is all-or-nothing. A commit that cannot be made without attribution is simply not made, so no commit carries credit lines even under pressure to finish a step.

#### What the goal prompt is

The goal prompt is written for an AI coding agent (for example, Claude Code) that builds the whole plan by itself over many sessions. The prompt is in `goal_prompt.md` (not in the repository). I did not commit it. To start the build, open a fresh session and say: "Follow goal_prompt.md."

#### What the prompt contains

1. **Sources of truth.** `implementation.md` wins any conflict. The agent also reads the stage briefs, `plan_issues.md`, the configs and the existing code.
2. **Git rules.** No attribution or AI credit, ever. The agent never pushes and never adds a remote. Each stage gets its own local branch, and the agent never commits to or merges into `main`. Merging is your job.
3. **Experiment rules.**
   - The test split stays sealed. Only Stage 5 can read it.
   - The success criterion stays locked, and hyperparameters are tuned only on A1's validation split.
   - No fake numbers. If a result is bad, the agent reports it as it is.
4. **Things it must stop and ask you about**, after doing the prep work:
   - **Gemstone review:** The agent builds the contact sheet but does not pick the gemstones itself. Until your list exists, Stage 1 runs only as a dry run.
   - **Team inputs:** stage owners, the rubric, the deadline, the training machine and the license.
   - **Long training:** The agent asks before starting training runs if its benchmark estimates more than 12 hours.
5. **A progress file, `PROGRESS.md`.** The agent reads it at the start of every session so it can resume where it left off. It tracks each stage's status, the evidence for each "Done when" item, what is blocked, and how it resolved anything ambiguous.
6. **Build order.** Stage 0 comes first, starting with a check that moving the Phase 1 scripts does not change the data. Then Stage 1, then Stages 2 and 3 in parallel, then 4, 5 and 6. The dashboard can start early.
7. **How it checks its work.** `--check` and `pytest` must pass before the agent commits anything it calls done. It also does a rehearsal from a fresh clone and checks that every number in the report comes from an artifact.
8. **What "finished" means**, spelled out at the end.

#### Values I chose myself

Two values were my own choice, so change them if you want: the 12-hour limit before the agent must ask about training, and the branch names `stage/sN-*`.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
