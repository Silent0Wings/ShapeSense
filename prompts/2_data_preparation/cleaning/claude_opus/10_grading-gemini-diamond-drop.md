# 2_data_preparation/cleaning - Grading Gemini's answer on dropping the non-rhombus diamonds
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/01_diamond-drop.md](../gemini_4_neon/01_diamond-drop.md)
- Date: 2026-11-21

## Prompt

> Grade the Gemini 4 Neon answer in `gemini_4_neon/01_diamond-drop.md` against the repo, with a letter, a score out of 100 and a rubric, and save the grade in the equivalent Opus folder.

The exchange being judged: the team asked Gemini whether the diamond samples that are gems, cones or shields rather than rhombi should be dropped from the dataset. The file recommends dropping all 500 Quick, Draw! diamonds by a rule in `configs/pipeline.yaml`, then re-freezing the split.

This is not a real reply. The Gemini file says so in its own header: "From repo, not a saved chat. No Gemini 4 Neon reply to this question is saved." Its Response section reads "None saved" and restates the outcome from the repo. The rest of the file is labelled "augmented". I grade the content as recorded, as if it were Gemini's answer, but the grade says nothing about what Gemini actually said in the original chat.

## Response

### Grade: C (66 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 17 / 25 | The call is right: drop the whole (quickdraw, diamond) pair by rule, before the split. But the reasons given are generic (fast, deterministic, reproducible). It never ties the decision to the class definition (`configs/taxonomy.yaml`: "rhombus WITHOUT right angles") or to the measured harm, which is the real argument. |
| Read the question correctly | 13 / 20 | The question says "some" diamonds are not rhombi. The answer drops all of them, including the clear rhombi, and dismisses those in one clause ("aren't worth the effort"). It should have said plainly that good drawings are lost too, and why that is acceptable. |
| Fit to this project | 11 / 20 | It misses the main side effect for this project. After the drop, every diamond comes from one source, `kaggle_reevald` (`results/phase2_snapshot/split_stats.csv`: 700 train, 150 val, 150 test). Source and class are now the same thing for diamond, so a model could learn the source's drawing style instead of the shape. The answer also offers "relabel" without saying relabel to what. |
| Actionable advice | 13 / 20 | It names the exact config line and the fail-closed check, which a reader can act on. It proposes no check after the change, such as diamond F1 or per-source recall on validation. |
| Accuracy of details | 12 / 15 | The numbers I could check are right (see Validation). Soft spots: the only con listed for the adopted option is "Loses 500 images". The claim that the mechanism "is from I01" rests on another reconstructed file. The file opens with a stray header ("(final, with even more detail)") and ends by praising itself ("Why this entry is good"), which adds nothing. |

### What it got right
- Exclude by a (source, class) rule, not an image-by-image list. That is what the repo does: `configs/pipeline.yaml` has `exclude_source_labels: - [quickdraw, diamond]`.
- The rule fails closed. `src/stage1_freeze/exclusions.py` raises `ValueError` if a listed pair matches no row.
- The split is re-frozen after the exclusion, and the old and new counts it gives match the repo.
- The exclusion runs before the split, so the test set never holds the excluded images (`exclusions.py` docstring).

### What it got wrong or missed
- **No real reply.** Most of the file restates the repo's outcome and then explains why that outcome is good. It reads as a justification written after the fact, not advice given before it.
- **The evidence.** It never cites the symptom that made the drop worth doing. `docs/crisp_dm/iteration_1_quickdraw_diamonds.json` shows diamond F1 of 80.4 for A0_0 on validation, against 100% recall on the 150 `kaggle_reevald` diamonds for the same run. The inferred prompts file adds 59% Quick, Draw! diamond recall for A1_0, with 16 of 76 called triangle.
- **The single-source diamond class.** After the drop, diamond is the only class here that I saw tied to one source in `split_stats.csv`. That is a confound the report should name. I did not check every class's source mix.
- **No measured effect.** The answer does not say that the repo records no macro F1 that isolates this change (`inferred_prompts.md`, C01).

### What I would have answered for this project
1. Yes, drop them, and drop the whole Quick, Draw! diamond set by rule. The class definition is a rhombus without right angles. Most of these drawings are gems, cones or shields, so they are label noise that also blurs the pentagon, hexagon and triangle boundaries.
2. The cost is real: about 20 to 30% of them were clear rhombi on the review sheets (`claude_opus/03_f01-quickdraw-diamond-review.md`). Keeping only those would need a hand review, which is slow and hard to repeat. The class keeps 1,000 `kaggle_reevald` images, so the loss is acceptable.
3. Put the rule in `configs/pipeline.yaml`, apply it before the split, make it fail if it matches nothing, and re-freeze.
4. Then check two things on validation only: diamond F1 before and after, and whether the model now leans on source style, since diamond has a single source. State that confound in the report.

## Validation

- Checked against the Gemini file and these repo files:
  - `configs/pipeline.yaml`: `exclude_source_labels: - [quickdraw, diamond]`.
  - `src/stage1_freeze/exclusions.py`: raises `ValueError` when a pair matches no row (fail-closed, confirmed).
  - `src/stage1_freeze/leakage.py`: writes train, val and test "atomically as a set" with `os.replace` (atomic freeze, confirmed).
  - `results/llm_comparison/attribution_worksheet.csv`, rows F01 and C01: 500 drawings excluded, split 12,405 / 2,819 / 2,776, proposed by `gemini_4_neon`, attribution source "recollection".
  - `docs/notes/pairs/4_testing.md`: the earlier split 12,761 / 2,890 / 2,849 sums to 18,500, the pool before the 500 were removed.
  - `results/phase2_snapshot/fd_check.json`: 6 functional dependencies, all holding (the "6 FDs" claim, confirmed).
  - `results/phase2_snapshot/noise_bands.csv`: diamond `n_test` 150 (confirmed).
  - `results/phase2_snapshot/split_stats.csv`: diamond rows only for `kaggle_reevald` (700 / 150 / 150).
  - `docs/crisp_dm/iteration_1_quickdraw_diamonds.json`: diamond F1 80.4 for A0_0 on validation.
  - `configs/taxonomy.yaml`: diamond is a "rhombus WITHOUT right angles".
- The 20 to 30% figure comes from `claude_opus/03_f01-quickdraw-diamond-review.md`, where it is an estimate from two review sheets, not a count.
- I could not check the claim that the mechanism came from I01. The only support I found is `1_data_integration/claude_opus/04_I01_schema-harmonization-and-label-mapping.md`, which is itself a reconstruction. I did not run git to see when the rule was added.
- I did not check the 59% recall and 16 of 76 figures in the JSON myself. I read them in `inferred_prompts.md`, which cites the JSON. The A0_0 run in the JSON shows 93.4% Quick, Draw! recall, so the 59% belongs to A1_0, as that file says.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the Gemini file as the record of C01, with this grade beside it, and keep its "not a saved chat" header. The decision itself stands: all 500 Quick, Draw! diamonds stay excluded by rule. Naming the single-source diamond class in the report is my suggestion. Whether to add it is the team's call.

## Measured effect

None. No change was made. The repo records no macro F1 that isolates the effect of the exclusion (`inferred_prompts.md`, C01).
