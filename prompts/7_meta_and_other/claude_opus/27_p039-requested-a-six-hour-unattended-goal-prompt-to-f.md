# 7_meta_and_other - P039: Requested a six-hour unattended goal prompt to finish the work
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P039. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

generate a goal prompt for me to give you so that i can step out and you handle the work for the next 6 hours with 0 human supervision

## Response

#### Checking the run

I first checked where the run stands, so the prompt starts from the real state.

#### The goal prompt

The prompt is written for me, as an unattended agent in a fresh `/goal` run. It is in [.agents/goal_finish_6h.md](../../../.agents/goal_finish_6h.md), a git-ignored folder. To start it, type:

```
/goal Execute the goal defined in @.agents/goal_finish_6h.md exactly as written.
```

**What it tells me to do:**
- Wait for the Stage 4 retrain that is already running, and relaunch it if it dies.
- Run Stages 5 and 6, check the figures and the PDF, then test the export and demo.
- Finish the clean-copy rehearsal, update the tracker, and commit through the guard.
- Stop at 5 h 30 min no matter what, and write `ignore/handoff_phase2.md` in STAR format.

**Safeguards it sets:**
- Commits only through the guard, no pushes, no attribution.
- No edits to any code that finished training depends on.
- No changes of any kind after the test set is read. A failed verdict is reported as it is.

#### Before you step out

- **Keep the PC awake.** Turn off sleep and hibernate, and leave this VS Code window open. If the machine sleeps, training pauses while the time box keeps counting.
- **Permissions can stall it.** If a permission prompt appears while you are away, that step waits or gets denied. Keep this session's auto mode on. The prompt tells me to record anything blocked and move on.

#### What to expect

Only 1 of the 6 tuning runs has finished so far. My rough estimate is that Stage 4 ends around 09:30, with the 6 hours running to about 10:20. That leaves enough time for Stages 5 and 6, but not much slack. If training runs long, you will get an accurate handoff saying how far it got, not a rushed result.

##### Why the plan is built this way
An unattended run has no one to answer questions, so the prompt sets explicit rules in advance: a hard stop at 5 h 30 min, commits only through the guard, no pushes, and no edits to code that finished training depends on. The time box leaves about 50 minutes of slack before the 6-hour limit.

##### Risks to check before stepping out
- Sleep or hibernation pauses training while the time box keeps running, so the machine must stay awake.
- A permission prompt that appears while you are away will stall or deny a step. The plan asks for blocked steps to be recorded and skipped.

##### Consequence
Whatever state the run reaches, the handoff file (`ignore/handoff_phase2.md`) is the record. The estimates above (Stage 4 around 09:30, the run ending around 10:20) are predictions made at the time, not confirmed results.

I also saw that you have already committed the assets and the banner (`09755a9`, `f400043`), so nothing is left uncommitted.

The watcher timed out, which is routine. The Stage 4 retrain itself keeps running. I am not re-arming the watcher, because the 6-hour goal sets up its own watcher when you start it.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
