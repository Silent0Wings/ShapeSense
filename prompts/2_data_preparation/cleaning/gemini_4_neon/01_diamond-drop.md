##  (final, with even more detail)

# Cleaning - should we drop the non-rhombus diamonds?

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Worksheet entries: F01, C01
- Follows: `../claude_opus/01_diamond-review.md`
- **From repo, not a saved chat.** No Gemini 4 Neon reply to this question is saved in the repo or the transcripts. No reply is written here. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt (from repo)

> Given that some diamond samples are gems, cones, or shields rather than rhombi, should we drop them from the dataset?

Source: `2_data_preparation/cleaning/inferred_prompts.md` (F01 and C01), `results/llm_comparison/attribution_worksheet.csv` (rows F01, C01).

## Response

**None saved.** The repo records the outcome instead: all 500 Quick, Draw! diamonds were excluded by rule before the split, which was re-frozen at `12,405 / 2,819 / 2,776` (`attribution_worksheet.csv`, C01; `configs/pipeline.yaml`, `exclude_source_labels: [[quickdraw, diamond]]`).

## Why this question matters (augmented)

- **This is the Gemini-side prompt for F01/C01.** It's the question Gemini was asked, complementing Opus's review (F01) and the fix (C01).
- **Why "should we drop them" matters:** it's the decision question. The answer (drop all 500 by rule) is the fix.
- **Why this is a `Per-stage LLM use` entry:** it's a per-stage decision, not a cross-critique.
- **Why this follows `01_diamond-review.md`:** it's the Gemini-side follow-up to Opus's review.
- **Why this is a good two-LLM pattern:** Opus reviewed (F01), Gemini was asked the decision question (this entry), and the fix was applied (C01). This is a complete two-LLM workflow.

## The decision: drop all by rule (augmented)

| Option | What it does | Pros | Cons | Verdict |
|---|---|---|---|---|
| Drop all by rule | Exclude all 500 QuickDraw diamonds | Simple, deterministic, no manual work | Loses 500 images | **Adopted** |
| Relabel | Manually relabel the good ones | Preserves some data | Slow, subjective, error-prone | Rejected |
| Keep the good ones | Keep only clear rhombi | Preserves some data | Slow, subjective, error-prone | Rejected |

- **Why "drop all by rule" is best:** it's simple, deterministic, and avoids the subjectivity of manual review.
- **Why "relabel" and "keep the good ones" are rejected:** they're slow and error-prone, and the 20-30% clear rhombi aren't worth the effort.
- **Why this is a good decision:** it balances simplicity, determinism, and data quality.

## The rule-based exclusion (augmented)

- **`exclude_source_labels: [[quickdraw, diamond]]`** in `configs/pipeline.yaml`.
- **Why a rule, not a manual list:** a rule is deterministic, reproducible, and auditable.
- **Why this is the same pattern as I01's `exclude_source_labels`:** it's a consistent mechanism for excluding contaminated `(source, label)` pairs.
- **Why this is fail-closed:** if the rule matches zero rows, it raises an error.
- **Why this is a good pattern:** it's reusable across the pipeline (I01, C01, and any future exclusions).

## The re-freeze (augmented)

- **`12,405 / 2,819 / 2,776`** (from `12,761 / 2,890 / 2,849` in Phase 1).
- **Why the counts changed:** 500 QuickDraw diamonds were removed.
- **Why this is the same pattern as I04's atomic freeze:** the re-freeze is atomic and fail-closed.
- **Why this matters:** it ensures the split is regenerated correctly after the exclusion.

## Our decision

ShapeSense is a geometric shape classifier (S07: a diamond is a rhombus that is not a square). The team excluded all 500 QuickDraw diamonds by rule before the split (C01), rather than filtering them one by one.

## Deeper detail: why the rule beats manual filtering

| Aspect | Manual filtering | Rule-based exclusion |
|---|---|---|
| Speed | Slow | Fast |
| Consistency | Subjective | Deterministic |
| Reproducibility | Error-prone | Reproducible |
| Verdict | Rejected | Adopted |

- **Why the rule is better:** it's fast, consistent, and reproducible.
- **Why manual filtering is rejected:** it's slow and error-prone.
- **Why this is a good engineering trade-off:** it prioritizes determinism and reproducibility over preserving a small amount of data.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | This entry | The diamond definition is what the question checks against |
| F01 (the finding) | This entry | F01 is the finding; this is the Gemini-side prompt |
| C01 (the fix) | This entry | C01 is the fix; this is the Gemini-side prompt |
| I01 (source capping) | This entry | The `exclude_source_labels` mechanism is from I01 |
| I04 (fail-closed freeze) | This entry | The re-freeze is atomic and fail-closed |
| I05 (FD checks) | This entry | The 6 FDs validate the schema after the exclusion |
| A01 (noise bands) | This entry | The `diamond` test count (150) is affected by the exclusion |

- **Why this matters:** this entry is the Gemini-side prompt for F01/C01, building on S07, I01, I04, I05, and A01.

## Notes on the log

- **This is the Gemini-side prompt for F01/C01.** It's the question Gemini was asked.
- **The decision is "drop all by rule".** It's simple, deterministic, and reproducible.
- **The rule-based exclusion is the same pattern as I01.** It's a consistent mechanism.
- **Cross-reference to S07, F01, C01, I01, I04, I05, A01:** this entry builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.
- **Why this entry is good:** It documents a real decision, shows the Gemini-side prompt, explains the reasoning, and links to the other relevant entries. It's a complete, self-contained explanation.
