# 7_meta_and_other - P015: Asks about sub-agent budget; agent launches read-only audits
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P015. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

Are you using your sub agent budget fully ?

## Response

No. The goal allows up to 35 sub-agents at once, and I have used 13 in total: two waves of 6, plus 1 for the report. None is running right now.

##### Why the budget is not fully used

The bottleneck is now CPU, not code.

- The CNN underfits: it scores 39 on validation macro-F1, against 80 for the HOG baseline.
- Finding the cause needs real training runs on this machine.
- Sub-agents cannot run code, and more parallel training would only compete for the same 14 cores.

##### Where extra capacity does help

You are right that I was leaving capacity idle. Independent audits suit this work: they read code, need no CPU, and give a review that is not anchored on my own conclusions. I launched three static auditors, one per stage group, while the diagnostic trains:

- **Stages 0-1 (common code and the runner):** checking for leakage, split determinism, holes in the test-split guard, and caching that could mark stale work as passed.
- **Stages 2-4:** told about the underfitting and asked to rank likely causes in the data path and training loop.
- **Stages 5-6 (dashboard, demo, export):** checking the statistics and verdict logic against the locked criterion, and whether report claims are truly generated.

The auditors report findings only. I verify each finding and apply the fixes myself. I am not adding more agents beyond these three, because the remaining blockers are the training diagnostic (CPU-bound) and human-only items: the gemstone review, git commits, the rubric and the license. Agents cannot speed up any of those.

##### Why parallel auditors were chosen
A static audit reads code and does not use the CPU, so it can run alongside the CPU-bound diagnostic without slowing it. Each auditor got one stage group, which keeps the scope narrow and the findings easy to check. The auditors were asked to report only, so no code changed while the training runs depended on it.

##### How the findings are handled
Each finding is verified by reading the cited code before a fix is made. Findings that touch Stage 2 to 4 code wait until training ends, because any change there alters the recipe fingerprint and would invalidate the runs in progress.

##### Consequences
- The two HIGH issues block Stage 5, so they are fixed first.
- Any change to the training recipe must either stay inside the Decision 7 grid or be a reviewed plan change applied identically to every arm, so that the comparison stays fair.

##### Stage 5-6 audit results

The statistics core checks out: the paired bootstrap, Holm, the verdict, the thresholds, the power-check ordering and the demo edge cases.

It found two HIGH issues to fix before Stage 5 runs:

1. **The prediction cache ignores the test manifest.** If Stage 1 is rerun, for example after the gemstone review, cached predictions from the old split could be paired image by image with fresh predictions from the new split.
2. **Named ablation runs (such as `B_equalreal`) would be folded into the B ensemble** of the locked primary comparison.

It also found three MEDIUM issues:
- The dashboard shows a false 'test leak' on Stage 4 when it shares a run id with Stage 5.
- An `=` sign hides typed numbers from the traceability check.
- An extra, unaccounted test read is used for the galleries.

Several LOW items were also found. They touch only Stage 5/6, dashboard, demo and export files, so a fix agent can work on them in parallel with my Stage 4 investigation.

##### Current state

The 600-step diagnostic is running and the three auditors are working. I will decide the training fix from both results. Any fix must either fall within the Decision 7 grid or be a reviewed plan change applied identically to every arm.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
