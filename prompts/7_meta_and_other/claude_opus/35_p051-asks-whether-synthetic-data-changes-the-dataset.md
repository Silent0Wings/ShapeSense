# 7_meta_and_other - P051: Asks whether synthetic data changes the dataset size
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P051. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

what about synthethic data ?

## Response

##### Short answer

Synthetic data does not change the dataset size either. The dataset is still **35 MB** on disk.

##### Why it does not add to the size

The Stage 3 synthetic shapes are drawn by code during training, and they are never saved as files. Depending on the model, they make up about 12% to 17% of each training batch. That share is set by `synthetic_fraction` in [configs/pipeline.yaml](../../../configs/pipeline.yaml). This is also why the Stage 3 output folder holds only about 1 MB of settings and metadata.

##### Why it does not belong in the sheet

The cell asks what you collected from the data sources. Synthetic shapes do not come from any source, so they do not belong in that answer.

##### If you want to mention them anyway

Use this version, which is accurate:

```
18,000 rows (images), 35 MB (plus synthetic shapes generated during training, not stored)
```

##### Why synthetic data is handled like augmentation
Both are generated while training runs, so neither adds stored bytes. The 12% to 17% batch share is set by `synthetic_fraction` in the config, as the answer states; the exact values were not re-checked here. The note in parentheses keeps the sheet accurate if a reader asks about the generated shapes.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
