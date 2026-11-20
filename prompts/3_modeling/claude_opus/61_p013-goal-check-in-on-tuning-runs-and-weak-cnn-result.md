# 3_modeling - P013: Goal check-in on tuning runs and weak CNN results
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P013. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

Goal check-in: «Execute the goal defined in @.agents/goal_build_implementation.md exactly as written.» is still active, and evaluation has been deferred for 75 min because background work is still running:
- bxjuqixuz · shell · .venv/Scripts/python -u run_pipeline.py --stages 4 &gt; artifacts/run_s4.log 2&gt;&amp;1; echo exit=$?
- b857lhlcf · shell · SP="$(cygpath '<home>\AppData\Local\Temp\claude\f8be42c757e0c03c\[session ID removed]-5873-4a51-9c9b-… [+465 chars]
- bvgtwdycw · monitor · Stage 4: finished runs and failures
Check on their progress (e.g. read their output). If they are progressing, say so briefly and keep waiting; if they are stuck or no longer needed, fix or stop them and continue toward the goal.

## Response

#### Status

Both background jobs are still running. Before deciding anything, I took a stack sample of the rehearsal to confirm it is working and not hung.

- **Rehearsal:** the run is still in Stage 0, after its migration rebuild. Stage 0 is hashing the raw data archive, which is I/O-bound because it reads through the junction. Stages 1 to 3 follow.
- **Stage 4:** the six tuning runs are training. I confirmed this earlier with CPU sampling. None has finished yet, which fits roughly 1.5 to 2 hours per run under contention.

The monitor will report each completed run, so I am continuing to wait.

##### Progress since the last check

- Rehearsal Stages 1 and 2 are now running.
- Stage 4 tuning continues under the active monitor.

##### First tuning result

One tuning run finished at **val macro-F1 39.2**, well below the baselines of 75.6 and 80.4. It early-stopped at epoch 11, and its best checkpoint was at epoch 6.

A CNN this far below logistic regression points to a bug rather than a tuning outcome. My first suspect is that the training batches and the validation pass prepare pixels differently. I have not confirmed this yet.

##### Clean-copy checks

- In the clean copy, Stages 0 to 2 passed.
- Stage 1 recomputed the manifests from scratch, and they are byte-identical to the main tree. So the freeze is reproducible from the README on a fresh environment.
- Stage 3's throughput gate will be re-checked on an idle machine.
- The CNN diagnostic is running.

##### Why the first result is treated as a suspected bug
- A macro-F1 of 39.2 is far below the logistic-regression baseline (75.6) and HOG + SVM baseline (80.4). A gap that large usually points to a pipeline error, not a tuning choice, so the working assumption is a bug until disproven.
- The suspected cause is a mismatch between how training batches and validation images are prepared. If that is right, the model would learn on one input distribution and be scored on another. This is not confirmed, and the diagnostic is the test for it.
- The early stop at epoch 11 with a best checkpoint at epoch 6 is consistent with a model that stopped improving early, which fits this kind of mismatch, but it does not prove it.

##### Why the clean-copy checks matter
- Stage 1 recomputing manifests byte-identically shows the data freeze can be reproduced from the README on a fresh environment. This supports the reproducibility claim, but only for the stages that were rerun.
- Stage 3's throughput gate is not yet confirmed. It was affected by machine load, so it will be re-checked on an idle machine before it counts as a pass.

##### Next steps
- Read the CNN diagnostic output. If it confirms the preparation mismatch, the CNN recipe must be fixed and the tuning runs repeated before any CNN comparison.
- Keep the 39.2 result as an unverified early value. It should not be reported as a final CNN score.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
