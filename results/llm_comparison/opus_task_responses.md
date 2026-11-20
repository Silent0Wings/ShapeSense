# Opus 5.5 task responses

Written for: the project team, reviewing what Opus 5.5 was credited with in the commit log.

**How this was built.** Each row of [commit_tasks.csv](commit_tasks.csv) that names `opus_medium_5.5` (in `proposed_by`, `caught_by`, `llm_involved` or `owner`) is one task. The **claim** is the row's `proposed_by`/`caught_by` attribution plus the matching entries in [attribution_worksheet.csv](attribution_worksheet.csv). The **task** is the commit title and type. The **answer** is written as Opus 5.5 would respond, grounded only in the recorded evidence in those two CSVs and the entries they cite. No git commands were run. Simulation note: these answers are my reconstruction from the records, not a live Opus run.

**Split by stage.** Each task below is also filed as its own prompt and response in `prompts/<stage>/claude_opus/`, using the course stage from [commit_tasks.csv](commit_tasks.csv). Deployment, infrastructure and record-keeping tasks are filed under `4_testing`.

**Scope.** 36 ShapeSense commit tasks (T04 to T84) and the ShapeSense_Deployed tasks T86 to T90 that name Opus 5.5. Deployed tasks are answered from the repository's own README and freeze notes as recorded in the CSV; the HTML under `ShapeSense_Deployed` was not re-audited for this file.

---

## ShapeSense (training and evaluation pipeline)

### T04 - refactor: move Phase 1 scripts into src/stage1_freeze
- **Claim:** proposed by Opus 5.5. **Stage:** 1_data_integration. **Type:** maintenance.
- **Answer:** Proposed the move so that data freezing lives in one package. The benefit is that the freeze code can be tested and rerun on its own. No result changes, because the freeze output is hashed and checked by the stage 0 runner.

### T06 - feat(stage1): freeze leak-free splits with global pHash groups
- **Claim:** proposed by Opus 5.5, caught by Gemini 4 Neon and a team member. Worksheet: F01, F05, C01.
- **Answer:** Opus proposed grouping near-duplicates with a global perceptual hash so no near-copy crosses a split. F01 is the key finding: Opus read 100 random Quick, Draw! images and found most "diamonds" were not rhombi (gems, cones, shields). The response was to exclude all 500 by rule before any test read, then re-freeze the split at 12,405 / 2,819 / 2,776. F05 (source leakage) was documented, not removed.

### T09 - feat(stage4): add loader, baselines, CNN, tuning and seeded sweep
- **Claim:** proposed by Opus 5.5, caught by Gemini 4 Neon. Worksheet: F17, C09, D03.
- **Answer:** Opus proposed the CNN design critique. The first network had three blocks and a 22-px receptive field, too small to see a whole shape (F17). Change C09 moved to four blocks, 46 px. This is a fair attribution of a real design fix.

### T12 - docs: update reports and record CRISP-DM iteration 1
- **Claim:** proposed by Opus 5.5, inspected by a team member and Gemini 4 Neon. Worksheet: F01, C01.
- **Answer:** Recorded F01 and C01 in the iteration 1 report. The report now states that the diamond class was changed after a test-adjacent finding, which is the honest record.

### T11 - feat(stage6): add report build, traceability, export, dashboard and demo
- **Claim:** built by Opus 5.5 with assistance, D02 named by all members. **Stage:** deployment.
- **Answer:** Opus helped build the report and export stage. This is a supporting build, so I count it as assisted, not authored.

### T14 - docs: add pipeline banner image to README
- **Claim:** proposed by Opus 5.5 and a team member. **Type:** documented.
- **Answer:** Documentation only. Attribution is light: the banner idea came from Opus, the commit was made by a team member.

### T19 - fix: close the robustness items before the final Stage 4 rerun
- **Claim:** proposed by Opus 5.5, caught by Opus 5.5 with a team member. Worksheet: N02.
- **Answer:** Fixed the data-store overhead. `ImageStore` now reads its manifest once (e10169d) instead of on every batch. This was a real bottleneck: the GPU sat idle while the SQL catalog was queried.

### T20 and T21 - chore(config): run three trainings at once, then two after a VRAM stall
- **Claim:** proposed by Opus 5.5 and the same team member. Worksheet: F03, C14.
- **Answer:** Stage 4 stalled on the 8 GB GPU. T20 tried three parallel runs, and T21 reduced it to two after the stall. C14 pins `train.parallel_runs: 2`. The two commits show the sequence correctly: the first attempt was wrong and was corrected.

### T24 - docs(report): correct the Phase 2 report and add the LOSO and GPU statements
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon. Worksheet: F02, F17, C09, D03, D04.
- **Answer:** Corrected the report so it says leave-one-source-out runs use nine classes and are scored on Hand-Drawn triangles and rectangles only (F02). It also records the GPU move (D04). The correction matters because the earlier text overstated coverage.

### T25 - docs(readme): say the committed config needs a CUDA GPU
- **Claim:** proposed and caught by Opus 5.5. Worksheet: D04.
- **Answer:** The README now says the committed config needs a CUDA GPU, which matches `train.device: cuda`. A run fails rather than falling back to the CPU, so the README should say so.

### T26 - feat(studio): add the local server for the interactive dashboard
- **Claim:** proposed by Opus 5.5, built by a team member. **Stage:** deployment.
- **Answer:** Opus proposed a local server so the dashboard can read the stored results. No model change. Later dashboard commits (T27 to T31, T42, T73, T78, T79, T82) depend on this server.

### T27 - feat(studio): add the interactive CRISP-DM dashboard pages
- **Claim:** proposed by Opus 5.5, built with two team members.
- **Answer:** Opus proposed the page structure, one page per CRISP-DM step. This is the base for most later dashboard work.

### T30 - feat(studio): live slider updates, label badges, themed images and tooltips
- **Claim:** proposed by Opus 5.5 with two team members.
- **Answer:** Adds live sliders and tooltips. Interface only. Results were not changed.

### T34 - docs(crisp-dm): pre-register iteration 2 and add a fresh holdout
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, mediated by the team. Worksheet: F06, F13, C02, C15, C16.
- **Answer:** Opus proposed the pre-registration and the fresh holdout. F13 was the problem: the test split had been read in iteration 1. C02 built a 4,500-image holdout that informed no choice, sealed like the test split. C15 made A2 vs A0 the primary comparison, fixed before tuning. This is the strongest process fix in the log.

### T35 - feat(iteration-2): fix the transform, add arm A2, tuning and the fresh holdout
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, with the whole team checking. Worksheet: F06 to F09 and many C entries.
- **Answer:** Opus helped propose the per-arm search (C03 to C12). The rotation range was cut from 180 degrees to 20 (C03) after F07 showed full rotation removed an orientation clue. Augmentation and generator ranges were searched on validation (C04, C08), not set by hand. The result of A2 vs A0 failed (F14), and the response was recorded without a post-test change.

### T36 - feat(stage5): show ablation runs in the metrics table
- **Claim:** assisted by Opus 5.5, built by one team member.
- **Answer:** Opus assisted with the table. Presentation only.

### T40 - docs(crisp-dm): keep iteration 1 data for the dashboard and log iteration 2 results
- **Claim:** assisted by Opus 5.5, owned by one member. Worksheet: F14.
- **Answer:** Recorded F14 (A2 vs A0 failed: +0.06 on test, +0.08 on fresh holdout, both intervals include 0). The entry states no change was made after the test read. That is the correct handling.

### T41 - fix(report): keep the findings table inside the frame
- **Claim:** assisted by Opus 5.5 (not in log). **Type:** solved (not in log).
- **Answer:** Layout fix. Opus helped. No result change.

### T42 - feat(studio): show iteration 2, arm A2, the fresh holdout and a frozen iteration 1 page
- **Claim:** proposed by Opus 5.5 and a team member. Worksheet: F15, C19.
- **Answer:** F15 was a drawing limit that broke when the fourth arm was added. The fix ties the limit to the arm list and adds a test. C19 exports all four arms to `studio/out/arms` so every arm can be compared on the same drawing.

### T43 - chore(iteration-2): close the iteration and restore frozen winners in a clean clone
- **Claim:** proposed by Opus 5.5 and a team member. Worksheet: F16.
- **Answer:** F16: a clean clone could not find the tuning result. `run_pipeline.py` now restores the committed copy when it is absent, and the rehearsal reproduced every result. Good evidence of reproducibility (C42).

### T45 - chore: stop tracking compiled test caches added by mistake
- **Claim:** proposed by Opus 5.5 and two members. **Type:** maintenance.
- **Answer:** Removes committed `__pycache__` style files. Hygiene only.

### T46 - chore(iteration-3): freeze the iteration 2 report inputs and evidence
- **Claim:** proposed by Opus 5.5 and two members. Worksheet: F28.
- **Answer:** F28: Report Section K would have shown iteration 3 numbers. The fix makes both read the frozen iteration 2 copies, and the iteration 2 record stays unchanged.

### T48 - fix(stage5): repair the statistics and checks raised by the outside reviews
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, mediated by the team. Worksheet: C20, C21, C22, C28.
- **Answer:** Opus proposed the statistical fixes. C20: near-duplicate images are not independent, so the bootstrap now resamples phash clusters. C21: a Bonferroni-corrected interval for the per-class harm rule. C22: Holm correction on the bootstrap macro-F1 p-values. C28: the robustness check moved into Stage 5 so sealed perturbed sets are read in one place. The statistics are the more careful part of the log.

### T52 - feat(studio): add the project icon and a one-click launcher
- **Claim:** proposed by Opus 5.5, built by one member. **Type:** built.
- **Answer:** Convenience. No results involved.

### T56 - test(studio): forbid fresh holdout 2 and its Stage 5 folders in the sealed-data sweep
- **Claim:** proposed by Opus 5.5, built by one member. **Type:** tested.
- **Answer:** A test that stops the studio from reading sealed holdout 2 before its time. Good guard.

### T58 - feat(iteration-3): record the validation experiments under their CRISP-DM steps
- **Claim:** proposed by Opus 5.5, Gemini 4 Neon and two members. Worksheet: F11, C29, F20.
- **Answer:** F20: the 108-trial run hung silently for about 2 hours 17 minutes. C29 is the pre-registered rule for raising the training budget to 60 epochs with no early stopping, because each arm gained at least 0.5 validation points (A0 1.99, A1 0.51, A2 0.71). The entry records both the failure and the rule.

### T61 - docs(iteration-3): register optimization steps and audited candidates
- **Claim:** proposed by Opus 5.5 and two members. **Type:** documented.
- **Answer:** Registers the optimization steps (C31, C39) before they are used. Good: optimizations are only registered once measured.

### T62 - perf: optimize the pipeline without changing results
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, built by team members. Worksheet: F23, F24, C31, C34 to C36, N02.
- **Answer:** Opus proposed the speedups. F24 is the key check: converting pixels on the GPU would have changed every result, so the team measured it and used a CPU lookup table. F23: the first shared worker pool had five bugs, all found by audit before they did harm. Two reruns matched the earlier trials on every logged number.

### T64 - feat(iteration-3): reuse repeated search runs and fix two Stage 6 checks
- **Claim:** proposed by Opus 5.5 and a member. Worksheet: F26, C32.
- **Answer:** C32: nine of 200 search runs repeated a finished trial with identical settings. Those are reused, so 191 runs train. F26: a failed Stage 6 check could pass the stage. A failed check now fails the stage.

### T67 - docs(iteration-3): record the GPU error during the search
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, caught by two members. Worksheet: F22, C37.
- **Answer:** F22: the search stopped at 66 of 191 trials with a GPU error. The response was to confirm the GPU worked, stop the leftover process, relaunch, and carry over the 66 finished trials. C37 writes that as a rule for the next crash.

### T68 - docs(iteration-3): record the session's bugs, fixes and improvements by CRISP-DM step
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, caught by four members. Worksheet: F23, F19, F20, F25, C37.
- **Answer:** Records the session's failures by step. F25 is a useful correction: the GPU looked idle in Task Manager, but `nvidia-smi` and run records show training on the RTX 3080, with use swinging between 0% and 96% as it waits for batches.

### T69 - feat(iteration-3): freeze the search winners and the 60-epoch budget
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, caught by four members. Worksheet: F11, C26, C29, C38, C39.
- **Answer:** C26: the top five settings per arm are re-scored by grouped 3-fold CV, because one validation split can favour a setting by chance. C38 freezes the winners in `configs/pipeline.yaml`. F11 is recorded as not fixed in iteration 2 and addressed in iteration 3.

### T71 - test(stage5): expect hold-out runs for all five arms
- **Claim:** proposed by Opus 5.5 and a member. **Type:** tested.
- **Answer:** A test that expects hold-out runs for all five arms. Keeps the test suite in line with the arm list.

### T73 - feat(iteration-3): add report Section L and the final arms to the dashboard
- **Claim:** proposed by Opus 5.5 and one member. Worksheet: F28, C41.
- **Answer:** C41: Section L leads with the sealed result, so the verdict is readable where people look first.

### T75 - feat(studio): add the equal-weight All models vote
- **Claim:** proposed by Opus 5.5, caught by the team and a member. Worksheet: F30, C40, D01.
- **Answer:** D01 credits Opus with the idea of voting across models, which the test split later supported (soft-vote ensembles beat per-seed means for every arm). F30: the first vote comparison scored an empty class as zero. The fix balances halves by class and leaves absent classes out. C40 keeps equal weights because they scored 95.59 vs 94.80 for per-class weights on held-apart validation. That validation was reused, so the figures are optimistic, and the entry says so.

### T77 - docs(iteration-3): finish the CRISP-DM record
- **Claim:** proposed by Opus 5.5 and one member. **Type:** documented.
- **Answer:** Completes the CRISP-DM record. Documentation only.

### T78 - feat(studio): make the dashboard easier to explore and read
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, reviewed by the whole team. Worksheet: F11, C43 to C51.
- **Answer:** Many small readability fixes. C43: the main finding now shows every model, not only Full mix vs Real. C44: a slider walks iterations 1 to 3. C45: close dots spread into lanes instead of a log scale, which would distort distances. C51: the browser now receives update notices so stale pages are not shown.

### T79 - feat(studio): add the interactive network view and explain the models
- **Claim:** proposed by Opus 5.5 and two members, assisted. Worksheet: C48, C52.
- **Answer:** C48: an interactive diagram showing that the models share one network and differ only in their training images. C52: the home page now defines the five models and their training-image kinds in one place.

### T81 - feat(configs): add one generated config file per model
- **Claim:** built by one member, assisted by Opus 5.5. Worksheet: C53.
- **Answer:** C53: `configs/models` holds one generated file per model, so each model's full setup can be read in one place. Opus assisted, the member built.

### T82 - fix(studio): correct old failure charts and make results easier to read
- **Claim:** built by one member, assisted by Opus 5.5. Worksheet: F31, C54.
- **Answer:** F31: the page for failure F14 showed iteration 3 numbers. Earlier failures now read their own iteration's frozen record, so F14 shows +0.06 and +0.08. F11 shows a note because no per-epoch log was kept for that run.

### T84 - docs: record the final audit and the history cleanup
- **Claim:** proposed by Opus 5.5 and Gemini 4 Neon, with two members. Worksheet: C56, C57.
- **Answer:** C56: the final audit on 2026-11-10 found the README still listed the All models vote as future work, which was then corrected. C57 purged two local working notes and planning files from history, which is the right call before any public push.

### T85 - feat: initialize project directory structure with documentation and placeholders
- **Claim:** proposed by Opus 5.5 and one member, dated 2026-11-19. **Stage:** course deliverables. **Type:** built.
- **Answer:** Sets up the folder layout and placeholders for the course deliverables. This is the most recent commit in the log and matches the date. No results involved.

---

## ShapeSense_Deployed (public site)

These entries are credited to all members with Opus 5.5 and Gemini 4 Neon. They are summarized from the CSV and the deployed README.

### T86 - Deploy the public site: ONNX models with in-browser inference, Vercel hosting, interactive presentation
- **Claim:** built by all members, Opus 5.5 and Gemini 4 Neon. Worksheet: D02.
- **Answer:** D02 is Opus's proposal to deploy the project online: export five models to ONNX and run them in the visitor's browser with ONNX Runtime Web, no server. Browser output was checked against Python (logits within 1e-4). The public site was published at the URL in the worksheet.

### T87 - Releases: protected preview, three public freezes, phone layout, and the 11-16 and 11-17 live freezes
- **Claim:** all members with Opus 5.5 and Gemini 4 Neon.
- **Answer:** Release sequence on 2026-11-11 to 2026-11-17. The record is consistent with the freeze names. Released, not re-verified in this file.

### T88 - Interactive presentation: six parts, one per presenter, covering at least 90% of the source repository
- **Claim:** all members with Opus 5.5 and Gemini 4 Neon.
- **Answer:** Opus helped plan the six-part presentation. The 90% coverage claim is a stated target in the CSV. I did not measure it here, so treat it as unverified.

### T89 - Interactive explanations: each stage's design and data handling, animated CRISP-DM wheel, hover help, conclusion dots, stepped sliders and iteration stepper
- **Claim:** all members with Opus 5.5 and Gemini 4 Neon.
- **Answer:** Explanations for each stage, matching the stage-explanation work in C55 and the wheel in C44. Built on the studio layout.

### T90 - Live prediction: predict on demand, with a drawing toolbar above the canvas
- **Claim:** all members with Opus 5.5 and Gemini 4 Neon.
- **Answer:** Adds on-demand prediction in the browser, which relies on the ONNX export in D02. Interface plus inference, no new model.

---

## Summary of what the records show

- **Strongest Opus contributions:** F01 (finding that Quick, Draw! diamonds were not rhombi), C15 and F13 (pre-registration and a fresh holdout after the test split was read), C22 and C20 (statistics), and F24 (measuring before a GPU change).
- **Attribution to watch:** several rows say "assisted" or "proposed" rather than "built". The CSV records these as proposals, not authorship. Keep that distinction in any final write-up.
- **Not verified here:** no git commands were run, and the HTML under `ShapeSense_Deployed` was not re-audited. The Deployed answers rest on the CSV and worksheet records.
