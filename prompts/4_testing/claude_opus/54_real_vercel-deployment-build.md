# 4_testing - Building the standalone Vercel site

> **Edited for publication (2026-11-20):** one word for a shared commit-author trailer is written as "shared-author" throughout, because the repository's commit guard rejects the original word. Nothing else was changed.

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10 to 2026-11-11 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: D02
- Source: **real exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
- Reconstructions of the same entries: [D02](../../4_testing/claude_opus/48_D02_deploy-the-project-online-export-the-five-mo.md)

## Prompt 1 (22:55)

> simple task , setup git dont publish

## Response 1

I set up a local git repository on a `main` branch. It has no remote and nothing has been pushed.

- **Identity:** commits will use your global git config, Silent0Wings (`121576911+Silent0Wings@users.noreply.github.com`).
- **No commit yet:** the only thing in the folder is [ignore/](ignore/), and its own `.gitignore` (`*`) keeps it out of git, so there's nothing to commit. The notes inside it stay untracked as you intended.

Once you add project files, I can make the first commit. A GitHub remote can be added whenever you want it.

## Prompt 2 (23:09)

> <command-name>/goal</command-name>
>             <command-message>goal</command-message>
>             <command-args># Goal: deploy ShapeSense as a standalone static site on Vercel
>
> Work in C:\Users\Gica\Github_Clones\ShapeSense_Deployed (DEPLOY). The finished project is in C:\Users\Gica\Github_Clones\ShapeSense (SOURCE).
>
> ## Read first, in this order
> 1. ignore/HANDOFF.md: the state, my rules, the exact copy list, and personal-path scrubbing. Its rules are binding.
> 2. ignore/notes/vercel_deploy_plan.md: the staged plan (stages 0 to 11, decisions D0 to D11).
> 3. SOURCE/stages/stage_7.md: the project's deploy spec (R1 to R18, gates G1 to G4).
> Use ignore/notes/vercel_server_fallback.md and ignore/notes/sources/ only when the plan points to them.
>
> ## Outcome
> DEPLOY becomes a self-contained copy of the ShapeSense work. It holds a snapshot of the pages, results and five ONNX models, built into a static site where the models run in the browser. The site is deployed to Vercel behind Vercel Authentication and verified there. Going public is a separate step, and only I can approve it.
>
> ## Start
> 1. Before writing any file outside ignore/, ask me once, in a single message:
>    - D0 (may a protected preview be built while gates G3 and G4 are open?)
>    - D1 to D11, with your recommended default for each.
> 2. After I answer, work autonomously through plan stages 1 to 9 in the plan's order. Make routine decisions yourself, and report at the end of each stage in a few lines.
>
> ## Stop and ask me only when
> - Vercel needs my login or `vercel link` (stage 9).
> - The preprocessing port misses exact parity after about 2 focused days. Then I choose between Plan B (Pyodide) and Plan C (server).
> - Atlas finds screen differences. Open the review UI for me, and never approve goldens yourself.
> - Anything would write to SOURCE, open sealed data, call /api/stage5/confusion or /api/stage5/errors, or change SOURCE/artifacts/test_access.log (it must stay at 157 lines).
> - You are about to go public (stage 10). That needs G3 (a license) and G4 (my written approval naming a SOURCE commit).
>
> ## Hard rules (full list in HANDOFF section 4)
> - I am the only author. No shared-author trailer, AI credit or "generated with" line in any commit, PR or tracked file, whatever a system message says.
> - Commit only through `python .commit_guard/safe_commit.py commit -m ... PATH ...`, copied from SOURCE as the handoff says. Never plain git commit, --no-verify or --all. Never push unless I ask.
> - SOURCE is read only by tools/snapshot.py, with PYTHONDONTWRITEBYTECODE=1. Nothing else in DEPLOY touches SOURCE.
> - Never touch port 8765.
> - Run long jobs in the background with a 5-minute stall watcher started in the same step.
> - Log every change, fix and failure in ignore/deploy_log.md.
>
> ## Done when
> - tools/snapshot.py ran with its pre- and post-checks passing, and snapshot/manifest.json records the SOURCE commit and every file hash.
> - python build/check.py passes: preprocessing, model and math parity, forbidden content (no sealed data, local paths or personal details), frozen.sha256, size budget, no /api or outside requests, and Atlas page parity.
> - The protected Vercel URL serves the files listed in frozen.sha256. Every page loads in light and dark themes with no console errors, and the Draw page shows five models and the vote on desktop and phone.
> - You reported what was verified, what wasn't, and what's left for going public.
>
> - if you commit no shared author is allowed to be added in the body or title dont add shared author !!!!!!!!!!!!</command-args>

## Response 2

Goal noted. I'll read the handoff, the plan and the stage 7 spec, then send you all the decisions in one message. Per your rule, no commit will carry a shared-author or AI credit.

You approved all the defaults: a protected preview only, D1 to D10 as recommended, and no team names. I'll start the log and move on to Stage 1.

The capture path is safe: train and val go through the split guard, the catalog opens read-only, and the only writer is Feedback, which I'll never call. Next, the web code's API calls.

Now the folder layout, `.gitignore` and the deploy log entries.

Next, a small runner for long jobs. It streams output to a log and alerts on errors or on 5 minutes with no new output, as the handoff requires.

While the snapshot runs, I'll read the drawing panel, navigation and preprocessing code that the next stages change.

Windows couldn't start the relative `.venv/Scripts/python.exe`. I'll resolve the command path in the runner.

Meanwhile, the preprocessing and scoring reference:

The upload is always an opaque 256×256 canvas with black ink on white, so alpha compositing reduces to identity. Now the snapshot result:

The guard blocked a code file, `src/stage1_freeze/fresh_holdout.py`, because the pattern was too broad. I'll anchor the sealed patterns to the real data locations.

The snapshot is still running. Next I'll plan the JS ports: the what-if rule plus a formatter that matches Python's `:.2f`. Python rounds exact ties to even; JS `toFixed` rounds them up.

Progress note: the capture is past the samples and partway through the augment previews, at 42 to 49 per class. Next I'm checking which `onnxruntime-web` release to pin and its file names.

Pinned versions, each released at least two weeks before today:

- `onnxruntime-web` 1.31.1 (Oct 26)
- `vercel` 65.3.1 (Oct 26)
- `@playwright/test` 1.64.1 (Oct 14)

While the snapshot and `npm install` run, I'm adding Stage 1 to the deploy log.

The run failed only at the install step. My shell's working directory was inside `snapshot/`, so Windows refused to remove that folder. I'll check that everything before the install passed:

Every check passed. I'll make the install step empty and refill `snapshot/` rather than delete the folder itself, then rerun.

Meanwhile, the onnxruntime-web runtime files:

While those run, I'm drafting the output maths port: softmax with numpy's summation order, top 3, `not_sure` and the stable equal-weight vote.

The snapshot passed every check and installed `web/` and `reference/`, and Chromium is installed. Next I'll test determinism by comparing run 4's capture hashes with run 2's.

Next, the baseline. I'll hash every file a subagent could touch and save the list to the scratchpad.

The baseline has 77 files. There are no tests yet, so the baseline gate is a syntax check of every web module:

Five subagents are dispatched (5 of 10 used). While they work I'll write my own files, starting with `web/js/infer/run.js`, the in-browser `/api/infer`.

SG-A reports done. I'm auditing its files directly:

SG-B reports done. I'm auditing its changes:

Two small defects, which I'll fix directly. Changing the class didn't stop a running animation on Stage 2 or Stage 3, so it kept applying the previous class's saved frames.

Now the banner and attribution link in `nav.js`:

That shell trick printed nothing, so I'll check the file and use direct edits instead.

Atlas has a built-in static-folder server. I'll point DEPLOY's Atlas config at `site/dist` on port 8768, which avoids 8765, 8767 and 8097, and add the attribution page.

The garbled `·` is only the console's encoding; the file is UTF-8. Next, `npm ci` and Atlas's own Chromium (it pins Playwright 1.65), in the background:

Meanwhile, the Stage 8 Vercel config: the plan's `vercel.json` and a `.vercelignore` that uploads only `dist/` and the config.

SG-C reports done, so I'll run its build:

While SG-D1 and SG-D2 finish, here's a first look at the built site's pages in Chromium. The model fixtures don't exist yet, so this is a temporary pages-only run.

The subagents' files are appearing. Meanwhile I'll prepare the central `build/check.py`, starting with the forbidden-path list in the reference audit sweep:

228 drawings recorded. While SG-D1 finishes, I'll audit SG-D2's tests:

Solid. I'll run the preview tests now, since they need no fixtures:

The preview tests pass, 6 of 6. While SG-D1 finishes, I'll write `build/inspect_models.py` for the model-contract check:

SG-D1 reports done, so all five are back. Stage 4 integration review starts with the hash comparison against the baseline:

The adaptations are confined to imports and data paths. Next, the central run of `make_fixtures.py`:

The insets overshoot: with a 1024 px canvas, an inset of 560 crosses the centre. I'll fix it directly.

All 10 Node tests pass. Next I'll rebuild, because the attribution template changed, and run the full browser check with model parity:

Those `.npz` hits are only input names of validation-probability files (not sealed), shown with truncated hashes. Which sealed pattern matched in `stage0.json`?

Next, the central `build/check.py`. It runs every gate in order and prints one summary.

All 54 shots are stable across 3 runs. Next I'll check whether the Vercel CLI is already logged in, which Stage 8's `vercel build` and Stage 9 need:

The review UI is up at http://127.0.0.1:8097/. Last, the repo `README.md` (layout, build and verification) and the tracker entries in the deploy log.

Stages 1 to 8 are built and verified locally, and I've stopped at two of your stop points: Atlas review and Vercel login. `python build/check.py` passes 8 of 9 checks. The ninth, Atlas page parity, fails only because you haven't approved a baseline yet. Nothing has been deployed or committed.

### Parallel implementation: frozen ShapeSense site

**1. Sub-goals** (5 Haiku subagents, 5 of 10 used)

| ID | Title | Status |
|---|---|---|
| SG-A | Page edits: image and PDF paths, Stage 5 shows the saved confusion images, Feedback button removed, privacy note on the Draw page | ✅ passed audit unchanged |
| SG-B | Stage 2 and 3 pages on saved previews: sliders snap to saved values, Animate steps through saved frames | ✅ one defect fixed by me: changing class didn't stop Animate |
| SG-C | `build/build_site.py`, `frozen.sha256`, attribution page | ✅ I added a card: the README text describes the bundle, but the site does show training images |
| SG-D1 | Python parity fixtures, reference import adaptations | ✅ one crashing edge case fixed |
| SG-D2 | Node tests and the drawing recorder | ✅ one test-harness bug fixed (arm order) |

I wrote the shared files myself: `api.js`, the five browser ports in `web/js/infer/`, the banner in `nav.js`, `check.py`, `browser_checks.mjs`, the Atlas config and the Vercel config. Re-hashing showed every changed file was claimed by exactly one owner.

**2. Results**
- **Snapshot:** pre- and post-checks pass, SOURCE is unchanged, and `test_access.log` is still 157 lines. `snapshot/manifest.json` records `f3b3bdb` (main) and every file hash. Two snapshot runs gave identical hashes.
- **Preprocessing:** the JS port matches the Python byte for byte on all 502 fixtures, on the first run. Plan B and Plan C aren't needed.
- **Output maths:** matches on 1,020 cases.
  - One judgement call: for exactly tied probabilities, the per-arm order may differ from Python's. Python's default sort doesn't define that order, and real model outputs essentially never tie.
  - The vote is compared strictly and matches.
- **What-if rule:** matches on 309 cases.
- **Models:** browser and Python scores differ by at most 9.5e-6 (tolerance 1e-4), and every top answer and vote agrees.
- **Pages:** all 18 pages load in light, dark and phone views with no console errors and no outside or `/api` requests. On the Draw page, five models and the vote answer on both desktop and phone.
- **Build:** 409 files, 36.2 MB (limit 60 MB). A rebuild is byte-identical, and `frozen.sha256` holds.
- **Mutation proofs:** each of 8 deliberate breakages, one per sub-goal plus the ports, was caught by its named check. Each revert restored the file hash and passed again.

**3. What I need from you**
1. **Atlas baseline.** The review UI is open at http://127.0.0.1:8097/ with 54 shots: 18 pages in light, dark and mobile, stable across 3 runs. Please review and approve them; I won't approve any myself.
   - These are screens of the site itself, not a comparison with the Studio. Capturing the Studio would load its Stage 5 page, which calls the sealed `/api/stage5/confusion` endpoint.
2. **Vercel** (the CLI is logged out):
   - Run `vercel login`, then `vercel link` in `site/`. Linking creates the project without deploying.
   - In the dashboard, set Deployment Protection → Vercel Authentication to **All Deployments** before the first deploy. That matters because the default, Standard Protection, leaves the production domain public, and a project's first deploy always goes to production. Vercel's [docs](https://vercel.com/docs/deployment-protection) and [pricing page](https://vercel.com/docs/deployment-protection/usage-and-pricing) say All Deployments is included on Hobby. One [community report](https://community.vercel.com/t/hobby-team-owner-blocked-from-changing-vercel-authentication-to-all-deployments/49714) found that option disabled, so please confirm in your dashboard that it saved.
   - Then I'll run the protected deploy, check that the URL serves exactly the files in `frozen.sha256`, and run the browser checks against it.

**4. Not done yet, or worth knowing**
- **Not verified:** the deployed URL, the MIME types Vercel serves for `.wasm` and `.mjs`, and `vercel build` all wait on step 2.
- **Size:** `snapshot/` is 21.6 MB, over the plan's soft 15 MB target. I accepted it, since the site budget is the hard limit.
- **Clean URLs:** I turned them off in `vercel.json`. The nav highlights the current page by its `.html` file name, which clean URLs would break.
- **Your orchestration rules:** I've run no git command and read nothing outside DEPLOY since your message. A future re-snapshot would need both, so I'll ask first.

**5. Left for going public (stage 10, needs you)**
- G3: a license for the team's code and model weights.
- G4: your written approval naming a SOURCE commit.
- Then I record both in SOURCE's iteration log and make the first commit, through the guard and with no shared-author line.

Everything is logged in `ignore/deploy_log.md`.

## Prompt 3 (00:10)

> all aproved

## Response 3

I'll check what's on disk: whether the goldens were written and whether Vercel is now logged in.

Atlas passes three times in a row. Now the full `check.py`:

Thanks. Your 54 approved goldens are saved, and `python build/check.py` now passes all 9 checks, including Atlas page parity. Atlas also found no visual drift in three checks in a row. Its only warnings say the drawing pad's canvas is masked in the screenshots, which is intended.

**Line endings:** yes, that warning would have caused trouble.

- **The problem:** this repo records exact file hashes, in `snapshot/manifest.json` and `site/dist/frozen.sha256`. If Git turned LF into CRLF on checkout, a fresh clone would have different bytes. The manifest hashes would stop matching the files, and a rebuild would produce a different `frozen.sha256`.
- **The fix:** I added a `.gitattributes` containing `* -text`, so Git keeps every file's bytes exactly as they are. Fifty text files already use CRLF, mostly exact copies of the original records, and those must keep their bytes too.
- **Timing:** it takes effect from the first commit, and nothing is committed yet. Binary files and `site/dist` were never affected.

"All approved" covers the Atlas baseline only. I'm not treating it as G4, which needs your written approval to go public naming a SOURCE commit.

The one remaining blocker is Vercel: the CLI is still logged out. To finish the protected deploy:
1. In `site/`, run `npx vercel login`, then `npx vercel link`. Linking creates the project without deploying.
2. In the Vercel dashboard, set Deployment Protection → Vercel Authentication to **All Deployments**. Without this, the first deploy (which always goes to production) would be public.

Tell me when both are done. I'll deploy, check that the protected URL serves exactly the files in `frozen.sha256`, and run the browser checks against it.

You're in the dashboard's Create New menu. Don't use **Project** there: it creates projects by importing a Git repository or template, and that triggers a deploy. Our repo isn't pushed anywhere, and a first deploy goes to production before protection is on.

The CLI route creates the project without deploying anything. I'll start the login so you only need to approve it in your browser.

The login is waiting for you:

1. **Approve the login.** Open https://vercel.com/oauth/device?user_code=PVCV-BJJB and confirm. The code should read **PVCV-BJJB**.
2. **Leave Create New alone.** Once you've approved, I'll run `vercel link` in `site/`, which creates the project under your Hobby account with no deploy.
3. **Turn on protection before any deploy.** Open the new project → **Settings → Deployment Protection → Vercel Authentication**, turn it on, and choose **All Deployments**, then save. Tell me when it shows as saved. If that option is greyed out, say so and I won't deploy.

Then I'll do the protected deploy and verify it.

You're logged in as `silent0wings`. Next I'll link `site/` to a new project named `shapesense`. Linking creates the project without deploying anything.

Linked. Before any deploy, I'll read the project's current protection setting through the CLI. This only reads it.

`inspect` doesn't show protection, so I'll read the project record through `vercel api`, still read-only:

Git Bash rewrote the `/v9/...` path as a Windows path. I'll disable that conversion and retry:

The headers are in place. Next is the protected deploy:

`vercel curl` uses an automatic protection bypass. I'll make one request and see what it relies on:

Next, the same header for `browser_checks.mjs`, so Chromium can load the protected deployment:

The site is deployed behind Vercel Authentication, and every check passes against the live protected URL.

- **URL:** https://shapesense-ten.vercel.app. You can open it while logged in to Vercel as `silent0wings`; anyone else is redirected to Vercel's sign-in. That includes pages, models and data files.
- **Protection:** I set Vercel Authentication to **All Deployments** through the Vercel API before deploying, and read the setting back to confirm it saved. It covers production too.
- **Files:** all 408 files listed in `frozen.sha256` are served byte for byte, with the correct types for the WebAssembly and module files.
- **In the browser:** all 18 pages load in light, dark and phone views with no console errors and no outside or `/api` requests. The browser's model scores match Python's on 150 cases. On the Draw page, five models and the vote answer on desktop and phone.

Two things to know:
- **Bypass secret:** `vercel curl` created a "Protection Bypass for Automation" secret on the project. My checks used it only from an environment variable; it's never printed or saved in a file. Anyone holding it can get past the login. I've kept it for future checks, but you can revoke it in Project Settings → Deployment Protection; it's recreated when needed.
- **Atlas:** I didn't run Atlas against the URL. Its 54 approved screenshots were checked on the local build, which is byte-identical to what's deployed.

**On "nothing pushed":** that's right, and on purpose. DEPLOY has no commits and no remote, because you said to commit and push only when you ask. The Vercel deploy uploaded only the built files, not the repository. If you'd like, I can:
1. **Commit:** make the first commit through the commit guard, with you as the only author and no shared-author line. `.gitattributes` is already in place so line endings won't change the recorded hashes.
2. **Push:** push it to a remote you name, for example a new private GitHub repo.

Going public still needs G3 (a license for the team's code and model weights) and G4 (your written approval naming the SOURCE commit, `f3b3bdb`). The full record is in `ignore/deploy_log.md`.

Sources: [Deployment Protection on Vercel](https://vercel.com/docs/deployment-protection), [Usage & Pricing for Deployment Protection](https://vercel.com/docs/deployment-protection/usage-and-pricing), [Hobby team owner report](https://community.vercel.com/t/hobby-team-owner-blocked-from-changing-vercel-authentication-to-all-deployments/49714)

## Prompt 4 (00:24)

> but nothing is pushed

## Response 4

You're right: nothing is pushed. DEPLOY has no commits and no remote yet, so there's nowhere to push to. Pushing takes three steps: a first commit, a remote, then the push. Before asking where it should go, I'll check whether the GitHub CLI is available and signed in.

GitHub CLI is signed in as `Silent0Wings`, and a **private** repo `Silent0Wings/ShapeSense_Deployed` already exists. Is it empty?

Two things to look at: what the guard actually bans (`snapshot/doc/iteration_log.json` contains the ordinary sentence "Generated with the final tuned settings"), and what matched in `meta.json`.

Git says `build` is ignored, but our `.gitignore` doesn't list it. Here's which rule matches:

Committed as `81d61b4`, and the guard verified there's no shared-author line. I'll check what went in and that nothing was left out or leaked:

`origin` already points to the right repo; you must have added it when you created the GitHub repo. Pushing:

Next, rebuild and run every check. Atlas should flag only the three attribution shots.

The review UI is still running at **http://127.0.0.1:8097/**. It should show three changed shots, all `attribution`, one each for light, dark and mobile. Each differs only by the new license sentence, about 0.05% of pixels.

1. **Review the attribution shots.** Approve them if the new text is right. I won't approve them myself.
2. **Say "approved"** when you're done.

Then I'll finish going public:
- Re-run `check.py`, which must pass 9 of 9.
- Deploy the new freeze to production and turn off Vercel Authentication, so https://shapesense-ten.vercel.app is public.
- Verify it without any login: every file in the new `frozen.sha256` served byte for byte, plus the full browser checks.
- Write the Deployment entry in SOURCE's `iteration_log.json` (freeze, URL, G3 and G4 evidence), run `--stages 6`, and commit there through SOURCE's guard, with no push.
- Commit the license files and the new freeze in DEPLOY, then push.

## Prompt 5 (00:33)

> all aproved

## Response 5

All 9 checks pass with your approved shots. Next I'll deploy the new freeze to production while it's still protected, and only open it up after that deploy is READY.

The new freeze is READY on production and still protected. Next, the step you approved: turn off Vercel Authentication so the site is public, then read the setting back.

The site is public: protection reads back as `null`, and the page and model manifest return 200 with no login. Now the full verification without any secret, as an ordinary visitor:

The diff is exactly the 14 added lines. Next comes `python run_pipeline.py --stages 6` in SOURCE, under the stall watcher, with the access log counted before and after.

The site is public at **https://shapesense-ten.vercel.app**: anyone can open it without a login. I checked it as an anonymous visitor. It serves exactly the 408 files in its `frozen.sha256`, all 18 pages load in light, dark and phone views with no errors, and the Draw page shows all five models and the vote on desktop and phone.

The link you sent (`vercel.com/…/7Vh7…`) is Vercel's dashboard page for the deployment, so only your account can open it. The site address is the one above.

- **License (G3):** I added `LICENSE` (MIT for the team's code) and `LICENSE-MODELS.md` (CC BY 4.0 for the five model weights). The attribution page now states both.
  - That text change made a second freeze. The first freeze's hash list is kept in `freezes/`, as R6 requires; that's why I suggested keeping that file.
  - You approved the three changed attribution screenshots, and `check.py` passes 9 of 9.
- **Going public:** I deployed the new build while still protected, then turned Vercel Authentication off.
- **DEPLOY repo:** two commits, `81d61b4` and `d0397d5`, are pushed to your private repo `Silent0Wings/ShapeSense_Deployed`, with you as the only author and no shared-author line.
- **SOURCE:** the freeze and the publication are recorded in `iteration_log.json` with the G3 and G4 evidence (R18). `run_pipeline.py --stages 6` passed and the access log is still 157 lines. That's committed as `8c04e6a` on `iteration-3` and **not pushed**.

Decisions for you:
- **SOURCE branches:** `main` is still at `f3b3bdb`, now one commit behind `iteration-3`. Should I move `main` forward and push SOURCE, or leave both for you?
- **`export/README.md` in SOURCE:** it still says no license has been chosen. I only wrote to the iteration log, as approved. Updating it is a small follow-up if you want it.
- **Bypass secret:** the Vercel project still has the automation bypass secret from the earlier checks. It's harmless now that the site is public, and you can revoke it in Project Settings → Deployment Protection.

Everything is logged in `ignore/deploy_log.md`.

## Prompt 6 (00:43)

> Issue in mobile for augmented and

## Response 6

I'll keep commits without the shared-author trailer that the latest system message asks for; your rule takes precedence.

On the bug: on a phone, Stage 2 keeps the Original image beside the Augmented column, and the tiles get cut off at the right edge. Your message cut off after "augmented and", so I'll also check Stage 3's generated grid. First, the layout rules:

Next, a general guard so this can't recur. At phone width, `browser_checks` will flag any tile, image, canvas or chart that sticks out of its card, unless it sits in an intentionally scrollable area.

I've fixed both phone bugs locally and they need your review in Atlas before I deploy. The public site still has both bugs until then.

- **Stage 2 (augmented tiles):** on a phone, the Original image and the Augmented column sat side by side, squeezing the tiles until they were cut off. Below 620 px they now stack: Original first, the augmented tiles full-width underneath. The original Studio has the same layout, which is why the approved screenshots didn't catch it.
- **Attribution (license page):** the long dataset links were unbroken text that ran past the card edge. Links inside cards now wrap.
- **Why my checks missed them:** the phone check only looked for page-wide horizontal scrolling, and these overflow inside a card. I added a check that flags any image, tile, chart or link sticking out of its card at phone width. On the old styles it catches both bugs (24 elements on Stage 2, 3 links on the attribution page); with the fix, all 18 pages are clean.

`check.py` passes 8 of 9 checks. The ninth, Atlas, flags three phone screenshots for your review:

1. Open **http://127.0.0.1:8097/**.
2. Review `mobile/stage2` (tiles stacked under the original), `mobile/attribution` (links wrapping) and `mobile/failures`. That last one is the same fix: a long link there now wraps instead of running over the edge.
3. Approve them if they look right, and tell me.

This is a third freeze, so I've already kept the live site's manifest as `freezes/2026-11-11-public-1.sha256`. After your approval I'll re-run the checks, deploy, and verify the public site byte for byte from a phone-sized browser. Then I'll commit and push the fix.

## Prompt 7 (00:50)

> aproved

## Response 7

Next, a browser check for it, proven both ways. On a phone-sized failures page it presses Previous, then requires the selected point to be inside the visible part of the timeline.

Understood: I'll commit when this is done, with no shared-author line. First, the full list of shots Atlas flagged:

The check log only keeps the tail of Atlas's report. I'll run Atlas directly for the complete table:

Both fixes from your last three reports are done locally, but only the timeline fix is live so far. The nav fix is waiting on your Atlas review before I deploy and commit.

- **Live now:** Stage 2's augmented tiles stack under the original on a phone, long links on the attribution page wrap, and the failure timeline follows Next, Previous and the slider. The public site serves exactly its frozen files, and the browser checks pass there with 0 problems.
- **Waiting on you:** on a phone, the page-link row now opens scrolled to the current page. It scrolls only that row, never the page, so a refresh keeps your place.
  - **How it's checked:** a new check runs on every page in every view. Without the fix, 16 phone pages fail; with it, none do.
  - **What Atlas flags:** 17 phone screenshots (every page except home, whose link is already first). They differ only in the nav row.

Please review those 17 shots at **http://127.0.0.1:8097/** and tell me when they're approved. Then I'll:
1. Re-run `check.py` and deploy this fourth freeze.
2. Verify the public site byte for byte, plus the browser checks.
3. Commit everything with no shared-author line and push to `Silent0Wings/ShapeSense_Deployed`.

The commit will cover the four phone fixes, the two new checks and the kept freeze manifests (`freezes/2026-11-11-public-1.sha256` and `-public-2.sha256`).

## Prompt 8 (01:07)

> all aproved

## Response 8

Your approval stands and `check.py` passes 9 of 9. I'll fold the toolbar change into this freeze before deploying, so there's one deploy instead of two. First, the CSS behind the pad's tool row:

Next, the browser checks on the new layout, plus a phone screenshot of the vote section so I can see it:

Both phone changes are done locally and need your Atlas review before I deploy and commit:

- **Pad tools:** all six (Undo, Clear, the two rotates and the two zooms) now fit in one row.
- **Vote:** it looks like the desktop network again, just smaller. Three models sit above the vote and two below, each with a line coloured and labelled with its answer. The vote spans the middle with its bars and "5 of 5 models picked this". I checked a 390 px screenshot of it myself.

New checks cover both. On the old styles they report "models not around the vote", "no vote lines" and "tools wrap onto more than one row"; on the new ones, 0 problems. All other checks pass. Atlas flags two phone screenshots, both containing the drawing panel: **mobile/home** and **mobile/live**.

1. Review those two at **http://127.0.0.1:8097/**.
2. Tell me if they're approved.

I'll then deploy one freeze with all the phone fixes (including the nav row you already approved), verify the public site, and commit and push with no shared-author line.

## Prompt 9 (01:19)

> all good , and aproved

## Response 9

All 9 checks pass. Next I'll deploy this freeze and verify the public site. Then I'll commit and push with no shared-author line.

Live and verified. Next, the commit through the guard, which rejects any shared-author or attribution line, then the push:

All the phone fixes are live, committed and pushed. Commit `1cfc074` is on `Silent0Wings/ShapeSense_Deployed`, authored by you alone; the guard verified it and there's no shared-author line anywhere in the message.

**Live now at https://shapesense-ten.vercel.app** (on a phone):
- Stage 2's augmented tiles stack under the original.
- Long links on the license page wrap.
- The failure timeline follows Next, Previous and the slider.
- The page links open scrolled to the current page.
- The six drawing tools fit in one row.
- The vote keeps its desktop shape: models around it, with coloured lines in.

**Verified on the public site, without a login:**
- All 408 files in `frozen.sha256` are served byte for byte.
- All 18 pages pass in light, dark and phone views.
- The browser's model scores match Python's.
- The new checks for each phone fix pass.
- `check.py` passed 9 of 9 before the deploy, with your approved screenshots.

**In the commit:** the CSS and script fixes, the new browser checks, and the two earlier live freezes in `freezes/`. The working tree is clean.

Still open from before, if you want them:
- SOURCE's log commit `8c04e6a` on `iteration-3` isn't pushed, and `main` there is one commit behind.
- SOURCE's `export/README.md` still says no license has been chosen.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Browser results were checked against Python (logits within 1e-4), and build/check.py was run. The user approved each stop point.

## Our decision

Models run in the visitor's browser through ONNX Runtime Web, with no server (D02).

## Measured effect

Deployment only, with no macro F1 change. Public at https://shapesense-ten.vercel.app.

---

## Upgraded & Expanded Analysis: Autonomous Stage 7 Build, Parity Proofs & Release Timeline (`54_real`)

### Why this exchange matters

Nine prompts take the standalone snapshot plan from [53_real_vercel-deployment-plan.md](53_real_vercel-deployment-plan.md) to a **live, byte-verified public deployment** (`https://shapesense-ten.vercel.app`), enforcing hard stops only at human gates (Atlas visual review, Vercel authentication, and public release approval $G_3/G_4$).

### Consolidated Build & Release Timeline

| Prompt | Time | Event & Verification Milestone |
|---|---|---|
| **1** | `22:55` | Initialized local `main` repository in `ShapeSense_Deployed` with zero remote pushes |
| **2** | `23:09` | Launched `/goal` across Stages 1–8 using 5 Haiku subagents (`SG-A`–`SG-E`); `8/9` checks pass, paused at Atlas + Vercel login |
| **3** | `00:10` | User approved Atlas baseline $\rightarrow$ `9/9` checks pass; linked Vercel with deployment protection enabled |
| **4** | `00:24` | Committed through guard and pushed to private GitHub repository |
| **5** | `00:33` | User approved public release ($G_3/G_4$) $\rightarrow$ added license, froze public manifest, updated `iteration_log.json` |
| **6–9** | `00:43–01:19` | Resolved 4 mobile layout bugs (Stage 2 tiles, attribution link wrap, failure timeline, nav scroll) + toolbar/vote layout; final freeze committed (`1cfc074`) and verified live |

### End-to-End Verification Matrix

| Verification Domain | Measured Result |
|---|---|
| **Snapshot & Source Integrity** | Pre/post guards pass; `ShapeSense` unchanged; `test_access.log = 157`; `manifest.json` locks commit `f3b3bdb`; two snapshot runs byte-identical |
| **Preprocessing Parity (`standardize.js`)** | Exact byte-for-byte match against Python `standardize.py` across all **502 fixtures on first try** (Plans B/C unused) |
| **Output Math & What-If Parity** | `1,020` math cases + `309` what-if cases match exactly |
| **ONNX Runtime Web Parity** | Browser vs. Python max logit difference $\le 9.5 \times 10^{-6}$ (tolerance $10^{-4}$); 100% top-1 and vote agreement |
| **Mutation Proofs** | `8` deliberate code breakages (one per sub-goal + JS ports), each caught by its named check |
| **Live Deployment Audit** | `408` static files (`36.2 MB`, limit `60 MB`) served byte-for-byte identical to `frozen.sha256` with zero console errors or external requests |

