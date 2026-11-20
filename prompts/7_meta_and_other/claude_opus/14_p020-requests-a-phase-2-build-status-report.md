# 7_meta_and_other - P020: Requests a Phase 2 build status report
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P020. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

% status repport

## Response

### ShapeSense Phase 2 build: status

**19 of 25 tracked entries are done and verified. Stage 4 training is running.** Nothing has been committed or pushed, and no git was run.

#### Done, with in-tree evidence
- **Stage 0 infrastructure:**
  - validated configs, the status writer with its cache, and the test-split guard with its access log
  - hashing, the script migration (the rebuilt catalog is byte-identical), runner flags, and import boundaries (5 of 5 contracts kept)
  - placeholder report tables
- **Stage 1 data freeze** on real data:
  - 12,754 / 2,895 / 2,851 train, validation and test. The Phase 1 counts were expected to change. All leakage checks pass.
  - the manifests reproduce byte-identically, including in a fresh copy of the repo
  - the source-shortcut check **fired**, with a 43.8-point gain over the majority rate. The Hand-Drawn leave-one-source-out runs are therefore now required.
- **Stage 2 augmentation** and **Stage 3 generator:** QA sheets reviewed with no class-changing outputs. Stage 3 runs at about 5,000 img/s against a target of 2,000.
- **Stage 4 pieces:** the loader and sampler, and baselines at 75.6 (logistic regression on pixels) and 80.4 (linear SVM on HOG) validation macro-F1.
- **Stage 5 statistics, the dashboard, and the Phase 1 report fixes.**
- **Three independent audits** found 25+ issues. All confirmed issues are fixed, each with a test and a mutation check.

#### In progress: Stage 4 training
The first recipe underfit, at 39 validation macro-F1. The cause was the plan's own CNN: 3 blocks gave too small a receptive field. Augmentation also produced shapes smaller than the real ones.

Two fixes were made. Both are identical for every arm, and both were decided on validation only, with the test set untouched:
- **4 conv blocks**
- **augmentation framing that matches Stage 1**

A short check on real data showed large gains (A1 validation accuracy went from 37% to 69%). The 6 Decision 7 tuning runs are training now, which should take about 1 to 2 h. Then come 9 arm-by-seed runs plus 2 Hand-Drawn LOSO runs, about 2 more rounds.

#### Remaining after training
- **E28:** Stage 4 sign-off.
- **E30 Stage 5:** the power check first, then one test read per model, then the verdict.
- **E32 export bundle, E33 demo check, E35 Phase 2 report build.**
- **E19:** the last rehearsal step.

#### Needs you (none of it blocks training)
- **Gemstone review.** Contact sheets are in `artifacts/stage1/gemstone_contact_sheet_*.png`. Fill `configs/gemstone_ids.csv`, then rerun Stage 1.
- **Commit** the work and `configs/splits/`.
- **Rubric and deadline, project license, and owners in `CODEOWNERS`.**
- **Data hash check on a second machine.**
- **The 60-drawing live demo check.**

#### Plan deviations (all logged in `plan_issues.md`, P-45 to P-59)
- the 4-block CNN, which needs a team PR to amend Decision 8
- the Gradio demo instead of the Streamlit canvas
- 6 runs in parallel at 2 threads each, a CPU budget choice

#### Tuning progress
The monitor is re-armed. Tuning was about 1 h 25 min in, and no run had finished yet, which was expected.

About 2 h in with no finished run, I checked that the workers were still busy rather than stalled. All 6 were still busy. I read one worker's current epoch from its stack to estimate the time left.

The fix is working. All six runs were around epoch 15 of 30 and still improving:

| lr | dropout | best val macro-F1 so far |
|---|---|---|
| 0.003 | 0.4 | **85.5** |
| 0.003 | 0.2 | 85.1 |
| 0.001 | 0.2 | 81.4 |
| 0.0003 | 0.2 | 80.4 |
| 0.001 | 0.4 | 78.3 |
| 0.0003 | 0.4 | 75.5 |

That compares with 39.2 under the old recipe. The best runs already beat the HOG + SVM baseline (80.4). None had early-stopped, so the cosine schedule should anneal properly this time. The other two fixes appear to have resolved P-56.

#### Timing
About 7.5 min per epoch with 6 runs sharing the CPU, so the grid needs roughly 2 more hours. The 11-run sweep then takes about 2 rounds of up to about 4 h each. Stage 4 is therefore an overnight job on this CPU. Stages 5 and 6 are quick after it.

##### Why the timing matters
The sweep runs on a fixed CPU budget, so the schedule depends on how many runs share the 14 cores at once. Running 6 jobs at 2 threads each was a budget choice, recorded as a plan deviation. Changing that concurrency would change the timing estimates above.

##### Reading the tuning table
The table is mid-run data, not a final result. The best run so far (lr 0.003, dropout 0.4, 85.5) beats the HOG + SVM baseline of 80.4, but no run had finished, so the winner was not yet chosen.

##### Next steps
- Wait for the tuning grid to finish, then choose the winner on validation only.
- Review the Stage 1 gemstone list before the next data freeze, since a rerun changes the split.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
