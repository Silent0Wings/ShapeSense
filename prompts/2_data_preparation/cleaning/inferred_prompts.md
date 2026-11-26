##  — `prompts: 2_data_preparation/cleaning`



## F01 - Most Quick, Draw! diamonds were not rhombi.

- Iteration: Iteration 1
- LLM: opus_medium_5.5 (inspected, proposed by 40256377)
- State: Overcome
- CRISP-DM step: Data Understanding · Pipeline stage: 1 · Data freeze

**Prompt**
> Here is a review sheet of Quick, Draw! drawings labeled 'diamond'. Do they match our class definition of a diamond (a rhombus, four equal sides, not a square)? If most do not, should we drop, relabel or keep them, and how do we do that without touching the test split?

**Answer** 
No, most of them do not match. On the review sheets only about 20-30% are clear rhombi; the rest are gemstones with a faceted crown (5-6 outer vertices), cones, shields, triangles or scribbles (`claude_opus/03_f01-quickdraw-diamond-review.md`). That is harmful label noise, because drawings that look like pentagons, hexagons or triangles are labelled diamond and blur those boundaries too. The validation numbers confirm it: A1_0 recalls only 59% of the 76 Quick, Draw! diamonds, calls 16 of them triangle, against 95% recall on the 150 kaggle_reevald diamonds (same file, `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`).
- **Recommendation: drop all 500 by a written rule**, not by hand review. Keeping only clear rhombi would need about an hour of independent human review, and keeping them all leaves known noise in train and test. The cost is that diamond becomes a render-only class, which goes in the limitations next to pentagon and ellipse.
- **Without touching test:** make the decision from validation diagnostics only, apply the rule in Stage 1 before the split (`exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml`, applied by `src/stage1_freeze/exclusions.py`, which raises an error if a pair matches no row), re-freeze the split, and retrain every model so no run from the old split is reused.
- **Check:** the new split should be 12,405 / 2,819 / 2,776 with the leakage checks passing, and the test split should show no read before the re-freeze. This is what the repo records was done.

**Recommended (summary, from the exchange):** Opus agreed most were not rhombi (about 20-30% clear rhombi on two sheets) and called it harmful label noise. It gave three options (drop all by rule, human review keeping clear rhombi, keep as is) and recommended dropping all. After the user asked whether the models could learn the class, it measured Quick, Draw! diamond recall on validation (59% for A1_0, 16 of 76 called triangle). Real chat: `claude_opus/03_f01-quickdraw-diamond-review.md`.

**Documented cause:** They were gems, cones, shields or scribbles, which contradicts the class definition.

**Documented outcome:** Excluded all of them by rule before any test read (500 drawings), re-froze the split and retrained every model.

## Why this finding matters 

- **This is the first real data-quality finding.** It's not a hypothetical; it's a concrete, measurable problem (500 mislabeled drawings).
- **Why it matters for the shortcut:** mislabeled data is a form of noise that can hurt the classifier. If 70-80% of `diamond` images are actually gems/cones/shields, the model can't learn "diamond" from them.
- **Why it matters for the definition:** the class definition (S07) says a diamond is a rhombus with no 90° angles. If most QuickDraw "diamonds" are gems, they don't match.
- **Why it matters for the pipeline:** this is the kind of finding that justifies the whole cleaning step. Without it, the model would train on noise.

## The three options Opus gave 

| Option | What it does | Pros | Cons | Verdict |
|---|---|---|---|---|
| Drop all by rule | Exclude all 500 QuickDraw diamonds | Simple, deterministic, no manual work | Loses 500 images | **Adopt** |
| Human review keeping clear rhombi | Manually review and keep only clear rhombi | Preserves some data | Slow, subjective, error-prone | Reject |
| Keep as is | Keep all 500, accept the noise | No work | 70-80% noise, hurts classifier | Reject |

- **Why "drop all by rule" is best:** it's simple, deterministic, and avoids the subjectivity of manual review.
- **Why "human review" is rejected:** it's slow and error-prone, and the 20-30% clear rhombi aren't worth the effort.
- **Why "keep as is" is rejected:** 70-80% noise is too much; it would hurt the classifier.

## The recall measurement 

- **QuickDraw diamond recall on validation: 59% for A1_0** (16 of 76 called triangle).
- **Why this matters:** it shows the model was already confused by the noise. 59% recall means 41% of QuickDraw diamonds were misclassified (mostly as triangle).
- **Why "16 of 76 called triangle":** this is a specific, measurable confusion pattern. The model was calling diamonds "triangles", which suggests the gem/cone/shield shapes were being confused with triangles.
- **Why this justifies the exclusion:** if the model can't learn "diamond" from the noise, excluding it is the right call.

## The exclusion and re-freeze 

- **Excluded all 500 by rule** (`exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml`).
- **Before any test read:** this is critical. The exclusion happened before the test split was read, so it doesn't contaminate the evaluation.
- **Re-froze the split:** `12,405 / 2,819 / 2,776` (from `12,761 / 2,890 / 2,849` in Phase 1).
- **Retrained every model:** since the training data changed, all models had to be retrained.

**Why "before any test read" matters:**
- If the exclusion happened after the test split was read, it would be a form of leakage (the exclusion was informed by test performance).
- By excluding before any test read, the decision is clean and unbiased.


## C01 - Quick, Draw! diamonds

- Kind: change (data)
- LLM: both (proposed, proposed by gemini_4_neon)

**Prompt**
> Most Quick, Draw! drawings in our diamond class are gems, cones or shields, not rhombi. Should we exclude them all by a written rule, relabel them, or keep the good ones? How do we apply it before any test read and re-freeze the split without leaking information?

**Answer** 
Exclude them all by a written rule. Relabelling does not work, because a gem or a cone has no correct label in the 10-class taxonomy, and keeping the good ones needs a manual review list (the planned `configs/gemstone_ids.csv`, now marked superseded) that is slow, subjective and harder to reproduce. A source-by-label rule is deterministic and auditable: `exclude_source_labels: [[quickdraw, diamond]]` in `configs/pipeline.yaml`, applied by `apply_source_label_exclusions` in `src/stage1_freeze/exclusions.py`, which fails if the pair matches nothing. To avoid leakage:
1. Base the decision only on the contact sheets and validation diagnostics (`docs/crisp_dm/iteration_1_quickdraw_diamonds.json`), never on test results.
2. Apply the rule in Stage 1 before splitting, so the split is computed on the cleaned rows.
3. Re-freeze the split, rerun the leakage checks, and retrain every model, since all earlier runs saw the old data.
The recorded result is 500 drawings removed and a split of 12,405 / 2,819 / 2,776. The repo records no macro F1 measured after the exclusion that isolates its effect (`gemini_4_neon/01_C01_quick-draw-diamonds.md`).

**Before:** Included in the diamond class

**After:** All excluded by rule (500 drawings), split re-frozen at 12,405 / 2,819 / 2,776

**Documented reason:** Most were gems, cones or shields, not rhombi.

## Why this change matters 

- **This is the fix for F01.** It's the concrete action taken in response to the finding.
- **Why "both" LLMs proposed it:** this is a genuine two-LLM collaboration. Gemini proposed the rule, Opus inspected and confirmed.
- **Why "before any test read" matters:** it ensures the exclusion is unbiased.
- **Why "re-freeze the split" matters:** the split has to be regenerated after the exclusion, since the data changed.

## The rule-based exclusion 

- **`exclude_source_labels: [[quickdraw, diamond]]`** in `configs/pipeline.yaml`.
- **Why a rule, not a manual list:** a rule is deterministic, reproducible, and auditable. A manual list would be error-prone.
- **Why this is the same pattern as I01's `exclude_source_labels`:** it's a consistent mechanism for excluding contaminated `(source, label)` pairs.
- **Why this is fail-closed:** if the rule matches zero rows, it raises an error (per I01's `apply_source_label_exclusions`).

## The re-freeze 

- **`12,405 / 2,819 / 2,776`** (from `12,761 / 2,890 / 2,849` in Phase 1).
- **Why the counts changed:** 500 QuickDraw diamonds were removed, so the total went from 18,500 to 18,000, and the split counts shifted accordingly.
- **Why this is the same pattern as I04's atomic freeze:** the re-freeze is atomic and fail-closed, ensuring no partial manifests.

## Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| S07 (class definitions) | F01/C01 | The diamond definition (rhombus, no 90° angles) is what F01 checks against |
| I01 (source capping) | F01/C01 | The `exclude_source_labels` mechanism is from I01 |
| I04 (fail-closed freeze) | F01/C01 | The re-freeze is atomic and fail-closed |
| I05 (FD checks) | F01/C01 | The 6 FDs validate the schema after the exclusion |
| A01 (noise bands) | F01/C01 | The `diamond` test count (150) is affected by the exclusion |

- **Why this matters:** F01/C01 is the first real data-quality finding and fix, and it builds on the class definitions (S07), the exclusion mechanism (I01), the fail-closed freeze (I04), the FD checks (I05), and the noise bands (A01).

## Notes on the log

- **This is the first real data-quality finding and fix.** It's a concrete, measurable problem (500 mislabeled drawings) with a concrete, measurable fix (rule-based exclusion + re-freeze).
- **The recall measurement (59%, 16 of 76 called triangle) is informative.** It shows the model was already confused by the noise.
- **The "before any test read" constraint is critical.** It ensures the exclusion is unbiased.
- **The rule-based exclusion is the same pattern as I01.** It's a consistent mechanism for excluding contaminated `(source, label)` pairs.
- **The re-freeze is atomic and fail-closed.** It's the same pattern as I04.
- **Cross-reference to S07, I01, I04, I05, A01:** F01/C01 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.