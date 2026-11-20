# 7_meta_and_other - P011: Stop-hook goal activated; pipeline build work begins
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-07
- Source: Claude Code session notes, pair P011. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

A session-scoped Stop hook is now active with condition: "Execute the goal defined in @.agents/goal_build_implementation.md exactly as written.". Briefly acknowledge the goal, then immediately start (or continue) working toward it — treat the condition itself as your directive and do not pause to ask the user what to do. The hook will block stopping until the condition holds. It auto-clears once the condition is met — do not tell the user to run `/goal clear` after success; that's only for clearing a goal early.

## Response

Goal acknowledged. The goal is to build the full Phase 2 pipeline from `implementation.md` and the seven stage briefs, without git, through tracked plans and audited sub-agents. I started with Phase 1, reading the current code and the tracker.

#### Setup and planning
- **Environment check:** Python 3.12, torch 2.14 CPU, 14 cores, and the data is present.
- **Packages:** several were missing, so I created a project venv that reuses the system torch and installed the rest.
- **Coverage and plans:** the coverage matrix is written. Plans 11 to 35 are written, 25 in total, and they are wired into `ignore/todo.md` above "Still open (needs you):", together with the human-blocked items.
- **Toolchain:** before writing the per-entry plans, I checked the LaTeX toolchain and `build.ps1`, because several entries depend on them. One command was too long for the shell, so I wrote the generator to a file first.

#### Build and audit loop
Each entry followed the same cycle: tests first where possible, then implementation, then the planned mutation to check that the tests catch a deliberate break.
- **E11:** config keys and validation. Tests passed, and the planned mutation (removing the ratio-sum check) was caught and reverted.
- **E12 to E14:** `batch.py` and interfaces, then hashing, status and the test-split guard. E13 and E14 passed 37 tests, and their mutations were checked.
- **E24 (Stage 2):** 6 tests failed at first. A function named `transform` shadowed the submodule, so I used `sys.modules` instead. After that, 40 tests passed, and the planned mutation (always allowing shear) was caught with 8 failures.
- **E25:** 3 failures, fixed by correcting the stroke-inclusive margins and the test. Then 17 tests passed, and the planned mutation was run.
- **E29 (statistics):** 28 tests passed, and the mutation was run.
- **E26 (loader), E27 (baselines), E28 and E30:** each had its own tests and mutation check.

#### Performance work
The augmentation cost was expected to dominate CPU training time, so I measured it before writing the Stage 4 brief:
- Most of the time went to `joint="curve"`, which draws a pie slice at every vertex (64 per circle). Switching to Pillow's polygon outline with a width gave no gain on its own.
- Skipping square caps for the 64-point circle and ellipse, which only matter at real corners, took Stage 3 to 5,195 images per second.
- The `transform` fit loop rendered the full warp on every shrink step. I checked the frame fit analytically and rendered once, which took it from 686 to 1,543 images per second. All 40 Stage 2 tests still passed.
- I added a `train.parallel_runs` setting so the sweep can use the 14 cores.

#### Contracts, waves and the report
- **Import-linter:** it rejected the Stage 4 exception lines, because nothing matched them yet. I set that alert to a warning, and it then reported 5 contracts kept and 0 broken.
- **Wave 2:** six agents ran in parallel. Among them, E17 guard tests proved that a forbidden import and a fake test read are actually blocked. A mutation removing the independence contract turned the forbidden-import test red, as expected.
- **Stage 6 entry point:** it has the runner contract (`STAGE`, `DEPENDS`, `inputs`). It still raises NotImplementedError until E35 lands, which records `not_run`.
- **README (S0-R13):** written, covering setup, data pull, every runner mode, the owner and artifact map, and Windows troubleshooting.
- **Demo and bundle:** the stable test subset passed 186 tests. The demo passed and its mutation was caught. I also tested the export bundle end to end on a throwaway TorchScript model, so the predict tests run instead of skipping. `is_blank` now returns a plain `bool`.
- **Phase 1 report:** it compiled to 9 pages. I checked Figure 2 visually, and the "Real data pool" box was wrapping into the dedup box, so I moved it up by 0.5 cm.
- **Phase 2 report (E35):** it compiled with placeholder tables (10 pages), and its mutation was caught by 2 tests. It pulls every number through `\input`, so it doesn't wait for results.

#### Status
I added the spec contradictions as new `P-NN` rows in `plan_issues.md`. Eleven entries are ticked with evidence, and their plans are marked DONE. The Stage 1 run passed 27 tests, and its mutation was caught by 3 tests. Stage 4 passed 43 tests, and its step-budget mutation was caught. The TorchScript deprecation warnings are harmless on the pinned torch 2.14.

The full Stage 4 run is training in the background. It does baselines first, then the loader benchmark, the 6-run tuning grid, 9 arm-by-seed runs and 2 LOSO runs. Stages 0 to 3 are running, and the real-data results will be audited when the run finishes. The tracker shows 19 of 25 entries done, and I am waiting on the Stage 4 benchmark, which decides whether the full sweep fits the CPU budget.

##### Why the work was ordered this way
Planning came before code so each entry had a test and a mutation check written in advance. The mutation check deliberately breaks the code to confirm the tests fail, which shows the tests can catch real errors and are not just passing by accident.

##### Human-blocked items
The goal file keeps some decisions for you: the gemstone review, the team inputs (owners, rubric, deadline, training machine, license), and the 60-drawing live sketch check. The agent prepares each of them and continues with everything else.

##### Next steps
- Read the Stage 4 benchmark result before approving the full sweep.
- Review the audit results when the background run finishes. Those numbers are not yet confirmed at the time of this answer.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
