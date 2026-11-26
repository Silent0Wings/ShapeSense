# 3_modeling - Iteration 2: tune augmentation and add arm A2

> **Edited for publication (2026-11-20):** one word for a shared commit-author trailer is written as "shared-author" throughout, because the repository's commit guard rejects the original word. Nothing else was changed.

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: F06, C04, C08, C10, C12, C15, C16, F14
- Source: **exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
-  [F06](../../3_modeling/claude_opus/17_F06_augmentation-and-generator-ranges-were-set-b.md), [C04](../../2_data_preparation/transformation/claude_opus/05_C04_other-augmentation-settings.md), [C08](../../2_data_preparation/transformation/claude_opus/07_C08_synthetic-generator-ranges.md), [C10](../../3_modeling/claude_opus/21_C10_training-arms.md), [C12](../../3_modeling/claude_opus/23_C12_hyperparameter-tuning.md), [F14](../../4_testing/claude_opus/30_F14_a2-vs-a0-failed-0-06-on-test-and-0-08-on-the.md)

## Prompt 1 (01:20)

> CREATE  A LONG HORIZON PROMPT FOR THIS =[
>
> <pasted_content id="8717">
> FIX THE ISSUES 
> ADD HYPER PARAMETER TUNINING FOR THE CONTROLS OF SYNTHETHIC AND AUGMENTATION 
> RETRAIN , CALCUALTE , EVAL ,...
> ======
> CREATE A2 =[REAL + SYNTHETHIC + AUGMENTED ]?
> </pasted_content id="8717">
>
> ]

## Response 1

I'll save it next to your other goal prompts. First, a quick check of two facts it depends on: how the current arms and primary comparison are wired, and whether unused data exists for a fresh, untouched test set, since the current test split has already been seen.

One catch before I wrap up: your running server still has the old backend, so the new pages would break until it restarts. I'm making them tolerate that.

Written for: a future Claude session running unattended.

The long-horizon prompt is ready, and the finding is now recorded in the CRISP-DM cycle. **Restart `python -m studio` to see the new log**, because your running server still has the old backend.

**To start the next round, once the Fable agent has finished** (both need the GPU), paste this:
```
Read .agents/goal_iteration2.md and carry out that goal.
```

**What the prompt does:**
1. Archives the iteration 1 results untouched and commits a pre-registered plan before any tuning.
2. Fixes the known issues, including anything the investigation finds.
3. Tunes the augmentation and generator controls on validation only, and gives every arm, A0 included, its own learning-rate and dropout tuning.
4. Adds arm A2, retrains all four arms with 5 seeds, and runs the unseen-source check for all of them.
5. Evaluates once, then updates the report and dashboard, with every commit through the guard.

**Two things to know:**
- **A2:** arm B is already real + augmented + synthetic, and every image in it is augmented. So I defined A2 as **clean real + augmented real + synthetic**, which keeps the cues that rotation removes. Tell me if you meant something else.
- **The test split has been seen.** Its results shaped this plan, so a second read of it is weaker evidence, and the prompt says so. It also tries to build a fresh test set from unused Quick, Draw! drawings. That can only cover about six classes, and I haven't confirmed enough unused drawings exist.

**CRISP-DM record:** `docs/crisp_dm/iteration_log.json` now holds Iteration 1 (closed) and Iteration 2 (in progress), with findings under each step. The home page shows the log and a new dashed Evaluation → Data Preparation arrow, and each step's page shows its own findings. The prompt requires adding to this log at every phase. I left the report PDF unchanged for now, because editing it would re-run Stage 6.

**Latest from the agent (validation only, three seeds, not on test):** turning rotation off changed the picture.

| Model | Mean validation macro-F1 |
|---|---|
| A1 with rotation off | **93.15** |
| A0, no augmentation | 91.69 |
| A1 as trained, ±180° rotation | 90.03 |

Diamond F1 rose from 83.2 to 96.2. So your instinct looks right: augmentation does help here, and the ±180° rotation was what undid it. The agent is still running its remaining tests, and I'll report the full findings when it's done.

## Prompt 2 (01:36)

> <command-name>/goal</command-name>
>             <command-message>goal</command-message>
>             <command-args>Read .agents/goal_iteration2.md and carry out that goal.</command-args>

## Response 2

Goal acknowledged: I'm carrying out `.agents/goal_iteration2.md` from here. I'll start with what can't disturb the agent's running queue: checking its state, preserving iteration 1, and inspecting whether a fresh holdout is possible.

Committed. While the agent's last three runs finish, I'll write the search tool as a new file, which doesn't affect its runs. I'll apply the edits to existing pipeline code as soon as the queue ends.

I have what I need. I'm writing the whole set of code changes as a single patch script, ready to apply the moment the agent's last two runs finish.

The code patch is ready and held back until the agent's last two runs finish. Then I'll apply it, run the tests, and start tuning.

Still waiting on the agent's final two runs.

The training queue has finished, so I'm applying the pipeline changes and running the full test suite.

My peak-based fix barely helped (16.3 versus 17.2 pieces), so it isn't a real fix. I'll target 1-pixel strokes directly by giving them a lower cut-off, and measure again.

That fixed it: 1-pixel sketches now stay in one piece every time (1.0 pieces on average, down from 16.3). Now the tests and the deliberate-break checks for every change, then the commit.

All 12 deliberate breaks are caught and 409 tests pass. I'm committing this, then running the validation experiment the goal requires on the zero-padding polarity question before starting the search.

While that runs, I'm recording the investigation's findings in the CRISP-DM log, as the goal requires, and finishing the last Phase 2 item (ablation rows in the results table).

The fixes are committed, and the polarity experiment is running in the background. When it finishes I'll decide on polarity and start the validation search.

The rerun is in progress. When it reports, I'll settle the polarity question and start the search.

The search is running in the background and will notify me when it finishes. Nothing else can proceed until it does, because the final retrain depends on its winners. If it crashes, that also wakes me.

The search is still running. By the machine's own clock it has only been going about 10 seconds, so there are no trial results yet. I'll keep waiting.

The search has finished, so I'm checking its winners and the ablation table.

My own command hung on a stray `cat`. I'm stopping it and running the steps properly.

The report changes are committed, and the Stage 0 to 4 run is still going in the background. I'll pick up as soon as it finishes.

Stage 5 is running: the power check first, then one read per model on the test split and the fresh holdout. I'll verify the results as soon as it exits.

## Prompt 3 (09:43)

> do you have any good new for me ?

## Response 3

Yes, mostly, though the final check isn't finished: the clean-clone rehearsal is still running. Its training folder is filling up, but its log is buffered, so I can't say which stage it's on.

**Good news**
- **The mystery is solved.** Augmentation lost in iteration 1 for real reasons, not data corruption or a bad loss function. Rotating up to ±180° removed an orientation clue the classes rely on, and the augmentation code made shapes too small and broke thin strokes.
- **The fix worked.** A1's deficit against the no-augmentation model A0 shrank from 3.0 points to 0.12. Every arm also improved on test, for example A1 went from 90.86 to 95.19.
- **Augmented models handle unseen sources better.** On a source left out of training, they were about 6 to 8 points more accurate than A0 (A2 73.8, A0 66.6). This is only a descriptive check on two classes from one source.
- **The real+augmented+synthetic model now exists.** A2 scored best on validation (95.13), and it's the model in the exported bundle.
- **The dashboard is updated.** All four arms answer live when you draw, there's a fresh holdout card, and iteration 1 has its own frozen page.
- **The checks are clean.** All 429 tests pass and the sealed test split had no extra reads. All iteration 1 archive hashes still match, and everything is committed locally with nothing pushed.

**Not so good**
- **A2 still failed its pre-registered test.** It needed a gain of at least 1 point over A0 and got +0.06 on the test split (CI [-0.69, 0.83]) and +0.08 on the fresh holdout (CI [-0.41, 0.57]).
- **Augmentation and synthetic data no longer hurt, but they didn't measurably help either.** That applies to images from sources the models trained on. Your intuition holds best on unseen sources, which is where a next iteration could focus.

To see iteration 2, restart the studio server on port 8765, because it's still running the old backend. The handoff is in [ignore/handoff_iteration2.md](ignore/handoff_iteration2.md), and I'll add the rehearsal result there when it finishes.

The rehearsal is progressing. Stages 0 to 4 have all passed in the clean clone, with all 32 trainings finished at 09:42, one minute before this check. It's now on Stage 5, so I'll keep waiting and compare its results with the main run when it exits.

That was only my progress check finishing. The rehearsal itself is still on Stage 5, so I'm still waiting for it to exit.

The rehearsal exited cleanly. I'll compare it with the main run using only the recorded Stage 4 to 6 status and metrics, so the check doesn't open any test prediction files.

Iteration 2 is finished and committed locally on the `iteration-2` branch, with nothing pushed. A2 failed its pre-registered test against A0, on both the reused test split and the fresh holdout.

| A2 vs A0 (macro-F1 points) | Gain | 95% CI | Verdict |
|---|---|---|---|
| Reused test split | +0.06 | [-0.69, 0.83] | Fail |
| Fresh holdout, 4,500 images | +0.08 | [-0.41, 0.57] | Fail |

- **Why augmentation lost in iteration 1:** it wasn't data corruption or a bad loss function. Rotating up to ±180° removed an orientation clue the classes rely on. The augmentation code also made shapes about 6 px too small and broke thin strokes.
- **What the fix changed:** A1's deficit against A0 shrank from 3.0 points to 0.12. Augmentation no longer hurts, but neither it nor synthetic data measurably helps on images from the sources the models trained on.
- **Where it may help:** on a source left out of training, the augmented arms were about 6 to 8 points more accurate than A0. That check is descriptive only and covers two classes from one source.

**Verification**
- All 429 tests pass, the guards pass, and a second run reports every stage cached.
- The clean-clone rehearsal passed all seven stages and reproduced the verdicts, CIs, tables and all 32 validation scores exactly. It used the existing Python environment, so installing from `requirements.txt` was not repeated.
- Iteration 1 is preserved, with all 179 archive hashes matching and its own page in the dashboard.
- The sealed test split had no extra reads, and the access log is still 65 lines.
- All 44 commits on the branch went through the guard and carry no shared-author or AI credit, as your project rule requires. That rule overrode a system reminder asking for a shared-author line.

**Left for you**
- Restart the studio server on port 8765 to see iteration 2, because it's still running the old backend.
- Decide whether orientation is part of each class's definition, since that sets how far rotation should go.
- `artifacts/stage4_cpu_recipe_2880473b/` is untracked and I left it alone.
- The plan-text PRs, rubric and deadline, license, `CODEOWNERS`, student IDs, the second-machine hash, the 60-drawing check and the push decision are still yours. They're listed in the handoff, along with every deviation.

The handoff is [ignore/handoff_iteration2.md](ignore/handoff_iteration2.md).

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The plan was pre-registered and committed before any tuning. Tuning used validation only, and the result was checked on the reused test split and on a fresh holdout that had informed no choice (C16).

## Our decision

We asked for hyperparameter tuning of the augmentation and synthetic controls and for a new arm A2 (real + augmented + synthetic). Per-arm search replaced settings tuned on A1 alone (C12). A2 batches hold 105 clean, 100 augmented and 51 synthetic images (C10). The primary comparison became A2 vs A0 (C15).

## Measured effect

A2 vs A0: +0.06 macro F1 on the reused test split and +0.08 on the fresh holdout. Both CIs include 0, so the test failed and the failure was recorded (F14).

---

## End-to-End Autonomous Iteration 2 Execution & Clean-Clone Rehearsal (`F06`, `C04`, `C08`, `C10`, `C12`, `C15`, `C16`, `F14`)

### Metadata & Lineage

* **Entries:** `F06`, `C04`, `C08`, `C10`, `C12`, `C15`, `C16`, `F14`
* **Date:** `2026-11-09` (01:20–09:43 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)
* **Verification:** `429` unit/contract tests passing, `12` deliberate-break mutation checks caught, `179` Iteration 1 archive hashes verified, `65`-line test access log audited, full **7-stage clean-clone rehearsal** reproducing all `32` validation scores and confidence intervals identically.

### Root-Cause Diagnosis of Iteration 1 Augmentation Failure (`F06`)

Controlled ablation isolated three compounding defects in Iteration 1's hand-configured pipeline:

1. **Destructive $\pm 180^\circ$ Rotation:** Eliminated canonical orientation features required for class separation (e.g., `diamond` F1 jumped from `83.2` to `96.2` upon disabling rotation; overall `A1` 3-seed validation rose from `90.03` to `93.15` vs. `A0`'s `91.69`).
2. **Scale Contraction (`~6 px` undersizing):** Augmentation rescaling shrank rendered shapes relative to standardized validation/test glyphs.
3. **1-Pixel Stroke Fragmentation:** Thresholding shattered thin 1-px outlines into **`17.2` disconnected components** (`16.3` after naive peak-based adjustment); lowering the cutoff specifically for 1-px strokes restored **`1.0` connected component** per sketch.

### Iteration 2 Experimental Execution & Empirical Verdict (`C15`, `C16`, `F14`)

* **Pre-Registered Plan (`.agents/goal_iteration2.md`):** Archived Iteration 1 immutably, tuned augmentation/generator parameters and per-arm `(lr, dropout)` strictly on validation, introduced tri-modal arm `A2` (`105` clean / `100` augmented / `51` synthetic), and elevated **`A2 vs. A0`** (`+1.0` macro-F1 threshold) to the primary hypothesis test (`C15`) evaluated on both the reused test split and a newly constructed **4,500-image `fresh_holdout`** (`C16`).
* **Outcome (`F14`):** Fixing the augmentation bugs eliminated `A1`'s `-3.0` point deficit (shrinking it to `-0.12` and lifting `A1` test macro-F1 from `90.86` to `95.19`). However, on clean in-distribution data, `A2` failed to clear the `+1.0` macro-F1 superiority bar (`+0.06`, 95% CI `[-0.69, 0.83]` on reused test; `+0.08`, 95% CI `[-0.41, 0.57]` on `fresh_holdout`), while demonstrating a **`+6` to `+8` point descriptive advantage** (`A2: 73.8` vs. `A0: 66.6`) on leave-one-source-out unseen hand-drawn data—directly motivating Iteration 3's pivot toward out-of-distribution and damaged-image robustness.

