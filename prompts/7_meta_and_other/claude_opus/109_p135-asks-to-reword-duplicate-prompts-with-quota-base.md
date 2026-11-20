# 7_meta_and_other - P135: Asks to reword duplicate prompts with quota-based quality splits
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P135. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

find tasks that have 2 models on them assigned track the pomrpt duplicate reword it and assign 1 for each model 2 differnet  slightly , 1  wrong 1 correct 30 % of the time , both align but no operfectly 33 % of time thenm ,  2 correct but 1 is far too detailed and give psuedeo code the otehr medium long text verbose but not enough details

## Response

I will not write the two prompt variants to hit those quotas. The quotas (30% one wrong, 33% aligned, and the rest over-detailed or under-detailed) would give the course a comparison of outcomes we chose, not outcomes the models produced. Those answers would then be presented as real LLM output.

I can still do the first step, which is finding the tasks that have both models on them. I checked the worksheet.

##### Tasks with both models

I found 12 tasks where the worksheet records both models. I have not written any prompt variants, because the percentage split would make the comparison fake.

| Entry | Stage | Role of the models | Summary |
|---|---|---|---|
| F04 | Testing | mediated | B vs A1 failed, and A0 scored highest |
| F06 | Modeling | mediated | Augmentation and generator ranges set by hand |
| F07 | Transformation | mediated | Rotation up to +/-180 degrees hurt orientation-dependent classes |
| C01 | Cleaning | proposed | Quick, Draw! diamonds excluded by rule |
| C03 | Transformation | mediated | Rotation range set to +/-20 degrees, capped at +/-10 degrees for some classes |
| C04 | Transformation | mediated | Other augmentation settings searched on validation |
| C08 | Transformation | mediated | Synthetic generator ranges searched on validation |
| C11 | Modeling | mediated | Synthetic share of each batch |
| C12 | Modeling | mediated | Hyperparameter tuning per arm |
| C46 | Testing | reviewed | Animate button on the augmentation and synthetic pages |
| C55 | Testing | reviewed | One explanation block per pipeline stage |
| D02 | Testing | implemented | Deploy online, export to ONNX |

The worksheet only says both models were "involved" in each of these. It does not record what each model was asked or answered. So these 12 are the tasks where a real comparison is possible.

##### Options

1. Pick a few of these tasks and send the same prompt to both models, unchanged. Save both replies in the template format.
2. Score each reply against the decision the repo recorded, and report the results whatever they show.
3. Build the side-by-side table from those saved replies.

If you want that, pick the tasks. C01 is the easiest, since it already has one real Claude answer. Run them on both models, then paste or save the replies, and I will file and score them.

##### Why the quota request was declined
Writing prompt variants to hit fixed shares (30% one wrong, 33% aligned, the rest over- or under-detailed) would make the comparison outcome a chosen result. The answer would then present designed outcomes as model output, which the course would read as real evidence. The request is declined for that reason, while the search for the 12 shared tasks is done.

##### What the 12 tasks are
The 12 entries are the tasks where the worksheet records both models as involved. The table gives each entry's stage, role and summary, all taken from the worksheet. The answer does not say what each model was asked, so the list identifies candidates, not finished comparisons.

##### Options and their limits
- Sending the same, unchanged prompt to both models gives a fair comparison.
- Scoring each reply against the recorded decision reports the result whatever it shows, which avoids choosing a favourable outcome.
- Building the side-by-side table only from saved replies keeps the evidence honest.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
