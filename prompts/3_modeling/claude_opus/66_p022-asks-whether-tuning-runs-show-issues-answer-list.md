# 3_modeling - P022: Asks whether tuning runs show issues; answer lists tuning results
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P022. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

is there an issues >[

<pasted_content id="83b2">
2 background tasks · click a task for details

Launch Stage 4 with fixed recipe
shell · 175m 12s

Stage 4: finished runs and failures
</pasted_content id="83b2">

]

## Response

No issues. The log shows zero errors and zero tracebacks, and the run is behaving as designed.

##### Tuning run status
- **One tuning run just finished.** lr 0.0003, dropout 0.4 early-stopped at epoch 18, with a best of 75.5 val macro-F1 at epoch 13. This is the normal patience-5 stop for the weakest setting.
- **The other five were still improving** at about epoch 16 (best so far):

| lr | dropout | best val macro-F1 so far |
|---|---|---|
| 0.003 | 0.4 | **89.2** |
| 0.003 | 0.2 | 88.4 |
| 0.001 | 0.2 | 85.6 |
| 0.001 | 0.4 | 85.0 |
| 0.0003 | 0.2 | 80.4 |

The runs at lr 0.003 are already well above the HOG + SVM baseline (80.4).

##### Why the clock says 175 minutes
The 175 minutes on the clock is slow CPU training, not a fault. The whole grid takes about 3 h, with 6 runs sharing 14 cores. When the grid finishes, the winner is chosen on A1 validation and frozen, and the 11-run sweep starts. I will keep reporting as each run completes.

##### Completed runs, in order
1. Second tuning run: lr 0.0003, dropout 0.2 finished at 80.4 val macro-F1. Best at epoch 15, stopped at epoch 20. Four runs remain.
2. Third tuning run: lr 0.001, dropout 0.2 finished at 85.6. Best at epoch 16, stopped at epoch 21. Three remain, including the two leaders at lr 0.003.
3. Fourth tuning run: lr 0.001, dropout 0.4 finished at 85.0. Best at epoch 16. The two lr 0.003 runs (about 89 and 88 at that point) were still going.
4. Fifth tuning run: lr 0.003, dropout 0.2 finished at 88.4. One run was left, lr 0.003 with dropout 0.4, which was leading at about 89.2.

##### The tuning grid is complete
The Decision 7 winner, selected on A1 validation only, is **lr 0.003, dropout 0.4, at 89.2 val macro-F1** (best epoch 16 of 21).

| lr | dropout | val macro-F1 |
|---|---|---|
| **0.003** | **0.4** | **89.2** |
| 0.003 | 0.2 | 88.4 |
| 0.001 | 0.2 | 85.6 |
| 0.001 | 0.4 | 85.0 |
| 0.0003 | 0.2 | 80.4 |
| 0.0003 | 0.4 | 75.5 |

This is up from 39.2 under the old recipe, and above both baselines (80.4 for HOG + SVM, 75.6 for logistic regression). Every run early-stopped between epochs 18 and 21, after the validation curve had peaked.

##### Next step: the sweep
The sweep now starts with these frozen settings: A0, A1 and B, each with 3 seeds, plus the 2 Hand-Drawn LOSO runs, 6 at a time.

One deliberate choice: I am recording the winner in `tuning.json` and the Stage 4 status, but I am **not** editing the settings in `configs/pipeline.yaml` during the run. The values are part of the recipe fingerprint, so changing them mid-run would invalidate the finished runs. Once Stage 4 completes, I will add the winner to the config as a comment, following Decision 7's freeze-in-config rule. A comment does not change the parsed config, so it will not trigger a retrain.

The monitor is re-armed for the sweep (11 runs, 6 at a time). Each run takes about 3 h, so I expect the first round to finish in about 3 h.

##### Sweep health
The sweep is healthy. Round 1 (A0 and A1, each with 3 seeds) was at about epoch 6 with no errors:

| Run | Best val macro-F1 so far |
|---|---|
| A0_1 | 85.8 |
| A0_2 | 85.1 |
| A1_0 | 77.5 |
| A0_0 | 76.6 |
| A1_1 | 74.4 |
| A1_2 | 70.8 |

These numbers are early, so no comparison should be drawn from them yet. A1's augmented stream learns more slowly at first, which the tuning runs showed too. Round 2 (B with 3 seeds, plus the 2 LOSO runs) starts when this round finishes, in about 2 to 3 h. The monitor is re-armed.

##### Completed sweep runs
- **A0_2 is done:** 85.2 val macro-F1, early-stopped at epoch 11, best at epoch 6. This is expected for A0, which has no augmentation and so overfits sooner. A freed worker slot will pick up the next queued run.
- **A0_0 is done:** 87.6 val macro-F1, best at epoch 10, stopped at epoch 15.
- **A1_0 is done:** 89.15 val macro-F1. This matches the winning tuning run exactly. That run used the same arm (A1), seed (0) and hyperparameters, but it was trained in a different process. So R9 holds on real data: a run is reproducible from its arm and seed.

The monitor is re-armed and the sweep continues. Three of 11 sweep runs are done, and 6 workers are still training.

##### Why the tuning winner was not written into the config during the run
- The values in `configs/pipeline.yaml` feed the recipe fingerprint. Editing them mid-run would change the fingerprint and invalidate the finished runs, which would waste the compute already spent.
- Decision 7 requires the winner to be frozen in the config. Adding it as a YAML comment after Stage 4 completes respects that rule, because a comment does not change the parsed config and so does not trigger a retrain.

##### Why the reproducibility result matters
- A1_0 matching the tuning run at 89.15 means the same arm, seed and hyperparameters gave the same score in a separate process. That supports rule R9 on real data: a run is reproducible from its arm and seed alone.
- The early per-run numbers (for example, A0_2 at 85.2 and A0_0 at 87.6) are final only because the runs have finished. They are not a comparison between arms, because the arms have not all finished.

##### Consequences and next steps
- Three of 11 runs are done. The remaining eight include the B arm and the two LOSO runs, so the sweep is not yet able to answer the question it was built for.
- After the sweep, the winner is still only a training-set-level decision. Test evaluation happens later in Stage 5.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
