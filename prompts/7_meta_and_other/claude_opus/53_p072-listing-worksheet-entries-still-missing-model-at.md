# 7_meta_and_other - P072: Listing worksheet entries still missing model attributions
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P072. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

which ones are still missing

## Response

Nothing has changed since my last check. Two files are still missing a model.

##### Issue worksheet: 27 of 88 entries missing

26 of these entries have a team member as `proposed_by`, but no LLM entry:

| Stage | Entries |
|---|---|
| Data integration | F13 (test split already read), F18 (holdout build killed) |
| Cleaning | F01 (QuickDraw diamonds) |
| Transformation | C05 (framing margin), C06 (thin-stroke path) |
| Modeling | F03 (GPU stall), F11 (epochs and early stopping), F12 (polarity experiment), F19 (worker-pool crash), F21 (slow batch preparation), F24 (GPU pixel conversion), C13 (5 seeds per arm), C26 (CV winner selection), C29 (60-epoch budget) |
| Testing | F14 (A2 vs A0 failed), C23 (damage-level comparison), C42 (clean-clone rehearsal) |
| Deployment | F27 (report macro names), F31 (F14 page numbers), C41 (Section L), C46 (Animate button), C50 (failure timeline), C52 (models section), C53 (one config per model), C54 (screen review fixes), C55 (stage explanation block) |
| No proposer either | C40 (vote weighting, the team disagreement) |

For each entry, set `llm_involved` to `opus_medium_5.5`, `gemini_4_neon`, `both` or `none`, and set `llm_role` to match. If all 26 member-proposed rows used no LLM, I can set them all to `none` in one step.

##### Why these rows are grouped this way
The table groups the missing rows by course stage, so each group can be checked against the same evidence. Most rows have a team member as proposer, which means the decision was human and the only open question is whether a model was used in the work. The no-proposer row (C40) is handled separately because it has no proposer at all.

##### Consequence
Setting all 26 rows to `none` is a single bulk decision with a real risk: a row where a model did help would then be recorded wrongly. The answer offers the bulk step only on confirmation.

##### Commit table: all 85 tasks missing

Nothing has been filled in [commit_tasks.csv](../../../results/llm_comparison/commit_tasks.csv). I can fill the 42 commits linked to issues automatically from the worksheet. The other 43 need your input.

##### Why the commit table is separate
The worksheet records issues, while the commit table records tasks. A commit can solve several issues or none, so the model for a commit is derived from the issues it solved. Filling the commit table from the worksheet keeps the two files consistent, but only after the worksheet itself is complete.

##### What is still open
- The 27 missing worksheet entries, which include C40, must be resolved first, because the commit table depends on them.
- The 43 commits with no linked issue (feature, documentation and maintenance commits) have no derived model and need the user's input.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
