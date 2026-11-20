# 4_testing - F15: Drawing on the live page failed once the fourth arm was added. ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/33_F15_drawing-on-the-live-page-failed.md](../gemini_4_neon/33_F15_drawing-on-the-live-page-failed.md)
- Date: 2026-11-09
- Worksheet entry: F15 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / opus_medium_5.5 + 40248536
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `studio/server/schemas.py`, `studio/settings.py`, `studio/web/js/widgets/predict-panel.js`, `tests/studio/test_api_bounds.py`, `docs/crisp_dm/iteration_log.json`, commit `22faa35`, `ShapeSense_Deployed/web/live.html`, `ShapeSense_Deployed/web/failures.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Drawing on the live page fails with a validation error as soon as we add the fourth arm (`A2`). Why is client-side inference breaking as the arm count grows, and what test should prevent this from happening again?

## Response ()

> **Opus 5.5:** The breakage is a hard-coded request cap, not an ONNX Runtime session or memory limit. Adding a fourth lightweight CNN session is well within budget, so `POST /api/infer` is rejecting the request before inference ever starts:
>
> - **Root cause:** In `studio/server/schemas.py`, `InferRequest.arms` hard-codes `Field(max_length=3)`. Once `studio/settings.py` expands `ARMS` to `("A0", "A1", "B", "A2")` and `predict-panel.js` requests all four arms at once, Pydantic rejects the payload with HTTP `422`.
> - **Same pattern on feedback:** Keep `FeedbackRequest.results` aligned with `len(ARMS)` as well so submitting predictions for every active arm never hits the same wall.
> - **Browser/WASM scaling note:** As the static site moves inference into ONNX Runtime Web, keep each model's session cached lazily in a `Map` and run arms sequentially with `numThreads = 1` rather than instantiating duplicate sessions per stroke, so memory stays flat as arms are added.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Bump `max_length` from `3` to `4` | Fixes `A2`, but will break again when arm `P` is added | Skip; still brittle |
> | Bind `max_length=len(ARMS)` from `studio.settings` | Automatically tracks every arm change across Studio and tests | **Do this** |
> | Drop `max_length` completely | Allows unbounded duplicate lists in `/api/infer` | Skip; weakens API bounds |
>
> Pair the schema fix with a boundary test in `tests/studio/test_api_bounds.py` that posts `list(ARMS)` (expecting `200`) and `[*ARMS, "A0"]` (expecting `422`), so adding a fifth arm later cannot silently desynchronize the API schema from `ARMS`.

## Why this reading fits

Commit `22faa35` directly pairs adding `A2` to `studio/settings.py` (`ARMS`) with replacing `max_length=3` by `max_length=len(ARMS)` in `studio/server/schemas.py` and adding `test_every_arm_can_be_asked_for_at_once` in `tests/studio/test_api_bounds.py`. The `iteration_log.json` entry `F15` confirms the exact symptom, cause ("The API still accepted at most three arms"), and fix, and the pattern scaled without further schema edits when arm `P` was added in Iteration 3 (`4091dab`) and ported to `ShapeSense_Deployed/web/js/infer/run.js`.

## Validation

- Added `test_every_arm_can_be_asked_for_at_once` in `tests/studio/test_api_bounds.py`, verifying `POST /api/infer` returns `200` for `list(ARMS)` and `422` for `[*ARMS, "A0"]`.
- Checked `ShapeSense_Deployed/web/live.html` via `build/check.py` and `tests/browser_checks.mjs`: all five exported ONNX arms (`A0`, `A1`, `B`, `A2`, `P`) plus the equal-weight vote score the same drawing in-browser with logits within `1e-4` of Python.

## Our decision

Tied `InferRequest.arms` (and `FeedbackRequest.results`) in `studio/server/schemas.py` to `max_length=len(ARMS)` imported from `studio.settings`, updated `predict-panel.js` to render all registered arms, and locked the contract with the API bounds test.

## Measured effect

Live drawing inference works across all four Iteration 2 arms and later all five Iteration 3 arms (`ARMS = ("A0", "A1", "B", "A2", "P")`), with HTTP `200` on full-arm requests, HTTP `422` on over-limit lists, and zero API-schema breakage when `P` was added.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`F15`)

### The failure taxonomy: Schema–Config Desynchronization

This is an instance of **N+1 hard-coding**: a schema bound (`3`) that must equal the length of a configurable list (`ARMS`). The bug is not "`3` is wrong"; it is that **`3` is written down at all**. When `ARMS` grows to 4, the schema is stale; when it grows to 5 (`P`), it would be stale again if the fix were "bump to 4". The root cause is a **duplicated source of truth**.

| Fix | Residual risk | Verdict |
|---|---|---|
| Bump `3 → 4` | Re-breaks at 5 (`P`) | Treats symptom |
| `max_length=None` | Unbounded duplicate lists, no DoS guard | Weakens contract |
| `max_length=len(ARMS)` | None — tracks source of truth | **Correct level** |
| Derive at request time from registry | Same as above but adds import coupling | Over-engineered here |

### The boundary-test pattern (generalized)

The test posts `list(ARMS)` $\rightarrow$ `200` and `[*ARMS, "A0"]` $\rightarrow$ `422`. This is the **accept-boundary / reject-boundary pair**: the contract is only real if both sides are tested. A test that only checks the accept side would pass even if the schema had no upper bound at all.

### Scaling evidence

The fix survived the `P` addition (`4091dab`) with **zero schema edits** — the strongest possible evidence that the fix was at the right level. A symptom-level fix would have required a second edit; a source-of-truth fix required none.

