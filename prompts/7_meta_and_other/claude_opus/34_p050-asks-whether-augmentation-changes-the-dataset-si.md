# 7_meta_and_other - P050: Asks whether augmentation changes the dataset size in MB
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P050. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

35 MB with augmentation would be how much ?

## Response

It stays at about **35 MB**. Augmentation adds nothing to the dataset on disk.

##### Why augmentation does not change the size
- [configs/pipeline.yaml](../../../configs/pipeline.yaml) shows that augmentation (rotation, scaling, shear, noise and blur) is applied on the fly to each training batch.
- The Stage 3 synthetic shapes are also generated during training, not saved to disk.
- In the older copy, the Stage 2 and Stage 3 output folders take up about 1 MB. That is settings and metadata, not images.
- Each augmented image exists in memory for one training step and is then discarded.

##### Sheet value
The sheet value stays:

```
18,000 rows (images), 35 MB
```

The other teams report what they collected, so augmentation does not belong in this cell. If you want to mention it, it fits in the presentation's transformation step.

##### Why this matters for the sheet
Dataset size on disk is a property of the stored data. Augmentation is a training-time transformation, so it changes what the model sees but not what is saved. Reporting the augmented size would overstate the data the team collected.

##### What was verified
The claim that augmentation runs per batch rests on the config file the answer cites, which was not re-read for this expansion, so it stays as the original answer states it. The Stage 2 and 3 output sizes (about 1 MB) come from the older copy, not the current repo.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
