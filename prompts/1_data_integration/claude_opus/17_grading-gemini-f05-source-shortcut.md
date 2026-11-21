# 1_data_integration - Grading Gemini's answer on the source shortcut (F05)
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/01_F05_the-images-reveal-which-source-they-came-from.md](../gemini_4_neon/01_F05_the-images-reveal-which-source-they-came-from.md)
- Date: 2026-11-21

## Prompt

> Grade the recorded Gemini 4 Neon answer to F05 and put the grade in the equivalent Opus folder.

The exchange being judged: the user asked whether a classifier can tell which source an image came from, what that means for the shape classifier, and how to measure and report the risk.

This is not a real Gemini reply. The Gemini file says so in its header: the chat was not exported, no transcript exists in the repo, and a Drive search failed. Its Response section restates the repo record, and the sections marked "(augmented)" were written later from repo files. I grade the content as recorded, but it is a reconstruction, not what Gemini said at the time.

## Response

### Grade: B- (72 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 21 / 25 | Yes, a simple classifier can tell the source, and that means the shape model can lean on source style instead of shape. Holding out a whole source is the right test. Weak spot: it says the leak "can't be removed" because "no amount of pixel-level normalisation can erase" it. The repo only says it cannot be removed from these datasets. The stronger claim is not backed by any file. |
| Read the question correctly | 16 / 20 | It answers all three parts: can it, what it means, how to measure and report. It never says what a "large" gap means in practice for the shape classifier, which is the second part of the question. |
| Fit to this project | 13 / 20 | It names the right files, the right numbers and the Hand-Drawn hold-out. But it never uses the hold-out results that the repo already has, so the risk stays a warning rather than a number. Its link from F05 to I03 is wrong: I03 is pHash near-duplicate grouping for the split, not a shortcut fix. |
| Actionable advice | 13 / 20 | "Report it beside the results" and "run leave-one-source-out" are correct but already decided in `stage_1.md` R14. It gives no rule for reading per-class results and no next step beyond what was already planned. |
| Accuracy of details | 9 / 15 | The code details and headline numbers check out. The per-class reading is wrong: it ranks risk by raw accuracy and ignores each class's own majority rate. It also gives an unsourced reason for choosing the Hand-Drawn source. |

### What it got right
- The headline numbers match `results/phase2_snapshot/source_classifier.json`: pooled accuracy 0.91723259762309, majority rate 0.466893039049236, gain 45.03 points, 2,356 validation images, 7 classes checked.
- The method matches `src/stage1_freeze/source_check.py`: 16x16 mean pooling (`POOL_SIDE_PX = 16`), `LogisticRegression(max_iter=1000)`, fit on train and scored on val, classes with fewer than `MIN_SOURCES = 2` sources skipped.
- The three skipped classes (ellipse, pentagon, diamond) match the JSON, and the `[quickdraw, diamond]` exclusion is in `configs/pipeline.yaml`.
- The seven per-class accuracies round correctly from the JSON.
- The decision text matches F05 in `results/phase2_snapshot/iteration_log.json`: report beside the results, check with runs that hold out a whole source, state "Partly".

### What it got wrong or missed
- **Per-class risk is read backwards.** Raw accuracy is not the signal. The gain over each class's own majority rate is. From `source_classifier.json`: triangle 0.839 against 0.256 (about 58 points), square 0.944 against 0.399 (about 55), circle 0.936 against 0.398 (about 54), rectangle 0.833 against 0.500 (about 33), octagon 0.996 against 0.668 (about 33), hexagon 0.987 against 0.665 (about 32), star 0.989 against 0.728 (about 26). So the leak is strongest for triangle, square and circle, which have three or four sources. Octagon and star score high mostly because two sources with one dominant one is an easy baseline. The answer says the risk is highest for octagon and star and lowest for rectangle. That is wrong.
- **The hold-out results already exist and are not used.** `results/phase2_snapshot/per_source.csv` has them. A0 scores 90.2% on Hand-Drawn images when that source is in training (n = 451), and 63.9%, 63.6% and 69.5% over three seeds when it is held out (n = 302). The best arm, A2, scores 71.9%, 72.2% and 71.5%. That drop is the measured cost of the shortcut, and it is the answer to "how do we measure it."
- **I03 is not a follow-up to F05.** The I03 files are about global pHash Hamming-2 grouping so near-duplicates never straddle splits (`configs/pipeline.yaml`, `split.group_by: phash`). It does not stop "source dominance."
- **Why Hand-Drawn is the hold-out.** The answer says it is "the most distinctive source." `stages/stage_1.md` R14 and `shortcut_notice.md` name the Hand-Drawn experiment but give no reason, so this is a guess presented as fact.
- **Which arms must run it.** `shortcut_notice.md` requires hold-out runs for A1 and B. The answer does not say which arms. In the end all five arms ran it (`results/phase2_snapshot/status5.json`), which is more than the notice asked for.
- **Source styles.** "Sketch, render, hand-drawn" is roughly right from `docs/source.md` (Quick, Draw! doodles, two rendered sets, one hand-drawn set), but I did not open the images to check the Kaggle style.

### What I would have answered for this project
1. Yes. On the 7 classes with two or more sources, logistic regression on 16x16 pooled pixels names the source 91.7% of the time, against 46.7% for always guessing the largest source. That is 45 points over the 10-point trigger.
2. It means a high shape score can partly come from source style. The risk is largest where a class has many sources: triangle, square and circle gain about 54 to 58 points over their own baseline.
3. Measure it with the Hand-Drawn hold-out, which is already done. A0 drops from 90.2% on seen Hand-Drawn images to 63.6 to 69.5% when the source is unseen. Note that the two test sets differ in size (451 and 302), so the drop is a rough comparison, not a matched one.
4. Report three things side by side: the shape score, the source-classifier gain, and the hold-out drop per arm. Keep the single-source asterisk on ellipse and pentagon, as the notice requires.

## Validation

- Checked against the Gemini file, `src/stage1_freeze/source_check.py`, `results/phase2_snapshot/source_classifier.json`, `results/phase2_snapshot/shortcut_notice.md`, `results/phase2_snapshot/iteration_log.json` (F05), `results/phase2_snapshot/per_source.csv`, `results/phase2_snapshot/status5.json`, `configs/pipeline.yaml`, `stages/stage_1.md` (R13, R14), `docs/source.md`, and the headers of the Gemini I03 and I06 files.
- The per-class gains are my own subtraction from the JSON values, rounded to whole points.
- I did not check `tests/stage1/test_source_check.py`, the I06 claim in detail, or the images themselves.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep the Gemini file as the record, with this grade beside it. Use the gain over each class's own baseline, not raw accuracy, when the report discusses per-class risk. Cite the hold-out numbers from `per_source.csv` as the measured effect of the shortcut. Fixing the I03 link in the Gemini file is the team's call.

## Measured effect

None. No change was made.
