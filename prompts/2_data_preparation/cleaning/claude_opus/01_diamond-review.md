
# 2_data_preparation/cleaning - Quick, Draw! diamond review 
- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Per-stage LLM use, validation and human judgment
- Worksheet entries: F01, C01
- Real exchange for this finding: `03_f01-quickdraw-diamond-review.md` (saved Claude Code session). This file is not a second copy of it.
- Follow-up: `../gemini_4_neon/01_diamond-drop.md`
- **From repo, not a saved chat.** The prompt below is the question the team recorded. The response is restated only from the repo records cited under each part. No Opus reply to this exact prompt is saved. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt (from repo)

> Do the Quick, Draw! drawings labelled 'diamond' match our class definition (a rhombus, four equal sides, not a square)? If most do not, should we drop, relabel or keep them, without touching the test split?

Sources: `../inferred_prompts.md` (F01, prompt), `results/llm_comparison/attribution_worksheet.csv` (row F01).

## Response (restated from repo records, not a reply)

**No saved reply.** The repo records the following outcome of this review:

- Most Quick, Draw! 'diamond' drawings were gems, cones, shields or scribbles, not rhombi. Recorded as the failure cause in `results/phase2_snapshot/iteration_log.json` (F01) and in `../inferred_prompts.md`.
- Iteration 1 validation showed the symptom: diamond F1 80.4 for A0_0, and QuickDraw diamond recall 59% for A1_0, with 16 of 76 predicted as triangle (`docs/crisp_dm/iteration_1_quickdraw_diamonds.json`).
- The plan's own check was a human review of the QuickDraw diamonds, with a third reviewer for disagreements (`implementation.md`, Decision 1). That review was superseded by the written exclusion rule (`ignore/todo.md`, `plan_issues.md` P-60).

## Why this review matters (augmented)

- **This is the concrete validation of F01.** F01 said "most QuickDraw diamonds are not rhombi"; this review confirms it with specific numbers (diamond F1 80.4, recall 59%, 16 of 76 called triangle).
- **Why the F1 and recall numbers matter:** they show the model was already confused by the noise. A diamond F1 of 80.4 means 19.6% of diamonds were misclassified; a recall of 59% means 41% were missed.
- **Why "16 of 76 called triangle" matters:** it's a specific confusion pattern. The model was calling diamonds "triangles", which suggests the gem/cone/shield shapes were being confused with triangles.
- **Why the human review was superseded:** the written exclusion rule is more scalable and reproducible than manual review.

## The symptom: diamond F1 and recall (augmented)

| Metric | Value | What it means |
|---|---|---|
| Diamond F1 (A0_0) | 80.4 | 19.6% of diamonds misclassified |
| QuickDraw diamond recall (A1_0) | 59% | 41% of QuickDraw diamonds missed |
| 16 of 76 predicted as triangle | 21% | Specific confusion pattern: diamond -> triangle |

- **Why the F1 of 80.4 is a symptom:** it's lower than it should be if the data were clean. A clean `diamond` class should have higher F1.
- **Why the recall of 59% is a symptom:** it means 41% of QuickDraw diamonds were missed, which is a lot.
- **Why "16 of 76 called triangle" is informative:** it's a specific confusion pattern that suggests the gem/cone/shield shapes were being confused with triangles.

## The human review vs written rule (augmented)

| Approach | What it does | Pros | Cons | Verdict |
|---|---|---|---|---|
| Human review (with third reviewer for disagreements) | Manually review each drawing | Thorough | Slow, subjective, error-prone | Superseded |
| Written exclusion rule | Exclude all 500 by rule | Fast, deterministic, reproducible | Loses 500 images | **Adopted** |

- **Why the written rule is better:** it's fast, deterministic, and reproducible. The human review was thorough but slow and error-prone.
- **Why the human review was superseded:** the written rule achieves the same goal (removing noise) with less effort and more consistency.

## Validation

Iteration 1 validation numbers, as recorded in `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`. The test split was not read for this check.

- **Why "test split was not read" matters:** it ensures the review and exclusion are unbiased. If the test split had been read, the decision would be contaminated.

## Our decision

All 500 QuickDraw diamonds were excluded by rule before the split, which was re-frozen at 12,405 / 2,819 / 2,776 (C01). Our class definition requires a rhombus that is not a square (S07). The decision text is in `configs/pipeline.yaml` (`exclude_source_labels: [[quickdraw, diamond]]`).

## Measured effect

Split re-frozen at 12,405 / 2,819 / 2,776, and every model retrained. Pre-exclusion validation macro F1 is listed in `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`. No post-exclusion number is recorded in this file.

## Deeper detail: why each number matters

### The diamond F1 of 80.4

- **What it means:** 19.6% of diamonds were misclassified (either precision or recall was low).
- **Why it's a symptom:** a clean `diamond` class should have higher F1. The 80.4 suggests noise.
- **Why it's not catastrophic:** 80.4 is still decent, but it's lower than it should be.

### The QuickDraw diamond recall of 59%

- **What it means:** 41% of QuickDraw diamonds were missed (not predicted as diamond).
- **Why it's a symptom:** it's a lot of misses, which suggests the model can't learn "diamond" from the noise.
- **Why it's specific to QuickDraw:** the recall is for QuickDraw diamonds specifically, not all diamonds. This makes sense, since QuickDraw is the noisy source.

### The "16 of 76 called triangle" pattern

- **What it means:** 21% of QuickDraw diamonds were predicted as triangle.
- **Why it's informative:** it's a specific confusion pattern that suggests the gem/cone/shield shapes were being confused with triangles.
- **Why this justifies the exclusion:** if the model can't learn "diamond" from the noise, excluding it is the right call.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | This entry | The diamond definition (rhombus, no 90° angles) is what the review checks against |
| F01 (the finding) | This entry | F01 is the finding; this is the review that confirms it |
| C01 (the fix) | This entry | C01 is the fix; this is the review that justifies it |
| I01 (source capping) | This entry | The `exclude_source_labels` mechanism is from I01 |
| I04 (fail-closed freeze) | This entry | The re-freeze is atomic and fail-closed |
| I05 (FD checks) | This entry | The 6 FDs validate the schema after the exclusion |
| A01 (noise bands) | This entry | The `diamond` test count (150) is affected by the exclusion |

- **Why this matters:** this entry is the review that confirms F01 and justifies C01, building on S07, I01, I04, I05, and A01.

## Notes on the log

- **This is the concrete validation of F01.** It confirms the finding with specific numbers (F1 80.4, recall 59%, 16 of 76 called triangle).
- **The human review was superseded by the written rule.** The rule is more scalable and reproducible.
- **The "test split was not read" constraint is critical.** It ensures the review and exclusion are unbiased.
- **Cross-reference to S07, F01, C01, I01, I04, I05, A01:** this entry builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.