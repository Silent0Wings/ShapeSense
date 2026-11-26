# 4_testing - Stage 6 plan: report, dashboard, export and demo

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-08
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner brief for Stage 6 (report, figures, dashboard and packaging) and one implementation plan each for the dashboard, export, demo and both reports.

## Response (saved output, verbatim)

### `stages/stage_6.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 6 — Report, figures, dashboard and packaging

> Owner brief. Everything here is about Stage 6 only. The full project
> plan is `../implementation.md`; shared rules live there under
> *Stage 0* and *Shared conventions*.

- **Owner:** ______
- **Pipeline stage:** `--stages 6` · **Code folders:** `src/stage6_report/`, `dashboard/`
- **Depends on:** Stage 5 for results tables; everything else starts day 1
- **Blocks:** nothing — this is the finish line
- **Effort:** 1–2 days for the report + 0.5–1 day for the dashboard

## Focus

Turn the artifacts of Stages 0–5 into **three things people outside the
code can use**: the Phase 2 report, a read-only dashboard that shows the
state of all seven stages, and an exported model that runs on a fresh
image. The rule for all three: **every number comes from an artifact,
never typed by hand.**

## Goals

1. Fix the Phase 1 report so it matches the plan (three arms, gemstone
   filter, Figure 2, typos).
2. Build the dashboard early so the team uses it as a progress board.
3. Write the Phase 2 report: results, figures, error galleries,
   limitations, ablations if time allows.
4. Export the best model with `standardize.py` bundled.

## Out of scope

- Computing metrics or running statistics (Stage 5) — you only display
  what Stage 5 wrote.
- Training anything, except ablation runs that are just new entries in
  `configs/pipeline.yaml#runs` (the pipeline trains them, not you by hand).

## Inputs

| Input | Where |
|---|---|
| All stage results | `artifacts/stage1 … s5/` and their `status.json` |
| Results tables and confusion figures | `artifacts/stage5/tables`, `artifacts/stage5/figures` |
| Phase 1 report source | `phase1_report.tex`, `build.ps1` |
| QA sheets, parameter ranges | `artifacts/stage2/qa`, `artifacts/stage3/` |

## Requirements

**Must — report fixes (start day 1)**
- R1. Figure 2 (`fig:evalsplit`): add the validation split, the dedup
  stage, seed annotations and the A1 arm (TikZ in `implementation.md`).
  **Also move it out of its `0.32\linewidth` minipage** — the extended
  picture is about 10.9 × 11.8 cm, so that minipage scales
  `\footnotesize` labels to roughly 4 pt. Give it `0.60\linewidth` or
  its own full-width figure.
- R2. Section A evaluation goal: describe three arms.
- R2b. **Split paragraph** (`phase1_report.tex:466–467`): replace
  12,761 / 2,890 / 2,849 with Stage 1's new counts. This is where split
  sizes live — `tab:stats` (Table 3) holds per-source file counts and
  needs no change. Decision 15 guarantees the old numbers are wrong;
  treat this as a scheduled task, not a surprise.
- R3. Sections C and D and the label-mapping table: state the gemstone
  filter and the removed count from `artifacts/stage1/status.json`.
- R4. Fix typos: "clasifies", "geometrc", "categoreis", "dosent" (×2),
  "chnage", "dont" (×2), "training..", "later..", and spaces before
  periods.

**Must — Phase 2 report**
- R5. Results tables are generated from `artifacts/stage5/tables/*.tex`
  (`\input{}`), never retyped.
- R6. Limitations: reevald's dashed-line hint, gemstone diamonds (what
  was removed), the near-duplicate pentagon groups, single-source
  classes (pentagon, ellipse) with the Stage 1 source-classifier caveat.
- R7. State the generator's parameter ranges from
  `artifacts/stage3/param_ranges.json`.
- R8. The report builds through the pipeline, which calls
  `build.ps1 -File phase2_report.tex`. The `-File` argument is not
  optional: `build.ps1` defaults to `phase1_report.tex`, so without it
  the stage compiles the wrong document.
- R8b. State Decision 13's framing in the results section: B is compared
  with A1 at an equal step budget, with 30% of each batch **substituted**
  by synthetic images rather than added. The number means "does swapping
  in synthetic data help", and the report has to say so.

**Must — dashboard**
- R9. Streamlit app, read-only: it reads `artifacts/` and
  `configs/pipeline.yaml` only; it never computes results and never reads the
  test split (import-linter: `dashboard` may import `common.status` only).
- R10. 8 tabs: Overview (7 status lights) plus one tab per stage,
  Stage 0 included — it writes a `status.json` like every other stage.
- R11. Missing artifacts show as grey "not run" instead of crashing.

**Must — packaging**
- R12. Export the best model to `export/` as ONNX, together with
  `standardize.py`, `predict.py` and `labels.json`. A smoke test loads
  it and predicts on a fresh image.

**Must — deployment demo (CRISP-DM step 6)**
- R13. `demo/app.py`, started with `python run_pipeline.py --demo`, has a small 256×256
  drawing canvas (black stroke ~8 px on white), an **Infer** button and
  a **Clear** button.
- R14. Infer sends the drawing through `export/predict.py`, which calls
  the same `standardize.py` used in training, and shows the predicted
  class, the top-3 confidences and the 64×64 image the model saw.
- R15. The demo imports only `export/` (import-linter: `demo → export`
  only).
- R16. Edge cases: an empty canvas shows "Draw a shape first" — test
  the **alpha** channel (`rgba[..., 3].sum() == 0`), because the canvas
  returns unpainted pixels as `(0, 0, 0, 0)` and an RGB-darkness test
  reads a blank canvas as solid ink; a `standardize.Rejected` exception
  (no contrast — a dot or a stray mark) shows the same message instead
  of a traceback; a top confidence below 0.5 is shown as "not sure"; a
  missing model shows "no exported model yet".
- R17. Demo drawings are informal evidence only: they are not test
  data, never used for training, and never change the verdict.
- R18. Update the report's CRISP-DM figure (`fig:crisp`): Deployment is
  no longer "not in this report".
- R19. State that the primary test measures **same-source** generalization.
  If Decision 12 fired, include the separate Hand-Drawn leave-one-source-out
  result; do not present either as universal sketch generalization.
- R20. Complete the course-requirements checklist from the official rubric
  and record any unmet item as a submission blocker.
- R21. Include source/license attribution in the report and
  `export/README.md`, and state whether images, derived outlines, weights
  or only code are redistributed.

**Should**
- Ablations if time allows, each one a new entry in
  `configs/pipeline.yaml#runs`: `B_equalreal` (Decision 13 — 256 real
  plus 110 synthetic per batch, so synthetic is *added* rather than
  substituted), synthetic ratio 0/15/30/50% (0% = A1, free),
  per-augmentation removal, sketch-only test slice.
- Error galleries come from `artifacts/stage5/figures/errors_<pair>.png`.
  You cannot build them yourself — Stage 6 may not read test images, so
  Stage 5 renders them.

## Deliverables

- Updated `phase1_report.tex` (fixes) and the Phase 2 report PDF.
- `dashboard/app.py`.
- `export/` — `model.onnx`, `predict.py`, `standardize.py`, `labels.json`.
- `demo/app.py` — the draw-and-infer app.
- `artifacts/stage6/status.json` — build result, traceability check, smoke test.
- `export/README.md` — usage plus source/license attribution.
- Completed rubric/deadline checklist and contribution record.

## Done when

- [ ] Report compiles via the pipeline, from `phase2_report.tex`.
- [ ] Every number in the report traces back to a Stage 5 (or Stage 1/3)
      artifact, including the split counts and the test-read count from
      `artifacts/stage5/status.json → checks.test_reads`.
- [ ] The equal-compute framing (Decision 13) is stated in the results.
- [ ] Same-source vs unseen-source claims are labelled correctly.
- [ ] Export loads and predicts correctly on a fresh image.
- [ ] Attribution is present in both the report and `export/README.md`.
- [ ] The official rubric checklist has no unexplained unchecked item.
- [ ] Dashboard shows all seven stages with correct status lights.
- [ ] `python run_pipeline.py --demo` turns a mouse drawing into a prediction using only
      `export/`, and every edge case in R16 behaves as specified.

## Interfaces you use

Read-only: every `artifacts/sN/` folder. You provide nothing to other
stages — Stage 6 is the end of the pipeline.

## Pitfalls

- **Retyping a number** from the console into LaTeX — it goes stale the
  next time the pipeline reruns.
- **Dashboard that recomputes metrics** — two sources of truth that can
  disagree; it must only display.
- **Exporting without `standardize.py`** — a fresh RGB 256×256 image
  would hit the model unprocessed and fail silently.
- **Hiding a failed verdict** — a "fail" with honest CIs is a valid,
  reportable result (CRISP-DM loops back).
- **Pasting the TikZ snippet outside the existing figure** — the `box`
  and `arr` styles are only defined in the `fig:evalsplit` picture.
- **Leaving the extended figure in its narrow minipage** — it compiles
  without error and is unreadable in print. Check the PDF at 100%, not
  the source.
- **Keeping Stage 0's placeholder tables** — they compile fine and show
  a dash where a result belongs. Confirm the Stage 5 tables actually
  overwrote them before submitting.

## Glossary

- **Traceability**: every reported number can be followed back to the
  file that produced it. Example: "macro-F1 0.912" ↔
  `artifacts/stage5/tables/metrics.csv`, row B, seed mean.
- **Generated table**: a LaTeX table written by code and pulled in with
  `\input{}`. Example: `\input{artifacts/stage5/tables/metrics.tex}`.
- **Status light**: the dashboard's colour for one stage, from its
  `status.json`. Example: grey = not run, green = passed, red = failed.
- **Streamlit**: a Python library that turns a script into a web app.
  Example: `st.tabs(["Overview", "1 Data", ...])`.
- **Ablation**: removing or varying one ingredient to see its effect.
  Example: synthetic ratio 15% instead of 30%.
- **Model export**: saving a trained model in a standalone format.
  Example: `torch.onnx.export(model, dummy, "model.onnx")`.
- **Smoke test**: a minimal check that something runs at all. Example:
  load `model.onnx`, predict one PNG, get a class name back.
- **Deployment (CRISP-DM step 6)**: putting the model where people can
  use it. Example: the draw-and-infer demo.
- **Train/serve skew**: when live inputs are prepared differently from
  training inputs. Example: resizing the canvas with a plain `resize()`
  instead of `standardize.py` gives thick grey strokes the model never
  saw.
- **Softmax confidence**: the model's output scores turned into
  probabilities that sum to 1. Example: hexagon 0.81, octagon 0.12,
  circle 0.04.

## Missions

### M1 Find the untraceable number (recognition)
Prompt: which sentence breaks the traceability rule?

1. "Model B reached a macro-F1 of \input{artifacts/stage5/tables/b_macro_f1.tex}."
2. "Synthetic ellipses use axis ratios between 1.2 and 2.0
   (`param_ranges.json`)."
3. "Model B improved macro-F1 by about 2 points."
4. "The gemstone filter removed \input{artifacts/stage1/gemstones.tex} drawings."
5. "The split holds 12,761 train, 2,890 validation and 2,849 test images."

Expected outcome: sentence 3 — "about 2 points" is typed by hand with no
artifact behind it. Sentence 5 is worse: the numbers are precise, they
look authoritative, and they are Phase 1 values that Decision 15 and the
gemstone filter both invalidate. Sentence 2 is acceptable if the numbers
are copied by a script, or better, generated.

### M2 CSV → LaTeX table (application)
Prompt: generate the results table from Stage 5's CSV.

```python
import pandas as pd

df = pd.read_csv("artifacts/stage5/tables/metrics.csv")   # arm, seed, accuracy, macro_f1
summary = (df.groupby("arm")[["accuracy", "macro_f1"]]
             .agg(["mean", "std"]))
# TODO: format as "mean ± std" with 3 decimals, order rows A0, A1, B
summary_tex = ...
open("artifacts/stage6/results_table.tex", "w").write(summary_tex)
```
Expected outcome: a `booktabs` table with rows A0, A1, B and columns
"Accuracy" and "Macro-F1" showing `0.xxx ± 0.xxx`; `\input{}` of it
compiles in the report, and changing the CSV changes the PDF on the next
the pipeline.

### M3 Overview tab + export smoke test (synthesis)
Prompt: build the dashboard Overview tab that never crashes on missing
stages, and a smoke test for the exported model.

```python
import json, pathlib, streamlit as st

COLORS = {"passed": "🟢", "failed": "🔴", "not_run": "⚪"}

def load_status(stage):
    p = pathlib.Path(f"artifacts/{stage}/status.json")
    return json.loads(p.read_text()) if p.exists() else {"status": "not_run"}

overview, *stage_tabs = st.tabs(["Overview", "0 Infra", "1 Data", "2 Augment",
                                  "3 Synthetic", "4 Training", "5 Evaluation",
                                  "6 Report"])
with overview:
    for s in [f"stage{i}" for i in range(7)]:
        info = load_status(s)
        # TODO: one row: light, stage name, owner, finished_at, and for
        #       stage5 the verdict (a "fail" verdict is still status "passed")
```
```python
def test_export_predicts():
    img = Image.open("tests/fixtures/fresh_hexagon.png")   # RGB, any size
    assert predict(img) == "hexagon"                       # predict() runs standardize first
```
Expected outcome: with only Stage 1 run, the Overview shows one green
and six grey lights and no error; the Stage 5 row shows the verdict when
it exists, separately from the status light. The smoke test passes on a
fresh RGB image of any size.

### M4 Draw and infer (synthesis)
Prompt: build the deployment demo. Draw a shape, press Infer, and show
the prediction plus the image the model actually saw.

```python
import numpy as np, streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from export.predict import predict_proba, preprocess   # export/ only (R15)

st.title("Draw a shape")
canvas = st_canvas(stroke_width=8, stroke_color="#000000",
                   background_color="#FFFFFF", width=256, height=256,
                   drawing_mode="freedraw", key="pad")

if st.button("Infer"):
    rgba = canvas.image_data                       # 256x256x4 uint8, or None
    # Unpainted canvas pixels are (0, 0, 0, 0): RGB black with alpha 0.
    # Testing rgba[..., :3] < 128 counts every blank pixel as ink, so the
    # warning would never fire. Test alpha.
    if rgba is None or rgba[..., 3].sum() == 0:
        st.warning("Draw a shape first")
    else:
        img = Image.fromarray(rgba.astype(np.uint8), "RGBA")
        try:
            x64 = preprocess(img)                  # standardize.py -> 64x64
        except Rejected:                           # no contrast: a dot, a smudge
            st.warning("Draw a shape first")
        else:
            probs = predict_proba(x64)             # {"hexagon": 0.81, ...}
            top3 = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
            # TODO: show top3[0] (or "not sure" if < 0.5), bars for top3,
            #       and st.image(x64, width=128) labelled "what the model saw"
```
`standardize._flatten_alpha` already composites RGBA onto white, so the
RGBA array can go straight in — no manual conversion, and no second
resize path that would diverge from training.
Expected outcome: drawing a rough hexagon and pressing Infer shows a
prediction within about a second, three confidence bars, and a clean
64×64 black-outline image. Infer on an empty canvas shows the warning
(check this first — it is the edge case the obvious implementation gets
wrong), a single dot shows the same warning rather than a traceback, and
deleting `export/model.onnx` gives a friendly message. The live sketch check (each team member draws all 10
classes, 60 drawings in total) produces a count you can quote as an
anecdote.

When you finish M4, run `quiz-topic` on "reproducible reporting and
deployment".
````

### `31_s6_dashboard.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E31 evidence line

# Plan 31: S6 read-only dashboard

**Stage:** `stages/stage_6.md` R9–R11, Done-when D8, Mission M3 · **Plan refs:** `implementation.md` § Dashboard
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E31) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The team needs a progress board that never computes or reads test data.

## 2. Root Cause & Investigation
No `dashboard/`.

## 3. Architecture & Modular Design Strategy
`dashboard/view_model.py` (pure: status → light, rows) and `dashboard/app.py` (Streamlit), reading only `artifacts/` and `configs/pipeline.yaml`, importing nothing from `src` except `src.common.status`.

## 4. Proposed Changes by File
- `dashboard/__init__.py`, `app.py`, `view_model.py`.
- `tests/dashboard/test_view_model.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_missing_status_is_grey_not_run`, `::test_verdict_separate_from_light`, `::test_only_stage1_run_one_green_six_grey`, `::test_eight_tabs`.
- **Smoke**: headless Streamlit start returns HTTP 200.
- **Break verification**: map missing → red → grey test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- import-linter keeps `dashboard → src.common.status` only.
````

### `32_s6_export.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 32: S6 ONNX export bundle

**Stage:** `stages/stage_6.md` R12, R21 (export README), Done-when D5 · **Plan refs:** `implementation.md` § Deployment demo; § Attribution
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E32) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The best model must run from `export/` alone with identical preprocessing.

## 2. Root Cause & Investigation
No `export/` code.

## 3. Architecture & Modular Design Strategy
`src/stage6_report/export.py`: choose the model by **validation** macro-F1 (no test peeking), `torch.onnx.export`, copy `standardize.py` verbatim, write `labels.json`. `export/predict.py`: `preprocess`, `predict_proba`, `predict` (numpy/PIL/onnxruntime only). `export/README.md`: usage + attribution + redistribution statement.

## 4. Proposed Changes by File
- `src/stage6_report/export.py`; `export/predict.py`, `export/README.md`, `export/__init__.py`.
- `tests/export/test_predict.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_predict_on_fresh_rgb_image_any_size`, `::test_preprocess_uses_standardize`, `::test_labels_json_matches_taxonomy`.
- **Break verification**: plain resize instead of standardize → preprocessing test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Validation-only selection, documented in the README.
````

### `33_s6_demo.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 33: S6 draw-and-infer demo

**Stage:** `stages/stage_6.md` R13–R17, Done-when D9, Mission M4 · **Plan refs:** `implementation.md` § Deployment demo
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E33) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
CRISP-DM Deployment step.

## 2. Root Cause & Investigation
`streamlit-drawable-canvas` fails with Streamlit 1.61 → the plan's fallback: Gradio `Sketchpad`.

## 3. Architecture & Modular Design Strategy
`demo/logic.py` (pure, imports `export` only): `is_blank(rgba)` (alpha test), `infer(rgba)` → result or message (`Draw a shape first`, `not sure` below 0.5, `no exported model yet`), catching `Rejected`. `demo/app.py`: Gradio Blocks, 256×256 Sketchpad (black ~8 px brush), Infer + Clear, top-3 bars, 64×64 image.

## 4. Proposed Changes by File
- `demo/__init__.py`, `logic.py`, `app.py`.
- `tests/demo/test_logic.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_blank_canvas_alpha_zero_is_blank`, `::test_single_dot_message`, `::test_low_confidence_not_sure`, `::test_missing_model_message`, `::test_drawing_returns_top3_and_x64`.
- **Break verification**: RGB-darkness blank test → alpha test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- The 60-drawing live sketch check is BLOCKED-ON-HUMAN.
````

### `34_s6_phase1_report_fixes.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E34 evidence line

# Plan 34: S6 Phase 1 report fixes

**Stage:** `stages/stage_6.md` R1–R4, R2b, R18 · **Plan refs:** `implementation.md` Decisions 1, 2, 15; § LaTeX-ready extension of Figure 2
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E34) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The Phase 1 report contradicts the plan in several places.

## 2. Root Cause & Investigation
`phase1_report.tex`: `fig:evalsplit` in a 0.32\linewidth minipage; Split paragraph lines 466–467; gemstone 'might' wording; typo list; `fig:crisp` Deployment; `scripts/` paths moved by E15.

## 3. Architecture & Modular Design Strategy
Text edits; numbers come from Stage 1 via generated `\input` snippets (`artifacts/stage1/report_counts.tex`, `gemstones.tex`).

## 4. Proposed Changes by File
- `phase1_report.tex`.
- `src/stage1_freeze/report_snippets.py`.

## 5. Test Strategy & Verification Plan
- **Report**: `.\build.ps1` compiles; Figure 2 page inspected at 100 %.
- **Grep**: none of the listed typos remain; no `12,761`.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Gemstone count reads `dry run` until the human list exists.
````

### `35_s6_phase2_report.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 35: S6 Phase 2 report, traceability, Stage 6 run

**Stage:** `stages/stage_6.md` R5–R8, R8b, R19–R21, Should 1–2, Done-when D1–D4, D6, D7 · **Plan refs:** `implementation.md` Decisions 9–14; § Attribution
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E35) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The Phase 2 report must be generated from artifacts.

## 2. Root Cause & Investigation
Skeleton from E18.

## 3. Architecture & Modular Design Strategy
`phase2_report.tex` `\input`s Stage 5 tables, Stage 1 counts, Stage 3 ranges (`param_ranges.tex` generated from JSON), Stage 5 figures. `traceability.py` flags digits outside `\input` and placeholder dashes. `run(config)`: snippets, build via `build.ps1 -File phase2_report.tex`, traceability, export, status.

## 4. Proposed Changes by File
- `phase2_report.tex`; `src/stage6_report/snippets.py`, `traceability.py`, `run.py`.
- `tests/stage6/test_traceability.py`, `tests/stage6/test_snippets.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_flags_hand_typed_number`, `::test_flags_phase1_counts`, `::test_input_lines_ok`, `::test_flags_placeholder_tables`.
- **Report**: build via the pipeline; PDF read.
- **Break verification**: whitelist all digits → hand-typed test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Rubric checklist (R20) and license choice are BLOCKED-ON-HUMAN; ablations (Should 1) DEFERRED unless time remains.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Status lines record 'verified in tree' or 'evidence in ignore/todo.md' (E31 to E35).

## Our decision

Dashboard, ONNX export, demo, Phase 1 report fixes and the Phase 2 report.

## Measured effect

Reporting only, with no macro F1 change.

---

##  Analysis: Stage 6 Traceability, Export & Deployment Contracts (`E32`–`E36`)

### Decomposition of Stage 6 into Five Auditable Deliverables

Stage 6 (`stages/stage_6.md` and plans `32_s6_report.md` through `36_s6_dashboard.md`) enforces the rule that **no number appears in the report or UI unless traced to a machine-generated artifact**:

| Plan ID | Target Component | Core Verification & Isolation Invariant |
|---|---|---|
| **`E32` (`32_s6_report.md`)** | `src/stage6_report/{run,traceability}.py`, `phase2_report.tex` | Compiles the LaTeX report (`-halt-on-error`) and runs `check_report` traceability + dataset attribution checks (hardened to fail-closed in `F26` with frozen per-iteration snapshots in `F28` and letter-only macro stems in `F27`). |
| **`E33` (`33_s6_export.md`)** | `export/{model.onnx,standardize.py,predict.py,labels.json}` | Packages the winning model as a self-contained ONNX bundle verified by an automated smoke test (`export_smoke_test`) and byte-identity check against `A2` (`C56`). |
| **`E34` (`34_s6_demo.md`)** | `demo/app.py` | Imports exclusively from `export/` (proving external consumers can run the bundle standalone) and checks alpha-channel ink presence (`rgba[..., 3].sum() == 0`) before inference. |
| **`E35` & `E36` (`35–36_s6_dashboard.md`)** | `dashboard/` $\rightarrow$ `studio/` $\rightarrow$ `ShapeSense_Deployed` | Read-only artifact viewer displaying all 7 stage status lights, validation curves, confusion matrices, and CRISP-DM iteration logs with zero test-split access. |

