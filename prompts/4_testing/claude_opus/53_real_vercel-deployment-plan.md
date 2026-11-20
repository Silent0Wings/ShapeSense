# 4_testing - Planning the Vercel deployment

> **Edited for publication (2026-11-20):** one word for a shared commit-author trailer is written as "shared-author" throughout, because the repository's commit guard rejects the original word. Nothing else was changed.

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 to 2026-11-10 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: D02
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [D02](../../4_testing/claude_opus/48_D02_deploy-the-project-online-export-the-five-mo.md)

## Prompt 1 (16:41)

> create a final stage in documentataion , once the experiment is done , all stages done and we reach a pass on all metrics , we then setup a ffrozen version of dashboard in a isolated folder at root that will be deployable on vercel , with active onnx models that can be interacted with , this will be done once 100% fully done and the user aproves of the work ,

## Response 1

I'll check where the stages are documented so this goes in the right place, and what the export already provides.

Now I'll write the stage brief and link it from the places that list the stages.

Written for: your team and whoever builds this stage later.

The final stage is now documented as Stage 7 in `stages/stage_7.md` and committed locally. Nothing has been built, and the `deployment/` folder won't exist until the stage starts. The README, `implementation.md` and the Stage 6 brief now point to it.

**What it sets out**
- **The site:** a frozen, static copy of the dashboard in its own `deployment/` folder at the root, deployable on Vercel. Every number is fixed and every file's hash is recorded.
- **Live models:** the ONNX models run in the visitor's browser, so there's no server and drawings never leave their device. The stage requires a test proving browser preprocessing matches the Python version.
- **What it can't include:** sealed test or holdout images, and controls that need Python. Those are removed or shown as pre-rendered examples.

**Four gates must all be met before any file is written**
1. All stages are finished and the final iteration is closed.
2. The pre-registered main verdict is Pass and every validity check passed.
3. A license is chosen and image rights are cleared. I added this gate because `export/README.md` says the code and weights have no license yet, and a public site needs one.
4. You approve a specific commit in writing and say it can be published. A finished goal or passing tests doesn't count as approval.

**Check that gate 2 is what you meant**
I took "pass on all metrics" to mean the main verdict plus all validity checks. The secondary comparisons aren't included, since they only report differences between models and have no pass mark.

Iteration 2 failed this kind of test, and iteration 3 may fail too. If it does, the site stays blocked until a new pre-registered iteration passes or you waive the gate in writing, and the site would have to state that waiver on its first page. The pass rule itself never gets loosened to open the gate.

The experiments are at 58 of 108 and the 5-minute watcher is still on.

The watcher restarted at 16:43 with 58 of 108 trials done.

## Prompt 2 (14:42)

> if you had open questions about how to delpoy to vercel onnx runtime or pythhon what questions would you ask ?

## Response 2

These are the questions I'd ask, grouped by the decision each one settles. My guess at the likely answers is at the end.

**What goes online**
1. Is it the whole Studio (all stage pages, charts and the CRISP-DM record) or only the live "Draw and predict" page?
2. Public link, or private behind a password or Vercel's login?
3. Which data may leave the laptop? Today the allowlist decides that at runtime. A deploy would freeze it into public files, so every artifact that ships needs a yes. Sealed data never ships.

**Where the model runs**
4. In the visitor's browser with `onnxruntime-web`, or on Vercel in a Python function? Each model has only about 242k parameters, so the browser can handle it easily. A Python function would hit Vercel's bundle-size limit if it included PyTorch, and it brings cold starts.
5. Which models does the vote panel need online? All five (A0, A1, B, A2, P), and one seed each or every seed? That sets how many ONNX files ship.
6. How strict should the match with PyTorch be? I'd export to ONNX and require identical predictions on the validation drawings, never the test set. The 64×64 preprocessing would also have to be rewritten in JavaScript and checked the same way.

**Account, repo and upkeep**
7. Whose Vercel account, and which plan? The free plan is for non-commercial use only.
8. There's no git remote yet. Should I deploy from GitHub (that needs a remote and a push, which is your decision) or straight from the Vercel CLI?
9. Which branch: `iteration-3`, or `main` after the merge?
10. Vercel can't rerun the training pipeline. When results change, should the deploy rebuild from committed exported files, and who triggers it?
11. Should drawings people make on the live page be stored? I'd assume no, for privacy.
12. Does the deploy wait for the open human items: license, Stage 7 approval and the rubric check?

**What I'd recommend if you have no strong preference:** export the pages to static JSON, convert the models to ONNX, and run them in the browser. You'd get a free static site with no Python server and nothing to keep running. Questions 2, 3, 7 and 8 are the ones only you can answer.

The Atlas capture is still running, with the stall watcher on it. I'll open the review page when it finishes.

The Atlas review page isn't open yet. The first capture got only part of the way, because my command had a 10-minute limit that cut it off. It saved all 17 light screens and 8 dark ones. So far, 19 of those 25 screens differ from your approved versions, which fits the stage page changes.

The remaining 9 dark screens and all 17 mobile screens are capturing now in the background, with the stall watcher on. When that finishes, I'll open the review page on port 8097 so you can go through every changed screen. I won't approve anything myself.

## Prompt 3 (14:47)

> create a plan md in that same non tracked folder that has detailed staged plan entires to how to implement the full thing

## Response 3

I'll look at how the Studio currently serves pages and predictions, then write a staged plan based on the real code paths.

The models are already exported to ONNX for the Studio, which makes this simpler. I'm checking the export bundle and its preprocessing next.

I have what I need. Writing the plan now.

I wrote the plan to [ignore/notes/vercel_deploy_plan.md](ignore/notes/vercel_deploy_plan.md), next to the research notes. It isn't tracked by git.

It has 12 stages, from your decisions through to upkeep. Each stage lists its tasks, the files involved and how we know it's done. It's based on the real Studio code, which turned up a few things the research notes didn't cover:

- **The models are already ONNX**, about 1 MB each, so the browser can load them as they are.
- **Preprocessing is the hard part.** It isn't a simple resize: it uses scipy filters, hole filling, erosion and outline redraw, plus Pillow's own resizing. The plan ports it to JavaScript and requires it to match Python byte for byte on test drawings. If that can't be reached in about 2 days, there are two fallbacks: run the real Python in the browser, or run it in one Vercel Python function.
- **The Stage 2 and 3 sliders can't be precomputed for every setting.** By default the deploy shows saved previews at fixed slider values. The other option is a small Python function to keep them fully live.
- **Two data questions only you can answer:**
  - The Evaluation page shows misclassified test-set images. The plan keeps them out of the public site by default.
  - Training images can only go public if each dataset's license allows it.

The rough total is 8 to 10 working days. A read-only version of the site, without live drawing, could go up as a protected preview after about 2 days.

The Atlas capture is still running. I'll open the review page when it finishes.

All 51 screens are captured. I'm counting the changed ones and opening the review page.

The review page is open in your browser at http://127.0.0.1:8097/. All 51 screens were captured, and 43 of them differ from the approved versions.

Most of the changes are expected:
- All seven stage pages have the new explanation block and navigation.
- Home, Business and Live share the updated layout.
- Changes, Failure and Failures pick up the new CRISP-DM log entries, including F31.

Experiments changed only on mobile, so it's worth a closer look. The other 8 screens match.

Approve or deny each screen there. I haven't approved anything. Tell me when you're done and I'll stop the review server and run a final check.

## Prompt 4 (17:30)

> adjust the plan so that all the work for deployement has to happen in =[""C:\Users\Gica\Github_Clones\ShapeSense_Deployed""]

## Response 4

First I'll check whether the folder exists and how the Studio reads the Stage 5 prediction files. Moving the build out of the repo changes which files it touches.

I haven't implemented anything. I've only edited the plan files, and `ShapeSense_Deployed` is still empty. The last step is updating the paths in the fallback file to match.

I've only changed the plan, nothing else. `ShapeSense_Deployed` is still empty, and the ShapeSense repo has no new changes. The plan now says where every piece of the work would happen.

**Where the work happens:**
- **`ShapeSense_Deployed`** would hold all of it: code, its own Python environment, the npm packages, fixtures, tests, the built site, the Vercel project (in `site/`) and its own git repo.
- **`ShapeSense`** is read-only for the deploy. The build only reads its code, results and models. A source guard checks before and after each run that nothing in it changed and that the access log is still at 157 lines.
- **Plan notes stay** in `ShapeSense/ignore/notes/`, since they're planning rather than deployment work.

**What changed in the plan because of the move:**
- **The repo-root problem goes away.** Vercel never sees ShapeSense's `requirements.txt` with torch and gradio.
- **Page changes become an overlay.** Instead of editing `studio/web/js`, the deploy's files are laid over a copy of the pages in the built site. The build stops if the original `api.js` changes upstream, so the overlay can't silently fall out of date.
- **Imports from ShapeSense can't leave `__pycache__` behind.** Bytecode writing is turned off when the deploy's scripts import ShapeSense code, and the source guard checks for stray cache folders.
- **Decision D10 is new.** It covers the only two writes the deploy would ever make to ShapeSense: the CRISP-DM log entry and the URL in the README. Both happen only at go-live, with your OK.

**One new risk:** the Stage 5 confusion counts are read from the sealed prediction files. The plan's default (D3) is that the build never calls that endpoint. The Evaluation page would use the existing confusion images instead.

Both [vercel_deploy_plan.md](ignore/notes/vercel_deploy_plan.md) and [vercel_server_fallback.md](ignore/notes/vercel_server_fallback.md) use the new paths.

## Prompt 5 (17:34)

> the plan should be we move the parts needed to the new folder and deploy as a standolone representaion of this work =[
>
> <pasted_content id="8717">
> I've only changed the plan, nothing else. ShapeSense_Deployed is still empty, and the ShapeSense repo has no new changes. The plan now says where every piece of the work would happen.
>
> Where the work happens:
>
> ShapeSense_Deployed would hold all of it: code, its own Python environment, the npm packages, fixtures, tests, the built site, the Vercel project (in site/) and its own git repo.
> ShapeSense is read-only for the deploy. The build only reads its code, results and models. A source guard checks before and after each run that nothing in it changed and that the access log is still at 157 lines.
> Plan notes stay in ShapeSense/ignore/notes/, since they're planning rather than deployment work.
> What changed in the plan because of the move:
>
> The repo-root problem goes away. Vercel never sees ShapeSense's requirements.txt with torch and gradio.
> Page changes become an overlay. Instead of editing studio/web/js, the deploy's files are laid over a copy of the pages in the built site. The build stops if the original api.js changes upstream, so the overlay can't silently fall out of date.
> Imports from ShapeSense can't leave __pycache__ behind. Bytecode writing is turned off when the deploy's scripts import ShapeSense code, and the source guard checks for stray cache folders.
> Decision D10 is new. It covers the only two writes the deploy would ever make to ShapeSense: the CRISP-DM log entry and the URL in the README. Both happen only at go-live, with your OK.
> One new risk: the Stage 5 confusion counts are read from the sealed prediction files. The plan's default (D3) is that the build never calls that endpoint. The Evaluation page would use the existing confusion images instead.
>
> Both vercel_deploy_plan.md and vercel_server_fallback.md use the new paths.
> </pasted_content id="8717">
>
> ] does that clear confusion ?

## Response 5

Yes, that clears it up. I had planned for a deploy folder that reads ShapeSense live on every build. You want a standalone snapshot: copy what's needed into `ShapeSense_Deployed` once, and from then on it builds, tests and deploys on its own, with no link back to ShapeSense.

**What the plan would change to:**
- **A single copy step, run from inside `ShapeSense_Deployed`.** It reads ShapeSense once and copies in only what the site needs:
  - the pages (`studio/web`)
  - the five models and `labels.json`
  - the approved result files and images from the allowlist
  - the small pieces of Python the parity tests compare against: `standardize.py`, the vote and softmax code, and `whatif.py`
  - the saved page data and Stage 2 and 3 previews, generated once during that step
- **A manifest records what was copied:** the ShapeSense commit, plus each file's source path and hash. That says exactly which version of the work the deployed site represents.
- **After that, ShapeSense isn't needed.** The overlay, tests, build and Vercel deploy all run from the copied files. No ShapeSense imports, no `PYTHONPATH` to it and no live reads.
- **Updating means re-running the copy step.** After a retrain, the copy step runs again, and the manifest diff shows what changed.
- **Things that get simpler:**
  - The source guard shrinks to one check around the copy step.
  - The overlay drift check now compares against the copy, not the live repo.
  - The `__pycache__` risk goes away, because nothing imports from ShapeSense after the copy.
- **Things that stay the same:**
  - Sealed files are never copied.
  - The Stage 5 confusion counts still come from the confusion images, not the prediction files (D3).
  - Torch and gradio never come along.

I'm reading "move" as **copy**, so ShapeSense keeps all its files and keeps working as it does now. If you meant actually removing parts from ShapeSense, say so, because that would break its pipeline and dashboard.

Should I rewrite the plan this way?

## Prompt 6 (22:52)

> is the content of this =[C:\Users\Gica\Github_Clones\ShapeSense_Deployed\ignore] still valid , not your work this will be handed off to another session to work on a deployable vercel version , prepare it with enough context to staart cleanly what to copy where to get the files

## Response 6

I'll check the deploy notes against the repo as it stands now, then rewrite them for the standalone-copy model and add a handoff file, so a new session can start from the folder alone. First, the main plan:

The plan still describes the old read-in-place model and has a few stale facts. I'll gather the facts a copy list needs: what the Studio reads, what it imports, and how big it is.

Page bundles don't read the sealed prediction files. Next I'll check which API calls the web pages make, so the snapshot list is complete.

Next I'll check that the copy sources exist and how big they are.

All 77 allowlisted files exist, about 4.3 MB in total, and the samples come back as base64 PNG inside JSON. Next, the rest of the stage 7 brief, which the deploy has to satisfy:

The brief's R16 fails the build on absolute local paths, and some allowlisted status files contain `C:\Users\Gica…`. I'll find out exactly which ones, and confirm the referenced test files exist.

Now the other two notes. I'll find their stale references: the read-in-place model, `deploy/` paths, the guard path and the unmerged-branch assumption.

I'll put the no-shared-author commit rules and your saved preferences into the handoff. First I'll read the memory files so they're carried over exactly.

Next I'll confirm the files on the copy list exist and check how big the Atlas tool is.

Now the handoff file, which is the entry point for the new session:

Next I'll check the two reference files I haven't confirmed yet, and update the fallback note for the standalone model.

`test_whatif_parity.py` doesn't exist, even though `whatif.py` names it. I'll find the real what-if test so the copy list points at it.

`ShapeSense_Deployed` already has a `.git` folder, so someone ran `git init` since this morning. I'll check its state so the handoff describes it correctly.

Written for: the next Claude session building the Vercel version.

The notes were only partly valid, so I rewrote the plan and added a handoff file. The new session should start by reading `ignore/HANDOFF.md`. ShapeSense itself is unchanged: its tree is clean and the access log is still 157 lines.

**What was out of date:**
- **The plan still had ShapeSense read on every build.** It used an overlay and a source guard instead of the standalone copy you asked for. I rewrote [vercel_deploy_plan.md](../ShapeSense_Deployed/ignore/notes/vercel_deploy_plan.md) so one script reads ShapeSense once and copies or captures everything into `ShapeSense_Deployed`. After that, the deployed folder never touches ShapeSense, and re-running the script refreshes it.
- **It assumed `iteration-3` still needed merging.** `main` already equals it, at f3b3bdb.
- **It missed rules from the project's own deploy spec (`stages/stage_7.md`):**
  - a `frozen.sha256` manifest of the built files
  - a "frozen record" banner on every page
  - dataset attribution
  - a ban on local paths and personal details
  - removing dead controls such as Feedback
- **Seven of the files the dashboard shows contain `C:\Users\Gica\…`.** The copy step now has to scrub that path and fail if any local path, "Gica" or an email address remains.
- **One test the copy list relied on doesn't exist.** `whatif.py` names `test_whatif_parity.py`, but the real checks are in `tests/studio/test_stage5_views.py`, so the list points there.
- **The fallback and research notes** now match the copy model, and the branch question in the research notes is marked settled.

**What the handoff covers:**
- **Rules:**
  - Your commit rules: no shared-author or AI credit lines, commits only through the guard, a copy of the guard in the new folder, and no pushes unless you ask.
  - The sealed-data rules, and ShapeSense staying read-only.
  - Port 8765 is yours.
- **Your preferences:**
  - Work autonomously.
  - Run long jobs with a 5-minute stall watcher.
  - Record every change. The handoff keeps a running deploy log and moves it into the CRISP log at go-live.
  - Atlas approvals are yours.
  - Subagents are haiku at medium effort, at most 10, with their work verified.
- **The copy list:**
  - what to copy and where to, file by file
  - which endpoints to capture and how, and which ones never to call
  - what must never be copied
  - which files contain your path
- **The current state:** commits, the GitHub repo, test results and the four gates.
- **A first-session order of work.**

**What the new session will ask you first:**
- **Whether a protected preview may be built now.** The deploy spec says no files are written until all four gates hold, and two are still open: a license for the code and model weights, and your written approval to publish. Going public needs both either way.
- **About ten setup choices:** your Vercel account, whether the site starts behind a login, and whether the team's names appear on the site. The plan gives a default for each.

`ShapeSense_Deployed` is already a git repo on `main` with no commits and no remote. The notes folder is git-ignored there.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

The plan was checked against the Vercel documentation the user pasted.

## Our decision

We changed the plan from a deploy folder that reads ShapeSense live to a standalone snapshot in ShapeSense_Deployed (exchange 5).

## Measured effect

Deployment only, with no macro F1 change.

---

## Upgraded & Expanded Analysis: From Read-in-Place Overlay to Standalone Snapshot (`53_real`)

### Why this exchange matters

This six-prompt arc records an architectural plan being **corrected by the user** (Exchange 5): rejecting a read-in-place overlay that imports from `ShapeSense` on every build in favor of a **standalone immutable snapshot** in `ShapeSense_Deployed` (`D02`).

| Aspect | Rejected (Read-in-Place) | Adopted (Standalone Snapshot) |
|---|---|---|
| Copy step | None | Single `tools/snapshot.py` execution reads `SOURCE` once |
| Manifest | None | Records `SOURCE` commit (`f3b3bdb`) + per-file SHA-256 hashes |
| Post-copy builds | Every build reads `SOURCE` | `SOURCE` never touched again; zero `__pycache__` leak risk |
| Path & PII scrubbing | Runtime filter | Copy step scrubs `C:\Users\Gica\...` and fails closed if any local path/PII remains |
| Handoff readiness | Context-dependent | Self-contained `ignore/HANDOFF.md` + 12-stage `vercel_deploy_plan.md` |

### Cross-Session Lineage

* **Related sessions:** [52_real_is-the-project-done-and-final-audit.md](52_real_is-the-project-done-and-final-audit.md) (identifies the four Stage 7 gates $G_1$–$G_4$), [54_real_vercel-deployment-build.md](54_real_vercel-deployment-build.md) (executes the standalone snapshot build and Vercel release).

