# Stage 7 — Frozen public dashboard

> Owner brief. This is the final stage of the project. It starts only after
> every gate below is met. The full project plan is `../implementation.md`.

- **Owner:** ______
- **Status:** not started, blocked by the gates below
- **Pipeline stage:** none. `run_pipeline.py` does not run this stage, and it never reads or changes pipeline outputs
- **Code folder:** `deployment/` at the repository root, created only when this stage starts
- **Depends on:** Stages 0–6 finished and the closing iteration closed
- **Blocks:** nothing — this is the finish line

## Focus

Publish one frozen copy of the dashboard as a static website on Vercel. Every
number and figure is fixed at freeze time. The exported ONNX models stay live:
a visitor can draw a shape and the models score it in the visitor's browser.

## Gates

All four must hold before any file in `deployment/` is written.

| Gate | Requirement | Evidence |
|---|---|---|
| G1 Work complete | Every stage has status `passed`, the closing iteration is `closed` in `docs/crisp_dm/iteration_log.json`, and its handoff is complete | `artifacts/stage*/status.json`, the log and the handoff |
| G2 Metrics pass | The closing iteration's pre-registered primary verdict is Pass, and every validity check in every stage passed | `artifacts/stage5/status.json` |
| G3 License | The team has chosen a license for its code and model weights, and every image shown publicly is allowed by its source's license | `export/README.md`, attribution page |
| G4 User approval | The user has approved this work in writing for a named commit, and has said it may be published | A dated entry under Deployment in the iteration log |

- G2 is read from the verdict as written. A failed verdict blocks this stage.
  The rule is never loosened to open the gate. The way forward is a new
  pre-registered iteration on fresh sealed data, or an explicit written waiver
  from the user, which the site must then state on its first page.
- G4 cannot be inferred. A finished task or a passing test run is not approval.

## Out of scope

- Training, tuning or evaluating anything. The site only displays what the
  closing iteration recorded.
- Changing `studio/`. The working dashboard stays as it is, and the frozen copy
  is built from it.
- Any server code. The site has no backend.

## Inputs

| Input | Where |
|---|---|
| Pages, styles, scripts and icon | `studio/web/` at the approved commit |
| Page data and figures | The responses of the studio's read-only endpoints, captured at freeze time |
| ONNX models and labels | The bundle written by `studio/tools/export_arms.py` |
| Preprocessing | `src/stage1_freeze/standardize.py` |

## Requirements

**Must — isolation**
- R1. `deployment/` holds everything the site needs. It imports nothing and
  loads nothing from outside its own folder, and no other code imports it.
- R2. The Vercel project's root directory is `deployment/`, so nothing else in
  the repository is uploaded.
- R3. Third-party scripts, including the ONNX runtime, are copied into the
  folder at a pinned version. The site loads nothing from a CDN.

**Must — frozen**
- R4. One build script produces the folder. Nobody edits its contents by hand.
- R5. Each file's SHA-256 is recorded in `deployment/frozen.sha256`, along with
  the approved commit. A test fails if any file differs.
- R6. A correction is a new freeze with a new approval, recorded in the
  iteration log. The old manifest is kept.

**Must — static pages**
- R7. No page calls `/api`. Stored responses replace read-only calls.
- R8. Controls that need Python (augmentation and generator previews, saving a
  wrong prediction) are removed or shown as pre-rendered examples. No dead
  control ships.
- R9. Every page says it is a frozen record and shows the commit and the date.

**Must — live models**
- R10. Models run in the browser through ONNX Runtime Web. The site offers
  every arm in the export bundle, plus the equal-weight "All models vote"
  answer if that goal was finished first. The vote is labelled as having no
  measured score.
- R11. Drawings never leave the visitor's browser, and the page says so.
- R12. Blank or rejected drawings, low confidence and a model that fails to
  load behave as in `stages/stage_6.md` R16.

**Must — preprocessing parity**
- R13. Browser preprocessing must match `standardize.py`, which uses NumPy,
  Pillow and SciPy. Either run that same file in the browser (Pyodide) or port
  it to JavaScript. Choose at build time and record why.
- R14. A parity test compares browser and Python output on a committed set of
  non-sealed drawings. The 64×64 images must match, and the model scores must
  meet the tolerance in `tests/studio/test_parity.py`.

**Must — data safety**
- R15. No sealed split ships: no test or fresh-holdout image, path, CSV or
  per-image prediction. Only aggregate tables and matrices from Stage 5 do.
  Error galleries rendered from sealed images stay out.
- R16. The build fails on any forbidden path, using the same list as
  `tests/studio/_audit_sweep.py`. It also fails on absolute local paths,
  personal details or secrets.
- R17. Source and license attribution from `export/README.md` is on the site.

**Must — record**
- R18. The freeze and the publication are recorded under Deployment in
  `docs/crisp_dm/iteration_log.json` and shown in the frozen site.

## Deliverables

- `deployment/` — pages, frozen data, models, runtime and `frozen.sha256`.
- The build script and its tests.
- The public Vercel address, recorded in the iteration log.

## Done when

- [ ] Gates G1–G4 are recorded with their evidence.
- [ ] The site works from a plain static file server with the studio stopped.
- [ ] The browser shows no request outside the site, and none to `/api`.
- [ ] Every arm predicts on a drawing in a current desktop browser and on a phone.
- [ ] The parity test passes.
- [ ] The forbidden-content check and the `frozen.sha256` check pass.
- [ ] Every page renders in light and dark themes with no dead control.
- [ ] The deployed address serves the same files as `frozen.sha256`.
- [ ] Vercel's size limits were checked at deployment time.
- [ ] The user has confirmed the deployed site.

## Pitfalls

- **Freezing before the gates are met** — the site would publish a result that
  has not earned it.
- **A plain browser resize instead of the real preprocessing** — predictions
  look plausible and are wrong in ways no error reports.
- **Copying the whole `artifacts/` folder** — it holds sealed predictions.
- **Hiding a removed control's result** — pre-render an example or take the
  control away, and do not leave a button that fails.

## Glossary

- **Freeze**: one fixed copy with recorded file hashes. Example: `frozen.sha256`.
- **Static site**: files served as they are, with no server code. Example: an
  HTML page, a JSON file and an `.onnx` model.
- **ONNX Runtime Web**: runs an ONNX model inside the browser. Example: the
  drawing is scored on the visitor's own device.
- **Parity test**: proves two code paths give the same output. Example: Python
  and browser preprocessing on the same drawing.
