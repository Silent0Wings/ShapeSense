# 4_testing - Is the project done? Final audit

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C42, C56
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [C56](../../4_testing/claude_opus/47_C56_final-audit-on-2026-11-10.md)

## Prompt 1 (12:34)

> Would to say project is done ?

## Response 1

**The research is done, but I wouldn't call the project done yet.**

**Finished:** iteration 3 is closed, the pre-registered test passed, and a clean clone reproduced the results. The dashboard and report are built, and all the work is committed locally on `iteration-3`.

**What still stands between this and done, all needing you or the team:**
- **Getting it off this machine:** nothing is pushed, this clone has no git remote, and `iteration-3` isn't merged into `main`. You also still need to decide about pushing `.agents/goal_prompt.md:36` from commit `47bcb5c`.
- **Course requirements:** the Phase 2 rubric and deadline haven't been checked against the work, and the six student IDs and `CODEOWNERS` are still missing.
- **Team decisions:** the plan-text PRs, and whether orientation is part of each class's definition.
- **Two open checks:** the raw-archive hash on a second machine, and the 60-drawing live check.
- **Public site (Stage 7):** not started. It needs a chosen license and your written approval of a named commit, so it only matters if you want it published.
- **Small leftovers:** approving the changed screens in Atlas, the F07, F08 and F10 previews, and the iteration column on Changes.

**What the result doesn't prove:** the gain is on synthetic damage, using sources the models saw in training. It doesn't show the models handle new sources, and the clean-image gain is small. Any new claim would need a new pre-registration and a new sealed holdout.

If there's a deadline, I'd start with the rubric check, because it may reveal missing work. Then add the remote and push, so the work isn't only on this laptop.

## Prompt 2 (20:23)

> your task is to do a final audit , in this audit you will clean up and confirm and finalize this solution , update the dashboard and and inform the user of anything , user is saticified with the models and needs no more ccleaning , just a final checkup

## Response 2

I'll start by checking the repo's current state, the open to-do and handoff notes, and how the dashboard gets rebuilt. Then I'll run the checks and record the audit.

The user committed the recipe folder's `.gitkeep` themselves at 17:36 (commit 20c4ed7). I'll report that rather than rewrite history. Next I'll look at the CRISP log and how the dashboard is built.

The CPU recipe experiment has no entry in the CRISP log. I'll check what it is and whether it finished.

While the tests run, I'll check the README and docs for stale facts, and find out how the studio reads the CRISP log.

Stage 6 is in sync with the log. While the tests run, I'll look for stale claims in the README.

Line 28 says the vote option and the public dashboard are still to come. I'll check whether the vote is already built and what the stage 7 gates are.

The vote option is already built, so README line 28 is out of date. I'll also check the stage 7 gates, since they decide whether deployment can start.

Nothing tracked looks like junk. I'll fix README line 28 now, while the tests finish.

The README isn't a hashed stage input, so this edit leaves the cache alone. Now I'm waiting on the test run.

All 535 tests passed. Next I'll run the guard check and confirm the access log and sealed data are unchanged.

The guards pass and the access log is unchanged. Last, I'll confirm the shipped model matches the A2 export.

Everything checks out. I'll record the audit in the CRISP log under Deployment, then re-run stage 6 so the dashboard and its hashes pick it up.

Stage 6 is re-running in the background, with a stall watcher. I'll check its result, the access log and the changed files once it finishes.

Stage 6 re-exported the model. I'll confirm it still matches A2.

The final audit passed. Nothing needed fixing apart from one out-of-date sentence in the README, and the dashboard now includes the audit.

**What I checked:**
- **Tests:** all 535 pass, and so do both guards (import boundaries and contract tests).
- **Pipeline:** all seven stages are `passed`, and stages 0 to 5 stayed cached. Nothing was retrained or re-evaluated.
- **Sealed test data:** the access log is still exactly 157 reads, all from the evaluation code. Nothing sealed was opened.
- **Shipped model:** `export/model.onnx` is identical to the A2 export, both before and after the stage 6 re-run.
- **Tracked files:** no stray logs, caches or other junk are tracked.

**What I changed (two files, not committed):**
- [README.md](README.md) still listed the "All models vote" option as future work. It's already built, so the README now says that, and that the public dashboard is the last step.
- [iteration_log.json](docs/crisp_dm/iteration_log.json) has a new Deployment entry called "Final audit on 2026-11-10". After that I re-ran stage 6, and it passed. The studio reads the log on every request, so the entry shows when you reload the page.

**Things you should know:**
- **Two of the four public-deployment gates are still open.** Gate 1 (work complete) and Gate 2 (results pass) both hold. Gate 3 needs a license for the team's code and model weights, and none has been chosen. Gate 4 is your written approval to publish, which only you can give. The stage 7 rules block deployment until both are settled.
- **The stage 7 brief and your deploy plan disagree on where the site lives.** The brief in [stage_7.md](stages/stage_7.md) puts it in a `deployment/` folder inside this repo. Your plan puts it in the separate `ShapeSense_Deployed` folder. Settle this before deployment work starts.
- **Commit 20c4ed7 added the recipe folder's `.gitkeep`.** That folder holds the old CPU runs backed up during the machine move, and the project rules say it should never be committed. The commit holds only that empty file, and its title says "results", which is misleading. Since nothing is pushed, you can remove the file in a new commit or leave it.
- **Nothing is pushed.** The `iteration-3` branch is 85 commits ahead of `main`.

If you want these two changes committed, say so and I'll commit them through the guard.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

All 535 tests and both guards pass. All seven stages are passed and cached. The test access log is unchanged at 157 reads, and the shipped model matches the A2 export byte for byte.

## Our decision

We asked for one final audit with no new cleaning. A clean clone reproduced the results (C42).

## Measured effect

No macro F1 change. The audit confirmed the frozen results (C56).

---

## Upgraded & Expanded Analysis: Research Completion vs. Project Publishability (`52_real`)

### Why this exchange matters

Two prompts, two distinct epistemic registers:
1. **Prompt 1 (Scoping boundary):** Distinguishes *research done* (Iteration 3 closed, pre-registered `+9.20` pass, clean-clone rehearsal verified) from *project done*, enumerating every item that requires human authority (git remote/push, Phase 2 rubric/deadline check, student IDs, `CODEOWNERS`, license selection $G_3$, written publish approval $G_4$).
2. **Prompt 2 (Executed final audit `C56`):** Converts the scoping answer into an automated verification sweep without overclaiming completion:

| Check | Result |
|---|---|
| Tests | `535 / 535` pass |
| Guards | Import-boundary (`import-linter`) + contract tests pass |
| Pipeline | All `7` stages `passed`; stages `0–5` stayed cached |
| Sealed test data | `artifacts/test_access.log` unchanged at exactly `157` reads (`13 + 52 + 92`) |
| Shipped model | `export/model.onnx` byte-identical to `A2` export before and after Stage 6 rerun |
| Tracked files | Zero stray logs, caches, or untracked build artifacts |
| Deployment gates | $G_1$ & $G_2$ met; $G_3$ (license) & $G_4$ (written approval) explicitly left open |

### Cross-Session Lineage

* **Related sessions:** [51_real_confusion-matrix-vs-first-run.md](51_real_confusion-matrix-vs-first-run.md) (next day's matrix inquiry), [53_real_vercel-deployment-plan.md](53_real_vercel-deployment-plan.md) (resolves the `deployment/` vs. `ShapeSense_Deployed` location conflict flagged in Prompt 2), [54_real_vercel-deployment-build.md](54_real_vercel-deployment-build.md) (executes the gated Stage 7 build).

