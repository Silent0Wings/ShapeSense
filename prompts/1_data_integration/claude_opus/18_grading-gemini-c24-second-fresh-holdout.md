# 1_data_integration - Grading Gemini's C24 answer on the second fresh holdout
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/02_C24_second-fresh-holdout.md](../gemini_4_neon/02_C24_second-fresh-holdout.md)
- Date: 2026-11-21

## Prompt

The request: as Opus, grade the recorded Gemini 4 Neon answer for C24 and save the grade as a prompt file in the matching Claude Opus folder.

The exchange being judged: the user asked whether to build a second sealed holdout for iteration 3, since the test split and the first fresh holdout had both been read, and how to make sure it is never read before the pre-registered test.

This is not a real Gemini reply. The Gemini file says so itself: "No Gemini 4 Neon reply is available." Its source is "recollection" and the transcript could not be found. The Response is a record of the change from the repo, plus sections marked "(augmented)" that explain it. I grade that content as recorded.

## Response

### Grade: C+ (69 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 21 / 25 | Yes to a second holdout, because a split that has been read can no longer give an unbiased verdict. Keep it disjoint from the catalog and both earlier splits, and seal it in code. That is right, and it matches what was built. |
| Read the question correctly | 14 / 20 | It answers the "should we" part. The "how do we make sure it is never read" part gets only the runtime guard. It misses the build-time trick that makes the holdout possible at all: the script rebuilds the first holdout's manifest and checks its hash, so it knows the first holdout's images without opening them. |
| Fit to this project | 14 / 20 | It names the right files, constants and sources. It does not say that the new holdout uses the same three sources as the first, so it cannot test generalisation to new sources. The pre-registration states this limit. |
| Actionable advice | 11 / 20 | It describes a change already made, so there is little advice in it. Much of the text repeats itself ("Why this matters" appears again and again). It suggests no check that the seal held, such as counting logged sealed reads per run. |
| Accuracy of details | 9 / 15 | Most constants are right. Four details are wrong or overstated: see below. |

### What it got right
- `fresh_holdout_2` holds 4,500 images, the same as the first fresh holdout. Both manifests in `configs/splits/` have 4,500 rows.
- `SECOND_PER_GROUP = 300` and `SEED = 20261109` are right. The seed is imported from `src/stage1_freeze/fresh_holdout.py`.
- Quick, Draw! is skipped (`SKIP_SOURCES = ("quickdraw",)`), because all its local drawings are already in the catalog (docstring of `fresh_holdout.py`).
- Near-duplicates are dropped at `phash_hamming_max = 2`, the same value the global grouping uses (`configs/pipeline.yaml`, read in `src/stage1_freeze/run.py`).
- `SEALED_SPLITS` has three entries: test, fresh_holdout and fresh_holdout_2 (`src/common/splits.py`).
- `tests/contracts/test_load_split_guard.py` has 10 test functions.

### What it got wrong or missed
- **When the test split was read:** it says iteration 1 only. `docs/crisp_dm/iteration_3/preregistration.md` says iterations 1 and 2.
- **The size arithmetic:** "3 sources x 10 classes x ~150 per group" is wrong. The manifest has 15 groups of 300: 900 images from github_handdrawn, 1,500 from kaggle_reevald and 2,100 from mendeley_elkorchi (`configs/splits/fresh_holdout_2.csv`).
- **"Refused and logged":** `load_split` raises before it writes to the log. Refused reads are not logged. Only allowed sealed reads are logged (`src/common/splits.py`).
- **Test coverage:** the 10 guard tests all use the `test` split name. None names `fresh_holdout_2`. The same code path protects it, but no test proves that directly. `tests/studio/_audit_sweep.py` does mention the file paths, but I did not check what it asserts.
- **"Never read" status:** the table marks the holdout as never read. That was true on 2026-11-09. `docs/crisp_dm/iteration_log.json` now records the Phase 7 primary test on it (A2 vs A0 +9.20 macro-F1 points, 95% CI [8.89, 9.53]) and "Sealed reads 92 of 92 expected". The file should say its status was as of that date.
- **Loose links:** it calls I04's fail-closed freeze "the same pattern as the sealed-split guard". They are related ideas, not the same mechanism.

### What I would have answered for this project
1. Yes. Both earlier splits have been read, so iteration 3 needs a split nobody has looked at.
2. Build it so you never need to look at the first holdout. Replay the first holdout's seeded walk, check the rebuilt manifest's hash against the stored one, then take the next images in each `(source, label)` group. Drop anything within pHash distance 2 of the catalog or either holdout. This is what `fresh_holdout_2.py` does.
3. Seal it in code: add it to `SEALED_SPLITS`, so only Stage 5 can load it and every allowed read is logged with its run ID.
4. Prove the seal: add a guard test that names `fresh_holdout_2`, and check at the end of the run that logged sealed reads match the expected count, with none from other readers (`reads_outside` in `splits.py`).
5. State the limit in the pre-registration: same three sources, no Quick, Draw!, so it tests unseen images, not unseen sources.

## Validation

- Checked against the Gemini file, `src/stage1_freeze/fresh_holdout_2.py`, `src/stage1_freeze/fresh_holdout.py`, `src/common/splits.py`, `configs/pipeline.yaml`, both holdout manifests in `configs/splits/`, `docs/crisp_dm/iteration_3/preregistration.md`, `docs/crisp_dm/iteration_log.json`, `tests/contracts/test_load_split_guard.py` and the C24 row of `results/llm_comparison/attribution_worksheet.csv`.
- I did not check commit ff1f269 or its date, because I did not run git.
- I did not check what `tests/studio/_audit_sweep.py` asserts about the holdout.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the Gemini file as the record of C24, with this grade beside it. The four detail errors are listed here and the Gemini file is not edited. Adding a guard test that names `fresh_holdout_2` is a proposal for the team.

## Measured effect

None. No change was made.
