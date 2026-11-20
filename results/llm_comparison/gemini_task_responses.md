# Gemini 4 Neon task responses

Written for: the project team, reviewing what Gemini 4 Neon was credited with in the commit log.

**How this was built.** Each row of [commit_tasks.csv](commit_tasks.csv) that names `gemini_4_neon` (in `proposed_by`, `caught_by`, `llm_involved` or `owner`) is one task. Tasks that already have a response in [opus_task_responses.md](opus_task_responses.md) are skipped, so this file covers only the missing ones. The **claim** is the row's attribution plus the cited entries in [attribution_worksheet.csv](attribution_worksheet.csv). The **task** is the commit title and type. The answer is written as Gemini 4 Neon would respond, grounded only in those recorded fields. No git commands were run. Simulation note: these are reconstructions from the records, not a live Gemini run.

**Skipped because already covered in the Opus file:** T06, T09, T12, T24, T34, T35, T48, T62, T67, T68, T69, T78, T84, and the Deployed entries T86 to T90.

**Scope.** 28 tasks. Rows with no claim fields beyond the attribution are answered from the title, stage and type only, and say so.

---

## Pipeline build (Gemini proposed or built)

### T02 - chore: add environment pins, import contracts and README
- **Claim:** proposed by Gemini 4 Neon. **Type:** maintenance. **Stage:** deployment (not a course stage).
- **Answer:** Proposed environment pins and import contracts so the project installs the same way on any machine. No results involved. Attribution is for the proposal, not the code.

### T05 - feat(stage0): add pipeline runner, hash cache and migration check
- **Claim:** proposed by Gemini 4 Neon. **Type:** built. **Stage:** infrastructure (supports testing).
- **Answer:** Proposed the runner and hash cache that later stage caching depends on. Stage 6 caching (F26) builds on this design. No result changes.

### T07 - feat(stage2): add class-safe augmentation and QA sheet
- **Claim:** built by a team member, assisted by Gemini 4 Neon. **Stage:** 2_data_preparation/transformation.
- **Answer:** Gemini assisted with the augmentation code and the QA sheet. The augmentation ranges were later found to be hand-set guesses (F06, C04), so the design was revised in iteration 2.

### T08 - feat(stage3): add synthetic shape generator with enforced margins
- **Claim:** proposed by Gemini 4 Neon, built with two members. **Stage:** 2_data_preparation/transformation.
- **Answer:** Proposed the generator and the enforced margins. The margin logic was later corrected because augmented shapes came out about 6 px too small (F08, C05). The proposal stands, the first margin value did not.

### T10 - feat(stage5): add power check, one-read test evaluation and verdict
- **Claim:** proposed by Gemini 4 Neon, built with a team member. **Stage:** 4_testing.
- **Answer:** Proposed the one-read test rule and the power check. This is the rule that later made the test split unusable for further choices (F13), so the rule itself held and the reuse was documented.

### T13 - assets icon and banners
- **Claim:** proposed by Gemini 4 Neon, with two team members. **Type:** other.
- **Answer:** Visual assets only. No results involved.

### T16 - docs(readme): explain the Stage 3 throughput gate needs an idle CPU
- **Claim:** assisted by Gemini 4 Neon, owned by a team member. **Type:** documented.
- **Answer:** Gemini helped write the note that the throughput gate needs an idle CPU. This was later shown to matter, since other programs were closed part way through a timing run (C39).

### T17 - feat: implement stage 4 training and stage 5 evaluation pipelines with tests
- **Claim:** proposed by Gemini 4 Neon. **Type:** built. **Stage:** 3_modeling.
- **Answer:** Proposed the stage 4 and stage 5 pipelines with tests. The first CNN was too shallow to see a whole shape (F17), fixed later in C09. Core proposal stands.

### T18 - feat(stage4): pin the GPU device and test the hold-out and device paths
- **Claim:** proposed by Gemini 4 Neon. Worksheet: F02, N01, D04.
- **Answer:** Proposed pinning `train.device: cuda` so a run fails rather than silently training on the CPU (N01). This is the fix that made later GPU runs trustworthy.

### T22 - fix(stage4): mark held-out runs so seed disagreement skips them
- **Claim:** proposed by Gemini 4 Neon, with two members. **Type:** solved (not in log).
- **Answer:** Proposed marking held-out runs so the seed-disagreement check does not treat them as errors. Fix to the checking logic only.

### T23 - chore(config): note the GPU Decision 7 winner in a comment
- **Claim:** proposed by Gemini 4 Neon, with a member. **Type:** maintenance. Worksheet: D04.
- **Answer:** A comment in the config noting the winner. Documentation of a decision, no result change.

### T29 - feat(studio): match the drawing pad to the theme
- **Claim:** proposed by Gemini 4 Neon, with a member. **Stage:** deployment.
- **Answer:** Interface change so the drawing pad follows the light or dark theme. No results involved.

### T33 - fix(studio): tolerate a server without the iteration log
- **Claim:** proposed by Gemini 4 Neon. **Type:** solved (not in log).
- **Answer:** The dashboard no longer breaks when the iteration log is missing. Robustness fix.

### T38 - chore(config): freeze the iteration 2 winners from the validation search
- **Claim:** proposed by Gemini 4 Neon, with two members, mediated by the team. Worksheet: F06, F07, C03, C04, C08, C11, C12.
- **Answer:** Proposed freezing the winners after the validation search. The search itself is the fix for F06 (hand-set ranges). The winners were chosen on validation only, so the freeze respects the test split rule.

### T39 - feat(report): keep iteration 1 frozen and add a generated iteration 2 report
- **Claim:** proposed by Gemini 4 Neon, with a member. **Stage:** deployment.
- **Answer:** Proposed keeping iteration 1 frozen while generating iteration 2. This is the design behind F31 and C41, where the reports read each iteration's own frozen record.

### T44 - feat(crisp-dm): record every failure and change by step, with a validation check
- **Claim:** mediated by the team, Gemini 4 Neon proposed the record. Worksheet: C17.
- **Answer:** Gemini proposed the step-by-step record. C17 is the robustness check that the record describes: clean accuracy does not show which model survives damage. Descriptive only, changes no verdict.

### T47 - docs(iteration-3): pre-register the robustness test and seal a second holdout
- **Claim:** proposed by Gemini 4 Neon, with two members, assisted. Worksheet: C23, C24, C28, F18.
- **Answer:** Proposed sealing a second holdout and pre-registering the robustness test. C23 changed the primary comparison to A2 vs A0 averaged over 23 damage levels on never-read holdout 2. F18 was a time limit that killed the second build, rebuilt with no limit.

### T49 - feat(stage4): add equal-real, data-fraction and synthetic-pretraining options
- **Claim:** proposed by Gemini 4 Neon, with two members. Worksheet: C25, C27.
- **Answer:** Proposed the extra training options: an arm P (pretrain on synthetic, then fine-tune on real) and scarcity options. Reported descriptively, so the test verdict is not affected.

### T50 - feat(stage4): search per arm with grouped CV and the pre-registered budget
- **Claim:** assisted by Gemini 4 Neon, built by a member. Worksheet: C26.
- **Answer:** Gemini assisted with the search design. The top five settings per arm are re-scored by grouped 3-fold CV (C26), because one validation split can favour a setting by chance.

### T51 - feat(studio): add a frozen Iteration 2 results page
- **Claim:** proposed by Gemini 4 Neon. **Type:** built.
- **Answer:** Proposed a frozen results page for iteration 2 so later iterations cannot change it. Matches the freeze approach in T46 and T73.

### T53 - docs(stage7): define the frozen public dashboard as the final stage
- **Claim:** proposed by Gemini 4 Neon. **Type:** documented. Worksheet: D02.
- **Answer:** Proposed making the frozen public dashboard the last stage, which is how the deployed site is organised.

### T55 - docs: add the CRISP-DM record and bring the living docs up to date
- **Claim:** assisted by Gemini 4 Neon, owned by a member. **Stage:** all stages.
- **Answer:** Gemini helped bring the living docs in line with the record. Documentation only.

### T59 - feat(stage4): prepare batches on seven CPU processes
- **Claim:** proposed by Gemini 4 Neon, with three members. Worksheet: F21, C30, N02.
- **Answer:** Proposed building batches on seven CPU processes. F21: an epoch fell from about 20 seconds to between 2 and 6 seconds, with identical validation scores at different process counts. C30 notes the batches differ from the earlier validation stream, which the record states.

### T63 - chore(studio): keep the saved drawings as informal feedback
- **Claim:** proposed by Gemini 4 Neon. **Type:** maintenance.
- **Answer:** Saves user drawings as informal feedback. Keep in mind these are not part of any evaluated dataset.

### T65 - fix(stage6): keep iteration evidence macros valid and distinct
- **Claim:** assisted by Gemini 4 Neon, owned by a member. Worksheet: F27.
- **Answer:** F27: report macro names broke for arm A2 and collided for hold-out runs. Digits are now spelled out and hold-out runs get their own names. Existing macro names did not change.

### T66 - feat(studio): explain the project and its findings in plain language
- **Claim:** proposed by Gemini 4 Neon. Worksheet: C33.
- **Answer:** C33: a new reader could not tell what the project does. The home page now states the finding in plain words, and the wording is generated from stored results.

### T72 - docs(iteration-3): record the pre-registered verdict
- **Claim:** assisted by Gemini 4 Neon, owned by a member. Worksheet: C23.
- **Answer:** Records the verdict on the pre-registered comparison (C23). Documentation of a fixed rule.

### T74 - fix(iteration-3): remove a duplicate arm and lead Section L with the result
- **Claim:** proposed by Gemini 4 Neon, assisted by a member. Worksheet: F29, C41.
- **Answer:** F29: the dashboard listed arm P twice. Removed, and every page was checked in a browser. C41: Section L leads with the sealed result.

---

## Summary

- **Gemini-proposed and built:** T05, T08, T10, T17, T18, T33, T51, T53, T59, T66, T74. These are the most direct attributions.
- **Assisted or mediated:** T07, T16, T38, T44, T47, T50, T55, T65, T72. The record marks these as assistance, not authorship.
- **Not verified here:** no git commands were run and no code was re-read. Each answer rests on the CSV and worksheet fields only.
