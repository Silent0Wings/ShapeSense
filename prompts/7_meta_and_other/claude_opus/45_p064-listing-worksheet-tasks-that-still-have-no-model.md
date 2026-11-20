# 7_meta_and_other - P064: Listing worksheet tasks that still have no model assigned
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P064. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

which tasks have no model assnged to them

## Response

##### Summary

**79 of the 88 entries have no model assigned, and 2 are only half filled.** Only 7 entries are fully attributed: F06, C04, C08, C11, C12, C17 and C40.

##### Half-filled entries (2)
- **F04** (B vs A1 failed): `caught_by` is test, but `proposed_by` is empty.
- **C28** (robustness check moved into Stage 5): `proposed_by` is gemini_4_neon, but `caught_by` is empty.

##### Entries with no model at all, by stage (79)

|Stage|Failures|Changes|
|-|-|-|
|Data (integration, cleaning)|F01, F05, F13, F18|C01, C02, C24, C34|
|Data preparation (augmentation, synthetic)|F07, F08, F09, F10|C03, C05, C06, C07, C35|
|Modeling|F02, F03, F11, F12, F17, F19, F20, F21, F22, F23, F24, F25, F30|C09, C10, C13, C14, C25, C26, C27, C29, C30, C31, C32, C37, C38, C39, C48, C53|
|Evaluation / testing|F14|C15, C16, C20, C21, C22, C23, C36, C42|
|Deployment / dashboard / report|F15, F16, F26, F27, F28, F29, F31|C18, C19, C33, C41, C43, C44, C45, C46, C47, C49, C50, C51, C52, C54, C55, C56, C57|
|**Total**|**29**|**50**|

##### Rows to fill first
- **F07 to F10 and C03, C05, C06, C07:** the rotation, framing, thin-stroke and stroke-width defects. They came out of the investigation into why augmentation and synthetic data hurt, so you may remember who found each one.
- **F01 and C01:** dropping the QuickDraw diamonds, your only real cleaning step.
- **F24:** the log says an outside report recommended dividing by 255 on the GPU. You measured that and rejected it. If you know which LLM made the recommendation, it is a clear example of not trusting an LLM blindly.
- **F14, C15 and C23:** the pre-registered tests and the iteration 3 redesign.

The 24 deployment and dashboard rows count for little in this course, so they can stay blank.

##### Why this list is useful
The table groups every entry without a model by stage, so the gaps can be read against the PDF's 30% per-stage section. Ordering the "rows to fill first" by the findings they support means the most graded evidence is filled first.

##### Caveat on the counts
The answer counts 79 entries with no model, 2 half-filled and 7 fully attributed. Those add up to the 88 rows. The record does not say the counts were re-checked against the worksheet file itself.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
