# 7_meta_and_other - P024: Requests another status report on Stage 4 training
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P024. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

status repport

## Response

##### Overall status

**19 of 25 entries are done.** Stage 4 (the main experiment's training) is running with no errors, and everything else waits on it. No git commands have been run.

##### Stage 4 training

**Tuning grid (Decision 7): done.** The winner was chosen on A1 validation only: lr 0.003 and dropout 0.4, at 89.2 validation macro-F1. Every grid run beat the old recipe's 39.2 by a wide margin.

**Sweep: 3 of 11 runs finished.**

|Run|Val macro-F1|Best epoch / epochs run|
|-|-|-|
|A0_0|87.6|10 / 15|
|A0_2|85.2|6 / 11|
|A1_0|89.15|16 / 21|

- A1_0 reproduces the tuning run with the same arm and seed exactly. That confirms the runs are deterministic (R9).
- **Running now:** A0_1, A1_1 and A1_2 are near the end (epochs 24-26 of 30). A1_2 has since finished at 87.7 validation macro-F1. B_0, B_1 and B_2 are at epochs 2-11.
- **Queued:** the 2 Hand-Drawn LOSO runs (A1 and B). They are required because the Stage 1 shortcut check fired.
- **Estimate:** about 4-6 h more, mostly for the B runs and the LOSO pair.

##### After Stage 4 (automatic, about 30-60 min)
- **Stage 5:** the power check on validation first, then exactly one test read per model, then the locked verdict for B versus A1, with confidence intervals.
- **Stage 6:** the export bundle, the Phase 2 report build and the traceability check. After that I verify the demo end to end and finish the clean-copy rehearsal.

##### Done since the last report
- Three independent audits found 25+ issues. All were fixed, with tests and mutation checks.
- The underfitting fix: a 4-block CNN plus standardized augmentation framing.
- Training resume is now locked to the recipe, so no runs can mix across a recipe change.
- The demo now starts cleanly without a model.

##### Gemstone labels and the diamond decision

You flagged the contact sheets, and I agreed with you. Most of the drawings labelled diamond are not diamonds in the taxonomy's sense. The definition is a rhombus without right angles: 4 equal sides and 4 vertices. On sheets 0 and 3, I estimate that only about 20-30% are clear rhombi. The rest are:
- **Gemstones:** a crown on top with facet lines, so 5-6 outer vertices (the Decision 1 target).
- **Cones, ice-cream shapes, shields and triangles.**
- **Scribbles, single lines and half-drawn outlines.**

This is label noise, and it is the harmful kind. Many of these drawings look like pentagons, hexagons or triangles while being labelled diamond. That teaches the model the wrong class boundaries, and it can hurt those other classes too, not just diamond.

|Option|Pros|Cons|
|-|-|-|
|**A. Drop all Quick, Draw! diamonds** (a rule by source and label)|Simplest and fully reproducible. No review list and no per-image judgement.|Diamond becomes render-only (rendered rhombi only). The model never sees a sketched diamond, which is a weakness on sketch inputs and in the demo. It also becomes a new single-source class, like pentagon and ellipse.|
|**B. Keep only clear rhombi** (the Decision 1 review, widened from gemstones to anything that is not a rhombus)|Clean labels, and some sketch diamonds are kept (maybe 100-150).|About an hour of human review by 2 reviewers plus a tie-breaker. I must not pick the images myself.|
|**C. Keep as is**|Nothing to do.|Known label noise in the training and test data, which the report would have to defend.|

**My recommendation is A.** It is defensible, reproducible and needs no review time. I would record it as a Decision 1 amendment and add "diamond is render-only" to the limitations, next to pentagon and ellipse. B is better if the team has an hour for review.

**Timing matters.** Either A or B changes the split, so Stage 1 must rerun and every Stage 4 run must be retrained. The sweep was about half done (4 of 11 runs), so its results would be discarded either way. The decision is better made now than after the sweep finishes.

##### Decision and implementation

**Decision applied: all Quick, Draw! diamonds are dropped, documented as CRISP-DM iteration 1.** I stopped the sweep first, because its runs used the old data.

- A config rule, `exclude_source_labels: [[quickdraw, diamond]]`, is applied in Stage 1 before the split. The contact sheets are still generated first, from the unfiltered rows, so the evidence of what was dropped stays visible.
- I fixed two problems along the way. The generated LaTeX line had lost its escaping because a newline had landed inside the string, and the fail-closed tests had to set an empty rule list in their fixture, since the rule has its own tests.
- The recipe fingerprint now includes the train and validation manifests, so no run trained on the old split can be reused after the re-split. The tests pass (47).
- Stage 0 reran first, because shared code had changed, and then Stage 1 re-froze the data.

##### Results

- **Data:** the rule removed 500 drawings. The new split is 12,405 / 2,819 / 2,776, and all leakage checks pass. The step budget was re-frozen from 50 to 49 steps per epoch. Training resume now also fingerprints the data.
- **Evidence:** saved before the old runs were overwritten, as the committed `docs/crisp_dm/iteration_1_quickdraw_diamonds.json` and `.tex`. It is generated by `src/stage6_report/iteration_evidence.py` from validation only. The test set was never touched.
- **Phase 2 report** (pages 3-4, rendered and checked): the CRISP-DM figure has a dashed "iteration 1" arrow from Modeling back to Data Preparation. A new section in B explains the finding. Table 2 shows the per-run evidence, with every number generated. Figure 2 shows one page of the doodles. The limitations now say diamond is render-only.
- **Phase 1 report:** the gemstone wording and label table point to the Phase 2 exclusion.
- **Tracking:** `plan_issues.md` entry P-60 is added, and a new ticked entry is in `ignore/todo.md`. The gemstone review item is marked superseded, so that human task is gone. The Decision 1 text still needs a team PR.
- The dashes on page 3 (class count, image size and so on) are expected for now. Those macros are filled in by Stage 6, which runs after training.

##### Retraining

Stage 4 is retraining from scratch on the new split: the tuning grid first, then the 11-run sweep. That is roughly a day of CPU time, and the monitor reports each run. The monitor is re-armed, and the first results are expected in about 3 h.

The latest check is healthy, with no errors. The six tuning runs on the new split are at about epochs 10-13. Their best validation macro-F1 so far ranges from 70 to 85, and the two lr 0.003 runs lead at about 85.

##### Needs you (does not block training)
- **Gemstone review:** the contact sheets in `artifacts/stage1/gemstone_contact_sheet_*.png` feed `configs/gemstone_ids.csv`, followed by a rerun of Stage 1. (The diamond decision above supersedes this.)
- **Committing** the work, including `configs/splits/`.
- **Rubric and deadline, license, `CODEOWNERS` owners, a second-machine data hash, and the 60-drawing demo check.**
- **A team PR** for the logged plan deviations (P-45 to P-59), mainly the Decision 8 change to 4 blocks.

I will add every issue found so far as new entries, using the canonical audit format. Bugs go under `## 🐞 Bug fixes` and improvements under `## 🔧 Code improvements`, both above "Still open (needs you):". Fixed issues are ticked with their evidence. Open issues stay unticked, with a proposed fix and test. One constraint: open items that touch Stage 2-4 code cannot be changed while Stage 4 trains, because any code change there alters the recipe fingerprint. Their entries say so.

##### Why the diamond decision came first
Option A and option B both change the split, which would invalidate every Stage 4 run. The sweep was partly finished (4 of 11 runs), so deciding before it completed avoided spending more CPU time on data that would be thrown out. The recommendation (option A) was chosen because it is reproducible and needs no review time, while option B would have depended on about an hour of human review by two reviewers plus a tie-breaker.

##### What was checked after the change
- The contact sheets were generated from the unfiltered rows first, so the evidence of what was dropped remains visible.
- Leakage checks pass on the new split, and the recipe fingerprint now covers the train and validation manifests.
- The evidence file was generated from validation only. The test set was not touched.

##### Consequences and open items
- The Decision 1 text still needs a team PR, so the written plan and the code are not yet aligned.
- Diamond is now render-only, so the model never sees a sketched diamond. This is a stated limitation, not a fix.
- The gemstone review item is marked superseded, which removes that human task.
- Retraining from scratch takes roughly a day of CPU time, with the first results expected in about 3 hours at the time of this report.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
