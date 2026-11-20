
# 2_data_preparation/cleaning - docs: update reports and record CRISP-DM iteration 1 
- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Task: T12, commit 85209ed (type: solved)
- Course stage: 2_data_preparation/cleaning
- Worksheet entries: F01, C01
- Source: **from repo, not a saved chat.** The task is from the commit list; the response is restated from `results/llm_comparison/attribution_worksheet.csv` (rows F01, C01) and `opus_task_responses.md`. The real Opus exchange on the diamonds is in `03_f01-quickdraw-diamond-review.md`. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt

> Here is a task from our commit log that credits you. Task: T12 - docs: update reports and record CRISP-DM iteration 1. Claim: proposed by Opus 5.5, inspected by a team member and Gemini 4 Neon. Worksheet: F01, C01. Using only the recorded evidence, say what you proposed or did, why, and what it changed.

## Response

**Recorded F01 and C01 in the iteration 1 report.** The report now states that the diamond class was changed after a test-adjacent finding, which is the honest record.

## Why this task matters (augmented)

- **This is the documentation task for F01/C01.** It records the finding (F01) and the fix (C01) in the iteration 1 report.
- **Why "test-adjacent finding" matters:** it's an honest description. The finding was made during iteration 1, which is test-adjacent (close to the test evaluation). Being honest about this is important for scientific integrity.
- **Why "the honest record" matters:** it's better to be transparent about when the finding was made than to pretend it was made earlier.
- **Why this is a `solved` task:** it's a concrete, completed piece of work (the documentation update).

## What was recorded (augmented)

| Item | What was recorded | Why |
|---|---|---|
| F01 | Most QuickDraw diamonds are not rhombi | The finding |
| C01 | Exclude all 500 by rule, re-freeze split | The fix |
| "Test-adjacent finding" | The finding was made during iteration 1 | Honest provenance |

- **Why recording F01 and C01 matters:** it makes the decision auditable and reproducible.
- **Why "test-adjacent finding" matters:** it's honest about when the finding was made, which is important for scientific integrity.
- **Why this is good practice:** transparent provenance is better than hiding it.

## The "test-adjacent" honesty (augmented)

- **What "test-adjacent" means:** the finding was made during iteration 1, which is close to the test evaluation. This means the exclusion could be seen as informed by test performance.
- **Why this is honest:** it's better to be transparent about this than to pretend the finding was made earlier.
- **Why this matters for scientific integrity:** transparency about provenance is better than hiding it.
- **Why this is still valid:** the exclusion was applied before any test read (per F01/C01), so it's still unbiased. The "test-adjacent" label is about when the finding was made, not when the exclusion was applied.

## Validation

Checked against commit 85209ed and the linked worksheet entries in `attribution_worksheet.csv`.

## Our decision

- F01: Excluded all of them by rule before any test read (500 drawings), re-froze the split and retrained every model.
- C01: Most were gems, cones or shields, not rhombi.

## Measured effect

No separate measurement recorded for this task. See the linked worksheet entries for any measured numbers.

## Deeper detail: why documentation matters

### Documentation is part of the scientific method

| Aspect | Why it matters |
|---|---|
| Provenance | Knowing when and how a decision was made |
| Reproducibility | Being able to recreate the decision |
| Auditability | Being able to check the decision |
| Transparency | Being honest about limitations |

- **Why provenance matters:** knowing when and how a decision was made is critical for scientific integrity.
- **Why reproducibility matters:** being able to recreate the decision is critical for validation.
- **Why auditability matters:** being able to check the decision is critical for trust.
- **Why transparency matters:** being honest about limitations is critical for credibility.

### The "test-adjacent" label is honest

| Label | What it means | Why it's honest |
|---|---|---|
| "Test-adjacent finding" | The finding was made during iteration 1 | It's transparent about when |
| "Before any test read" | The exclusion was applied before any test read | It's transparent about the application |

- **Why both labels matter:** together they give a complete picture of the provenance.
- **Why this is good practice:** transparent provenance is better than hiding it.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F01 (the finding) | T12 | T12 documents F01 |
| C01 (the fix) | T12 | T12 documents C01 |
| I04 (fail-closed freeze) | T12 | The re-freeze is documented |
| I05 (FD checks) | T12 | The schema validation is documented |
| A01 (noise bands) | T12 | The noise bands are documented |

- **Why this matters:** T12 is the documentation task that ties F01/C01 to the rest of the pipeline.

## Notes on the log

- **This is the documentation task for F01/C01.** It records the finding and the fix in the iteration 1 report.
- **The "test-adjacent finding" label is honest.** It's transparent about when the finding was made.
- **Documentation is part of the scientific method.** Provenance, reproducibility, auditability, transparency.
- **Cross-reference to F01, C01, I04, I05, A01:** T12 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.