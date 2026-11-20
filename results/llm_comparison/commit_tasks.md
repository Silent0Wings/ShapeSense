# Commit tasks

Each commit is one task (T01 to T85 in this repository). T86 to T90 cover ShapeSense_Deployed, grouped by category: it solved an issue, faced one, or built, documented or
maintained part of the pipeline. Issues are the failures (F) and changes (C) in
[`attribution_worksheet.csv`](attribution_worksheet.csv). Editable copy: [`commit_tasks.csv`](commit_tasks.csv).

| Task type | Tasks |
|---|---|
| solved | 39 |
| built | 23 |
| documented | 9 |
| maintenance | 6 |
| solved (not in log) | 4 |
| faced (recorded) | 4 |
| other | 2 |
| tested | 2 |
| released | 1 |

| Task | Date | Commit | Title | Type | Course stage | Solved | Faced |
|---|---|---|---|---|---|---|---|
| T01 | 2026-11-07 | `d2e0d0d` | Initial commit | other | setup |  |  |
| T02 | 2026-11-08 | `5524668` | chore: add environment pins, import contracts and README | maintenance | deployment (not a course stage) |  |  |
| T03 | 2026-11-08 | `ce53e03` | feat(common): add validated config, status, split guard and hashing | built | infrastructure (supports testing) |  |  |
| T04 | 2026-11-08 | `982c2f4` | refactor: move Phase 1 scripts into src/stage1_freeze | maintenance | 1_data_integration |  |  |
| T05 | 2026-11-08 | `6af8b0b` | feat(stage0): add pipeline runner, hash cache and migration check | built | infrastructure (supports testing) |  |  |
| T06 | 2026-11-08 | `dd0218b` | feat(stage1): freeze leak-free splits with global pHash groups | solved | 2_data_preparation/cleaning / 1_data_integration | F01 F05 C01 |  |
| T07 | 2026-11-08 | `c9f5ce3` | feat(stage2): add class-safe augmentation and QA sheet | built | 2_data_preparation/transformation |  |  |
| T08 | 2026-11-08 | `6e3be2f` | feat(stage3): add synthetic shape generator with enforced margins | built | 2_data_preparation/transformation |  |  |
| T09 | 2026-11-08 | `62c5fe8` | feat(stage4): add loader, baselines, CNN, tuning and seeded sweep | solved | 3_modeling | F17 C09 D03 |  |
| T10 | 2026-11-08 | `8f16f26` | feat(stage5): add power check, one-read test evaluation and verdict | built | 4_testing |  |  |
| T11 | 2026-11-08 | `6e633e7` | feat(stage6): add report build, traceability, export, dashboard and demo | built | deployment (not a course stage) | D02 |  |
| T12 | 2026-11-08 | `85209ed` | docs: update reports and record CRISP-DM iteration 1 | solved | 2_data_preparation/cleaning | F01 C01 |  |
| T13 | 2026-11-08 | `240ef2f` | assets icon and banners | other | deployment (not a course stage) |  |  |
| T14 | 2026-11-08 | `ba563ff` | docs: add pipeline banner image to README | documented | deployment (not a course stage) |  |  |
| T15 | 2026-11-08 | `431cd98` | chore(config): note the Decision 7 tuning winner in a comment | maintenance | 3_modeling |  |  |
| T16 | 2026-11-08 | `61cdf30` | docs(readme): explain the Stage 3 throughput gate needs an idle CPU | documented | deployment (not a course stage) |  |  |
| T17 | 2026-11-08 | `69b9265` | feat: implement stage 4 training and stage 5 evaluation pipelines with tests | built | 3_modeling |  |  |
| T18 | 2026-11-08 | `a71b5e1` | feat(stage4): pin the GPU device and test the hold-out and device paths | solved | 3_modeling | F02 N01 D04 |  |
| T19 | 2026-11-08 | `e10169d` | fix: close the robustness items before the final Stage 4 rerun | solved | 3_modeling | N02 |  |
| T20 | 2026-11-08 | `a77ebe7` | chore(config): run three trainings at once on the 8 GB GPU | solved | 3_modeling | F03 C14 |  |
| T21 | 2026-11-08 | `45f7fe0` | chore(config): train two runs at once after a VRAM stall | solved | 3_modeling | F03 C14 |  |
| T22 | 2026-11-08 | `817dbc8` | fix(stage4): mark held-out runs so seed disagreement skips them | solved (not in log) | 3_modeling |  |  |
| T23 | 2026-11-08 | `52f6e64` | chore(config): note the GPU Decision 7 winner in a comment | maintenance | 3_modeling | D04 |  |
| T24 | 2026-11-08 | `8984a50` | docs(report): correct the Phase 2 report and add the LOSO and GPU statements | solved | 3_modeling | F02 F17 C09 D03 D04 |  |
| T25 | 2026-11-08 | `ed7f55a` | docs(readme): say the committed config needs a CUDA GPU | documented | 3_modeling | D04 |  |
| T26 | 2026-11-08 | `7ca99e8` | feat(studio): add the local server for the interactive dashboard | built | deployment (not a course stage) |  |  |
| T27 | 2026-11-09 | `3cdd983` | feat(studio): add the interactive CRISP-DM dashboard pages | built | deployment (not a course stage) |  |  |
| T28 | 2026-11-09 | `b50f6e5` | fix(studio): keep the draw panels from jumping | solved (not in log) | deployment (not a course stage) |  |  |
| T29 | 2026-11-09 | `07ef679` | feat(studio): match the drawing pad to the theme | built | deployment (not a course stage) |  |  |
| T30 | 2026-11-09 | `faeb101` | feat(studio): live slider updates, label badges, themed images and tooltips | built | deployment (not a course stage) |  |  |
| T31 | 2026-11-09 | `cb769a7` | feat(studio): make the per-class F1 chart easier to read | built | deployment (not a course stage) |  |  |
| T32 | 2026-11-09 | `d5c6e2d` | feat(studio): record CRISP-DM findings per step, opening iteration 2 | faced (recorded) | 4_testing |  | F04 |
| T33 | 2026-11-09 | `30808f3` | fix(studio): tolerate a server without the iteration log | solved (not in log) | deployment (not a course stage) |  |  |
| T34 | 2026-11-09 | `7f356d6` | docs(crisp-dm): pre-register iteration 2 and add a fresh holdout | solved | 4_testing / 3_modeling / 1_data_integration | F06 F13 C02 C15 C16 |  |
| T35 | 2026-11-09 | `87711f3` | feat(iteration-2): fix the transform, add arm A2, tuning and the fresh holdout | solved | 2_data_preparation/transformation / 3_modeling / 4_testing | F06 F07 F08 F09 C03 C04 C05 C06 C08 C10 C11 C12 C16 |  |
| T36 | 2026-11-09 | `8456bb1` | feat(stage5): show ablation runs in the metrics table | built | 4_testing |  |  |
| T37 | 2026-11-09 | `321b7ea` | docs(crisp-dm): record the polarity experiment | faced (recorded) | 3_modeling |  | F12 |
| T38 | 2026-11-09 | `5acfb7c` | chore(config): freeze the iteration 2 winners from the validation search | solved | 2_data_preparation/transformation / 3_modeling | F06 F07 C03 C04 C08 C11 C12 |  |
| T39 | 2026-11-09 | `a474930` | feat(report): keep iteration 1 frozen and add a generated iteration 2 part | built | deployment (not a course stage) |  |  |
| T40 | 2026-11-09 | `cf79298` | docs(crisp-dm): keep iteration 1 data for the dashboard and log iteration 2 results | faced (recorded) | 4_testing |  | F14 |
| T41 | 2026-11-09 | `4882086` | fix(report): keep the findings table inside the frame | solved (not in log) | deployment (not a course stage) |  |  |
| T42 | 2026-11-09 | `22faa35` | feat(studio): show iteration 2, arm A2, the fresh holdout and a frozen iteration 1 page | solved | deployment (not a course stage) | F15 C19 |  |
| T43 | 2026-11-09 | `3a5a3b3` | chore(iteration-2): close the iteration and restore frozen winners in a clean clone | solved | deployment (not a course stage) | F16 |  |
| T44 | 2026-11-09 | `0f8a702` | feat(crisp-dm): record every failure and change by step, with a validation robustness check | solved | 4_testing | C17 |  |
| T45 | 2026-11-09 | `8fb6c8f` | chore: stop tracking compiled test caches added by mistake | maintenance | infrastructure (supports testing) |  |  |
| T46 | 2026-11-09 | `d12a48e` | chore(iteration-3): freeze the iteration 2 report inputs and evidence | solved | deployment (not a course stage) | F28 |  |
| T47 | 2026-11-09 | `ff1f269` | docs(iteration-3): pre-register the robustness test and seal a second fresh holdout | solved | 1_data_integration / 4_testing | C23 C24 C28 | F18 |
| T48 | 2026-11-09 | `4c7cb90` | fix(stage5): repair the statistics and checks raised by the outside reviews | solved | 4_testing | C20 C21 C22 C28 |  |
| T49 | 2026-11-09 | `1f2f15d` | feat(stage4): add equal-real, data-fraction and synthetic-pretraining options with grouped folds | solved | 3_modeling | C25 C27 |  |
| T50 | 2026-11-09 | `686fcc9` | feat(stage4): search per arm with grouped CV and the pre-registered budget rule | solved | 3_modeling | C26 |  |
| T51 | 2026-11-09 | `cd48779` | feat(studio): add a frozen Iteration 2 results page | built | deployment (not a course stage) |  |  |
| T52 | 2026-11-09 | `8a8c2de` | feat(studio): add the project icon and a one-click launcher | built | deployment (not a course stage) |  |  |
| T53 | 2026-11-09 | `6f6f4a4` | docs(stage7): define the frozen public dashboard as the final stage | documented | deployment (not a course stage) | D02 |  |
| T54 | 2026-11-09 | `3deea10` | docs: record the equal-weight model vote as the next step | documented | deployment (not a course stage) |  | D01 |
| T55 | 2026-11-09 | `9b298b9` | docs: add the CRISP-DM record and bring the living docs up to date | documented | all stages (CRISP-DM record) |  |  |
| T56 | 2026-11-09 | `002ba8c` | test(studio): forbid fresh holdout 2 and its Stage 5 folders in the sealed-data sweep | tested | deployment (not a course stage) |  |  |
| T57 | 2026-11-09 | `4009d46` | feat(studio): add the iteration 3 experiments page | built | deployment (not a course stage) |  |  |
| T58 | 2026-11-09 | `52e79e1` | feat(iteration-3): record the validation experiments under their CRISP-DM steps | solved | 3_modeling | F11 C29 | F20 |
| T59 | 2026-11-09 | `b3bb15d` | feat(stage4): prepare batches on seven CPU processes | solved | 3_modeling | F21 C30 N02 |  |
| T60 | 2026-11-09 | `cb38be5` | docs(iteration-3): record the speed-up investigation under Modeling | solved | 3_modeling | F21 |  |
| T61 | 2026-11-09 | `4787d55` | docs(iteration-3): register optimization steps and audited candidates | documented | 3_modeling |  |  |
| T62 | 2026-11-09 | `534643d` | perf: optimize the pipeline without changing results | solved | 3_modeling / 1_data_integration / 2_data_preparation/transformation / 4_testing | F23 F24 C31 C34 C35 C36 N02 |  |
| T63 | 2026-11-09 | `79f9c2d` | chore(studio): keep the saved drawings as informal feedback | maintenance | deployment (not a course stage) |  |  |
| T64 | 2026-11-09 | `69dcb02` | feat(iteration-3): reuse repeated search runs and fix two Stage 6 checks | solved | deployment (not a course stage) / 3_modeling | F26 C32 |  |
| T65 | 2026-11-10 | `607a29a` | fix(stage6): keep iteration evidence macros valid and distinct | solved | deployment (not a course stage) | F27 |  |
| T66 | 2026-11-10 | `f6117b3` | feat(studio): explain the project and its findings in plain language | solved | deployment (not a course stage) | C33 |  |
| T67 | 2026-11-10 | `b81b67f` | docs(iteration-3): record the GPU error during the search | faced (recorded) | 3_modeling |  | F22 C37 |
| T68 | 2026-11-10 | `6b310f8` | docs(iteration-3): record the session's bugs, fixes and improvements by CRISP-DM step | solved | 3_modeling | F23 | F19 F20 F25 C37 |
| T69 | 2026-11-10 | `e9fd141` | feat(iteration-3): freeze the search winners and the 60-epoch budget | solved | 3_modeling | F11 C26 C29 C38 C39 |  |
| T70 | 2026-11-10 | `14dc042` | docs(iteration-3): record the final retraining before the sealed read | documented | 3_modeling |  |  |
| T71 | 2026-11-10 | `a5d57b3` | test(stage5): expect hold-out runs for all five arms | tested | 4_testing |  |  |
| T72 | 2026-11-10 | `abd8059` | docs(iteration-3): record the pre-registered verdict | solved | 4_testing | C23 |  |
| T73 | 2026-11-10 | `4091dab` | feat(iteration-3): add report Section L and the final arms to the dashboard | solved | deployment (not a course stage) | F28 C41 |  |
| T74 | 2026-11-10 | `ec84804` | fix(iteration-3): remove a duplicate arm and lead Section L with the result | solved | deployment (not a course stage) | F29 C41 |  |
| T75 | 2026-11-10 | `916e7df` | feat(studio): add the equal-weight All models vote | solved | deployment (not a course stage) | F30 C40 D01 |  |
| T76 | 2026-11-10 | `7f66f1d` | docs(iteration-3): close the iteration | solved | 4_testing | C42 |  |
| T77 | 2026-11-10 | `989b610` | docs(iteration-3): finish the CRISP-DM record | documented | all stages (CRISP-DM record) |  |  |
| T78 | 2026-11-10 | `ff7ddbf` | feat(studio): make the dashboard easier to explore and read | solved | deployment (not a course stage) / 3_modeling | F11 C43 C44 C45 C46 C47 C48 C49 C50 C51 |  |
| T79 | 2026-11-10 | `b39a942` | feat(studio): add the interactive network view and explain the models | solved | 3_modeling / deployment (not a course stage) | C48 C52 |  |
| T80 | 2026-11-10 | `33858dc` | feat(studio): show augmented copies coming from one source image | built | 2_data_preparation/transformation |  |  |
| T81 | 2026-11-10 | `8acbe4a` | feat(configs): add one generated config file per model | solved | 3_modeling | C53 |  |
| T82 | 2026-11-10 | `9d24f95` | fix(studio): correct old failure charts and make results easier to read | solved | deployment (not a course stage) | F31 C54 |  |
| T83 | 2026-11-10 | `7719006` | feat(studio): open every pipeline stage with the same explanation block | solved | deployment (not a course stage) | C55 |  |
| T84 | 2026-11-10 | `f3b3bdb` | docs: record the final audit and the history cleanup | solved | deployment (not a course stage) | C56 C57 |  |
| T85 | 2026-11-19 | `5f65ae9` | feat: initialize project directory structure with documentation and placeholders | built | course deliverables |  |  |
| T86 | 2026-11-11 to 2026-11-17 | ShapeSense_Deployed | Deploy the public site: ONNX models with in-browser inference, Vercel hosting, interactive presentation | built | deployment (not a course stage) | D02 |  |
| T87 | 2026-11-11 to 2026-11-17 | deployed: freezes: 2026-11-11-protected-preview, 2026-11-11-public-1, 2026-11-11-public-2, public-3-phone-layout; commits c671315 610d76c | Releases: protected preview, three public freezes, phone layout, and the 11-16 and 11-17 live freezes | released | deployment (not a course stage) | D02 |  |
| T88 | 2026-11-16 | deployed: 44e3230 b19e25d 6c67833 | Interactive presentation: six parts, one per presenter, covering at least 90% of the source repository, with graphic slides | built | deployment (not a course stage) | D02 |  |
| T89 | 2026-11-16 | deployed: b16b172 863ee07 5fef3bb | Interactive explanations: each stage's design and data handling, animated CRISP-DM wheel, hover help, conclusion dots, stepped sliders and iteration stepper | built | deployment (not a course stage) | D02 |  |
| T90 | 2026-11-17 | deployed: 24f7170 | Live prediction: predict on demand, with a drawing toolbar above the canvas | built | deployment (not a course stage) | D02 |  |
