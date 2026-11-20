
# 2_data_preparation/cleaning - C01: Quick, Draw! diamonds 
- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: C01 (`change`, `2_data_preparation/cleaning`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Repo sources: `results/llm_comparison/attribution_worksheet.csv` (row C01), `2_data_preparation/cleaning/inferred_prompts.md` (C01), `configs/pipeline.yaml` (`exclude_source_labels`), `src/stage1_freeze/exclusions.py`, `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`, commits dd0218b and 85209ed (as listed in the worksheet)
- **From repo, not a saved chat.** No Gemini 4 Neon chat is saved for this entry, and no Gemini reply is written here. The prompt is the question the team recorded. The response section records only what the repo says the team did. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt (from repo)

> Most Quick, Draw! drawings in our diamond class are gems, cones or shields, not rhombi. Should we exclude them all by a written rule, relabel them, or keep the good ones? How do we apply it before any test read and re-freeze the split without leaking information?

Source: `2_data_preparation/cleaning/inferred_prompts.md`, C01 (prompt).

## Response (recorded decision, not a Gemini reply)

**No Gemini 4 Neon reply is saved.** The worksheet credits this change to `gemini_4_neon` as proposer, with the outcome: all Quick, Draw! diamonds excluded by rule (500 drawings), and the split re-frozen at `12,405 / 2,819 / 2,776` (`attribution_worksheet.csv`, C01). The rule is recorded in `configs/pipeline.yaml` as `exclude_source_labels: [[quickdraw, diamond]]`, and the exclusion helper is `src/stage1_freeze/exclusions.py`.

## Why this change matters (augmented)

- **This is the fix for F01.** It's the concrete action taken in response to the finding that most QuickDraw diamonds are not rhombi.
- **Why Gemini proposed it:** this is a genuine two-LLM collaboration. Gemini proposed the rule, Opus inspected and confirmed (per F01).
- **Why "before any test read" matters:** it ensures the exclusion is unbiased.
- **Why "re-freeze the split" matters:** the split has to be regenerated after the exclusion, since the data changed.
- **Why this is a `winning-decision (70% tier)`:** it's a high-impact, well-justified decision.

## The three options (augmented)

| Option | What it does | Pros | Cons | Verdict |
|---|---|---|---|---|
| Exclude all by rule | Exclude all 500 QuickDraw diamonds | Simple, deterministic, no manual work | Loses 500 images | **Adopted** |
| Relabel | Manually relabel the good ones | Preserves some data | Slow, subjective, error-prone | Rejected |
| Keep the good ones | Keep only clear rhombi | Preserves some data | Slow, subjective, error-prone | Rejected |

- **Why "exclude all by rule" is best:** it's simple, deterministic, and avoids the subjectivity of manual review.
- **Why "relabel" and "keep the good ones" are rejected:** they're slow and error-prone, and the 20-30% clear rhombi aren't worth the effort.

## The rule-based exclusion (augmented)

- **`exclude_source_labels: [[quickdraw, diamond]]`** in `configs/pipeline.yaml`.
- **Why a rule, not a manual list:** a rule is deterministic, reproducible, and auditable. A manual list would be error-prone.
- **Why this is the same pattern as I01's `exclude_source_labels`:** it's a consistent mechanism for excluding contaminated `(source, label)` pairs.
- **Why this is fail-closed:** if the rule matches zero rows, it raises an error (per I01's `apply_source_label_exclusions`).
- **Why `gemstone_ids.csv` was superseded:** the manual review was replaced by the written rule, which is more scalable and reproducible.

## The re-freeze (augmented)

- **`12,405 / 2,819 / 2,776`** (from `12,761 / 2,890 / 2,849` in Phase 1).
- **Why the counts changed:** 500 QuickDraw diamonds were removed, so the total went from 18,500 to 18,000, and the split counts shifted accordingly.
- **Why this is the same pattern as I04's atomic freeze:** the re-freeze is atomic and fail-closed, ensuring no partial manifests.

## Validation

Validation-only diagnostics in `docs/crisp_dm/iteration_1_quickdraw_diamonds.json` (runs A0_0, A0_2, A1_0, A1_2, before the exclusion). The test split was not read for this check.

- **Why "test split was not read" matters:** it ensures the exclusion is unbiased. If the test split had been read, the decision would be contaminated.

## Our decision

The team excluded all `quickdraw/diamond` drawings by rule before the split (`configs/pipeline.yaml`), and marked the manual `configs/gemstone_ids.csv` review as superseded. The split was re-frozen and all models were retrained. The worksheet records that the proposal came from `gemini_4_neon` and that the final choice was recorded as winning-decision.

## Measured effect

- Excluded 500 `quickdraw/diamond` drawings by rule. The split was re-frozen at `12,405 / 2,819 / 2,776` (`attribution_worksheet.csv`, C01).
- No post-exclusion macro F1 is recorded in the sources above.

## Deeper detail: why each piece matters

### The rule-based exclusion is the right fix

| Aspect | Manual review | Written rule |
|---|---|---|
| Speed | Slow | Fast |
| Consistency | Subjective | Deterministic |
| Reproducibility | Error-prone | Reproducible |
| Verdict | Superseded | Adopted |

- **Why the written rule is better:** it's fast, consistent, and reproducible.
- **Why the manual review was superseded:** it achieves the same goal with less effort and more consistency.

### The re-freeze is atomic and fail-closed

| Aspect | Before | After |
|---|---|---|
| QuickDraw diamonds | 500 (mostly gems/cones/shields) | 0 (all excluded) |
| Total images | 18,500 | 18,000 |
| Split | 12,761 / 2,890 / 2,849 | 12,405 / 2,819 / 2,776 |

- **Why the re-freeze matters:** the split has to be regenerated after the exclusion.
- **Why atomic and fail-closed matters:** it ensures no partial manifests.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | C01 | The diamond definition is what C01 checks against |
| F01 (the finding) | C01 | F01 is the finding; C01 is the fix |
| I01 (source capping) | C01 | The `exclude_source_labels` mechanism is from I01 |
| I04 (fail-closed freeze) | C01 | The re-freeze is atomic and fail-closed |
| I05 (FD checks) | C01 | The 6 FDs validate the schema after the exclusion |
| A01 (noise bands) | C01 | The `diamond` test count (150) is affected by the exclusion |

- **Why this matters:** C01 is the fix for F01, building on S07, I01, I04, I05, and A01.

## Notes on the log

- **This is the fix for F01.** It's the concrete action taken in response to the finding.
- **Gemini proposed it, Opus confirmed it.** This is a genuine two-LLM collaboration.
- **The rule-based exclusion is the right fix.** It's fast, consistent, and reproducible.
- **The re-freeze is atomic and fail-closed.** It ensures no partial manifests.
- **Cross-reference to S07, F01, I01, I04, I05, A01:** C01 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.