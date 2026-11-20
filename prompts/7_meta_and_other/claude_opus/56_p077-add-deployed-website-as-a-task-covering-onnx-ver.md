# 7_meta_and_other - P077: Add deployed website as a task, covering ONNX, Vercel and interactive presentation
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P077. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

also add the deployed website as a task , deploying and buikldng the onnx and resarching vecel documentaiton to deploy the model online as a inferedbakle backewned interactive + intearctive slide , built by opus end gemini neon by all memebers

## Response

I will add the deployed website as one task. Its work lives in the separate `ShapeSense_Deployed` repo, which I cannot run git on, so the dates come from that repo's README.

#### A correction to the wording

The site has no server-side backend. The README says the five ONNX models "run in the visitor's browser through ONNX Runtime Web, so there is no server". The entry describes it that way.

The summary counts at the top of the task table are now out of date. I will regenerate them from the CSV.

#### What I added

I added the deployed site as a task, and found and added 13 more tasks from the deployed repo.

**The deployment task: D02** in [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv), which now has 92 entries.
- **What it covers:** exporting the five models to ONNX, researching Vercel's documentation, and publishing the site with live, interactive prediction (draw a shape, and all five models and their vote predict it), plus the interactive six-part presentation.
- **Owner:** all members.
- **LLMs:** both, role `implemented`.
- **Commits:** linked to `6e633e7` (ONNX export, T11) and `6f6f4a4` (Stage 7 plan, T53) in this repo.

#### The inference backend

There is no server. The models run in the visitor's browser through ONNX Runtime Web, and the browser results were checked against Python (within 1e-4). The entry describes it that way.

#### Tasks I missed from the deployed repo

I read its history file as a plain file, without running git, and added these to [commit_tasks.md](../../../results/llm_comparison/commit_tasks.md):
- **T86:** the whole deployment, as one umbrella task.
- **T87 to T90:** four releases from the `freezes/` folder: protected preview, public 1 and public 2 (all 2026-11-11), and the phone layout.
- **T91 to T99:** nine commits from 2026-11-16 and 2026-11-17:
  - Stage explanations.
  - **The six-part presentation, one part per presenter.**
  - Presenting 90% of the source repo.
  - Graphic slides.
  - The animated CRISP-DM wheel and hover help.
  - Conclusion dots and sliders.
  - The 11-16 release.
  - **The Predict button.**
  - The 11-17 release.

The task list now has 99 tasks, and I refreshed the counts at the top of the table. The tasks that mention the presentation are noted as part of the presentation deliverable, since that is 10% of the grade.

#### One gap I cannot close

The deployed copy was cloned on 2026-11-16, so its history file only has commits from after that date. The commits that built the site from 11-11 to 11-16 exist only as release snapshots. If you run the command below in `ShapeSense_Deployed` and save the output, I will add those commits too:

```
git log --reverse --date=short --format="%h|%ad|%s" > ..\ShapeSense\ignore\deployed_commits.txt
```

##### Why the deployed site is one umbrella task
The site is the main deliverable for the deployment and presentation parts of the course. Its work spans ONNX export, Vercel research, in-browser prediction and the interactive presentation, which are one piece of delivered work, so D02 is a single row with all members as owner.

##### What was checked
- The "no backend" claim was taken from the deployed repo's README, which the answer quotes. The browser-versus-Python agreement (within 1e-4) is the answer's own report and was not re-run here.
- The task count (99) and the new D02 row count (92 entries) are the answer's totals after these additions.

##### Consequence
The early build commits (11-11 to 11-16) are still missing, because they exist only as release snapshots in the deployed history. Until the user runs the export, those dates and commit links remain open.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
