# 3_modeling - Iteration 3 search results and final retraining

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 to 2026-11-10 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C29, C38, C39, F22
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [C38](../../3_modeling/claude_opus/28_C38_search-winners.md)

## Prompt 1 (17:31)

> ok keep working  , and good luck , you can do it !!

## Response 1

Thanks, I'll keep going. The experiments are running with the 5-minute watcher on, and once they finish I'll write up the results and move on to the tuning search. If anything goes wrong, I'll deal with it and tell you.

Not a hang: both workers are fully busy and the GPU is active. They're on the 60-epoch training-length trials, which take about twice as long, so gaps over 5 minutes are expected here. The count is still 78 of 108, and the newest finished at 17:26 with no errors.

80 of 108 trials are done at 17:38, with 2 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 17:43 with 80 of 108 trials done.

81 of 108 trials are done at 17:48, with 1 finished in the last 5 minutes.

82 of 108 trials are done at 17:53, with 1 finished in the last 5 minutes.

Not a hang: another trial finished while I was checking, so the count is now 83 of 108. Both workers are busy and the log has no errors. These 60-epoch trials are just slow.

84 of 108 trials are done at 18:03, with 2 finished in the last 5 minutes.

The experiments are progressing: 84 of 108 trials were done at 18:03, with 2 finished in the previous 5 minutes and no errors at the last check. I'm still waiting, with the 5-minute watcher on.

86 of 108 trials are done at 18:08, with 2 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 18:13 with 87 of 108 trials done.

89 of 108 trials are done at 18:18, with 2 finished in the last 5 minutes.

90 of 108 trials are done at 18:23, with 1 finished in the last 5 minutes.

92 of 108 trials are done at 18:28, with 2 finished in the last 5 minutes.

93 of 108 trials are done at 18:33, with 1 finished in the last 5 minutes.

95 of 108 trials are done at 18:38, with 2 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 18:43 with 98 of 108 trials done.

101 of 108 trials are done at 18:48, with 3 finished in the last 5 minutes.

All 108 trials have finished. The same job now scores them on the damaged validation sets and writes the result files. I'll confirm it moved on to scoring and watch that step too, since a hang there wouldn't raise any alert.

All 108 trials are done with no errors, and the job has moved on to scoring: its main process is busy and the GPU is active. No result files exist yet. I'm watching that step for errors or a 15-minute gap.

The scoring step has written its first result file, for the scarcity experiment, at 18:57.

The equal-real results are written too, so 2 of the 7 result files are done.

The training-length results are written, so 3 of the 7 result files are done.

The BatchNorm results are written, so 4 of the 7 result files are done.

The re-framing results are written, so 5 of the 7 result files are done.

The experiments job finished cleanly. Now I'll read all the results.

The first scoring pass has reproduced nothing yet, because the re-score is still running. While it runs I'll add the histogram charts to the experiments page.

The histogram charts are on the page. I'm waiting for the re-score to finish, then I'll check it matches the first pass before recording any findings.

Phase 4 is committed and the GPU is free. Before starting about 200 trials, I'll confirm the adopted budget actually reaches them, then launch the search with its watcher in the same step.

The budget reaches every phase, and the CV step correctly stays at its pre-registered 15 epochs. Launching the search.

**Phase 4 is finished and Phase 5, the tuning search, is now running.** All 108 experiments completed, and scoring them twice gave identical numbers. These are validation results on three seeds, so they answer your questions but aren't the final verdict, which comes from the sealed test in Phase 7.

| Your question | Answer on validation |
|---|---|
| Is A0 weakest on damaged images? | Yes. A0 66.3, A1 77.7, B 77.1, A2 80.3, P 75.6 |
| Does A1 improve robustness? | Yes, by 11.4 points over A0 |
| Is A2 best overall? | Yes, on both clean (95.2) and damaged images |
| Does B help most when real data is scarce? | Not beyond augmentation. At 10% of real images, A1 and B both scored 91.6, and A0 scored 81.3 |
| Does synthetic pretraining recover the domain gap? | Partly. P is best at 10% and 25% of real images, but with all of them it only matches B and stays below A2 |
| Do equal real images per step help? | No. B lost 2.0 points and A2 lost 0.5 |
| Does BatchNorm recalibration help? | No. B lost 0.7 points and A2 lost 0.8 |
| Does re-framing alone cause errors? | Not much, 0.3 to 1.1 points for the arms trained on it, and it keeps shape proportions |

The class and source mix of validation and test is also nearly identical, so that doesn't explain why those two sets disagreed earlier.

**One decision came out of this:** the pre-registered rule moves every arm to 60 epochs with no early stopping. A1 cleared the 0.5-point bar by only 0.01, but the rule was fixed in advance, so it applies.

**What changed:**
- All of this is recorded under its CRISP-DM steps and shown on the Iteration 3 experiments page, including the histograms.
- The last two review points are closed by these measurements.
- It's all committed locally.

**Next:** the search has 200 trials and should take roughly 12 to 14 hours, longer than I first estimated because of the doubled training length. The 5-minute watcher is on.

Your `studio/feedback/` folder has appeared as untracked, presumably from drawings you saved. I've left it alone and out of the commits.

The search watcher started at 19:11 with 0 of 200 trials done.

The search is healthy: both workers are busy on their first trials and the GPU is active. A 60-epoch trial takes longer than 5 minutes, so these early "no new trial" flags are expected.

The first trial finished at 19:21, about 10 minutes after starting, so this flag was also not a hang. Two trials run at a time, which works out to about 12 trials an hour. The search should finish around 7 to 8 a.m. tomorrow.

With trials taking 10 minutes, every other 5-minute check will say "no new trial" even when things are fine. I'll only act on a gap of about 15 minutes or more.

2 of 200 search trials are done at 19:26.

The count is still 2 of 200 at 19:31, which is expected with 10-minute trials.

## Prompt 2 (02:47)

> check on the progress

## Response 2

**82 of 191 trials are done as of 02:47, all full runs, with no errors.** All 12 pretraining trials have finished, and the search has moved on to learning rate and dropout.

| Phase | Done |
|---|---|
| Augmentation, generators, batch mix, pretraining | 80 of 80 |
| Learning rate and dropout | 2 of 26 |
| Cross-validation | 0 of 75 |
| Confirmation | 0 of 10 |

It's running faster than before: the latest epochs took a median of 1.4 to 2.0 seconds, down from 2.3 or more, and the GPU is at 97%. Closing your other programs probably helped, though part of the gain is that A0 trials need no image preparation.

The new estimate is finishing **around 4:30 to 5:30 a.m.**

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 02:47 with 82 of 191 trials done.

85 of 191 trials are done at 02:52, with 3 finished in the last 5 minutes.

89 of 191 trials are done at 02:57, with 4 finished in the last 5 minutes.

92 of 191 trials are done at 03:02, with 3 finished in the last 5 minutes.

95 of 191 trials are done at 03:07, with 3 finished in the last 5 minutes.

98 of 191 trials are done at 03:12, with 3 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 03:17 with 101 of 191 trials done.

105 of 191 trials are done at 03:22, with 4 finished in the last 5 minutes.

115 of 191 trials are done at 03:27, with 10 finished in the last 5 minutes. The jump is the search reaching the short 15-epoch cross-validation trials.

122 of 191 trials are done at 03:32, with 7 finished in the last 5 minutes.

135 of 191 trials are done at 03:37, with 13 finished in the last 5 minutes.

141 of 191 trials are done at 03:42, with 6 finished in the last 5 minutes.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 03:47 with 153 of 191 trials done.

160 of 191 trials are done at 03:52, with 7 finished in the last 5 minutes.

172 of 191 trials are done at 03:57, with 12 finished in the last 5 minutes.

179 of 191 trials are done at 04:02, with 7 finished in the last 5 minutes.

189 of 191 trials are done at 04:07, so the search is almost finished.

The search finished cleanly. Now Phase 5's close-out: reading the winners, then freezing them into the config.

**Phase 5 is complete and Phase 6, the final retraining, is running.** The search finished at about 04:10, far ahead of the original 13 to 17 hour estimate: 191 trainings, no errors after the one crash. The winners are frozen in the config and committed locally.

| Arm | Mean validation macro-F1 (3 seeds) |
|---|---|
| Real only (A0) | 94.2 |
| Real + augmented (A1) | 95.2 |
| Real + synthetic (B) | 95.1 |
| Full mix (A2) | 95.8 |
| Synthetic pretraining (P) | 95.2 |

These are validation scores, and validation guided the tuning, so they aren't the verdict.

Phase 6 is first re-running stages 0 to 3, then training 40 runs, with the watcher on. It stops before Stage 5, so no sealed data is read. The access log is at 65 lines, and I'll confirm it's still 65 afterward.

The retraining watcher started at 04:11 with 0 of 40 runs done.

That's the search watcher closing out. The search finished at 191 trials, and the retraining is underway.

At 04:16 there are 0 of 40 runs, as expected: stages 0 to 3 run before training starts, and the guard tests have just passed.

4 of 40 runs are done at 04:21, with all 4 finished in the last 5 minutes.

6 of 40 runs are done at 04:26, with 2 finished in the last 5 minutes.

The retraining is progressing: 6 of 40 runs were done at 04:26, with no alerts from the watcher. I'll keep waiting.

9 of 40 runs are done at 04:31, with 3 finished in the last 5 minutes.

12 of 40 runs are done at 04:36, with 3 finished in the last 5 minutes.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

All 108 experiments were scored twice with identical numbers. The search winners were confirmed on three seeds.

## Our decision

Winners were frozen in configs/pipeline.yaml (C38). The budget moved to 60 epochs with no early stopping, under the pre-registered rule (C29).

## Measured effect

Validation gains for the longer budget: A0 +1.99, A1 +0.51, A2 +0.71 (C29). The search ran 175 trainings in about 3 h 50 min (C39).

---

## Phase 4 Ablation Matrix, Phase 5 Tuning & Phase 6 Retrain (`C29`, `C38`, `C39`, `F22`)

### Metadata & Lineage

* **Entries:** `C29` (*60-epoch budget with early stopping disabled*), `C38` (*Freezing Iteration 3 search winners*), `C39` (*Search throughput*), `F22` (*Crash recovery*)
* **Date:** `2026-11-09` to `2026-11-10` (17:31–04:36 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)

### Phase 4 Diagnostic Ablation Findings (`108` Trials, Double-Scored Identically)

Prior to launching the 200-trial search, 108 controlled 3-seed validation experiments resolved eight open mechanistic hypotheses:

| Diagnostic Question | Empirical Validation Result (`3 seeds`) | Architectural / Protocol Decision |
| --- | --- | --- |
| **Damaged-image robustness across arms** | `A2: 80.3` > `A1: 77.7` > `B: 77.1` > `P: 75.6` > `A0: 66.3` (`+11.4` pts `A1` vs `A0`, `+14.0` pts `A2` vs `A0`) | Confirmed `A2` superiority on both clean (`95.2`) and damaged distributions. |
| **Low-data regime (`10%` & `25%` real data)** | At `10%` real: `A1 = 91.6`, `B = 91.6`, `A0 = 81.3`; `P` led at `10%` and `25%` but trailed `A2` at `100%` | Synthetic pretraining (`P`) aids extreme data scarcity; tri-modal mixing (`A2`) dominates at full scale. |
| **Equal-real step compensation (`B_equalreal`)** | `B` dropped `-2.0` pts; `A2` dropped `-0.5` pts | Rejected extra real draws per step; retained strict equal-compute substitution. |
| **Post-hoc BatchNorm recalibration** | `B` dropped `-0.7` pts; `A2` dropped `-0.8` pts | Rejected BN statistics recalibration. |
| **60-epoch horizon without early stopping (`C29`)** | Gains over 30-epoch early-stopped baseline: `A0 +1.99`, `A1 +0.51`, `A2 +0.71` (clearing the pre-registered `+0.50` bar by `0.01` on `A1`) | Locked `max_epochs: 60` and `early_stopping_patience: 999` globally across all arms. |

### Phase 5 Search Completion & Phase 6 Final Retrain Launch

* Following recovery from the trial-66 crash, the search accelerated to **`1.4–2.0 s/epoch` median** (`97%` GPU utilization) and finished all **191 unique trainings** at `04:10` (`~3 h 50 m` active compute, beating the `12–14 h` conservative estimate by `>3×`).
* 3-seed validation winners (`A0: 94.2`, `A1: 95.2`, `B: 95.1`, `A2: 95.8`, `P: 95.2`) were frozen into `configs/pipeline.yaml` (`C38`), triggering the **40-run Phase 6 final retrain** (`5 arms × 5 main seeds + 15 LOSO holdout runs`) while keeping `artifacts/test_access.log` strictly frozen at `65` lines.

