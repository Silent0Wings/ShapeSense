# 4_testing - C41: Iteration 3 report section and dashboard results
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/40_C41_iteration-3-report-section-and-dashboard-res.md](../claude_opus/40_C41_iteration-3-report-section-and-dashboard-res.md)
- Date: 2026-11-10
- Entry: C41 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / 40248536
- LLM role: assisted
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, phase2_report.tex, src/stage6_report/iteration3.py, tests/stage6/test_iteration3.py, studio/data/pages.py, studio/web/js/pages/robustness.js, results/phase2_snapshot/status5.json, results/phase2_snapshot/robust_sealed.json, commits 4091dab, ec84804

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** The report stops at Section K (Iteration 2) and the dashboard only shows four arms and validation robustness. How should we structure report Section L and the dashboard updates so they lead with the sealed Iteration 3 verdict, include arm `P`, and draw every number from recorded tables?

## Response
Good plan. Here is how I would structure it so the verdict is the first thing a reader sees and every number traces back to Stage 5.

**Report: a new Section L after Section K.**
1. One opening paragraph: iteration 3 is a separate experiment and does not change the iteration 1 or 2 verdicts. State why the question moved, from clean accuracy on familiar sources to survival under damage, and point to `docs/crisp_dm/iteration_3/preregistration.md`.
2. "What changed in the method": arm P (synthetic pretraining, then real fine-tuning) reported descriptively, outside the corrected comparisons, and the trials per arm. Say plainly that A0 has no augmentation settings to search and so received fewer trials.
3. A per-arm table: validation, clean holdout, damaged holdout, unseen source, for all five arms.
4. "Pre-registered result": the primary A2 vs A0 delta, CI, verdict and the strict reading, then the source-clustered interval with the "three sources, coarse" caveat, then sealed reads against expected.
5. Secondary comparisons, Holm-corrected.
6. "How much weight this can carry": the clean-image delta on the same holdout, and the reused test split and first holdout reported as weaker evidence.
7. Limitations: same sources as training, no Quick, Draw! images, synthetic damage, rotation not meaningful for circles.

**Where the numbers come from.** Generate one macro file from the Stage 5 status in the same way as iteration 2, with names like `\IthreeDelta`, `\IthreeCILo`, `\IthreeVerdict`, `\IthreeSourceCILo`, `\IthreeReads`. A missing input should print a dash, never a stale value. Section L reads the live Stage 5 folder, since that is where the sealed result lands, while Section K keeps reading the frozen iteration 2 copies.

**Dashboard.** Add P to the arm list everywhere it is enumerated, and give the robustness page a "sealed" section fed from `robust_sealed.json` beside the earlier validation check, labelled so nobody mistakes one for the other.

Checks before merging:

| Check | Why |
|---|---|
| Traceability check passes on the new section | No hand-typed numbers |
| Test: macros come from the artifacts, missing inputs show a dash | Guards the generator |
| Arm P appears once per list | Easy to duplicate when lists are extended |
| Strict reading reported, not required | Matches the pre-registration |

One wording caution: lead with the verdict, but do not write it as "augmentation works" in general. The pre-registered claim is about damaged copies of images from sources seen in training.

## Validation
`src/stage6_report/iteration3.py` generates the `Ithree*` macros, and `tests/stage6/test_iteration3.py` holds `test_macros_come_from_the_artifacts` and `test_missing_inputs_show_a_dash`. Section L in `phase2_report.tex` follows the order above. `studio/data/pages.py` serves `robust_sealed` beside `robustness`, and `studio/web/js/pages/robustness.js` renders "Sealed holdout 2: clean against damaged".

## Our decision
Report Section L leads with the sealed result, and the dashboard shows arm P and the sealed robustness results (commits 4091dab and ec84804). The verdict has to be readable where people look for it, drawn from the recorded tables.

## Measured effect
Report and dashboard: iteration 2 and four arms -> Section L and five arms. Numbers shown come from `status5.json`: A2 vs A0 on 23 damage levels of 4,500 never-read images, +9.20 points, CI [8.89, 9.53], verdict pass, strict pass true; source-clustered CI [3.89, 9.42]; clean delta +0.64, CI [0.19, 1.07]; sealed reads 92 of 92.

---

## Upgraded & Expanded Technical Analysis (`C41`)

### 1. Section L as a Pure Projection of `status5.json` (`src/stage6_report/iteration3.py`)
- **Why Section K Reads Frozen Copies While Section L Reads Live `artifacts/stage5/`:** Section K documents a *closed* historical iteration whose inputs must never mutate (`docs/crisp_dm/iteration_2/`, sealed by `frozen.sha256`, cf. `F28`), whereas Section L reports the *active* Iteration 3 sealed evaluation (`artifacts/stage5/status.json` and `robust_sealed.json`, protected by `92/92` single-read accounting).
- **Zero-Literal Macro Projection & Dash Discipline:** `src/stage6_report/iteration3.py::collect()` maps every Section L metric to a letter-only TeX macro (`\IthreeDelta`, `\IthreeCILo`, `\IthreeCIHi`, `\IthreeVerdict`, `\IthreeSourceCILo`, `\IthreeReads`, etc.) with `MISSING = "--"` fallback whenever an upstream field is absent (`test_macros_come_from_the_artifacts`, `test_missing_inputs_show_a_dash`). Stage 6's fail-closed traceability check (`F26`) then verifies that 100% of numbers rendered in Section L trace to committed/generated artifacts.

### 2. Narrative Ordering, Scope Precision, and Dashboard Separation
1. **Seven-Part Epistemic Structure of Section L:**
   - **(1) Experiment Boundary:** States that Iteration 3 is a separate pre-registered experiment (`docs/crisp_dm/iteration_3/preregistration.md`) that does not alter Iteration 1 or 2 verdicts, motivated by clean-image saturation (~`95.4`).
   - **(2) Method Additions:** Introduces arm `P` (synthetic pretraining + real fine-tuning) explicitly as a *descriptive* comparator outside the Holm family (preserving family-wise power), and notes `A0`'s smaller trial count (6 trials, no augmentation parameters).
   - **(3) Four-Context Per-Arm Table:** Places validation, clean holdout, 23-level damaged holdout, and unseen-source LOSO side by side across all 5 arms (`A0`, `A1`, `B`, `A2`, `P`).
   - **(4) Primary Result First:** Reports `A2 vs A0 = +9.20`, 95% cluster CI `[8.89, 9.53]`, `verdict = pass`, `strict_pass = true` (`8.89 >= 1.0`), coarse 3-source sensitivity CI `[3.89, 9.42]`, and `92 of 92` sealed reads (`extra_reads = 0`).
   - **(5–7) Holm Secondaries, Evidence Weight, and Scope Limitations:** Reports the 4 Holm-corrected damaged secondaries (`p_holm = 0.004`), the separate clean `fresh_holdout_2` family (`+0.64 [0.19, 1.07]`), weaker reused `test` / `fresh_holdout` context, and explicit scope boundaries (same training sources, zero `Quick, Draw!`, synthetic perturbations, rotational invariance of circles).
2. **Dashboard Isolation (`robust_sealed` vs. `robustness`):** `studio/data/pages.py` serves `robust_sealed.json` alongside validation `robustness.json` and `studio/web/js/pages/robustness.js` labels `"Sealed holdout 2: clean against damaged"` distinctly from the validation sweep, while arm `P` is added with a strict uniqueness invariant across all 5-arm lists (cf. `F29`).


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the most important sentence is the caution: "lead with the verdict, but do not write it as 'augmentation works' in general." The verdict (+9.20, pass) is true, but the claim it supports is narrow: damaged copies of images from sources seen in training. Overstating it is the main risk in the report.

**Changelog:** [1] the epistemic caution as the central point; [2] Section K frozen and Section L live have different freeze requirements, because one describes a closed verdict and the other a live one; [3] `MISSING` as a dash conflates "not computed" with "computed, missing"; [4] the live read assumes Stage 5's sealed result is written once and never re-run.

**Open questions:** Is `status5.json` frozen at the moment of the sealed read, or does Stage 6 read a live file? If live, a re-run of Stage 5 changes Section L silently. Is there a test that every macro Section L references is generated by `iteration3.py`? A missing macro that falls back to a dash is visible; a macro never generated and never referenced means a number the report claims is not shown at all.
