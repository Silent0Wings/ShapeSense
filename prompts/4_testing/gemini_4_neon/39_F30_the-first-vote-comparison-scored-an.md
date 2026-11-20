# 4_testing - F30: The first vote comparison scored an empty class as zero
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/38_F30_the-first-vote-comparison-scored-an-empty-cl.md](../claude_opus/38_F30_the-first-vote-comparison-scored-an-empty-cl.md)
- Date: 2026-11-10
- Entry: F30 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / opus_medium_5.5 + 40248536
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, scripts/vote_check.py, tests/studio/test_vote.py, results/phase2_snapshot/exp_vote_check.json, commit 916e7df

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** Our first validation comparison between equal-weight and per-class-weight voting scored some classes as zero on a random half of validation, dragging the score down by 10 points. Why is that happening, and how should we split and score so absent classes don't distort the comparison?

## Response
The zero is not a model error. It is an empty class.

**Cause.** You split by near-duplicate group, which is right, because a group split across the halves would leak. But the groups are large, and a random group split pays no attention to class. With some seeds, one half ends up with no image of a class at all. Two things then go wrong:

1. **Scoring.** Macro-F1 over all ten classes gives that class F1 = 0 (no true positives, nothing to recall), and averaging it in costs about 10 points, the size of one class out of ten. The vote did nothing wrong; the denominator did.
2. **Weights.** If the class is absent from the learning half, every arm's F1 there is 0, so its weight is 0 for every arm. That class can then never win the weighted vote on the scored half, which penalises the per-class vote for a reason unrelated to model quality.

**Fix, in three parts:**

| Part | Change | Why |
|---|---|---|
| Split | Two folds with `StratifiedGroupKFold`: groups stay whole and the halves are balanced by class | Removes most empty classes at the source |
| Score | Macro-F1 over the classes present in the scored half | An absent class says nothing about the vote |
| Weights | A class missing from the learning half gets weight 1.0 for every arm | Falls back to the equal vote for that class instead of a zero |

Also score both directions (learn on half 1 and score on half 2, then swap) and average, so one lucky split does not decide it.

**Decision rule.** Fix it before running: keep per-class weighting only if it beats the equal vote by at least a set margin, say 0.5 points, the margin iteration 3 used for its budget rule. Otherwise keep the simpler equal vote. Note in the output that these are validation probabilities already used for tuning, so the scores are optimistic and say nothing about test data. This check must not read any sealed set.

A unit test should build a case where a class is missing from one half and assert that the score is not dragged to zero.

## Validation
`tests/studio/test_vote.py::test_a_class_missing_from_a_half_is_not_scored_as_zero` covers the failure, and `test_validation_halves_keep_each_group_whole` and `test_compare_reports_every_arm_and_keeps_equal_weights_without_a_clear_win` cover the split and the rule. `scripts/vote_check.py` implements `split_groups` (stratified, group-preserving), `_score` (present classes only) and `_class_weights` (weight 1.0 for a missing class), with `ADOPT_MARGIN = 0.5`.

## Our decision
Halves are now balanced by class, absent classes are left out of the score, and a class missing from the learning half gets equal weights. A test covers it (commit 916e7df). State: Overcome.

## Measured effect
- Before: an empty class cost about 10 macro-F1 points and gave the per-class weights a zero.
- After (`exp_vote_check.json`, validation only): equal vote 95.59, per-class vote 94.80, gain -0.79 against the 0.5 margin, so `keep` is `equal`. Single arms: A0 94.39, A1 95.10, B 95.01, A2 95.77, P 95.05.

---

## Upgraded & Expanded Technical Analysis (`F30`)

### 1. Coupling Between Unstratified Group Splitting, Zero-Support F1, and Zero Vote Weights
When validation images are partitioned into a weight-learning half $H_{\text{learn}}$ and a scoring half $H_{\text{score}}$ by pure random group splitting over large `phash_group` clusters without class stratification, a minority class $c$ can receive zero support ($N_c = 0$) in one of the halves:
1. **Scoring Half Distortion ($N_c(H_{\text{score}}) = 0$):** Standard 10-class macro-F1 sets $\text{F1}_c = 0.0$ when $\text{TP}_c + \text{FP}_c + \text{FN}_c = 0$, penalizing the macro average by $-\frac{1}{10}\text{F1}_c \approx -9.5$ points purely from a zero-denominator artifact.
2. **Learning Half Weight Collapse ($N_c(H_{\text{learn}}) = 0$):** Per-class vote weighting sets arm $a$'s weight on class $c$ proportional to its F1 on $H_{\text{learn}}$: $w_{a, c} = \text{F1}_{a, c}(H_{\text{learn}}) = 0.0 \;\forall a$. On $H_{\text{score}}$, the weighted probability for class $c$ becomes $\sum_a w_{a, c} p_{a, c}(x) = 0$, making it mathematically impossible for the per-class vote to predict class $c$.

### 2. Three-Layer Fix & Pre-Committed Parsimony Rule (`ADOPT_MARGIN = 0.5`)
- **Source Prevention (`StratifiedGroupKFold(n_splits=2)`):** Balances class proportions across the two halves while keeping every `phash_group` intact (`test_validation_halves_keep_each_group_whole`).
- **Present-Class Macro-F1 (`_score`):** Computes $\frac{1}{|\mathcal{C}_{\text{present}}|} \sum_{c \in \mathcal{C}_{\text{present}}} \text{F1}_c$ where $\mathcal{C}_{\text{present}} = \{c : N_c(H_{\text{score}}) > 0\}$ (`test_a_class_missing_from_a_half_is_not_scored_as_zero`).
- **Uniform Fallback Weight (`_class_weights`):** Whenever $N_c(H_{\text{learn}}) = 0$ (or $\max_a w_{a, c} = 0$), sets $w_{a, c} = 1.0 \;\forall a$, gracefully degrading to equal-weight voting on that class.
- **Bidirectional Cross-Fitting & Parsimony Gate:** Averaging $(H_1 \to H_2)$ and $(H_2 \to H_1)$ yields `equal = 95.59` vs. `per_class = 94.80` (`gain = -0.79 < ADOPT_MARGIN = 0.5`), decisively retaining the simpler parameter-free equal vote without touching any sealed split.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the teaching sentence is "the zero is not a model error. It is an empty class." The failure looks like a model problem and is a denominator problem. The three-part fix addresses three symptoms of one root cause: split prevents most empty classes, score stops a zero entering the average, and weights stop a zero-weighted class from losing the vote. Fixing only one part leaves the other two symptoms.

**Changelog:** [1] "empty class, not model error" as the teaching point; [2] three parts map to three symptoms; [3] bidirectional scoring is stated as a reason, but the reporting format (one number or both) is not; [4] `ADOPT_MARGIN = 0.5` is borrowed from iteration 3's budget rule, and the choice of 0.5 over 0.3 or 1.0 is not justified; [5] the validation-optimism note is the epistemic guard.

**Open questions:** Does the comparison run both directions and report the average, or one direction? The measured effect is one number, which suggests one direction. If so, the stated fix is not fully applied. Does the output record which classes fell back to equal weight? Without that, the 0.79-point gap could be driven by a fallback class that a reader cannot see.
