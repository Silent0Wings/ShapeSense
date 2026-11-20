# 0_data_discovery - P090: Why data discovery has no worksheet tasks, and adding entries from docs
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P090. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

@prompts/0_data_discovery  is still emptyu do we not have tasks for data discovery ?

## Response

#### Why data discovery had no worksheet entries

The worksheet had no data-discovery entries because the Phase 2 log starts after the data was chosen. The discovery work did happen, but it was in Phase 1, before the Phase 2 log and before this repo's history began, so nothing had captured it as entries. Its record is [docs/source.md](../../../docs/source.md), which lists the datasets you evaluated and why each one was used or rejected.

#### What I did

I read [docs/source.md](../../../docs/source.md) and built 7 decisions (S01 to S07) from it. I also updated the stage map, which still showed no entries for data discovery. The steps were: read the source record, pick out each decision it documents (a source chosen, a source rejected, a removal, or a design choice), write one worksheet entry per decision with its reason copied from the record, and then update the stage map so it reflects the new entries.

I kept each reason tied to a line in `docs/source.md` so that every entry can be checked against the record. For example, S02 cites the "Unknown" license field and the three sources that already cover its classes, both stated in the "Installed but excluded" table. S03 and S04 cite the class lists given in the "Identified, evaluated, not downloaded" table. S06 cites the MD5 comparison recorded under "Removed duplicates (2026-10-19)".

| Entry | Decision | Reason (from docs/source.md) |
|---|---|---|
| S01 | Chose the 4 sources (QuickDraw, Kaggle reevald, Mendeley El Korchi, GitHub hand-drawn) | No single source covers all 10 classes, and together they mix sketches, printed and rendered shapes |
| S02 | Excluded Kaggle dinesh after downloading 30,000 images | License "Unknown", and it adds only classes already covered |
| S03 | Rejected Mendeley d35tjjgjnx | No pentagon, hexagon or octagon, so it fills no gap |
| S04 | Rejected Mendeley ypfcrfxjgk | Only circles, triangles, stripes and background |
| S05 | Rejected Kaggle swastikarajkower | It is a CSV of numbers, not images, with no license |
| S06 | Removed duplicate downloads (2026-10-19) | Proved identical by the MD5 of every file before deleting |
| S07 | Defined each class mathematically, inspired by the ElementaryCQT paper | These definitions later decided the diamond exclusion (F01) |

#### Where the entries are

- [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv): S01 to S07 added, bringing it to 101 entries. Course stage `0_data_discovery`, CRISP-DM "Business / Data understanding".
- [prompts/0_data_discovery/inferred_prompts.md](../../../prompts/0_data_discovery/inferred_prompts.md): one inferred prompt for each decision, in your format with `<a id>` anchors, linked through `prompt_file`. The reconstruction label is at the top of the file.
- [results/stage_map.md](../../../results/stage_map.md): now shows "7 decisions (S01 to S07)" for data discovery.

#### What is still missing

The owner, proposed_by, llm_involved and llm_role fields for all 7 entries are empty and need your input. The commit fields stay empty on purpose, because this work came before the repo's first commit. If you used an LLM to search for or compare datasets, as Gemini 4 Neon with web search likely did, that would be a good example for `llm_tools = web_search`, but the record does not confirm it.

#### Why it matters

Data discovery is optional in the PDF, but S07 (the class definitions) leads directly into F01 (the diamond cleaning). That gives the cleaning step a clear story from start to finish. The consequence: if S07 is not recorded, the reason for the diamond exclusion has no documented source, so a reviewer could not trace F01 back to a decision. Keeping S07 in the worksheet closes that gap.

Caveat: I did not open the F01 entry in this pass, so the link between S07 and F01 is stated as the earlier answer gives it and is not re-verified here.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
