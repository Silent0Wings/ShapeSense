# 4_testing - Iteration 3 verdict on the sealed holdout

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C23, C28
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt (04:36)

> status repport

## Response

**Iteration 3 is about 65% done by phases: Phases 0 to 5 are complete and Phase 6, the final retraining, is running.** It's at 12 of 40 runs as of 04:36, with no errors, and the newest run finished at 04:36.

| Item | State |
|---|---|
| Tuning search | Done: 191 trainings, winners frozen in the config |
| Retraining | 12 of 40 runs, about 2 to 3 minutes each, expected to finish around 5:45 to 6 a.m. |
| Sealed data | Still unread: the access log is at 65 lines, unchanged |
| The next five to-dos | Four are done, and "All models vote" waits for the final models |
| Git | Latest commit `5b44d60`, nothing pushed |

**Validation scores for the winners (not a verdict):** Real only 94.2, Real + augmented 95.2, Real + synthetic 95.1, Full mix 95.8, Synthetic pretraining 95.2.

**Next:** Phase 7, the single evaluation on sealed data, gives the pre-registered verdict. After that come the report, dashboard and export, then the voting option and close-out. Those should take several hours in total.

The session needs to stay open and the laptop awake for this to continue.

The 5-minute retraining watcher has been restarted for the next 30 minutes.

The new watcher started at 04:41 with 15 of 40 runs done.

18 of 40 runs are done at 04:46, with 3 finished in the last 5 minutes.

21 of 40 runs are done at 04:51, with 3 finished in the last 5 minutes.

24 of 40 runs are done at 04:56, with 3 finished in the last 5 minutes.

26 of 40 runs are done at 05:01, with 2 finished in the last 5 minutes.

29 of 40 runs are done at 05:06, with 3 finished in the last 5 minutes.

The 5-minute retraining watcher has been restarted for the next 30 minutes.

The new watcher started at 05:11 with 32 of 40 runs done.

35 of 40 runs are done at 05:16, with 3 finished in the last 5 minutes.

37 of 40 runs are done at 05:21, with 2 finished in the last 5 minutes.

Phase 6 finished cleanly. Before any sealed read, the goal requires checking that Stage 4 passed, no sealed data was read, every run used the same GPU, and the validation table is saved first.

One Stage 5 test fails. I won't touch sealed data until I understand it.

**Phase 6 is complete and Phase 7, the one evaluation on sealed data, has started.** Retraining finished at about 05:25: all 40 runs passed, on the RTX 3080, with no sealed reads.

Final validation macro-F1, averaged over 5 seeds, saved before the sealed read:

| Arm | Validation macro-F1 |
|---|---|
| Real only (A0) | 94.33 |
| Real + augmented (A1) | 95.27 |
| Real + synthetic (B) | 95.12 |
| Full mix (A2) | 95.82 |
| Synthetic pretraining (P) | 95.22 |

The verdict comes from this evaluation. It needs Full mix to beat Real only by at least 1.0 macro-F1 point on damaged images from the sealed holdout, with a confidence interval that excludes 0 and no harmed class. The validation scores above don't decide it. A watcher is tracking the sealed-read count and errors, and if this stage fails it can't simply be relaunched without checking the access log first.

The sealed evaluation watcher started at 05:27 with the access log at 65 lines.

At 05:32 the sealed read count has gone from 65 to 146 lines, which is the evaluation reading the sealed sets. I'll compare the final count with the expected one when it finishes.

At 05:37 the access log is at 157 lines, 11 more in the last 5 minutes, and the evaluation is still writing results.

The access log is holding at 157 lines at 05:42, so the reads may be done. Files are still being written.

The access log is still at 157 lines at 05:47, and the evaluation is still writing results.

No change in the read count at 05:52. The evaluation is still producing results.

The watcher has been restarted for the next 30 minutes.

The new watcher started at 05:57 with the access log at 157 lines.

No change in the read count at 06:02, and the evaluation is still producing results.

No change in the read count at 06:07, and the evaluation is still producing results.

No change in the read count at 06:12. It's still writing about 72 prediction files every 5 minutes, which fits scoring 25 models across 23 damage levels on the CPU. That pace should finish in about 10 minutes.

Stage 5 finished. I'll read the verdict from its saved results and confirm the read accounting. I'm reading only the status and tables, never the sealed predictions.

The number check caught one hand-typed figure of mine in Section L, which is exactly its job. I'll remove it, then do the dashboard work for the final five arms and the sealed results.

All 36 Stage 6 tests pass. Now the dashboard work: arm P everywhere, sealed robustness results shown beside the validation ones, and a Stage 5 page that reports the real pre-registered test.

All five earlier stages show unchanged inputs, so Stage 5 will be skipped and won't read anything. Running Stage 6 and the model re-export now, with a watcher.

**The iteration 3 result is a Pass, on the pre-registered test.** Full mix (A2) beat Real only (A0) by **+9.20 macro-F1 points** on damaged images, with a 95% interval of [8.89, 9.53] and no harmed class. This was measured on 4,500 images that had never been read, across 23 damage levels.

| Arm | Damaged images | Clean images |
|---|---|---|
| Real only (A0) | 75.6 | 97.8 |
| Real + augmented (A1) | 82.6 | 98.3 |
| Real + synthetic (B) | 83.2 | 98.0 |
| Full mix (A2) | 84.8 | 98.5 |
| Synthetic pretraining (P) | 84.3 | 98.0 |

**How to read it:**
- The gain is in **surviving damage**. On clean images the same comparison is only +0.64 points.
- Your hypotheses held: A0 was weakest, A1 improved robustness, and A2 was best, though A2's lead over A1 didn't appear on every seed.
- The older evaluation sets, which had already been read, still don't pass: +0.52 on the test split and +0.54 on the first fresh holdout.
- This holdout uses sources seen in training, so it doesn't test new sources.

The evaluation is sound: 92 sealed reads of 92 expected, none unaccounted for, and the earlier 65 access-log lines are unchanged.

**Now running:** Stage 6 is building the report and export, and the model re-export follows it. Stage 5 is confirmed cached, so nothing is read twice. Then come the voting option and the close-out checks.

All 61 studio tests pass, including the hash check that had been failing until the pipeline reran. No page shows an error. I'll look at the report section and the key pages myself.

The rehearsal is running and needs no attention. While it runs, I'll build the "All models vote" option, which only touches dashboard code, so the rehearsal isn't affected.

"All models vote" is built, tested in a real browser, and committed. In a live test it answered alongside all five models, all agreeing on "square", with no page errors.

That leaves only the clean-clone rehearsal, which is rerunning the whole pipeline from scratch. Once it finishes I'll compare its results to the main run, write the final handoff, and close iteration 3.

The rehearsal is running normally, but it only started about 2 minutes ago, at 06:25. It's in the early stages, so there are no training runs yet and no errors. The full rerun should take about 2 to 3 hours. I'll keep waiting with the watcher on.

The rehearsal is at 0 stages and 0 of 40 runs at 06:30, still working through its opening stage.

The rehearsal has reached training: 3 of 40 runs are done at 06:35.

6 of 40 rehearsal runs are done at 06:40, with 3 finished in the last 5 minutes.

9 of 40 rehearsal runs are done at 06:45, with 3 finished in the last 5 minutes.

11 of 40 rehearsal runs are done at 06:50, with 2 finished in the last 5 minutes.

The rehearsal watcher has been restarted for the next 30 minutes.

The new rehearsal watcher started at 06:55.

17 of 40 rehearsal runs are done at 07:00, and the rehearsal has made no sealed reads yet.

19 of 40 rehearsal runs are done at 07:05, with 2 finished in the last 5 minutes.

22 of 40 rehearsal runs are done at 07:10, with 3 finished in the last 5 minutes.

25 of 40 rehearsal runs are done at 07:15, with 3 finished in the last 5 minutes.

27 of 40 rehearsal runs are done at 07:20, with 2 finished in the last 5 minutes.

The rehearsal watcher has been restarted for the next 30 minutes.

The new rehearsal watcher started at 07:25.

33 of 40 rehearsal runs are done at 07:30, and the rehearsal has made no sealed reads yet.

36 of 40 rehearsal runs are done at 07:35, with 3 finished in the last 5 minutes.

38 of 40 rehearsal runs are done at 07:40, with 2 finished in the last 5 minutes.

The rehearsal finished all 40 runs at 07:45 and is now in its own evaluation stage, with its separate read log at 45 so far.

The rehearsal's evaluation stage is progressing at 07:50, with its read log at 81.

The rehearsal watcher has been restarted for the next 30 minutes.

The new rehearsal watcher started at 07:55.

At 08:00 the rehearsal's read log is at 92, the same count as the main run, and it's now finishing the evaluation.

The rehearsal is still finishing its evaluation at 08:05, with reads unchanged at 92.

The rehearsal is still finishing its evaluation at 08:10, with reads unchanged at 92.

The rehearsal is still finishing its evaluation at 08:15, with reads unchanged at 92.

The rehearsal is still finishing its evaluation at 08:20, with reads unchanged at 92.

The rehearsal watcher has been restarted, and it now also shows how many evaluation files are being written.

The new rehearsal watcher started at 08:25.

The rehearsal is still working through its evaluation at 08:30, with 41 files written in the last 5 minutes and reads steady at 92.

The rehearsal is progressing: all 40 runs are done, and its evaluation stage wrote 41 files in the 5 minutes before 08:30, with reads steady at 92 and no alerts. I'll keep waiting for it to finish.

The rehearsal's evaluation is still progressing at 08:35, with 40 files written in the last 5 minutes.

The rehearsal's evaluation is still progressing at 08:40, with 39 files written in the last 5 minutes.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The pre-registered test ran on 4,500 never-read images across 23 damage levels, with a harm rule per class.

## Our decision

The pass was accepted as pre-registered. No change was made after the read.

## Measured effect

A2 vs A0: +9.20 macro F1, 95% CI [8.89, 9.53], with no harmed class (C23).

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`50_real` — The Pre-Registered Verdict)

### Chain of Custody for the `+9.20` Verdict (`C23`, `C28`)

`50_real` is the capstone of the four-layer `4_testing` evidence system:
1. **Layer 1 — Measurement Integrity (`C20`, `C21`, `C36`):** The `+9.20` macro-F1 gain and its `[8.89, 9.53]` 95% CI are computed via `phash_group` cluster resampling (`C20`) across all 23 damage levels simultaneously (`C36` C-contiguous single matrix product per 64-draw block), gated by the Bonferroni + bootstrap-SE two-floor class-harm rule (`C21`, `harmful_classes: []`).
2. **Layer 2 — Provenance & Read Accounting (`C28`, `F28`, `F16`):** Before unsealing `fresh_holdout_2` (`4,500` never-read images), `artifacts/test_access.log` stood at `65` lines (`13` from Iter 1 + `52` from Iter 2). Stage 5 executed exactly `92` expected reads (`65 -> 157` lines) and remained cached during Stage 6 report/dashboard generation.
3. **Layer 3 — Environment-Independent Reproduction:** The clean-clone rehearsal re-executed all 40 training runs and all 92 evaluation reads in an isolated checkout, reproducing `+9.20 [8.89, 9.53]` and every table bit-for-bit.
4. **Layer 4 — Conditioned Honesty (`C41`, `C54`):** Both the session report and the published artifacts explicitly separate the primary damaged-image verdict (`A2 84.8` vs. `A0 75.6`, `+9.20` points) from the clean `fresh_holdout_2` difference (`98.5` vs. `97.8`, `+0.64` points, CI `[0.19, 1.07]`) and the older contaminated splits (`+0.52` reused test, `+0.54` first fresh holdout).

