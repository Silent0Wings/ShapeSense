# 2_data_preparation/cleaning - Quick, Draw! diamond review

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08, 07:09 to 07:28
- Worksheet entries: F01, C01
- Source: **real exchange**, from the saved Claude Code session `c781aed8-5873-4a51-9c9b-cf98b371b0e2.jsonl` (main transcript, entries 3157 to 3452). The user prompt, both multiple-choice questions with their answers, every assistant reply in the thread, and the measurement output are copied in full. Hyphens replace dashes, and local paths are shortened to repo-relative ones. Tool calls (code edits, test runs, report builds) are not reproduced. They are listed in the transcript.

## Prompt

> ISSUES GEMSTONES DONT LOOK LIKE ASTABLE GEOMETRIC SHAOPE BUT MORE LIKE A DOODLES , I DONT THINK IT IS WISE TO KEEP IT =[artifacts/stage1/gemstone_contact_sheet_3.png] OPINON ? @artifacts/stage1/gemstone_contact_sheet_0.png @artifacts/stage1/gemstone_contact_sheet_1.png @artifacts/stage1/gemstone_contact_sheet_2.png @artifacts/stage1/gemstone_contact_sheet_3.png @artifacts/stage1/gemstone_contact_sheet_4.png

## Response

I agree with you. Most of these aren't diamonds in the taxonomy's sense. The definition is "rhombus *without* right angles": 4 equal sides, 4 vertices. On sheets 0 and 3, I'd estimate only about 20-30% are clear rhombi. The rest are:
- **gemstones:** a crown on top with facet lines, so 5-6 outer vertices (Decision 1's target)
- **cones / ice-cream shapes, shields, triangles**
- **scribbles, single lines, half-drawn outlines**

So this is label noise, and the harmful kind: many of these drawings look like pentagons, hexagons or triangles while labelled "diamond". That teaches the model the wrong boundaries and can hurt those classes too, not just diamond.

There are three options. The trade-off is clean labels against sketch coverage for the diamond class:

| Option | Pros | Cons |
|---|---|---|
| **A. Drop all Quick, Draw! diamonds** (a rule by source × label) | Simplest, fully reproducible, no review list, no judgement per image | Diamond becomes **render-only** (reevald rhombi). The model never sees a sketched diamond, which is a weakness on sketch inputs and in the demo, and it's a new single-source class (like pentagon/ellipse) |
| **B. Keep only clear rhombi** (the Decision 1 review, broadened from "gemstones" to "anything not a rhombus") | Clean labels and keeps some sketch diamonds (maybe 100-150) | About an hour of human review by 2 reviewers plus a tie-breaker. I must not pick the images myself |
| **C. Keep as is** | Nothing to do | Known label noise in the training data and the test set, and the report must defend it |

**My recommendation is A now.** It's defensible, reproducible and needs no review time. I'd record it as a Decision 1 amendment and add "diamond is render-only" to the limitations, next to pentagon and ellipse. B is better if the team has an hour for review.

**Timing matters.** Either A or B changes the split, so Stage 1 reruns and every Stage 4 run must be retrained. The current sweep is about half done (4 of 11 runs), so its results would be discarded either way. If you're going to change it, it's better to decide now and stop the sweep than to finish it first.

### Question 1 (multiple choice, as asked in Claude Code)

> Quick, Draw! 'diamond' drawings (500 images) are mostly gemstones/doodles, not rhombi. Changing this re-splits the data and restarts all CNN training (the current sweep, ~half done, would be discarded). What should I do?
>
> A: Drop all (Recommended). Exclude every Quick, Draw! diamond by rule (source × label). Reproducible, no review. Diamond becomes render-only; documented as a Decision 1 amendment + limitation. I stop the sweep now, rerun Stage 1, retrain everything.
>
> B: Human review. Your team marks the non-rhombus drawings in configs/gemstone_ids.csv (md5 list) from the contact sheets; I keep training paused/stopped until the list exists, then rerun Stage 1 and retrain.
>
> C: Keep as is. Leave the data unchanged; the current sweep continues; the report lists the label noise as a limitation.

**User's answer:** "IT DEPENDS , WHAT IS THE PERORMANCE OF THIS shape , can the models learn it ?"

### Measurement run by Opus (validation only, test split untouched; no assistant text was saved before this tool call)

```
A0_0               macroF1=87.6 diamondF1=80.4 | recall kaggle_reevald=100% (n=150) | recall quickdraw=93% (n=76)
A0_2               macroF1=85.1 diamondF1=90.1 | recall kaggle_reevald=97% (n=150) | recall quickdraw=86% (n=76)
A1_0               macroF1=89.2 diamondF1=82.4 | recall kaggle_reevald=95% (n=150) | recall quickdraw=59% (n=76)
   per-class F1: {'circle': 93.1, 'ellipse': 77.2, 'triangle': 91.1, 'square': 91.4, 'rectangle': 81.2, 'pentagon': 99.4, 'hexagon': 89.2, 'octagon': 87.8, 'star': 98.9, 'diamond': 82.4}
   QD diamonds predicted as: [('diamond', 45), ('triangle', 16), ('ellipse', 8), ('square', 3), ('rectangle', 2), ('pentagon', 1)]
   non-diamonds predicted diamond (QD): [('hexagon', 4), ('octagon', 4), ('triangle', 4), ('star', 2)]
   diamond precision overall: 82.0
A1_2               macroF1=87.7 diamondF1=72.0 | recall kaggle_reevald=82% (n=150) | recall quickdraw=51% (n=76)
tuning_0.003_0.4   macroF1=89.2 diamondF1=82.4 | recall kaggle_reevald=95% (n=150) | recall quickdraw=59% (n=76)
```

### Question 2 (multiple choice, as asked in Claude Code)

> Given the numbers (QD 'diamonds' are learned as gem doodles; augmented models label many as triangles; this biases B vs A1), how should the Quick, Draw! diamonds be handled? Any change restarts Stage 1 + all training.
>
> A: Drop all (Recommended). Exclude all 500 Quick, Draw! diamonds by rule; diamond becomes render-only (documented limitation + Decision 1 amendment). I stop the sweep now and retrain.
>
> B: Human review. Team keeps only clear rhombi by filling configs/gemstone_ids.csv from the contact sheets (~1 h); I stop the sweep and wait for the list.
>
> C: Keep as is. No change; sweep continues; the report documents the label noise and its bias against B.

**User's answer:** "drop them but , we mention this as 1 part of the cycle we follow since this repo is followwing a type of cyclic pipeline read this =[phase1_report.pdf]+[phase1_report.tex] document the fingind "

### Reply after the user's answer

Decision recorded: **drop all Quick, Draw! diamonds, and document it as a CRISP-DM iteration.** First I'm stopping the sweep, because its runs used the old data and would be discarded anyway.

(Between this reply and the final summary, Opus edited the Stage 1 rule, the tests, the recipe fingerprint and both reports, and re-froze the split. Those steps are tool calls and are not reproduced here.)

### Final response (07:28)

The documentation is done, and the training retrain is running. Summary:

**Decision applied: all Quick, Draw! diamonds are dropped, documented as CRISP-DM iteration 1.**
- **Data:**
  - A config rule, `exclude_source_labels: [[quickdraw, diamond]]`, applied in Stage 1 *before* the split.
  - It removed 500 drawings. The new split is **12,405 / 2,819 / 2,776**, and all leakage checks pass.
  - The step budget was re-frozen (50 -> 49 per epoch). Training resume now also fingerprints the data, so no run from the old split can be reused.
- **Evidence:** saved before the old runs were overwritten, as committed `docs/crisp_dm/iteration_1_quickdraw_diamonds.json/.tex`. It's generated by `src/stage6_report/iteration_evidence.py` from validation only (the test set was never touched).
- **Phase 2 report** (page 3-4, rendered and checked):
  - The CRISP-DM figure now has a dashed **"iteration 1"** arrow from Modeling back to Data Preparation.
  - A new section in B, "CRISP-DM iteration 1", explains the finding. Table 2 shows the per-run evidence, with every number generated, and Figure 2 shows one page of the doodles.
  - The limitations now say **diamond is render-only**, like pentagon and ellipse.
- **Phase 1 report:** the gemstone wording and label table point to the Phase 2 exclusion.
- **Tracking:** `plan_issues.md` P-60, a new ticked entry in `ignore/todo.md`, and the gemstone review item is marked superseded, so that human task is gone. The Decision 1 text still needs a team PR.

The dashes on page 3 (class count, image size and so on) are expected for now. Those macros are filled by Stage 6, which runs after training.

Stage 4 is retraining from scratch on the new split: the tuning grid, then the 11-run sweep. That's roughly a day of CPU time, and the monitor will report each run.

## Validation

The per-run validation numbers above (Quick, Draw! diamond recall 59% for A1_0, with 16 of 76 predicted as triangle). The test split was not read. Evidence file: `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`.

## Our decision

Option A, with the user's addition: drop all 500 Quick, Draw! diamonds by rule before the split, and record the finding as CRISP-DM iteration 1 instead of a silent fix.

## Measured effect

Macro F1 before the exclusion (validation, from the runs above): A1_0 89.2, A0_0 87.6, A0_2 85.1, A1_2 87.7. Diamond F1 on validation: A1_0 82.4, A1_2 72.0. The chat does not contain post-exclusion numbers. The split was re-frozen at 12,405 / 2,819 / 2,776, and every model was retrained. Diamond became a render-only class, recorded as a limitation.
