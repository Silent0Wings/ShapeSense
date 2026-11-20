# 4_testing - F15: Drawing on the live page failed once the fourth arm was added
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/34_F15_drawing-on-the-live-page-failed-once-the-fou.md](../claude_opus/34_F15_drawing-on-the-live-page-failed-once-the-fou.md)
- Date: 2026-11-09
- Entry: F15 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / opus_medium_5.5 + 40248536
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#f15, studio/settings.py, studio/server/schemas.py, studio/inference/arms.py, studio/tools/export_arms.py, tests/studio/test_api_bounds.py, studio/README.md, commit 22faa35

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** Drawing on the live page fails with a validation error as soon as we add the fourth arm (`A2`). Why is client-side inference breaking as the arm count grows, and what test should prevent this from happening again?

## Response
The symptom points at the request, not at the models. The live page asks `/api/infer` for every arm it finds, so the body grew from three names to four the moment A2 appeared in `studio/out/arms`. If the request schema still caps the `arms` list at three, Pydantic rejects the body with a 422 before any ONNX session is opened, and the page has nothing to show. That matches "worked with three, fails with four" exactly.

The bound was a hand-written number sitting next to a list that changes. The arm list already lives in one place, `studio/settings.py` (`ARMS`), and both `studio/inference/arms.py` (which arms are available) and `studio/tools/export_arms.py` (which arms are exported) read from the same idea of "every arm". The schema was the one place that kept its own copy.

| Option | Effect | Risk |
|---|---|---|
| Raise the literal cap to 4 | Fixes today's page | Breaks again with the next arm |
| Remove the cap | Never fails on count | Loses a bound on request size, which the schemas are meant to keep ("Every field has hard bounds") |
| Tie the cap to the arm list | `max_length=len(ARMS)` on `InferRequest.arms`, and the same for `FeedbackRequest.results` | None found; one source of truth |

Recommendation: the third. In `studio/server/schemas.py`:

```python
class InferRequest(_Strict):
    image: str = Field(max_length=MAX_BODY_BYTES)
    arms: list[str] = Field(max_length=len(ARMS))
```

Apply the same rule to the feedback body, since a saved wrong prediction carries one result per arm and would hit the same wall.

Then pin the behaviour in `tests/studio/test_api_bounds.py` with two assertions in one test: asking for every arm in `ARMS` at once returns 200, and asking for one more than that (`[*ARMS, "A0"]`) still returns 422. The first assertion is the regression test for this failure; the second keeps the bound honest, so the fix cannot quietly turn into "no limit".

Cautions:
- Keep the existing check that an unknown arm name (for example `C9`) is rejected with 422. The count bound and the name check are separate guards.
- The test should read `ARMS` rather than list arm names, otherwise it ages the same way the schema did.

## Validation
`tests/studio/test_api_bounds.py` holds `test_every_arm_can_be_asked_for_at_once`, which posts `list(ARMS)` and expects 200, then `[*ARMS, "A0"]` and expects 422. The same file keeps the 422 checks for a non-image body, an oversized PNG and the unknown arm `C9`. `studio/server/schemas.py` now bounds both `InferRequest.arms` and `FeedbackRequest.results` with `len(ARMS)`.

## Our decision
Tied the limit to the arm list and added a test. The team kept the bound instead of removing it, because every request field in the schemas has a hard limit by design. The iteration log records the failure as `Overcome`, with the cause "The API still accepted at most three arms."

## Measured effect
Before -> after, as drawn in `iteration_log.json`: "Ask all four arms -> The API allows three -> Error, no answer" -> "Ask all four arms -> The limit follows the arm list -> Four answers". `ARMS` in `studio/settings.py` now lists five arms (`A0`, `A1`, `B`, `A2`, `P`), and the bound follows that list. No separate timing or error-rate measurement was recorded.

---

## Upgraded & Expanded Technical Analysis (`F15`)

### 1. Schema Cardinality as a Derived Invariant (`max_length=len(ARMS)`)
- **The Failure Chain:** When the live Studio frontend requests predictions for every exported arm, the payload `InferRequest.arms` grows from $3$ to $4$ elements upon exporting `A2` (and to $5$ upon exporting `P`). Because `studio/server/schemas.py` hardcoded `Field(max_length=3)`, Pydantic rejected the request with HTTP `422 Unprocessable Entity` at the ASGI boundary before opening any ONNX Runtime session.
- **Why Removing the Bound Violates DoS Hardening:** Every field in `studio/server/schemas.py` enforces an explicit upper bound (`_Strict`, `MAX_BODY_BYTES`) so malformed or adversarial requests (e.g., passing $10,000$ repeated arm names) are rejected in $\mathcal{O}(1)$ validation time before model dispatch.
- **Single-Source Derivation:** Binding `max_length=len(ARMS)` on both `InferRequest.arms` and `FeedbackRequest.results` (where `ARMS` is imported from `studio/settings.py`, the same tuple consumed by `studio/inference/arms.py` and `studio/tools/export_arms.py`) eliminates the duplicated literal while preserving the hard ceiling.

### 2. Orthogonal Boundary Test Algebra (`tests/studio/test_api_bounds.py`)
`test_every_arm_can_be_asked_for_at_once` enforces two complementary boundary assertions derived dynamically from `ARMS` (never hardcoding arm names in the test):
1. **Exact-Ceiling Acceptance:** `POST /api/infer` with `arms = list(ARMS)` ($|\mathcal{A}|$ elements) returns HTTP `200 OK`.
2. **Ceiling-Plus-One Rejection:** `POST /api/infer` with `arms = [*ARMS, "A0"]` ($|\mathcal{A}| + 1$ elements) returns HTTP `422`.
3. **Orthogonal Membership Check:** Unknown arm names (`arms = ["C9"]`, length $1 \le |\mathcal{A}|$) still fail with HTTP `422`, proving cardinality and set-membership guards operate independently.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the three options are raise (breaks at the next arm), remove (loses a bound the schemas promise), and tie to `len(ARMS)` (correct). "Every request field has a hard limit by design" is the reason the bound stays.

**Changelog:** [1] three options with verdicts; [2] keep the bound; [3] two guards (count and name) with two tests; [4] the test reads `ARMS` so it ages.

**Open questions:** Did the fix predate `P`? If it came after, the five-arm case was exercised only indirectly. Is `FeedbackRequest.results` tested as well as inference?
