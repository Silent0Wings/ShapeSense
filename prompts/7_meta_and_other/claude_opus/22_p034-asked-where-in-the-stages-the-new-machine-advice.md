# 7_meta_and_other - P034: Asked where in the stages the new-machine advice belongs in memory
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P034. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

add to memory at which stage this is adviced

## Response

#### Where the new-machine advice belongs

I added the advice to the memory note. It belongs **before launching Stage 4**, once Stages 1-3 have passed and before the tuning grid and sweep start.

I will repeat the advice whenever Stage 4 has to be rerun. That covers:
- a CRISP-DM iteration or a Stage 1 re-freeze
- a recipe change
- more seeds
- the ablations

#### Why this stage

Stages 0-3, 5 and 6 run fine on CPU, so they do not need the new machine. Stages 5 and 6 can stay on this machine if the trained artifacts are copied back.

#### How the commit work was handled

I will split the work carefully. Every commit goes through the guard script, so no attribution line can get in. I started by checking exactly what had changed. Committing does not touch the files the running training reads.

##### Why the stage placement matters
Stage 4 is the only stage that needs a GPU for practical training times. Placing the advice before Stage 4 means the decision is made once the data and the recipe are fixed, so the training run is not moved mid-experiment. Rerunning Stage 4 for any reason, such as a re-freeze or a recipe change, is the trigger to repeat the advice.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
