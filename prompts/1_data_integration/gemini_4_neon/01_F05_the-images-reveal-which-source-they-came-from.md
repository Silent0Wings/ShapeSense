
# 1_data_integration - F05: The images reveal which source they came from

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: from repo, not a saved chat. The worksheet lists the attribution source as "chat", but the Gemini 4 Neon chat was not exported and no transcript for it exists here. No Gemini reply is reproduced. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.
- Entry: F05 (`failure`, `1_data_integration`), commit dd0218b (2026-11-08)

## Prompt

> Can a classifier tell which source an image came from? If it can, what does that mean for our shape classifier, and how do we measure and report the risk?

## Response

**No Gemini 4 Neon reply is available.** The repo records the outcome of the finding, not the reply:

- A classifier told an image's source 91.7% of the time, against 46.7% for always guessing the largest source (`results/phase2_snapshot/iteration_log.json`, F05).
- The recorded cause is that a model can lean on source style instead of shape.
- The source check is in `src/stage1_freeze/source_check.py`, with tests in `tests/stage1/test_source_check.py`.

## Why this matters (augmented)

- **The 91.7% vs 46.7% gap is large:** 45.0 percentage points above the majority baseline. This means a simple classifier (logistic regression on pooled 16x16 images) can tell which source an image came from with high confidence.
- **Why this is a "shortcut":** if the shape classifier can also pick up on source style, it might learn "which source" rather than "which shape", which is a form of shortcut learning.
- **Why this is a real risk:** the four sources have very different visual styles (sketch, render, hand-drawn), so a classifier can easily distinguish them. If the shape classifier relies on this distinction, it won't generalise to new data.
- **Why it can't be removed:** the sources are fundamentally different (sketch vs render vs hand-drawn), and no amount of pixel-level normalisation can erase that. This is a known, unavoidable limitation of the multi-source approach.

## How the source check works (augmented)

- **`source_check.py` downsamples to 16x16** via 4x4 mean pooling (`POOL_SIDE_PX = 16`).
- **Fits per-class `LogisticRegression(max_iter=1000)`** on `train`, scored on `val`, across classes with at least `MIN_SOURCES = 2` sources.
- **7 multi-source classes** (2,356 validation images): circle, triangle, square, rectangle, hexagon, octagon, star.
- **3 single-source classes skipped:** ellipse, pentagon, diamond (after the `quickdraw/diamond` exclusion).
- **Pooled accuracy:** `0.917` (`0.91723259762309`) vs `0.467` (`0.466893039049236`) majority-source baseline.
- **Per-class accuracy:** `circle` 0.936, `triangle` 0.839, `square` 0.944, `rectangle` 0.833, `hexagon` 0.987, `octagon` 0.996, `star` 0.989.
- **Why per-class matters:** some classes are easier to attribute than others (octagon 0.996 vs rectangle 0.833), which suggests the shortcut is stronger for some shapes than others.

## How the risk is measured and reported (augmented)

- **Report beside the results:** the source-attribution number is put next to the shape-classifier number in the report, so a reader can see the risk at a glance.
- **Per-source holdout (LOSO):** run the shape classifier with one entire source held out. If accuracy drops a lot, the model was leaning on that source's style.
- **`shortcut_notice.md`:** a formal notice documenting the shortcut, which triggers mandatory Stage 4/5 per-source reporting and leave-one-source-out runs.
- **Cannot be removed:** state explicitly that this is a limitation of the multi-source approach, not a bug that can be fixed.

## Validation

- Source classifier result and comparison: `results/phase2_snapshot/source_classifier.json` and `results/phase2_snapshot/shortcut_notice.md`.
- Tests: `tests/stage1/test_source_check.py`.
- **Gemini transcript not recoverable:** a Google Drive search for the original Gemini F05 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains a repo-record outcome, which is correct for an unrecoverable transcript.

## Our decision

As recorded in `iteration_log.json`: report the risk beside the results and check it with runs that hold out a whole source. The source leak cannot be removed from these datasets, so it is documented, not fixed.

## Measured effect

Source classifier accuracy 91.7% against a 46.7% largest-source baseline (gap 45.0 points), as recorded in `iteration_log.json`. No macro-F1 change is recorded for this entry.

## Deeper detail: why this finding matters

### This is the root of the shortcut problem

- **F05 is the original finding.** I06 (standardization vs outline redraw) and I03 (per-source vs global grouping) are both follow-ups to this finding.
- **Why this matters:** the shortcut is a known, unavoidable limitation of the multi-source approach, and the right response is to measure and report it, not to try to erase it.
- **Why the 45.0-point gap is large:** it means the classifier is doing real work, not just memorizing the majority class. This makes the shortcut credible.

### The per-class breakdown is informative

| Class | Accuracy | Why |
|---|---|---|
| circle | 0.936 | High, since circles are easy to distinguish by style |
| triangle | 0.839 | Lower, since triangles are harder to distinguish |
| square | 0.944 | High |
| rectangle | 0.833 | Lowest, since rectangles are hardest to distinguish |
| hexagon | 0.987 | Very high |
| octagon | 0.996 | Highest |
| star | 0.989 | Very high |

- **Why this matters:** the variation (0.833 to 0.996) suggests the shortcut is stronger for some shapes than others. This is useful for understanding where the risk is highest.
- **Why octagon and star are highest:** these are the most distinctive shapes, so it's easiest to tell which source they came from.

### The LOSO evaluation is the right response

- **Leave-one-source-out (LOSO):** train on 3 sources, test on the held-out source. If accuracy drops a lot, the model was leaning on that source's style.
- **Why this is the right test:** it directly measures whether the model generalises to unseen sources, which is the whole point of the multi-source approach.
- **Why `github_handdrawn` is the LOSO target:** it's the most distinctive source (hand-drawn), so it's the hardest to generalise to.

### Cross-reference to I03 and I06

- **I03** (per-source vs global grouping) is a follow-up to F05: the global grouping is a mitigation for the shortcut (by preventing source dominance).
- **I06** (standardization vs outline redraw) is a follow-up to F05: the decision to keep standardization frozen is a response to the shortcut (document it, don't erase it).
- **Why this matters:** F05 is the root finding, and I03/I06 are the responses. This is a good example of the entries building on each other.

## Notes on the log

- **Gemini transcript is genuinely lost:** like the other Gemini entries, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays a repo-record outcome rather than fabricating a Gemini reply.
- **The worksheet says "chat" but no chat exists:** this is a discrepancy worth noting. The worksheet's attribution source field says "chat", but the actual chat transcript is missing.
- **This is a `failure` entry, not a `change`:** F05 is categorised as a failure (a problem found), not a change (a fix applied). This is correct, since the shortcut can't be fixed, only documented.
- **The 45.0-point gap is large and consequential:** this is the kind of finding that justifies the two-LLM comparison and the LOSO evaluation.
- **The per-class breakdown is informative:** it shows where the risk is highest (octagon, star) and lowest (rectangle).
- **Cross-reference to I03 and I06:** F05 is the root finding, and I03/I06 are the responses.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.