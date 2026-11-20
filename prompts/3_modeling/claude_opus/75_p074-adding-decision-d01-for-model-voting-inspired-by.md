# 3_modeling - P074: Adding decision D01 for model voting inspired by MLP voting
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P074. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

add the decision to add voting as a way to increase the quality of our model overal performacen it cam as inspiration from mlp voting

## Response

The weighting of the vote is already recorded as C40, which covers the team disagreement between equal and weighted voting. What is not recorded is the decision to add voting at all, or where the idea came from. I will add it as a new decision entry, D01. A new C number would clash with the IDs in your iteration log.

##### What was updated

The CSV was updated, but the two rows in the readable table did not match my pattern, so I fixed those rows directly. I added **D01**, the decision to use voting, to [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv), which now has 89 entries.

- **Summary:** add model voting to raise overall performance, by combining the class probabilities of several models instead of trusting one.
- **Inspiration:** voting across MLP models.
- **Stage:** 3_modeling (CRISP-DM: Modeling).
- **Commits:** `3deea10` (planned the vote) and `916e7df` (built it). Both are linked in [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md) as tasks T54 and T75.
- **Related entries:** C40 (the weighting disagreement) and F30 (the scoring bug in the vote comparison).

##### Evidence from your results

The results support the decision. On the test split, the 5-seed vote beat the average single model for every arm. Figures are macro F1, from `metrics.csv`:

| Arm | Average single model | 5-model vote | Gain |
|---|---|---|---|
| A0 | 94.6 | 95.5 | +0.9 |
| A1 | 95.8 | 96.2 | +0.4 |
| B | 95.6 | 95.8 | +0.2 |
| A2 | 95.8 | 96.0 | +0.2 |
| P | 95.8 | 96.2 | +0.4 |

C40 then settled the weighting: equal weights scored 95.59, against 94.80 for per-class weights.

##### What is still missing

The model columns of D01 are still empty. I need to know whether voting was the team's own idea, inspired by MLP voting from class, or whether an LLM suggested or helped design it. That answer decides the values for `proposed_by`, `llm_involved` and `llm_role`.

##### Why the attribution fields are left empty
- The attribution worksheet exists to show who proposed each decision and whether an LLM shaped it. Filling those columns from a guess would misstate the origin, so they stay empty until the team confirms the source.
- The result table supports voting on its own merits. The gains were positive for every arm, and the largest was A0 at +0.9 macro F1. Those figures are from `metrics.csv`, so they are taken from the repo, not recalled.
- The weighting question (equal versus per-class weights) is settled separately in C40, where equal weights scored 95.59 against 94.80. That result is why the weighting is not repeated in D01.

##### Consequences
- D01 is recorded with its evidence, but its attribution is incomplete until the origin question is answered.
- The commit links (`3deea10`, `916e7df`) and task links (T54, T75) are taken from the cross-reference file and were not re-read in this session.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
