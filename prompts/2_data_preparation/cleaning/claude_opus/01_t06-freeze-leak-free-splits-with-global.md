
# 2_data_preparation/cleaning - feat(stage1): freeze leak-free splits with global pHash groups 
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T06, commit dd0218b (type: solved)
- Course stage: 2_data_preparation/cleaning / 1_data_integration
- Worksheet entries: F01, F05, C01
- Source: **from repo, not a saved chat.** The task is from the commit list; the response is restated from `results/llm_comparison/attribution_worksheet.csv` (rows F01, F05, C01) and `opus_task_responses.md`. The real Opus exchange on the diamonds is in `03_f01-quickdraw-diamond-review.md`. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt

> Here is a task from our commit log that credits you. Task: T06 - feat(stage1): freeze leak-free splits with global pHash groups. Claim: proposed by Opus 5.5, caught by Gemini 4 Neon and a team member. Worksheet: F01, F05, C01. Using only the recorded evidence, say what you proposed or did, why, and what it changed.

## Response

**Opus proposed grouping near-duplicates with a global perceptual hash so no near-copy crosses a split.** F01 is the key finding: Opus read 100 random Quick, Draw! images and found most "diamonds" were not rhombi (gems, cones, shields). The response was to exclude all 500 by rule before any test read, then re-freeze the split at 12,405 / 2,819 / 2,776. F05 (source leakage) was documented, not removed.

## Why this task matters (augmented)

- **This is the task that ties F01, F05, and C01 together.** It's the concrete implementation that addresses both the diamond noise (F01/C01) and the source leakage (F05).
- **Why "global pHash groups" matters:** it's the fix for the Phase 1 per-source grouping bug (I03). Global grouping ensures no near-duplicate crosses a split.
- **Why "freeze leak-free splits" matters:** it's the goal of the whole Stage 1 data integration. The splits must be leak-free for the evaluation to be valid.
- **Why this is a `solved` task:** it's a concrete, completed piece of work (the global grouping + exclusion + re-freeze).

## The three findings and their resolutions (augmented)

| Finding | What it is | Resolution |
|---|---|---|
| F01 | Most QuickDraw diamonds are not rhombi | Exclude all 500 by rule, re-freeze split |
| F05 | Images reveal which source they came from (91.7% vs 46.7%) | Document, don't remove (LOSO evaluation) |
| C01 | QuickDraw diamonds are gems/cones/shields, not rhombi | Same as F01: exclude by rule |

- **Why F01 and C01 are the same:** C01 is the change (the fix), F01 is the failure (the finding). They're two sides of the same coin.
- **Why F05 is "documented, not removed":** the source leakage can't be removed from these datasets (per I06), so it's documented and handled via LOSO evaluation.
- **Why this is a good pattern:** find the problem (F01/F05), fix what can be fixed (C01), document what can't (F05).

## The global pHash grouping (augmented)

- **`global_groups(phashes, max_hamming=2)`** runs union-find over all 18,000 active pHashes at once.
- **Why global (not per-source):** per-source grouping (the Phase 1 bug) allowed cross-source near-duplicates to straddle train and test. Global grouping fixes this.
- **Why `max_hamming=2`:** it's tight enough to catch cross-source near-duplicates, loose enough to not merge distinct shapes.
- **Why this is the fix for I03:** I03 is the decision to go global; T06 is the implementation.

## The exclusion and re-freeze (augmented)

- **Excluded all 500 QuickDraw diamonds by rule** (`exclude_source_labels: [[quickdraw, diamond]]`).
- **Before any test read:** ensures the exclusion is unbiased.
- **Re-froze the split:** `12,405 / 2,819 / 2,776` (from `12,761 / 2,890 / 2,849` in Phase 1).
- **Retrained every model:** since the training data changed.

## Validation

Checked against commit dd0218b and the linked worksheet entries in `attribution_worksheet.csv`.

## Our decision

- F01: Excluded all of them by rule before any test read (500 drawings), re-froze the split and retrained every model.
- F05: Reported beside the results and checked with runs that hold out a whole source. It cannot be removed from these datasets.
- C01: Most were gems, cones or shields, not rhombi.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why each piece matters

### The global pHash grouping is the architectural fix

| Aspect | Per-source (Phase 1 bug) | Global (T06 fix) |
|---|---|---|
| Leakage | High (cross-source near-dups straddle) | Zero (`no_phash_group_spans: true`) |
| Stratum ratio | Tight | Some drift |
| Verdict | Reject | Adopt |

- **Why global is better:** it eliminates cross-source leakage, which is the whole point.
- **Why some drift is acceptable:** it's a cosmetic issue, not a validity issue.
- **Why this is the fix for I03:** I03 is the decision; T06 is the implementation.

### The exclusion is the data-quality fix

| Aspect | Before | After |
|---|---|---|
| QuickDraw diamonds | 500 (mostly gems/cones/shields) | 0 (all excluded) |
| Total images | 18,500 | 18,000 |
| Split | 12,761 / 2,890 / 2,849 | 12,405 / 2,819 / 2,776 |

- **Why excluding is better:** it removes 500 noisy images that would hurt the classifier.
- **Why "before any test read" matters:** it ensures the exclusion is unbiased.
- **Why the re-freeze matters:** the split has to be regenerated after the exclusion.

### The F05 documentation is the honest response

| Aspect | F05 |
|---|---|
| Source attribution | 91.7% vs 46.7% (45.0-point gap) |
| Can it be removed? | No (per I06) |
| Response | Document + LOSO evaluation |

- **Why documenting is better than trying to remove:** the shortcut can't be removed from these datasets, so documenting it and designing the evaluation around it is the right call.
- **Why LOSO evaluation:** it directly measures whether the model generalises to unseen sources.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | T06 | The diamond definition is what F01 checks against |
| I01 (source capping) | T06 | The `exclude_source_labels` mechanism is from I01 |
| I03 (global grouping) | T06 | T06 is the implementation of I03 |
| I04 (fail-closed freeze) | T06 | The re-freeze is atomic and fail-closed |
| I05 (FD checks) | T06 | The 6 FDs validate the schema after the exclusion |
| I06 (standardization) | T06 | The shortcut is documented, not removed |
| F01 (the finding) | T06 | F01 is the finding; T06 is the fix |
| F05 (the finding) | T06 | F05 is the finding; T06 documents it |
| C01 (the fix) | T06 | C01 is the fix; T06 implements it |
| A01 (noise bands) | T06 | The `diamond` test count (150) is affected by the exclusion |

- **Why this matters:** T06 is the task that ties F01, F05, and C01 together, building on S07, I01, I03, I04, I05, I06, and A01.

## Notes on the log

- **This is the task that ties F01, F05, and C01 together.** It's the concrete implementation that addresses both the diamond noise and the source leakage.
- **The global pHash grouping is the architectural fix.** It eliminates cross-source leakage.
- **The exclusion is the data-quality fix.** It removes 500 noisy images.
- **The F05 documentation is the honest response.** It documents the shortcut rather than trying to remove it.
- **Cross-reference to S07, I01, I03, I04, I05, I06, F01, F05, C01, A01:** T06 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.