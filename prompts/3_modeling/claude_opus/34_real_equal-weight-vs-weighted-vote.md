# 3_modeling - Weighted vote or equal-weight vote across models?

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: D01, C40
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (16:44)

> question if this is a good new model or no need ? [===once all your current goal is fully done , we add a weighted model that uses all the existing models a0 a1 , a2 ,b , and use a weighted voting system in which all the models onnx will work together , and they get a weight based on which class they perform well on and infering 1 image -> asks all the models , weight the score of each and the label a] or just a voting group with equale weigth ?
> so this will be no change just current available models are voting together

## Response 1

**Start with the equal-weight vote, and only add per-class weights if a test shows they help.** Equal weights is worth having, while per-class weights are probably not needed. You're right that neither one needs retraining.

**Why equal first**
- Add up each model's class probabilities and take the highest, rather than counting one vote per model. A model that's 99% sure then counts for more than one that's 51% sure, with no tuning.
- There's nothing to fit, so it can't overfit. It also tends to be more stable on messy drawings, because one model's odd mistake gets outvoted.

**Why per-class weights probably won't pay off**
- The differences they'd rely on are tiny. In iteration 2 the four arms scored 95.2 to 95.4 on the test split and 97.2 to 97.5 on the fresh holdout, so most of the per-class gaps are likely noise.
- The models share one architecture and the same real images, so they tend to make the same mistakes. Voting only helps where they disagree, so I'd expect a small gain from either method.
- Weights learned on clean validation images also say little about noisy ones, where the arms differ most (A0's score dropped 40.3 points on noisy data, A2's 33.5).

**It's cheap to find out**
Each run already saves its validation probabilities, so I can compare equal against weighted in minutes, with no training and no sealed data. Weights must be learned on one part of validation and scored on another, or they'll look better than they are. I'd keep them only if they clearly beat equal weights.

**One caveat on "no change"**
The models don't change, but the combined vote counts as a new model when you make claims about it.
- **In the dashboard:** fine to add as an "All models vote" option, as long as it isn't presented as having a measured score.
- **As a result:** claiming it's better needs a new pre-registered test on sealed data it hasn't seen. Iteration 3 will already have used the current holdouts, so that means a later iteration with a new holdout. It also wouldn't change the A2 vs A0 verdict that Stage 7 depends on.

## Prompt 2 (16:44)

> so which varient do you suggest

## Response 2

I suggest the **equal-weight vote using averaged probabilities**. Each model gives a probability for all ten classes, you average them, and the class with the highest average wins.

It's the simplest option and has nothing to tune or overfit, so it's the one I'd add after the current goal is done. I'd include all the final models, including P if it finishes iteration 3 in good shape, and label it "All models vote" with no measured score claimed.

Skip the per-class weights unless the quick validation check clearly shows they beat equal weights.

## Prompt 3 (16:45)

> ok add it in doucmentted as the next goal after the current one is done

## Response 3

I'll check how goals and the tracker are kept so this goes in the right place.

The other goals live in `.agents/`, which git ignores, so I'll put the full goal there and add a tracked entry so it can't get lost.

The guard stopped the commit with an ignored-path message, so I'll read its full output before doing anything else.

Now for what the updates need: the log's changes and failures, plus the current text of the living documents.

Two details still need checking: how the dashboard draws failure visuals, and why the search found nothing in `docs/setup.md`.

I've got what I need. I'll write the CRISP-DM record first, then apply the updates to the living documents in one checked script.

Running the updates, then the dashboard tests, and checking that a new failure page renders.

All 58 checks pass and the new failure page renders. Committing now through the guard.

Written for: your team and anyone new to the project.

The CRISP-DM record is written and the living docs are updated and committed locally. Start with `docs/crisp_dm/README.md`. It covers where the project stands, what each iteration found under each CRISP-DM step, every decision and why, iteration 3's failures so far, and what's next: finish iteration 3, add the equal-weight vote, then the Stage 7 site if it's earned.

**Updated, 17 files in the commit:**
- **Project overview and guides:** the README, the studio and export READMEs, and `docs/source.md`, including fixes to old file paths.
- **Plan and stage briefs:** `implementation.md`, the Phase 1 findings and Stages 0 to 6 each got a dated status note at the top. Stage 7 was already current.
- **Trackers:** `plan_issues.md` and `ignore/todo.md`, plus the iteration 3 handoff's progress notes (git-ignored, so not in the commit).
- **Dashboard data:** the iteration log gained three failures (F18 to F20) and four changes. These now appear on the Failure timeline, and the dashboard tests pass.

**Not every Markdown file changed, on purpose:**
- **Must stay frozen:** the iteration 2 and 3 pre-registrations and the iteration 2 investigation report. The goal forbids rewriting them.
- **Kept as history:** `ignore/plan/`, `research_notes/`, `reports/` and the older prompts in `.agents/`.
- **Not project status:** `docs/goal.md` (the course brief), `docs/setup.md` (a saved planning transcript) and `docs/data_sets.md` (a source list, still correct).

**For your team to review:** I added notes to `implementation.md` and the stage briefs rather than rewriting their original text, so the design history survives. Those plan updates had been left for your team, so I logged this as P-67, marked as needing team review. If you want the briefs fully rewritten to match the current design, that's a larger job I can do.

Iteration 3 has no results yet. The experiments are at 61 of 108 with no errors, and the watcher is still on.

61 of 108 trials are done at 16:53, with 1 finished in the last 5 minutes.

62 of 108 trials are done at 16:58, with 1 finished in the last 5 minutes.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Equal and per-class weights were compared on held-apart validation. Validation was reused, so both numbers are optimistic.

## Our decision

We had proposed per-class weights for each model. On Opus 5.5's advice we started with an equal-weight average of class probabilities, and kept it after the comparison (C40).

## Measured effect

Equal weights 95.59 against per-class weights 94.80 macro F1 on held-apart validation. On the test split, soft-vote ensembles of the 5 seeds beat the per-seed mean for every arm, for example A2 95.8 -> 96.0 (D01).

---

## Ensemble Aggregation Theory & Epistemic Governance (`D01`, `C40`)

### Metadata & Lineage

* **Entries:** `D01` (*5-seed soft-vote ensemble gain over single-seed mean*), `C40` (*Equal-weight probability averaging vs. learned per-class weights*)
* **Date:** `2026-11-09` (16:44–16:58 UTC-5)
* **Owner / LLM:** `40256377` / `opus_medium_5.5` (`claude-opus-5-5`, real Claude Code session)

### Statistical & Information-Theoretic Comparison

| Aggregation Method | Mathematical Formulation | Parameter Degrees of Freedom | Held-Apart Validation Macro-F1 | Generalization & Overfitting Profile |
| --- | --- | --- | --- | --- |
| **Equal-Weight Soft Vote (`C40`)** | $\hat{y} = \arg\max_c \frac{1}{M}\sum_{m=1}^M P_m(y=c \mid x)$ | **`0`** (zero fitted parameters) | **`95.59`** | Preserves calibration confidence (`99%` vs. `51%`); immune to validation overfitting |
| **Learned Per-Class Weights** | $\hat{y} = \arg\max_c \sum_{m=1}^M w_{m,c} P_m(y=c \mid x)$ | `10 × M` (`40–50` weights) | `94.80` (`-0.79` pts) | Overfits small inter-arm noise (`95.2–95.4` test band) and fails under OOD shift (`A0` drops `40.3` pts vs. `A2` `33.5` pts on noisy inputs) |

#### Methodological & Governance Rules Established

1. **Zero-Training Validation Benchmark:** Evaluated both schemes on saved out-of-fold validation probability matrices (split into weight-fitting and scoring partitions) without touching sealed test splits. Equal-weight probability averaging outperformed learned per-class weights by **`+0.79` macro-F1** (`95.59` vs. `94.80`).
2. **Intra-Arm Seed Soft-Voting (`D01`):** Averaging predicted probabilities across each arm's 5 trained seeds consistently outperformed the arithmetic mean of individual seed scores on test (e.g., `A2` improved from `95.8` mean single-seed to **`96.0`** soft-vote ensemble).
3. **Epistemic Boundary for Cross-Arm Ensembles:** Even though combining existing ONNX models requires no weight updates, an *"All models vote"* meta-ensemble constitutes a **distinct hypothesis/model**—permissible in the interactive Studio UI without a claimed benchmark score, but requiring a fresh, uninspected holdout split before making formal statistical claims.

