# Cross-critique: Gemini audit of the Claude-built pipeline

Claude built the pipeline; Gemini 4 Neon (with web search on) audited it. Each claim was then checked by the team
and given a verdict and an action. Source: `phase2_snapshot/iteration_log.json` (`audit`).

Model: Gemini 4 Neon. TODO: export the original Gemini chats into
`prompts/<stage>/cross_critique/` so every claim below can be traced to its prompt and response.

## Summary

27 claims.

| Verdict | Claims |
|---|---|
| Stands | 21 |
| Partly | 4 |
| Does not stand | 2 |

| What the team did | Claims |
|---|---|
| Fixed in iteration 3 | 11 |
| Disclosed | 9 |
| No action | 4 |
| Closed by experiment | 2 |
| Fixed in this record | 1 |

| Pipeline area | Claims |
|---|---|
| eval | 13 |
| model | 11 |
| prep | 2 |
| data | 1 |

## All claims

| ID | Area | Gemini's claim | Team verdict | Action | State |
|---|---|---|---|---|---|
| A01 | data | Per-class test counts are never checked against noise_bands.csv. | Stands | Stage 5 now stops if the test labels do not match the counts the thresholds were built for. | Fixed in iteration 3 |
| A02 | prep | B and A2 inherit augmentation settings searched on A1. | Stands | Disclosed here. Only the generator and mix were searched for B and A2. | Disclosed |
| A03 | prep | Scaling is defined twice, in training and in evaluation. | Stands | Training now imports the one shared constant. | Fixed in iteration 3 |
| A04 | model | Arms see different numbers of real images per step. | Stands | Measured in iteration 3 on validation. Giving B and A2 the same real images per step lowered clean macro-F1 by 2.0 and 0.5 points, so the arms keep their tuned batches. The unequal counts stay disclosed. | Closed by experiment |
| A05 | model | BatchNorm statistics include synthetic images in B and A2. | Stands | Measured in iteration 3 on validation. Recalibrating BatchNorm on real images lowered clean macro-F1 by 0.7 for B and 0.8 for A2, so it is not used. | Closed by experiment |
| A06 | model | One learning rate and dropout were shared by every arm. | Does not stand | Each arm was tuned separately. They happen to share a learning rate, and A0's dropout differs. | No action |
| A07 | model | Early stopping can end runs before the schedule finishes. | Partly | 17 of 20 main runs used all 30 epochs. A0 seed 1 ran 10, A1 seed 4 ran 13, B seed 3 ran 29. | Disclosed |
| A08 | model | Deterministic mode is overstated. | Partly | It is best-effort: non-deterministic operations only warn. In practice the clean-clone rehearsal reproduced all 32 validation scores exactly on this GPU. | Disclosed |
| A09 | model | Batches are drawn with replacement, so an epoch does not cover every image. | Stands | Disclosed here. An epoch is a fixed 49 steps, by design. | Disclosed |
| A10 | model | Synthetic shares are rounded differently from the real batch. | Stands | 27.8% and 19.8% are the configured values. Real batches hold 71 and 51 of 256 (27.7% and 19.9%), and the run logs average 27.73% and 19.92%. | Fixed in this record |
| A11 | model | Validation is reused for tuning, epoch selection and the power check. | Stands | Validation scores are optimistic. The verdicts use the test split and the fresh holdout only. | Disclosed |
| A12 | model | A1 and B train on no clean images. | Stands | Deliberate. A2 is the arm that adds them. | Disclosed |
| A13 | model | Baselines train on 600 real images per class. | Stands | Every class has at least 680 training images. Baselines are reference points only. | Disclosed |
| A14 | model | model.py still names three blocks as its default. | Stands | The default and its docstring now say four blocks. | Fixed in iteration 3 |
| A15 | eval | extra_reads is a constant, so that check cannot fail. | Stands | It now counts sealed reads logged by any module other than the evaluator. | Fixed in iteration 3 |
| A16 | eval | The stored error images have no hash check. | Stands | The file carries a model and manifest stamp, and a stale file is ignored. | Fixed in iteration 3 |
| A17 | eval | The gallery refresh forces an extra test read. | Partly | It happens only if the error file is missing, and it is counted. | No action |
| A18 | eval | Prediction cache keys miss preprocessing code. | Stands | The key now includes the preprocessing code. | Fixed in iteration 3 |
| A19 | eval | The bootstrap treats images as independent. | Stands | Comparisons now resample phash_group clusters, with a source-clustered check beside the primary. | Fixed in iteration 3 |
| A20 | eval | The interval covers test sampling, not seed variation. | Stands | Seed differences are reported separately. The preregistration says nothing changes after a test read. Left for the next iteration's preregistration. | Disclosed |
| A21 | eval | Nothing checks that ensembles have equal size. | Does not stand | The seed sets must match or the comparison raises an error. | No action |
| A22 | eval | The per-class harm rule has no multiple-testing correction. | Stands | The rule now uses a Bonferroni-corrected interval and the paired drop's bootstrap standard error. | Fixed in iteration 3 |
| A23 | eval | Rule 1 needs the interval above 0, not above the minimum gain. | Stands | This is the pre-registered rule, so it is intended. Iteration 2 fails either way. | No action |
| A24 | eval | McNemar is not exact for small counts, and differs from the primary metric. | Stands | McNemar is exact under 25 discordant pairs. Holm now uses bootstrap p-values on the same metric as the primary. | Fixed in iteration 3 |
| A25 | eval | The power check is optimistic. | Stands | Treat it as a rough lower bound on the interval width. | Disclosed |
| A26 | eval | One random generator is shared across analyses. | Stands | Each analysis has its own named generator. | Fixed in iteration 3 |
| A27 | eval | A2 has no pairwise test against A1 or B. | Partly | A2 vs A1 is now in the secondary comparisons. | Fixed in iteration 3 |
