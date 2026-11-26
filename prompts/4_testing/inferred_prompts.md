#  prompts: 4_testing

<a id="f04"></a>

## F04 - B vs A1 failed: -0.36 points, CI [-1.17, 0.41], and A0 with no augmentation scored highest.

- Iteration: Iteration 1
- LLM: both (mediated)
- State: Verdict stands
- CRISP-DM step: Evaluation · Pipeline stage: 5 · Evaluation

** prompt**

> Our pre-registered test B vs A1 failed (-0.36 macro-F1 points, CI [-1.17, 0.41]) and the arm with no augmentation scored highest. Without touching the test split again, how should we investigate why augmentation and synthetic data did not help?

**Answer** 
Leave the iteration 1 verdict as it is: `fail`, -0.36 points, CI [-1.17, 0.41], 13 of 13 planned test reads (`results/phase2_snapshot/iter1_status.json`). Do every diagnostic on train and validation only. A0 with no augmentation beating both augmented arms points at the augmentation pipeline first, not only at the synthetic data. So test these one at a time on validation: rotation off, ±15° and ±180°; shape size and stroke breaks before and after the transform; synthetic stroke width against real strokes; and whether labels survive batching. Fix any defects before tuning, then pre-register a new test. The recorded investigation (`docs/crisp_dm/iteration_2/investigation/report.md`) found no label bug (0 mismatches over 179 tracked images). On validation, A1 scored 90.03 at ±180°, 93.15 with rotation off and 93.17 at ±15°, against 91.69 for A0. Augmented shapes were too small (51.0 px against 56.0 to 57.8 px real), and the synthetic stroke was 2 px against 3.1 px real. Opus and Gemini both recommended this validation-only approach. Gemini also proposed a large per-arm search, and the team ran that only after the defects were fixed.

**Documented cause:** The rotation range and the transform defects found in the next part of this timeline.

**Documented outcome:** Kept the verdict unchanged and investigated on validation only, which started iteration 2.

<a id="f13"></a>

## F13 - The test split had already been read in iteration 1.

- Iteration: Iteration 2
- LLM: none (40256377)
- State: Partly
- CRISP-DM step: Evaluation · Pipeline stage: 1 · Data freeze, 5 · Evaluation

** prompt**

> The test split was already read in iteration 1. How do we run a second, honest test: can we reuse the test split, and how should we build a fresh holdout?

**Answer** 
You can reuse the test split, but only if you say so in the pre-registration and label it weaker evidence. Iteration 1 read it, and its per-class numbers shaped the plan for iteration 2, so a second read is not independent. That is what `docs/crisp_dm/iteration_2/preregistration.md` states. For a clean check, build a fresh holdout from raw files that never entered the catalog. Standardise them the same way, drop anything within the catalog's near-duplicate threshold, and seal the file under the same read log so that only Stage 5 reads it, once per model. The recorded holdout, `configs/splits/fresh_holdout.csv`, holds 4,500 images across all 10 classes. Its limits are stated: every source in it was seen in training, it has no Quick, Draw! images (all 3,500 local ones were already in the catalog), and its diamonds are renders only. Check the read counts. Iteration 2 logged 52 of 52 expected reads, 32 on the test split and 20 on the fresh holdout, with 0 extra reads (`results/phase2_snapshot/iter2_status.json`, `docs/crisp_dm/iteration_log.json`). The entry stays "Partly" because the holdout cannot test sources that training never saw.

**Documented cause:** No untouched test data remained after iteration 1.

**Documented outcome:** Pre-registered the reuse and built a fresh 4,500-image holdout. It has no Quick, Draw! images and uses sources seen in training.

<a id="f14"></a>

## F14 - A2 vs A0 failed: +0.06 on test and +0.08 on the fresh holdout, both CIs include 0.

- Iteration: Iteration 2
- LLM: opus_medium_5.5 (assisted, proposed by 40256377)
- State: Still open
- CRISP-DM step: Evaluation · Pipeline stage: 5 · Evaluation

** prompt**

> A2 vs A0 failed: +0.06 on test and +0.08 on the fresh holdout, both CIs include 0. How should we report this, and what could a third iteration test instead?

**Answer** 
Report it as a plain `fail` on both sets, with no change after the read. On the reused test split the result is +0.06 points, CI [-0.69, 0.83]. On the fresh holdout it is +0.08, CI [-0.41, 0.57]. Both are below the required 1.0 point and both intervals include 0 (`results/phase2_snapshot/iter2_status.json`). Call the test split contaminated evidence and the fresh holdout the cleaner check on seen sources. The cause is a ceiling. Once the defects were fixed, every arm scored about the same on images from familiar sources: fresh-holdout macro-F1 was 97.46 for A0, 97.42 for A1, 97.23 for B and 97.54 for A2. A third iteration needs a condition where the arms actually differ, on data nobody has read. Opus and Gemini both pointed to unseen sources, where the Hand-Drawn hold-out runs favoured the augmented arms. They also noted that this hold-out covers only two classes and its seeds vary widely. Opus offered damaged copies of a never-read holdout as the alternative. Iteration 3 took that route, and its pre-registration notes that it still does not test new sources.

**Documented cause:** With the defects fixed, every arm reaches about the same score on images from sources it trained on.

**Documented outcome:** Recorded as a failure. No change was made after the test read. A third iteration would need to target unseen sources.

<a id="f15"></a>

## F15 - Drawing on the live page failed once the fourth arm was added.

- Iteration: Iteration 2
- LLM: opus_medium_5.5 + 40248536
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> Drawing on the live page fails once a fourth arm is added. Find the cause and add a test that prevents it.

**Answer** 
The request schema caps the arm list, so the error comes before inference ever starts. In `studio/server/schemas.py`, `InferRequest.arms` was limited to 3 items. When `ARMS` in `studio/settings.py` grew to four, a request for every arm failed validation (an HTTP 422 in the Opus reading). Don't just raise the number to 4, because the next arm would break it again. Tie the limit to the arm list with `max_length=len(ARMS)`, and do the same for `FeedbackRequest.results`. Keep a bound rather than removing it. Add a test in `tests/studio/test_api_bounds.py` (`test_every_arm_can_be_asked_for_at_once`) that posts `list(ARMS)` and expects 200, then posts one arm too many and expects 422. That is the fix recorded in `studio/server/schemas.py`. When the fifth arm, P, was added later, it needed no schema change.

**Documented cause:** The API still accepted at most three arms.

**Documented outcome:** Tied the limit to the arm list and added a test.

<a id="f16"></a>

## F16 - A clean clone could not find the tuning result.

- Iteration: Iteration 2
- LLM: opus_medium_5.5 + 40304911
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 4 · Training, 6 · Report and export

** prompt**

> A clean clone cannot find the tuning result because artifacts/ is not in Git. How do we make the pipeline reproducible from a fresh clone?

**Answer** 
Keep `artifacts/` out of Git, because it is a build folder full of checkpoints and predictions. Commit the frozen tuning result as a source file instead, and have the runner restore it when it is missing. The recorded fix keeps the winners under `docs/crisp_dm/` and adds `restore_frozen_winners` to `run_pipeline.py`. Before the stages run, it copies the committed file into `artifacts/stage4/...` only if no file is already there, so a local run is never overwritten. Stage 4 and Stage 6 code stay untouched. Check it two ways. First, a unit test (`tests/stage0/test_runner.py::test_frozen_winners_restored_only_when_absent`) covers both the restore and the no-overwrite case. Second, run a full rehearsal on a fresh clone. The recorded rehearsal passed all seven stages and reproduced every result (`docs/crisp_dm/iteration_log.json`). The constant `FROZEN_WINNERS` now points at the iteration 3 copy, `docs/crisp_dm/iteration_3/search/winners.json`.

**Documented cause:** artifacts/ is not in Git, and Stages 4 and 6 read the winners from there.

**Documented outcome:** run_pipeline.py restores the committed copy when it is absent. The rehearsal then reproduced every result.

<a id="f26"></a>

## F26 - Stage 6 could pass with a failed report check.

- Iteration: Iteration 3
- LLM: opus_medium_5.5
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> Can Stage 6 pass when a report check fails? Review the stage's pass logic and its cache inputs.

**Answer** 
Yes, it could. In `src/stage6_report/run.py` the failure gate looked only at the report-build and export smoke-test checks. The number-traceability and dataset-attribution results were recorded, but they never set the status to `failed`. The cache key was also too narrow. It hashed only the `runs` part of the config and left out the preprocessing code (`src/stage1_freeze/standardize.py`) and the Stage 3 generator status. Any other config edit, a preprocessing change or a generator change could therefore hit a stale cached pass. Fix: collect all four check failures and fail the stage if any is false; hash the whole config; add `standardize` and `stage3_status` to `inputs()`. Check it with `tests/stage6/test_run_status.py`. It has four tests: all checks pass, a failing traceability or attribution check fails the stage, any config change invalidates the cache, and the cache tracks preprocessing and generator status. The current `inputs()` in `src/stage6_report/run.py` does all of this.

**Documented cause:** A failed number-traceability or attribution check still left the stage marked as passed, and its cache missed some inputs.

**Documented outcome:** A failed check now fails the stage, and the cache tracks the whole config, the preprocessing code and the generator status.

<a id="f27"></a>

## F27 - Report macro names broke for arm A2 and collided for hold-out runs.

- Iteration: Iteration 3
- LLM: gemini_4_neon (assisted, proposed by 40211352)
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> Report macro names break for arm A2 and collide for hold-out runs. Why, and how do we rename them without changing existing names?

**Answer** 
There are two causes. First, a LaTeX control word ends at the first non-letter, so a digit in a macro name cuts the name short. The old code spelled out only some digits, which missed the "2" in A2 and seeds above 2. Second, the name builder kept only the first and last parts of a run name, so `A0_loso_0` produced the same stem as `A0_0`. Because the macros use `\providecommand`, the second definition was silently ignored. Fix it with one letter-only stem builder. Spell out every digit 0 to 9, and add the middle parts of a run name between the arm and `Seed<n>`. Names without middle parts then come out exactly as before. Gemini proposed this (`DIGIT_WORDS`, `_macro_word`, `macro_key` in `src/stage6_report/iteration_evidence.py`). Check it with tests that existing names such as `A0_0`, `A1_2` and `B_1` keep their macros, that no generated name contains a digit, and that `A0_loso_0` differs from `A0_0` (`tests/stage6/test_iteration_evidence_macros.py`).

**Documented cause:** LaTeX macro names cannot contain digits, and runs such as A0_loso_0 got the same name as A0_0.

**Documented outcome:** Digits are spelled out and hold-out runs get their own names. Existing macro names did not change.

<a id="f28"></a>

## F28 - Report Section K would have shown iteration 3 numbers.

- Iteration: Iteration 3
- LLM: opus_medium_5.5
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> Will the iteration 2 tables in the report change after iteration 3 overwrites the Stage 5 folder? Check where each table reads its numbers.

**Answer** 
Yes, as things stand. Two Section K tables were read from the live Stage 5 output, so when iteration 3 rewrote that folder, Section K would have shown iteration 3 numbers under an iteration 2 heading. A closed iteration's section has to be fixed for good. Copy the iteration 2 tables, data, figures and generated macros into `docs/crisp_dm/iteration_2/` with a SHA-256 manifest (`frozen.sha256`). Point Section K at those copies, and stop Stage 6 from regenerating the iteration 2 files. Don't type the numbers into the report by hand, because that breaks the traceability rule. Check it with `tests/stage6/test_frozen_iteration2.py`, which verifies every hash in the manifest, and by confirming that Section K still shows iteration 2's +0.06 (reused test) and +0.08 (fresh holdout) after iteration 3 has run. In the current report, the Section K tables read `docs/crisp_dm/iteration_2/tables/`, while Section L reads the live `artifacts/stage5/tables/`.

**Documented cause:** Two iteration 2 tables were read from the live Stage 5 folder, which iteration 3 overwrote.

**Documented outcome:** Both now read the frozen iteration 2 copies, and the iteration 2 record stays as it was.

<a id="f29"></a>

## F29 - The dashboard listed arm P twice.

- Iteration: Iteration 3
- LLM: gemini_4_neon + 40248536
- State: Overcome
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> The dashboard lists arm P twice. Find which script added it and how to make the correction safe to re-apply.

**Answer** 
The duplicate is in the dashboard's arm list. `ARM_SERIES` in `studio/web/js/pages/boot.js` held two entries for P, because a correction script appended P again when it was re-applied without checking whether P was already there. Every chart and legend built from that list then showed P twice. Remove the second entry, and make any such script idempotent so that running it again changes nothing: check whether the key exists before adding it, or merge by arm key instead of appending, and assert that the keys are unique before writing. Gemini also suggested deriving the predict panel's labels from the single `ARM_NAMES` list in `plain.js`, so the arm lists cannot drift apart. Check by opening every dashboard page and confirming each of the five arms appears exactly once. The log records that every page was checked in a browser (`docs/crisp_dm/iteration_log.json`). The repo does not name which correction script made the duplicate.

**Documented cause:** A correction script added P a second time when it was re-applied.

**Documented outcome:** Removed the duplicate, and checked every page in a browser.

<a id="f31"></a>

## F31 - The page for failure F14 showed iteration 3 numbers.

- Iteration: Iteration 3
- LLM: none (40304911)
- State: Partly
- CRISP-DM step: Deployment · Pipeline stage: 6 · Report and export

** prompt**

> The page for failure F14 shows iteration 3 numbers. How do we make each failure page read the frozen record of its own iteration?

**Answer** 
Give each failure its iteration number, and point the chart at that iteration's frozen record whenever the iteration is not the live one. The recorded fix in `studio/web/js/widgets/failure-visuals.js` sets `LIVE_ITERATION = 3` and maps iterations 1 and 2 to their frozen records (`iteration1`, `iteration2`). A verdict chart whose source is `stage5` then reads the frozen record for any earlier failure, so F14 shows +0.06 on test and +0.08 on the fresh holdout instead of iteration 3's +9.20. Where the frozen record lacks the data a chart needs, show a note rather than reading the live folder. F11's training curve is a case of this: no per-epoch log was kept for that run. Check by opening each earlier failure page and comparing its numbers with `results/phase2_snapshot/iter1_status.json` and `iter2_status.json`. The entry stays "Partly" because the previews on F07, F08 and F10 still run on the current settings, not on the settings of their own iteration.

**Documented cause:** Its chart read the live results, which changed when iteration 3 finished. A screen review found it.

**Documented outcome:** Earlier failures now read the frozen record of their own iteration, so F14 shows +0.06 and +0.08. F11 shows a note, because no per-epoch log was kept for that run. The live previews on F07, F08 and F10 still use the current settings.

## Changes, decisions and notes

<a id="c15"></a>

## C15 - Primary comparison

- Kind: change (eval)
- LLM: gemini_4_neon (proposed)

** prompt**

> Iteration 2 asks whether the full mix beats real images alone. Which comparison should be the single pre-registered primary test (B vs A1 or A2 vs A0), and how do we register it before any tuning?

**Answer** 
Use A2 vs A0. The question is whether the full mix beats real images alone, and only A2 (clean real, augmented real and synthetic in each batch) against A0 (real images only) asks that directly. B vs A1 asks a narrower question about adding synthetic data to augmented data, and neither of those arms sees clean real images. Keep one primary test so that error control stays simple, and run the other pairs as a Holm-corrected secondary family (A1 vs A0, B vs A0, A2 vs B). To register it, write and commit `docs/crisp_dm/iteration_2/preregistration.md` before the first tuning run. It should name the primary comparison, keep the locked thresholds (gain of at least 1.0 point, 95% CI excluding 0, no harmful class), list the search spaces, and state that nothing changes after a test read. Then set the pair in `configs/pipeline.yaml` (`evaluation.primary`) rather than in code. Gemini proposed this. To check it, confirm that the pre-registration commit comes before the tuning commits and that Stage 5 reports its primary as "A2 vs A0" (`results/phase2_snapshot/iter2_status.json`).

**Before:** B vs A1

**After:** A2 vs A0, pre-registered before tuning

**Documented reason:** Iteration 2 asks whether the full mix beats real images alone.

<a id="c16"></a>

## C16 - Evaluation data

- Kind: change (eval)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40253714)

** prompt**

> The test split has been read once. Besides reusing it under a pre-registered note, what evidence can we add that the first read could not have touched, and how do we report both together?

**Answer** 
Add a sealed fresh holdout built from raw images that never entered the catalog. Standardise it the same way, remove near-duplicates of every existing train, validation and test image, and let only Stage 5 read it, logged once per model. The recorded holdout has 4,500 images across all 10 classes (`docs/crisp_dm/iteration_2/preregistration.md`). Report both sets side by side with the same comparison and rule. Label the reused test split weaker evidence and the fresh holdout the cleaner check, and state the holdout's limits: seen sources only, no Quick, Draw! images, renders-only diamonds. Gemini's design was adopted with two corrections. The holdout could not include Quick, Draw!, and its comparison uses the cluster bootstrap rather than an image-level one. Check that the two sets tell the same story. In iteration 2 they did: +0.06, CI [-0.69, 0.83] on test and +0.08, CI [-0.41, 0.57] on the fresh holdout, with 52 of 52 logged reads (`results/phase2_snapshot/iter2_status.json`).

**Before:** Test split

**After:** Reused test split plus the fresh holdout

**Documented reason:** To add evidence the first read could not have touched.

<a id="c17"></a>

## C17 - Robustness check

- Kind: change (eval)
- LLM: gemini_4_neon (mediated, proposed by team)

** prompt**

> Clean accuracy does not show which model survives damaged images. Design a robustness check: fixed perturbed copies of validation, which damage types and levels, and how all 20 models are scored. It must stay descriptive and change no verdict.

**Answer** 
Build the damaged copies of validation once, with a fixed seed, so every model is scored on exactly the same pixels. Then score all 20 models (four arms, five seeds each) and report the mean and spread per arm and damage level. Use damage that cannot change a shape's class, so no stretching that turns a circle into an ellipse. Cover several families at mild to severe levels. The recorded check (`results/phase2_snapshot/robustness.json`) uses seed 20261109 on the 2,819 validation images. It has 32 sets: clean, plus rotation (including a 0° control), Gaussian noise, salt and pepper, blur, JPEG, brightness, contrast and square occlusion. Keep it outside Stages 4 and 5, run no hypothesis test, and label it descriptive on the dashboard. The file's own note says it "changes no verdict". The result was striking. Mean macro-F1 over the 30 damaged levels was 52.80 for A0, 59.85 for A1, 60.65 for B and 62.18 for A2, while clean scores were within about 2 points of each other. That gap is what shaped iteration 3's primary test.

**Before:** None

**After:** Fixed perturbed copies of validation, scored by all 20 models

**Documented reason:** Clean accuracy does not show which model survives damage. Descriptive only; changes no verdict.

<a id="c18"></a>

## C18 - Shipped model

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed)

** prompt**

> Which trained model should we ship? Propose a selection rule that uses validation macro F1 only, and say how to record the choice so it cannot be changed after a test read.

**Answer** 
Ship the completed Stage 4 run with the highest validation macro-F1, choose it without reading any test or holdout metric, and break ties by config order. One guard is essential: exclude the leave-one-source-out runs. They train and validate on a 9-class split, so their validation scores are higher and cannot be compared with the 10-class runs. Gemini's first rule missed this. Without the filter it would have picked a LOSO model such as `A1_loso_handdrawn_0` at 97.57. Record the choice in `export/model_card.json` (run, arm, seed, validation macro-F1, `"selection": "validation macro-F1"`) and in the Stage 6 status, and let the Stage 6 cache hash the Stage 4 status so the choice is bound to pre-test numbers. The rule picked A2_2 in iteration 2. Under the same rule, iteration 3 picked A2_0 at 95.99 (`results/phase2_snapshot/model_card.json`). The final audit confirmed that the shipped model is the A2 export byte for byte.

**Before:** A0_0

**After:** A2_2, chosen by validation macro-F1

**Documented reason:** The selection rule picked the best validation run.

<a id="c19"></a>

## C19 - Live models in the studio

- Kind: change (deploy)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> The studio loads A0 from the bundle and A1 and B separately. How do we export all four arms to one folder so the live page can compare every arm on the same drawing?

**Answer** 
Export every arm the same way into `studio/out/arms/`, with one manifest, and remove the special case that loaded A0 from the shipped bundle. In `studio/tools/export_arms.py`, add A0 to the export list beside A1, B and A2. Write each arm's best-validation run to `studio/out/arms/<arm>/model.onnx`, and record its run, validation macro-F1 and SHA-256 in `manifest.json`. In `studio/inference/arms.py`, read every arm from that folder only. Leave `export/` as the single shipped model. This matters because the shipped bundle moved to A2, and an A0 that still pointed at `export/` would have silently loaded the wrong model. Check that the manifest lists every arm with a validation score, and that one drawing gets an answer from each arm. Adding the fourth arm exposed a request limit, recorded as failure F15. The export list now holds five arms, matching `ARMS` in `studio/settings.py`.

**Before:** A0 from the bundle, A1 and B separately

**After:** All four arms exported to studio/out/arms

**Documented reason:** To compare every arm on the same drawing.

<a id="c20"></a>

## C20 - Bootstrap

- Kind: change (eval)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40253714 + 40304911)

** prompt**

> Our bootstrap resamples images independently, but near-duplicate images share a phash group. How should the bootstrap resample clusters instead, and should we add a source-clustered check beside the primary?

**Answer** 
Resample whole `phash_group` clusters, so all near-duplicates of an image enter or leave a draw together. Score both arms on the same cluster weights in every draw. Resampling images one at a time treats near-duplicates as independent, which makes the interval too narrow. Yes, add a source-clustered interval, but only as a descriptive sensitivity check. With three sources, resampling three clusters is too coarse to decide the test. Opus also proposed a separate named random generator for each analysis, so that adding a comparison cannot change the primary interval. Check it with tests: duplicated images should widen the interval, and the result should not depend on the order of the analyses (`tests/stage5/test_iteration3_repairs.py`). On iteration 3's sealed primary, the cluster interval was [8.89, 9.53] and the source-clustered interval was [3.89, 9.42], both well above 0 (`results/phase2_snapshot/status5.json`). Fresh holdout 2 has 4,500 clusters for 4,500 images, and no image-level interval on the same data is recorded for comparison.

**Before:** Images resampled independently

**After:** phash_group clusters resampled, source-clustered check beside the primary

**Documented reason:** Near-duplicate images are not independent.

<a id="c21"></a>

## C21 - Harm rule

- Kind: change (eval)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Our harm rule runs one test per class with no correction across ten classes. How do we control false alarms? Propose a corrected interval and the standard error of the paired drop.

**Answer** 
Ten uncorrected tests at α = 0.05 give roughly a 40% chance of at least one false harm flag (1 - 0.95^10). Correct for the family. Bonferroni is the simplest choice for an interval rule: use a two-sided level of 1 - 0.05/10 for each class, so a class is flagged only if its corrected lower bound on the drop is above 0. Take the standard error of the paired drop from the same bootstrap, as the standard deviation of the per-class drops across resamples, and require the drop to exceed max(minimum drop points, that standard error). Opus first leaned towards Holm or FDR, for a little more power. The team chose Bonferroni because it keeps the harm check interval-based in `src/stage5_eval/criterion.py` and leaves Holm for the secondary family. Check it with `tests/stage5/test_iteration3_repairs.py::test_harm_needs_the_corrected_interval_and_the_standard_error_floor`, which covers flagged, not flagged under the corrected bound, and not flagged under the standard-error floor. The sealed iteration 3 primary flagged no class (`harmful_classes: []` in `results/phase2_snapshot/status5.json`).

**Before:** One test per class, no correction

**After:** Bonferroni-corrected interval, bootstrap standard error of the paired drop

**Documented reason:** Ten classes tested at once raise false alarms.

<a id="c22"></a>

## C22 - Secondary tests

- Kind: change (eval)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40256377)

** prompt**

> Our secondary tests use Holm on McNemar accuracy p-values, while the primary uses bootstrap macro F1. How do we make the primary and secondaries use one metric, and what should we still report from McNemar?

**Answer** 
Take the secondary p-values from the same paired cluster bootstrap on macro-F1 that produces the primary interval. Compute a two-sided p-value from that bootstrap's distribution of differences, with a +1 pseudo-count so it is never 0, and apply Holm to those values. Then the primary and every secondary measure the same thing. McNemar measures accuracy, which can disagree with macro-F1 when per-class recall shifts. Keep McNemar as a descriptive accuracy check: report b, c, both right, both wrong, the statistic and p. Use the exact binomial test when b + c is under 25 and the continuity-corrected test otherwise. Gemini proposed this, and the iteration 3 pre-registration adopted it. With 2,000 resamples, the smallest raw p is 2/2001, about 0.001. Every damaged-image secondary on fresh holdout 2 hit that floor, giving a Holm p of 0.004 (`results/phase2_snapshot/status5.json`). Check it with `tests/stage5/test_stats.py`, which covers the exact/approximate switch and bounded p-values.

**Before:** Holm on McNemar accuracy p-values

**After:** Holm on bootstrap macro-F1 p-values, with exact McNemar reported

**Documented reason:** One metric across the primary and secondaries.

<a id="c23"></a>

## C23 - Primary comparison

- Kind: change (eval)
- LLM: gemini_4_neon (assisted, proposed by 40248536)

** prompt**

> Clean accuracy no longer separates A2 from A0. Should the primary comparison average over damage levels on the never-read second holdout instead, and how do we pre-register it before reading that holdout?

**Answer** 
Yes. On clean images from seen sources the arms sit within about 0.1 point of each other (iteration 2: +0.06 and +0.08), so a clean primary would only repeat that ceiling. The iteration 2 validation robustness check showed a gap of about 9 points under damage (`results/phase2_snapshot/robustness.json`). First, build and seal fresh holdout 2 from images that have never been read, excluding the first holdout's images without reading them. Then commit `docs/crisp_dm/iteration_3/preregistration.md` before any tuning or sealed read. It should name A2 vs A0, ensemble macro-F1 averaged over a fixed list of damage levels, the cluster-bootstrap rule and the corrected harm rule. Choose the levels in advance, and drop those where every arm collapsed on validation. Seven levels had every arm under 30% accuracy (salt and pepper 10% and 20%, blur 2 and 3, brightness -0.4, contrast × 0.5 and × 0.25), which leaves 23. The pre-registration says plainly that holdout 2 uses the same sources, so it does not test new sources. The sealed result was +9.20, CI [8.89, 9.53], pass, with 92 of 92 reads (`results/phase2_snapshot/status5.json`).

**Before:** A2 vs A0 on clean images

**After:** A2 vs A0 averaged over 23 damage levels on never-read fresh holdout 2

**Documented reason:** Clean accuracy had stopped separating the arms.

<a id="c28"></a>

## C28 - Robustness check location

- Kind: change (eval)
- LLM: gemini_4_neon (mediated, proposed by team)

** prompt**

> Our robustness check is a separate script that only reads validation. Should it move into Stage 5, and how do we build the perturbed sets once, hash them and make sure sealed sets are read in only one place?

**Answer** 
Yes, move it into Stage 5. A separate script cannot read a sealed split without breaking the rule that only `src.stage5_eval.evaluate` reads sealed data and every read is logged. Put the shared damage functions in a common module and the evaluator in `src/stage5_eval/robust.py`. Build each damaged set from the images returned by Stage 5's one logged read, with the fixed seed, and save it once. Record a manifest holding the hash of the source split file and a SHA-256 for each set. On every later run, check those hashes and stop with an error on any mismatch, or if a set is missing and the images are not in memory, rather than rebuilding it silently or reading the CSV again. Cache predictions per model and level. Check that read accounting still balances: iteration 3 logged 92 of 92 expected reads with 0 extra (`results/phase2_snapshot/status5.json`). Gemini proposed this structure and it was adopted. The clean-clone rehearsal also reproduced the robustness figures.

**Before:** A separate script on validation only

**After:** Moved into Stage 5, with perturbed copies built once and hashed

**Documented reason:** So sealed perturbed sets are created and read in only one place.

<a id="c33"></a>

## C33 - Dashboard wording

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed)

** prompt**

> A new reader of our dashboard home page cannot tell what the project does or what it found: it shows arm codes, a bare FAIL and a process title. Rewrite it in plain words, generated from the stored results.

**Answer** 
Write the words in code, from the stored records, rather than typing them. Put the plain-language helpers in one module (`studio/web/js/plain.js`). It should map arm codes to names (Real only, Real + augmented, Real + synthetic, Full mix, Synthetic pretraining), and turn a verdict into a headline such as "Clear gain" or "No clear gain" instead of a bare FAIL. Build the finding sentence from the stored label, gain, interval and rule, and pass the locked success criterion from `configs/pipeline.yaml` through the page data. Open the home page with what the project does: draw a shape and a small model names it. Add a row showing the ten shapes, then the main finding with an interval picture showing 0 and the required +1 line. Gemini proposed this and it was adopted. A later screen review added "on damaged images" plus the clean result to iteration 3 headlines (C54). Check that every number on the page matches the stored JSON and that no metric is hard-coded. No reader test of the new wording is recorded.

**Before:** Arm codes, a bare FAIL and a process title on the home page

**After:** Plain statement of the finding, names for the arms, the ten shapes, a picture of each verdict

**Documented reason:** A new reader could not tell what the project does or what it found. The wording is generated from the stored results.

<a id="c36"></a>

## C36 - Bootstrap calculation

- Kind: change (eval)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Our bootstrap runs one matrix product per damage level. Can we combine them into one product per block with the same random draws, and how do we confirm every number stays the same?

**Answer** 
Yes. Stack the per-cluster confusion counts for all levels into one sparse matrix of shape (levels × k × k, clusters), and do one product with each block's multinomial weights. Keep the block size and the draw call unchanged, so the random weights are identical. One detail matters for exact equality. NumPy's floating-point sums depend on memory layout, so make the per-class scores C-contiguous before taking the mean over levels. Otherwise the last bit of a result can change. The code in `src/stage5_eval/stats.py` carries that comment. To confirm nothing changed, compare the delta, interval, drops, standard error and p-values from the old loop and the new product on the same named generator. Then run the Stage 5 tests and a clean-clone rehearsal, which reproduced +9.20, CI [8.89, 9.53] and every table. No before/after timing is recorded, so the speed gain is not measured.

**Before:** One matrix product per damage level

**After:** One combined product per block, with the same random draws

**Documented reason:** Removes repeated work without changing any number.

<a id="c41"></a>

## C41 - Iteration 3 report section and dashboard results

- Kind: change (deploy)
- LLM: opus_medium_5.5 (assisted, proposed by 40248536)

** prompt**

> The report and dashboard stop at iteration 2 and four arms. Plan a report section and dashboard update that lead with the sealed iteration 3 result, show arm P and the sealed robustness results, all drawn from the recorded tables.

**Answer** 
Build Section L the same way as Section K. A generator (`src/stage6_report/iteration3.py`) reads the Stage 5 status, the iteration 3 winners and the iteration log, and writes the `\Ithree*` macros and tables, so no number is typed by hand. It also spells digits out in macro names (see F27). Open Section L with the verdict: the five-arm table, the pre-registered primary with its interval, the strict-pass flag and the sealed read count, then the Holm-corrected secondaries and the clean and earlier-set results. Move the log, failure and change tables to the end. On the dashboard, add P once to the shared arm list. Lead the evaluation page with the damaged fresh holdout 2 result and move the reused test split and first holdout into a context table. Let the robustness page switch between the sealed holdout and the validation check. Check it with `tests/stage6/test_iteration3.py` (macros come from the artifacts, missing inputs show a dash) and the report's traceability check, then read the numbers on the pages against `results/phase2_snapshot/status5.json`: +9.20, CI [8.89, 9.53], clean +0.64, CI [0.19, 1.07], 92 of 92 reads.

**Before:** The report and dashboard stopped at iteration 2 and four arms

**After:** Report Section L leads with the sealed result, and the dashboard shows arm P and the sealed robustness results

**Documented reason:** The verdict has to be readable where people look for it, drawn from the recorded tables.

<a id="c42"></a>

## C42 - Clean-clone rehearsal

- Kind: change (eval)
- LLM: none (40297573)

** prompt**

> Our results were only produced in the working folder. How do we rehearse on a fresh clone to show that all seven stages pass and reproduce the verdict and every table from the committed code alone, and what differences are acceptable?

**Answer** 
Clone the repository into a new folder, set up the pinned environment and run the full pipeline from there, with nothing copied from the working folder. Inputs that are deliberately committed, such as the frozen tuning winners, are restored by the runner itself (see F16). Then compare the outputs with the main run: every stage status, the Stage 5 verdict and interval, each robustness figure, every validation score and every results table. Differences are acceptable only where a value identifies the run rather than the result, which means run IDs, timestamps and absolute folder paths. Any other difference means the result depends on something that is not committed. The recorded rehearsal passed all seven stages and reproduced the verdict, every robustness figure, all 40 validation scores and every results table, apart from run IDs and folder paths (`docs/crisp_dm/iteration_log.json`). Its first attempt exposed the missing tuning result (F16). No chat export exists for this entry. The exact command sequence is not in this entry's record.

**Before:** Results had only been produced in the working folder

**After:** A fresh clone passed all seven stages and reproduced the verdict, every robustness figure, all 40 validation scores and every results table, apart from run IDs and folder paths

**Documented reason:** It shows the result depends on the committed code and recipe, not on leftovers in one folder.

<a id="c43"></a>

## C43 - Main finding shows every model

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40297573 + 40248536)

** prompt**

> Our main finding chart only plots Full mix against Real only. How do we show every model against Real only on one axis, mark the tested comparison, and handle a model with no interval?

**Answer** 
Plot each model's gain over Real only on damaged images as one row on a shared linear axis, with the 0 line and the required +1 line. Put the pre-registered Full mix row first, labelled "(tested)" and in full colour, and mute the others. Take B vs A0 and A1 vs A0 with their intervals from the Holm-corrected secondary family. Synthetic pretraining (P) was descriptive, so no bootstrap was run for it. Show its point difference with no whisker and the text "no range", and never invent an interval. Add a note saying that the test and the +1 target apply only to Full mix. The sealed values (`results/phase2_snapshot/status5.json`) are Full mix +9.20 [8.89, 9.53], Real + synthetic +7.52 [7.18, 7.89] and Real + augmented +6.98 [6.64, 7.33]. For P, 84.25 against 75.63 damaged macro-F1 gives +8.62 with no range. Gemini proposed this design, and `tests/studio/test_verdict_rows.py` checks the ordering, P's missing interval, and that older records list no other rows.

**Before:** The chart plotted Full mix against Real only and nothing else

**After:** Full mix, Synthetic pretraining, Real + synthetic and Real + augmented on one axis, each against Real only, with Full mix marked as the tested one

**Documented reason:** A reader could not see how the other models compared. Synthetic pretraining has no line because it was descriptive and no interval was calculated.

<a id="c44"></a>

## C44 - CRISP-DM cycle slider

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40297573)

** prompt**

> Our CRISP-DM wheel only shows the latest state and hides iteration 3's trip back. Design a slider that walks iterations 1 to 3 and shows each iteration's frozen result, its route back and what each step found.

**Answer** 
Add a slider from 1 to 3 with a clickable tick for each iteration. Keep the six forward arrows around the wheel. For stop n, draw the trips back for iterations 1 to n, with earlier trips faded and the current trip highlighted. Put the iteration's frozen result in the centre: iteration 1 B vs A1 -0.36 (fail), iteration 2 A2 vs A0 +0.06 (fail), iteration 3 A2 vs A0 +9.20 (pass). Show a short finding on each step and open the full text in a panel when the step is clicked. Two refinements came out of testing Gemini's draft. Each stop has to read its own frozen record, through `iteration_results()` in `studio/data/lights.py`, not one live status file. And the full findings were cut off inside the small SVG boxes, so the boxes got short captions with the full text moved to the panel, steps with no finding are dimmed, and a keyboard-friendly list sits beside the wheel. Check by walking all three stops and comparing the results with `results/phase2_snapshot/iter1_status.json`, `iter2_status.json` and `status5.json`. A test checks that each iteration reports its own result.

**Before:** One static wheel of the latest state, missing iteration 3's trip back

**After:** A slider walks iterations 1 to 3. Each stop shows that iteration's frozen result, its route back and what each step found

**Documented reason:** The wheel hid how the project moved from one question to the next.

<a id="c45"></a>

## C45 - Per-class chart readability

- Kind: change (deploy)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> On our per-class chart, dots with close scores hide each other and a fifth score column runs off the chart. Should we use a log scale, or spread close dots into lanes on a linear axis? Propose a layout that keeps distances honest.

**Answer** 
Keep the linear axis and spread close dots into lanes. A log scale stretches only one end of the axis, so the same 1-point gap would look different in different rows. The collision is a layout problem, not a scale problem. Sort each row's dots by score, and move a dot into the next lane, alternating above and below, when it would land too close to a dot already placed. Only the rows that need lanes grow taller. Add a note that vertical position carries no meaning, shown only when some row used a lane. Give each model its own value column and compute the chart width from the last column, so a fifth column fits. Put each row's best score on a pill in that model's colour. A zoomed axis is fine if its start is stated. The Evaluation chart starts at the lowest score rounded down to a multiple of 5, and the validation-by-seed chart reuses the layout zoomed to its own scores. Opus recommended this, and it is in `studio/web/js/svg/charts.js` (`dodge`, `scoreRows`). Check it on the five-arm data. No separate measurement is recorded.

**Before:** Dots with close scores hid each other, and a fifth score column ran off the chart

**After:** Close dots spread into lanes on the same linear axis, and the chart widens to fit every column. The validation chart by seed uses the same layout, with its axis zoomed to the scores. The winning score in each row sits on a pill in that model's colour

**Documented reason:** A log scale would stretch only one end of the axis and distort distances, while lanes keep the axis honest.

<a id="c46"></a>

## C46 - Animate button on Augmentation and Synthetic generator

- Kind: change (deploy)
- LLM: both (reviewed, proposed by 40211352)

** prompt**

> Review this Animate feature for the Augmentation and Synthetic generator pages: every enabled slider moves in small random steps with one random draw, and lines run from the original image to each augmented copy. Is it clear and correct, and what would you change?

**Answer** 
The idea is sound, and the most important choice is already right: keep the random draw fixed while the sliders move, so every change on screen comes from the settings and not from a new draw. Changes worth making: keep each lo/hi pair ordered while it moves, because the server rejects a crossed pair ("scale_lo must not exceed scale_hi" in `schemas.py`); bounce off the slider limits; stop when the user drags a slider; skip ticks while the tab is hidden; switch the label between Animate and Stop with `aria-pressed`; and avoid letting stale previews overwrite newer ones. For the lines, add space between tile rows so they do not cross tiles, redraw them on resize, and hide them from screen readers. Don't add a speed slider or per-slider toggles. Opus and Gemini both reviewed it, and the recorded widget does these things (`studio/web/js/widgets/controls.js`, `fan-lines.js`, 700 ms interval, ordered pairs kept by `keepOrdered`). On the static site, previews come from saved snapshots, so check that the button still works there. No measurement of its effect is recorded.

**Before:** Sliders only moved by hand

**After:** Animate walks every enabled slider in small random steps with the same random draw, until stopped. On Augmentation, directed lines run from the original image to every augmented copy, with more space between rows

**Documented reason:** It shows how the images respond to the settings.

<a id="c47"></a>

## C47 - Interval chart and table readability

- Kind: change (deploy)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40211352)

** prompt**

> On our interval chart only the small dot and line show a tooltip, numbers float above their dots, and the earlier-sets table has no tooltips. How do we make each row easy to follow and explain itself on hover?

**Answer** 
Fix it in the shared chart components so every page benefits. Shade alternate rows across the full width. Draw a faint dotted guide from the label to the interval or dot. Move the estimate and its range into a right-aligned value column with tabular figures, instead of text floating above the dot. Lay a transparent band over the whole row and attach the tooltip to it, so the label, guide, mark and number all explain themselves. In the earlier-sets table, give each column a tooltip. "Data" says whether the row is the never-read holdout or a test split already read. "95% CI" says in words whether the range stays above zero, stays below it or includes it. "Result" says whether the rule applied. That matters because, for example, +0.64, CI [0.19, 1.07] on clean images and +0.52, CI [-0.24, 1.22] on the reused test split (`docs/crisp_dm/README.md`) are easy to misread. Opus proposed this. It is in `ciChart` and `valueBars` in `studio/web/js/svg/charts.js`, and the Experiments page uses the same components. No measurement is recorded.

**Before:** Only the small dot and line had a tooltip, each row's numbers floated above its dot, and the earlier-sets table had no tooltips

**After:** Rows are shaded with a guide from label to dot and a value column, the whole row shows a tooltip, and every cell of the earlier-sets table explains itself. The dot charts on the experiments page got the same shading and guides

**Documented reason:** Rows were hard to follow across the chart, and labels and values gave no feedback on hover.

<a id="c49"></a>

## C49 - Vote panel with coloured lines

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40253714 + 40304911)

** prompt**

> Our vote panel shows six answers in a grid with nothing tying them to the vote. Design a layout that shows at a glance which models agree and what the vote chose, using colour per label and per model.

**Answer** 
Put the vote in the middle with the five models around it, and draw a line from each model to the vote in the colour of the label that model predicted. Agreement then shows as lines of the same colour, and dissent stands out. Give each class label its own colour, and use a separate colour per model on the model names. Add a tooltip on each name saying what that model trained on. Show a tally such as "k of 5 models picked this", and move "what the model saw" under the drawing pad. Keep the note that the vote is an equal-weight average with no claimed score. This was Gemini's design, and it was carried into the public site's predict panel. Check it at desktop and phone widths in light and dark themes: all six slots (five models and the vote) should update in place, the curves should stay readable where they cross, and no element should stick out of its card. No reader test is recorded.

**Before:** All six answers sat in a grid with nothing tying them to the vote

**After:** The models surround the vote, a line from each takes the colour of its predicted label, and each label has its own colour. Each model name has its own colour and a tooltip saying what it trained on, and what the model saw now sits under the drawing

**Documented reason:** It shows at a glance which models agree and what the vote chose.

<a id="c50"></a>

## C50 - Failure timeline graph

- Kind: change (deploy)
- LLM: none (40253714)

** prompt**

> Our failure timeline is a set of tables and four totals. Design a graph that puts every failure in order, one lane per CRISP-DM step and one band per iteration, with a slider that shows each failure as Situation, Task, Action and Result.

**Answer** 
Read the failures from `docs/crisp_dm/iteration_log.json` in the order they happened. Give each CRISP-DM step that has a failure its own lane and each iteration its own vertical band, and draw each failure as a point whose shape and colour show how it ended (Overcome, Partly, Still open). Link each point to its failure page and give it a tooltip. A slider walks the points in order. For the current point it shows four boxes built from the log fields: Situation is the step plus the failure, Task is finding and dealing with the cause, Action is what was done, and Result is the end state. Generating everything from the log means the graph cannot drift from the record. This is how `studio/web/js/widgets/failure-graph.js` works. Check that every logged failure appears once in the right lane and band. The change entry says 30 failures, but the log now holds 31, so the graph should show F31 too. No chat export exists for this entry.

**Before:** The timeline was a set of tables and four totals

**After:** A graph puts all 30 failures in order, one lane per CRISP-DM step and one band per iteration, with a mark for how each ended. A slider walks the points and shows each as Situation, Task, Action and Result

**Documented reason:** It shows where failures clustered and how the project moved between steps.

<a id="c51"></a>

## C51 - Dashboard updates reach the browser

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40304911)

** prompt**

> After an update, a browser can keep showing an old copy of a dashboard page. How do we make the server ask the browser to check for a newer copy on every load, and open the dashboard only once the server answers?

**Answer** 
Have the static file handler send `Cache-Control: no-cache` on the HTML, JS and CSS it serves. The browser can still keep a copy, but it must check with the server before using it, so an edited page shows on the next load. In the launcher, don't open the browser on a timer. Poll the local server until it answers, then open the dashboard at its localhost address. The recorded fix uses a `FreshStaticFiles` handler, and `scripts/run_studio.bat` polls up to 60 times (about 60 s) before opening `http://localhost:8765`. Gemini proposed it, and the same commit widened pages and added P to the Stage 2 and 3 headers. Check it by reading the response headers, and by editing a page such as the CRISP-DM wheel and confirming the change appears on a normal refresh. Also start the launcher from cold and confirm the page opens only after the server is up. No timing measurement is recorded.

**Before:** A browser could keep showing an old copy of a page after an update

**After:** The server tells the browser to check for a newer copy on every load, and the Stage 2 and 3 headers now name arm P. The launcher opens the dashboard at its localhost address once the server answers. Pages now use the full width of the window

**Documented reason:** An update to the CRISP-DM wheel did not appear until the cached page was replaced.

<a id="c52"></a>

## C52 - Section explaining the models and data

- Kind: change (deploy)
- LLM: opus_medium_5.5 (assisted, proposed by 40256377)

** prompt**

> A new reader cannot tell what our five models are or what their training images mean. Write a home page section with a real, an augmented and a generated example, and one card per model with what it tests and its batch make-up.

**Answer** 
Define the three kinds of training image first, then the five models as mixes of them. Part 1 is one row of three tiles for the same class: a real standardised drawing, that drawing after the default Stage 2 augmentation, and a Stage 3 generated shape. Give each kind a fixed colour, and add buttons for the next class and another example so it is clearly not one cherry-picked image. Part 2 opens with "all five models share one network and differ only in what they trained on". Then comes one card per model with its plain name and code, one line on what it tests, and a stacked bar of its batch make-up in the three image colours. Read the counts from the recipes the server computes and the `configs/models/` files rather than typing them. Opus gives, for a batch of 256: B 0/213/43, A2 105/120/31, and P after pretraining 0/256/0. P needs two bars, because it pretrains on synthetic images first, and the epoch ranges should be labelled from the data. Keep the section below the headline finding. It is in `studio/web/js/widgets/models-explainer.js`. No measurement is recorded.

**Before:** The five model names and the kinds of training image were never defined in one place

**After:** The home page shows a real, an augmented and a computer-generated example of a shape, and a card per model with what it tests and the make-up of its batches

**Documented reason:** A new reader could not tell what the models were or what their training data meant.

<a id="c54"></a>

## C54 - Screen review fixes

- Kind: change (deploy)
- LLM: opus_medium_5.5 (assisted, proposed by 40304911)

** prompt**

> Review every screen of our dashboard for misleading headlines, low contrast, long pages, colliding labels and small touch targets. List the problems and the fixes, most important first.

**Answer** 
Order them by harm. Anything that misleads comes before anything that is merely hard to read.
1. The headline gives the A2 vs A0 gain without saying it was measured on damaged images. Say "on damaged images" and give the clean result: +9.20, CI [8.89, 9.53] damaged against +0.64, CI [0.19, 1.07] clean (`results/phase2_snapshot/status5.json`). Fix it once in the shared sentence builder (`finding()` in `studio/web/js/plain.js`), then search for any other bare 9.20.
2. The Business page blends the iterations. Separate them, each with its own question, comparison and image condition.
3. The home page is too long. Replace the full lists with summaries that link to their pages, and fold each finding after its first sentence.
4. Model names and batch text are faint. Raise their contrast in both light and dark themes.
5. Chart labels collide. Rotate wide labels and anchor the end labels inward rather than truncating them.
6. Phone touch targets are small. Raise controls to about 44 px under the 620 px breakpoint.
Opus gave this order and it was applied. The only recorded measurement is that the home page became "about half as long" (`docs/crisp_dm/iteration_log.json`).

**Before:** A review of every screen found misleading headlines, faint model names, very long pages and colliding labels

**After:** The headline says the gain is on damaged images and gives the clean result, the Business page separates the iterations, the home page is about half as long, findings fold after their first sentence, model names and batch text pass contrast, chart labels no longer collide, and phone touch targets are larger

**Documented reason:** Readers should be able to trust and read the results on every screen.

<a id="c55"></a>

## C55 - One explanation block per pipeline stage

- Kind: change (deploy)
- LLM: both (reviewed, proposed by 40248536)

** prompt**

> Each stage page of our dashboard shows its tools and tables in its own way and most never state the stage's point. Propose one explanation block every stage opens with (job, inputs, what it does, outputs, key finding, checks), read from stored results. Then review the other model's version.

**Answer** 
Use one shared widget, not seven copies. It renders the job (one sentence), a three-step flow (Goes in → What it does → Comes out), the key finding, and "How we know it worked", with Previous and Next links. Stage 6 links on to the live drawing page. Two rules make it trustworthy. The key finding must be computed from stored results, never typed. And each check badge must come from the stage's stored status and tell "Passed" and "Failed" apart from "Recorded" (a number stored without a pass rule), so that nothing is overstated. Reviews of both versions added three changes: move the key results higher on Data freeze, Training and Evaluation; show a real drawing beside a generated one on Synthetic generator; and keep the block short enough that the first interactive tool stays visible. It is in `studio/web/js/widgets/stage-brief.js` (`stageBrief`, `stageNav`), and all seven pages from `stage0.js` to `stage6.js` use it. Check that every badge matches the `status*.json` files and that a failed check shows as failed. No reader measurement is recorded.

**Before:** Each stage page showed its tools and tables in its own way, and most never stated the stage's point

**After:** Every stage opens with the same block: its job, what goes in, what it does, what comes out, the key finding and the checks that show it worked, read from stored results, with links to the previous and next stage. Key results moved higher on Data freeze, Training and Evaluation, and Synthetic generator shows a real drawing beside a generated one

**Documented reason:** Each stage should explain itself clearly to a reader new to the project.

<a id="c56"></a>

## C56 - Final audit on 2026-11-10

- Kind: change (deploy)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Audit the whole project before any public deployment: tests, guards, stage status and caches, the test access log, the shipped model, the README, and the Stage 7 publishing gates. Report what passes and what is still open.

**Answer** 
Run the checks from the cheapest mechanical ones to the gates that need a person, and record the evidence for each.
1. Full test suite: every test passes.
2. Both guards: both pass.
3. Stage status: all seven stages are `passed`, and a rerun is served from cache. A stage that reruns is itself a finding.
4. Test access log: it should equal 13 + 52 + 92 = 157 reads, with nothing after the sealed run.
5. Shipped model: compare its hash with the A2 export.
6. README: check it against what the studio offers. It still called the "All models vote" option future work.
7. Stage 7 gates.
The recorded outcome (`docs/crisp_dm/iteration_log.json`) is that all 535 tests and both guards pass, all seven stages are passed and cached, the log is unchanged at 157 reads, and the shipped model is the A2 export byte for byte. The README was fixed. G1 (work complete) and G2 (metrics pass: +9.20, CI [8.89, 9.53]) hold. G3 (a license for the team's code and weights) and G4 (the user's written approval to publish) were open at that point, because neither can be inferred from files. So the verdict was "complete, not yet publishable".

**Before:** The work had not been checked as a whole since the last screen review, and the README still listed the All models vote option as future work

**After:** All 535 tests and both guards pass, all seven stages are passed and cached, the test access log is unchanged at 157 reads, and the shipped model is the A2 export byte for byte. The README now says the vote option exists. Stage 7 gates G1 and G2 hold; G3 (a license for the team's code and weights) and G4 (the user's written approval to publish) are still open

**Documented reason:** The solution should be confirmed complete before any public deployment.

<a id="c57"></a>

## C57 - Files that should never have been tracked purged from history

- Kind: change (deploy)
- LLM: gemini_4_neon (proposed)

** prompt**

> Some files that our ignore rules and project rules exclude are tracked in Git history, including local notes and unused images. How do we remove them from every commit on every branch and tag, keep them on disk, and check that all remaining commits still pass the commit guard?

**Answer** 
Copy the files somewhere outside the repository first, then rewrite history. A path filter over all refs (every branch and every tag) removes the files from every commit and drops the commits that become empty. A message and content rewrite can fix the lines that refer to local working notes. The files stay on disk as untracked copies, and new `.gitignore` rules stop them being added again. After the rewrite, run the commit guard's message, identity and content checks over every remaining commit, and run the test suite. Any branch that was already pushed needs a force push, and other clones must be re-cloned. The recorded purge (`docs/crisp_dm/iteration_log.json`) kept the removed files under `ignore/purged_files/`, added rules for `plan_issues.md` and the backup folder, dropped four commits, and left every remaining commit passing all three guard checks. Gemini planned it. The exact rewrite tool and commands are not recorded in this entry.

**Before:** Two local working notes, the to-do list and nine planning notes under ignore/, and the CPU-run backup folder's .gitkeep were tracked although the ignore rules or project rules exclude them, and so was the local triage file plan_issues.md. One note quoted the attribution text the commit guard bans. Seven early research and setup notes (docs/setup.md, docs/goal.md, reports/ and research_notes/) and 18 unused images and source files (15 sample images, two unused banner and icon images, and a Paint project file) were also tracked, and a few lines referred to local working notes

**After:** On 2026-11-10 they were removed from every commit on every branch and tag and kept on disk untracked, with .gitignore rules for plan_issues.md and the backup folder. The removed notes and images are kept locally under ignore/purged_files/, and the lines that referred to local working notes were reworded in every commit. The four commits that touched only these files were dropped. All remaining commits pass the commit guard's message, identity and content checks

**Documented reason:** Nothing outside the ignore and project rules should be published if the branches are pushed.

<a id="d02"></a>

## D02 - Deploy the project online: export the five models to ONNX, research the Vercel documentation, and publish a frozen static site with live, interactive inference (draw a shape, all five models and their vote predict it) and an interactive six-part slide presentation

- Kind: decision (Stage 7)
- LLM: both (implemented)

** prompt**

> We want to publish the project online as a frozen static site: export the five models to ONNX, run them in the visitor's browser with ONNX Runtime Web on Vercel, let a visitor draw a shape and see all five models and their vote, and add a slide presentation. Plan it and check browser results against Python.

**Answer** 
Build the public site in its own repository from a frozen snapshot, with no server. Vercel serves static files only, with no build or install step and a strict Content-Security-Policy. Pin ONNX Runtime Web locally, so no CDN is needed, and hash every file. Export all five arms to ONNX as self-contained files, and score them plus the equal-weight vote in the browser. The step most likely to go wrong is preprocessing. Port `standardize.py` exactly, matching Pillow's resampling and the median and morphology steps, rather than using a canvas resize, which silently changes predictions. Put the presentation in six parts, one per presenter, with charts drawn from the snapshot. To verify, test preprocessing parity on fixtures byte for byte. In headless Chromium, check that browser logits are within 1e-4 of Python `onnxruntime` and that no outside or `/api` requests are made. Then check the live URL byte for byte against the frozen hashes. The record shows 502 preprocessing fixtures matched, logits within 1e-4, and the site public at https://shapesense-ten.vercel.app since 2026-11-11 (`ShapeSense_Deployed`). G3 and G4 were open at the 2026-11-10 audit (C56). They were closed before release: the deployed repository's README says both were met before publication on 2026-11-11, and it ships an MIT `LICENSE` for the code and `LICENSE-MODELS.md` (CC BY 4.0) for the weights. That matches Gemini's account.

**Documented outcome:** Models run in the visitor's browser through ONNX Runtime Web, with no server; browser results checked against Python (logits within 1e-4). Public at https://shapesense-ten.vercel.app since 2026-11-11; presentation live 2026-11-16; Predict button live 2026-11-17. Separate repository: ShapeSense_Deployed.
