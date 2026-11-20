# 4_testing - F14: A2 vs A0 failed on test and on the fresh holdout
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/30_F14_a2-vs-a0-failed-0-06-on-test-and-0-08-on-the.md](../claude_opus/30_F14_a2-vs-a0-failed-0-06-on-test-and-0-08-on-the.md)
- Date: 2026-11-09
- Entry: F14 (`failure`, `4_testing`)
- Owner / Proposed by: 40256377 / 40256377
- LLM role: assisted
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, docs/crisp_dm/iteration_2/data/stage5_status.json, docs/crisp_dm/iteration_2/data/verdict.csv, docs/crisp_dm/iteration_2/data/comparisons.csv, docs/crisp_dm/iteration_2/data/metrics.csv, docs/crisp_dm/iteration_2/data/test_reads.csv, docs/crisp_dm/iteration_2/frozen.sha256, docs/crisp_dm/iteration_3/preregistration.md, commit cf79298

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** `A2` vs `A0` failed in Iteration 2: `+0.06` macro-F1 points on the reused test split (95% CI [-0.69, 0.83]) and `+0.08` on the fresh 4,500-image holdout (95% CI [-0.41, 0.57]), both from the same sources used in training. How should we report this, and what should a third iteration test instead?

## Response
Your reading holds, and the Stage 5 status supports recording it exactly as you propose.

**What the numbers say.** On the reused test split the primary gain is 0.06 points, CI [-0.69, 0.83], and McNemar has 42 against 44 discordant images (p 0.914). On the fresh holdout (4,500 images, never read before) it is 0.08, CI [-0.41, 0.57], with 63 against 64 discordant images. No class was flagged as harmed. Reads were 52 of 52 expected, so the evaluation itself is clean. Both rule conditions fail on both sets: the gain is below the required 1.00 point, and the interval includes 0.

**Why this is not a near miss.** The arms are essentially level on familiar sources. Ensemble macro-F1 on test is A0 95.3, A1 95.2, B 95.3, A2 95.4. On the fresh holdout it is A0 97.5, A1 97.4, B 97.2, A2 97.5. Once the iteration 1 defects were fixed, every arm reaches about the same ceiling on images from sources it trained on. No sensible setting change would move a 0.06 gain past 1.00 with an interval that clears 0, and trying one now would be tuning against a read test.

**Wording I would use:**
> Iteration 2 primary test A2 vs A0: fail. Test split +0.06 points, 95% CI [-0.69, 0.83]; fresh holdout (n = 4,500) +0.08, CI [-0.41, 0.57]. Both intervals include 0 and neither reaches the required gain. No change was made after the test read.

**What a third iteration could test instead.** The useful signal is where the arms do differ. The unseen-source runs (models trained without Hand-Drawn, scored on its triangles and rectangles, n = 302 per seed) give A0 75.8, 58.3 and 65.6% across three seeds, while A1 gives 77.5, 73.5 and 72.5%. That is a direction worth a pre-registered test, with caveats:

| Option | Strength | Caution |
|---|---|---|
| Target unseen sources | Where augmentation seems to help | The current hold-out covers only Hand-Drawn triangles and rectangles, and the per-seed spread is wide |
| Re-run the same clean comparison | Easy | Same ceiling, same likely outcome |
| Change the rule or threshold for iteration 2 | None | Not allowed after the read |

Two cautions for the third iteration. The test split and the first fresh holdout are now both read, so they can only be reported as contaminated evidence; any new primary needs data that has never been opened. And the new question, its data and its rule must be committed before any tuning starts.

## Validation
The figures were checked against `docs/crisp_dm/iteration_2/data/stage5_status.json` (primary and `fresh_holdout` blocks, `checks.test_reads` 52 of 52) and `verdict.csv` ("gain 0.06 < 1.00 points; CI includes 0 ([-0.69, 0.83])"). The iteration 2 record is hash-locked in `docs/crisp_dm/iteration_2/frozen.sha256`.

## Our decision
Recorded as a failure (commit cf79298). No change was made after the test read. A third iteration would need to target unseen sources. The entry stays "Still open" in the iteration log. The iteration 3 pre-registration later chose a never-read fresh holdout 2 and noted that it uses the same sources, so it does not test generalisation to new sources.

## Measured effect
A2 vs A0: +0.06 points, CI [-0.69, 0.83] on test; +0.08, CI [-0.41, 0.57] on the fresh holdout. Verdict fail on both. No before -> after change, since nothing was changed.

---

## Upgraded & Expanded Technical Analysis (`F14`)

### 1. Algebraic Proof of "Not a Near Miss" (Ceiling Compression)
The pre-registered Iteration 2 pass rule requires the conjunction:
$$\Delta \ge 1.00 \quad \wedge \quad \text{CI}_{\text{lo}} > 0.00$$
- **Reused `test.csv` ($N = 2,776$):** $\Delta = +0.06 < 1.00$ (**fail**) and $\text{CI}_{\text{lo}} = -0.69 \le 0.00$ (**fail**). Ensembles sit at a tight ceiling: `A0 = 95.3`, `A1 = 95.2`, `B = 95.3`, `A2 = 95.4`.
- **Sealed `fresh_holdout.csv` ($N = 4,500$):** $\Delta = +0.08 < 1.00$ (**fail**) and $\text{CI}_{\text{lo}} = -0.41 \le 0.00$ (**fail**). Ensembles sit at `A0 = 97.5`, `A1 = 97.4`, `B = 97.2`, `A2 = 97.5`.
- **Quantitative Distance from Threshold:** Clearing $\Delta \ge 1.00$ would require the point effect to expand by **$\sim 16.7\times$** ($0.06 \to 1.00$) while shifting the lower 95% confidence bound upward by $+0.70$ points. Descriptive McNemar discordant counts confirm near-exact symmetry (`42` vs `44` on `test.csv`, $p = 0.914$; `63` vs `64` on `fresh_holdout.csv`), showing zero directional preference on clean drawings from training sources.

### 2. Epistemic Boundary for Iteration 3 (Contamination & Question Shift)
- **Why Unseen Sources vs. Corruption Robustness:** On held-out `Hand-Drawn` triangles/rectangles ($n = 302$/seed), `A0` scored `75.8% / 58.3% / 65.6%` across three seeds while `A1` scored `77.5% / 73.5% / 72.5%` — a directional signal with wide inter-seed variance across only two classes.
- **Permanent Contamination of Read Splits:** Because both `test.csv` and `fresh_holdout.csv` have now been opened (`52 of 52` expected reads), neither can ever serve as a primary decision split again. Any Iteration 3 hypothesis must commit a new pre-registration before tuning and evaluate on a brand-new, never-opened holdout (`fresh_holdout_2.csv`), explicitly noting that because `fresh_holdout_2` draws from the same training sources, it tests *corruption robustness* rather than *unseen-source generalization*.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the sentence that makes the failure final is "no sensible setting change would move a 0.06 gain past 1.00 with an interval that clears 0." Any tweak after the read is tuning against a read test. Interval widths (1.52 on test, 0.98 on fresh) make a 1.00-point gain unreachable without a real effect.

**Changelog:** [1] "no sensible change" argument added; [2] fresh scores are higher than test for every arm, which the entry does not explain; [3] the Iteration 3 same-source limitation is stated.

**Open questions:** The unseen-source runs spread widely (A0 58 to 76%, A1 73 to 78% across seeds, n = 302 per seed). Is that source difficulty, seed variance, or sample size? Without an answer, "target unseen sources" is a direction, not a plan.
