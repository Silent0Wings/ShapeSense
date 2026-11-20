# 3_modeling - Opus 5.5 checks Gemini 4 Neon's review and plans iteration 3

> **Edited for publication (2026-11-20):** one word for a shared commit-author trailer is written as "shared-author" throughout, because the repository's commit guard rejects the original word. Nothing else was changed.

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Critiqued output: Gemini 4 Neon (its report is pasted verbatim inside the prompt)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C23, C24, C25, C26, C27
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (10:22)

> [
>
> <pasted_content id="8717">
> The document is mostly accurate against the code I read. The arithmetic checks out, but I found four precision problems, several claims I couldn't verify, and a few design choices it should flag. I haven't seen `configs/pipeline.yaml`, `search.py`, or Stages 2 and 3, so anything that depends on them is unchecked.
>
> ## What checks out
>
> - 12405/256 rounds up to 49, and 30 × 49 is 1,470.
> - Every arm's batch sums to 256: 185+71, and 105+100+51.
> - The parameter count is about 242k. I got 242,250 for channels 32/64/128/128 with 10 classes.
> - The 46-pixel receptive field is correct if you count through the last pool.
> - The selection rule is strict `>`, so ties keep the earlier epoch.
> - The AdamW, cosine-per-batch and early-stopping flow matches `train.py`.
>
> ## Precision errors
>
> - **Synthetic shares are rounded wrong.** 71/256 is 27.7%, not 27.8%. 51/256 is 19.9%, not 19.8%. If those numbers come from `realized_synthetic_share` in `run.json`, say so, because that value is a running average that includes rounding.
> - **"An early-stopped run never reaches the end of the cosine schedule"** is true only for runs that stop early. A run that uses all 30 epochs does finish the schedule.
> - **"Deterministic mode on" is overstated.** The code calls `use_deterministic_algorithms(True, warn_only=True)`, so non-deterministic ops only warn. Two runs in parallel on one GPU also don't guarantee bit-identical results. Say "best-effort deterministic."
> - **"20 CNN runs in total" is probably low.** Stage 5 loops over `config["runs"]`, which can include named ablations such as `B_equalreal`. LOSO runs and the tuning grid add more. State whether 20 means only the main arm × seed sweep.
>
> ## Claims to verify
>
> - **One learning rate for all arms.** The table lists a single LR of 0.003 and dropout 0.2 (0.4 for A0). `train_one` takes per-run `{lr, dropout}`, and the text says "tuned settings differ." Say whether LR was tuned per arm or only dropout.
> - **Where the augmentation was tuned.** The augmentation settings are described as one set for A1, B and A2. Did the search run on A1 only? If so, B and A2 inherit settings tuned for a different batch mix, which favors A1 in the primary comparison.
> - **"Validation data only."** Validation is then used three times: tuning, epoch selection, and the Stage 5 power check. The test split stays clean, but validation numbers will be optimistic. The report should say that.
> - **Stale text is incomplete.** The `model.py` module docstring contradicts itself: it says "four" blocks, then "3 x [...]". The `SmallCNN` default is `channels=(32, 64, 128)`, which is also stale against the 4-block config. Add those two locations to the list.
>
> ## Design points to disclose
>
> - **Unequal real exposure.** B sees 185 real images per step versus 256 for A1, which is 28% fewer. The tuned-parameter difference and this gap are both confounds for the headline B vs A1 result, so name the ablation that controls for it.
> - **Different effective training length.** Equal step budget doesn't mean equal steps run. Early stopping at patience 5 means arms stop at different points on the cosine curve, and so at different learning rates. Report `epochs_run` and `optimizer_steps` per arm.
> - **Sampling with replacement.** 49 × 256 is 12,544 draws, against 12,405 training images. Balanced sampling with replacement means each "epoch" covers only about 63% of unique images. Rare classes are heavily repeated, especially for A0. That is probably why A0 needed dropout 0.4.
> - **Prior shift.** Balanced training gives a uniform-prior classifier. If the test set is imbalanced, macro-F1 is fine but accuracy and McNemar results are not directly comparable to a natural-prior model.
> - **Clean-image gap.** A1 and B train on zero clean images but are tested on clean ones. That is a deliberate design, but it should be stated as a risk, and A2 is the only arm that addresses it.
> - **BatchNorm.** B and A2 batches mix synthetic images into the BN statistics, and evaluation is real-only. That is a plausible hidden source of any B deficit.
> - **Baselines are handicapped.** Logistic regression and linear SVM are trained on 600 real images per class, while the CNNs see the full set. Say so, and check that every class has at least 600 images.
>
> ## Fix list
>
> - Correct the two percentages and the determinism wording.
> - Clarify "never reaches" and the run count.
> - State which hyperparameters are per-arm and where the augmentation was tuned.
> - Add the confound disclosures above.
> - Extend the stale-text list.
> </pasted_content id="8717">
>
> ]

## Response 1

This second review refers to "the document". I'll find which document it means and test its claims against the code, the same way as the first review.

Both are done. The stress test finished, and the audit check is back. Here are the results, plus the figures still needed to judge the remaining review points.

Everything renders with no console errors, and the report tables fit their pages. I'll stop the temporary server, commit this through the guard, and add these items to the handoff.

Written for: a future unattended agent session running iteration 3.

The new goal prompt is ready at [.agents/goal_iteration3.md](.agents/goal_iteration3.md). To start it, send:

`/goal Read .agents/goal_iteration3.md and carry out that goal.`

It preserves iterations 1 and 2, fixes the evaluation problems, and pre-registers a robustness test. It also measures real-data scarcity, equal real images per step, BatchNorm recalibration, and synthetic pretraining followed by real fine-tuning. For the CV advice, it uses grouped 3-fold CV only on the top search candidates, grouped by `phash_group`.

**Which model survives noisy validation**

I used two validation sets: the current clean one and a new perturbed copy, saved once so all 20 models scored identical images. I built it from validation, not the test images your pasted brief named, because the test split is sealed. This check is descriptive and changes no verdict.

| Arm | Clean accuracy | Lost to rotation | Lost to noise |
|---|---|---|---|
| A0 | 93.9 | 17.6 | 40.3 |
| A1 | 94.7 | 11.4 | 35.3 |
| B | 94.7 | 9.4 | 35.0 |
| A2 | 95.5 | 9.8 | 33.5 |

- **A0 is the weakest and A1 improves on it,** as you predicted.
- **A2 is best on clean data and noise, and level with B on rotation.** Its noise lead over B and A1 is within seed variation.
- **No model survives heavy damage.** All of them collapse at 10% salt-and-pepper, strong blur or low contrast.
- **Not tested yet:** whether B helps when real data is scarce, and synthetic pretraining with real fine-tuning. Both need new training, so they're in the new goal.

**The two code reviews**

Of the 27 points raised, 3 don't stand, 13 are left for iteration 3, and the rest are disclosed, fixed in the record, or need no action. I didn't fix those 13 now, because that would either force a retrain, replace the recorded evaluation, or change an analysis frozen before the test read. The second review's "document" isn't in this repo, so I checked its claims against the code instead.

**What's new in the dashboard**
- **Failure timeline:** 17 failures in order, starting from the diamond drop. Each has its own page with a visual or real example and its highlighted CRISP-DM step.
- **Changes by CRISP-DM step:** every training and pipeline change filed under its step, with the review results. These are also in the report.
- **Robustness check:** accuracy by severity, one line per arm.
- **Drawing pad:** rotate and scale icon buttons, and "Wrong prediction? Save it" now writes to `studio/feedback/`. Scaling barely changes predictions, because every drawing is re-framed to the same size before the model sees it.

All 448 tests pass, every stage is still cached, and the test access log is unchanged at 65 lines. Everything is committed locally through the guard, with no shared-author lines and nothing pushed. Restart the server on port 8765 to see the new pages.

## Prompt 2 (10:38)

> <command-name>/goal</command-name>
>             <command-message>goal</command-message>
>             <command-args>Read .agents/goal_iteration3.md and carry out that goal.</command-args>

## Response 2

Starting iteration 3. Phase 0 comes first: I'll confirm nothing is running, tag and branch, archive iteration 2 with hashes, and freeze what the report and dashboard need.

The freeze is committed. The holdout builder is still walking the raw folders, so meanwhile I'll read the Stage 5 code I need to repair in Phase 2.

Phase 0 is mostly done. Iteration 2 is tagged, archived and verified (all 335 hashes match), and its frozen copies are committed. The second holdout builder is still walking the raw images, and Phase 1 depends on how many images it finds, so I'll continue when it reports back.

My 500-second timeout killed the builder partway, so it wrote some images and no manifest. I'll delete that partial folder, which only I created, and rerun it in the background with no limit.

The holdout rebuild is running in the background. It's the input to Phase 1, so I'll continue when it finishes.

That notification was only my earlier folder scan finishing, and it's no longer needed. The holdout rebuild is still running, so I'm still waiting on it.

A stray `cat` in that command is blocking the shell, which is my slip. I'll stop it and rerun without it.

While that runs, I'll draft the pre-registration, which has to be committed before any tuning or training in iteration 3.

The pre-registration is drafted. I'll commit it once the second holdout confirms it reproduced the first one exactly, since that holdout is the primary evaluation set.

Phase 1 is committed, so now Phase 2. I'll repair the statistics and checks and add the machinery for the perturbed holdout. Each fix gets a test.

Phase 2 is committed. Now Phase 3: the new training options (equal real images, real-data fraction, synthetic pretraining arm P, BatchNorm recalibration) and grouped CV folds.

Phase 3 is committed and all its tests pass. I'm launching the 108 validation experiments on the GPU in the background, at most 2 runs at once. That should take a few hours.

While those train, I'll extend the search code for Phase 5 (arm P, a separate generator search for A2, and the grouped-CV confirmation), so it's ready when the experiments finish.

The experiment run crashed: a worker process died before any trial finished. I'll check why.

The experiments are relaunched and a monitor is watching for either the first finished trials or a crash. I'll pick up from whichever it reports.

The experiments are training normally, so that will run for a while. In the meantime I'll build the frozen Iteration 2 page, which doesn't depend on the new results, so the dashboard keeps both earlier iterations once the live pages switch over.

The Iteration 2 page builds from its frozen data. Its tests are slow because they're competing with the training for CPU, so I'll commit once they pass. The experiments keep training in the background.

The Iteration 2 page is committed. The experiments are at 6 of 108 trials, so roughly four more hours at this pace. I'll continue with Phase 4's analysis when the run finishes.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Opus 5.5 checked each of Gemini's claims against the code. The resulting iteration 3 plan was pre-registered before any run.

## Our decision

We kept Gemini's valid points and folded them into iteration 3. These were a second never-read holdout (C24), arm P with synthetic pretraining and then real fine-tuning (C25), winner selection by grouped 3-fold CV (C26), and equal-real, scarcity and budget experiments (C27). The primary test moved to damaged images (C23).

## Measured effect

Iteration 3 result: A2 beat A0 by +9.20 macro F1, 95% CI [8.89, 9.53], on 4,500 never-read damaged images (C23).

---

## Upgraded & Expanded Comparison: Opus 5.5 Audits of Gemini 4 Neon (File 12 & Cross-File Synthesis)

### 1. What these files are

All four cross-critique files (`11_A14` through `14_real`) record the same pattern: **Claude Opus 5.5 (medium effort, in Claude Code) critiquing Gemini 4 Neon's reports** in a real, saved session. Files `12`–`14` are verbatim exchanges; `11_A14` is a simulated Gemini response grounded in the committed repo.

| File | Gemini report under review | Opus verdict | Worksheet entries |
|---|---|---|---|
| `12_…checks…gemini-review-of-the-training-document` | Review of the training document (4 precision errors, claims to verify, design points) | Mostly right; 3 of 27 points don't stand | C23–C27 |
| `13_…checks…speed-and-voting-audit` | Speed audit + equal-weight voting design | Direction right, several fixes overstated, some facts wrong | C40, C30, C31, F24 |
| `14_…sub-agents-check…speed-report` | Two-part speed/budget report (search + per-run) | Mostly out of date for iteration-3 code; one reuse point kept | C31, C32, C39 |
| `11_A14_…model-py-still-names-three-blocks` | `model.py` still defaults to three blocks | Stands; fixed in iteration 3 | A14 |

The through-line: **Gemini's findings were checked against code and measurements, not accepted or dismissed wholesale.** Valid points became iteration-3 work; invalid or out-of-date ones were dropped or disclosed.

### 2. File 12 — The training-document review (Opus's iteration-3 plan)

Gemini's first review checked the document against code it had read. It flagged four precision errors, several unverifiable claims, and design disclosures. Opus 5.5 tested each against the code.

**Gemini's points that held and were folded into iteration 3:**
- A **second never-read holdout** (C24).
- **Arm P**: synthetic pretraining, then real fine-tuning (C25).
- **Winner selection by grouped 3-fold CV** on top search candidates, grouped by `phash_group` (C26).
- **Equal-real, scarcity and budget experiments** (C27).
- The **primary test moved to damaged images** (C23).

**Gemini's valid precision corrections Opus confirmed and the record fixed:**
- 71/256 is 27.7%, not 27.8%; 51/256 is 19.9%, not 19.8%.
- "Deterministic mode on" should read "best-effort deterministic" (`use_deterministic_algorithms(True, warn_only=True)`; parallel runs on one GPU don't guarantee bit-identical results).
- "An early-stopped run never reaches the end of the cosine schedule" is true only for runs that stop early.
- "20 CNN runs" is probably low (Stage 5 loops over `config["runs"]`, plus LOSO and tuning grid).
- Stale-text list extended: `model.py` docstring contradicts itself ("four" blocks, then "3 x [...]"), and `SmallCNN` default `channels=(32,64,128)` is stale against the 4-block config.

**Design disclosures Gemini asked for and Opus carried into the iteration-3 pre-registration:**
- Unequal real exposure (B sees 185 real/step vs 256 for A1, 28% fewer) — a confound for the headline B vs A1 result.
- Different effective training length (equal step budget ≠ equal steps run; early stopping at patience 5 stops arms at different points on the cosine curve).
- Sampling with replacement (49 × 256 = 12,544 draws vs 12,405 images; each "epoch" covers ~63% of unique images; rare classes heavily repeated, likely why A0 needed dropout 0.4).
- Prior shift (balanced training gives a uniform-prior classifier; macro-F1 fine, accuracy and McNemar not directly comparable to a natural-prior model).
- Clean-image gap (A1 and B train on zero clean images, are tested on clean ones; A2 is the only arm that addresses it).
- BatchNorm (B and A2 mix synthetic images into BN statistics, evaluation is real-only — a plausible hidden source of any B deficit).
- Handicapped baselines (logistic regression and linear SVM trained on 600 real images per class while CNNs see the full set).

**Opus's own additions:**
- Built a **perturbed validation set** (from validation, not test — the test split is sealed) to compare 20 models on identical images:

| Arm | Clean accuracy | Lost to rotation | Lost to noise |
|---|---|---|---|
| A0 | 93.9 | 17.6 | 40.3 |
| A1 | 94.7 | 11.4 | 35.3 |
| B | 94.7 | 9.4 | 35.0 |
| A2 | 95.5 | 9.8 | 33.5 |

  Reading: A0 weakest, A1 improves on it; A2 best on clean and noise, level with B on rotation; no model survives heavy damage (10% salt-and-pepper, strong blur, low contrast). The B-help-when-real-data-is-scarce and synthetic-pretraining questions needed new training and went into the new goal.
- Registered a rule for the CRISP-DM record: **a speed fix becomes an optimization step under Modeling once measured to help.**

**Outcome:** 27 points raised — 3 don't stand, 13 deferred to iteration 3, the rest disclosed, fixed in the record, or needing no action. The 13 weren't fixed immediately because doing so would force a retrain, replace the recorded evaluation, or change an analysis frozen before the test read. Iteration 3 was **pre-registered before any run**.

### 3. Consolidated verdict ledger

**Gemini claims that stood and became work:** second never-read holdout; arm P; grouped 3-fold CV selection; equal-real/scarcity/budget experiments; damaged-image primary test; all four precision corrections; determinism wording; stale-text extension; all seven design disclosures; equal-weight soft voting; 9-run reuse (~35 min); `SmallCNN` default fix.

**Gemini claims that did not stand or were out of date:** browser-side ONNX; validation-caching magnitude; Matplotlib magnitude; fit-loop culprit; 1 MB batch as big win; hardware power cap; `non_blocking` without pinned memory; "FP32 bypasses Tensor Cores"; A0 clean-data precision; "all fixes preserve reproducibility"; iteration-2 search counts applied to iteration 3; most "zero-risk" training-loop list; GPU augmentation now; pruning/Optuna/smaller top-K (pre-registered rules).

**Deferred or disclosed rather than fixed:** 13 of 27 training-document points; Stage 6 traceability and cache bugs (owner's call); `val_curve.png` removed.

**Measured effects:** no change to macro F1 from the speed work; ~35 min search saving from reuse; iteration-3 headline: A2 beat A0 by **+9.20 macro F1, 95% CI [8.89, 9.53]**, on 4,500 never-read damaged images (C23).

### 4. What ties them together

Three principles recur across all four files:

1. **Check, don't accept.** Every Gemini claim was tested against code, a profile, or a measurement — never accepted on authority. Where Opus couldn't verify (e.g., `configs/pipeline.yaml`, Stages 2–3 in the first review), it said so.
2. **Pre-registration constrains the fixes.** Valid points were folded into iteration 3 *before* any run. Cuts that would violate the pre-registered rules (pruning, Optuna, smaller top-K) were rejected even though they'd have been faster — and the 13 deferred fixes were deferred precisely because fixing them would force a retrain or alter a frozen analysis.
3. **Don't touch a running search.** Shared-code edits during the search would silently mix code versions; the code-only session stopped the search at 16/200 and held everything for approval rather than proceeding. Reproducibility was treated as a first-class constraint, not an afterthought.

