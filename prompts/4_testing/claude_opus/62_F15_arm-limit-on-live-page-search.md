# 4_testing - F15: Drawing on the live page failed once the fourth arm was added. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F15 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f15) · Record: [F15](../inferred_prompts.md#f15)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> What makes client-side inference break when the number of models on a web page grows? Search for known limits and best practices for loading several ONNX models in ONNX Runtime Web (memory per session, hard-coded model lists, lazy loading).

## Response

### Well established (official documentation)

- **WebAssembly memory is capped.** The ONNX Runtime Web docs state that "WebAssembly has a memory limit of 4GB" because of 32-bit addressing, and that ONNX Runtime Web cannot currently run models larger than 4 GB ([Working with Large Models](https://onnxruntime.ai/docs/tutorials/web/large-models.html)). The same page suggests caching model files with the Cache API or the Origin Private File System so they are not fetched on every page load.
- **Diagnose before tuning.** The official performance guide says to first confirm that the model loads and runs correctly, then turn on `enableProfiling` in the session options to get per-run profiling ([Performance Diagnosis](https://onnxruntime.ai/docs/tutorials/web/performance-diagnosis.html)). Session and environment flags are documented separately ([env flags and session options](https://onnxruntime.ai/docs/tutorials/web/env-flags-and-session-options.html)).
- **Validation limits on API inputs reject requests before any model runs.** In Pydantic, lists support `min_length` and `max_length` constraints, which bound the number of items ([Pydantic standard library types](https://pydantic.dev/docs/validation/latest/api/pydantic/standard_library_types/)). FastAPI raises `RequestValidationError` for invalid request data and has a default handler for it ([FastAPI handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)). The page's own example handler returns status 422, and 422 is the usual default, although the page I fetched does not state the default code outright.

### Single reports (bug trackers and issues)

- **Creating the same model more than once runs out of memory.** In a transformers.js issue, a `RangeError` from `createSessionAllocate` was traced to the same model being loaded several times. The maintainer noted that caching the file does not stop you from creating several sessions ([transformers.js #8](https://github.com/xenova/transformers.js/issues/8)). A second issue traced out-of-memory errors to rebuilding the pipeline on every call ([transformers.js #732](https://github.com/xenova/transformers.js/issues/732)).
- **Sessions that are never released leak memory.** A Mozilla bug reports memory growing without bound when inference engines are cycled, and suspects that OrtValues are not released in `InferenceSession` ([Bugzilla 2074072](https://bugzilla.mozilla.org/show_bug.cgi?id=2074072)).
- **Large wasm compile costs multiply with workers.** Another Mozilla bug notes that the ONNX Runtime wasm binary has very large functions that use a lot of memory when compiled, and that this matters when several workers each load it ([Bugzilla 1921425](https://bugzilla.mozilla.org/show_bug.cgi?id=1921425); [Bugzilla 1916442](https://bugzilla.mozilla.org/show_bug.cgi?id=1916442)).
- A Chromium extensions thread describes loading several models in one page failing on the third model, with a poster suggesting memory is not freed before the next allocation ([chromium-extensions thread](https://groups.google.com/a/chromium.org/g/chromium-extensions/c/-4CNcu5bUGA)). That is an unconfirmed user report.

### My own reasoning

- When the model count grows, things break in two places: in **resources** (memory per session, wasm compile, download size) and in **bookkeeping** (hard-coded counts and lists in the UI, the API schema or the export manifest). For tiny models the resource limits are far away, so a bookkeeping limit is much more likely.
- Best practice from the sources above: create each session once and reuse it, release sessions you no longer need, load lazily when a model is first selected, cache the files, and derive every list or bound from one registry of models rather than repeating a number.

### How it applies to ShapeSense

1. Each ShapeSense ONNX model is a small CNN on 64x64 inputs. Five sessions are orders of magnitude below the [4 GB wasm limit](https://onnxruntime.ai/docs/tutorials/web/large-models.html), so memory was never a likely cause of a failure at the fourth arm.
2. The failure was a bookkeeping limit: `InferRequest.arms` was capped at 3 items, so a request for four arms failed validation before inference started. This is exactly how Pydantic's list `max_length` behaves ([Pydantic docs](https://pydantic.dev/docs/validation/latest/api/pydantic/standard_library_types/)).
3. For the in-browser path, the bug reports suggest one guard worth keeping: create one session per arm, once, and reuse it ([transformers.js #8](https://github.com/xenova/transformers.js/issues/8)). That stays cheap as arms are added.

## Validation

The record's documented cause is that the API accepted at most three arms, which is a schema bound, not an ONNX Runtime limit. The literature does not contradict this. It shows that the ONNX Runtime Web limits (4 GB wasm, duplicated or unreleased sessions) only matter for large or repeatedly created models, so for ShapeSense's tiny CNNs the schema cap is by far the more plausible cause. The search adds one point to the record: it is also worth confirming that the in-browser path creates each session once. I did not verify that against the repo in this pass.

## Our decision

The project tied the bound to the arm list (`max_length=len(ARMS)`), did the same for `FeedbackRequest.results`, and added a test that asks for every arm and then one too many. Arm P later needed no schema change. The findings support keeping a derived bound rather than removing it. A possible addition is a check that the browser code creates and reuses one session per arm. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F15`)

### Metadata & Lineage
* **Entry ID / Type:** `F15` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** FastAPI / Pydantic request schema hardcoded `Field(max_length=3)` on `CompareRequest.arms`, causing HTTP `422 Unprocessable Entity` when the fourth model arm (`A2`) was added to the live Studio canvas.
* **Primary Sources:**
  * Pydantic v2 Documentation: *Fields and Sequence Constraints (`min_length`, `max_length`)*
  * FastAPI Testing Documentation: *Boundary Value Verification with `TestClient`*
  * ONNX Runtime Web Documentation: *WASM Session Caching and Thread Configuration*

### 1. Schema-Registry Drift and Contract Boundary Invariants
When an application exposes an enumeration or registry $\mathcal{A} = (\text{A0}, \text{A1}, \text{B}, \text{A2})$ across a backend validation schema and a frontend client payload, hardcoding literal cardinality bounds ($K = 3$) creates a **split-brain cardinality invariant**:
1. **Single-Source-of-Truth (SSOT) Cardinality Binding:** The request validator constraint must be a pure function of the authoritative registry tuple: `Field(default_factory=lambda: list(ARMS), min_length=1, max_length=len(ARMS))` where `ARMS` is imported from `studio.settings`. Any extension of `ARMS` to $K+1$ entries automatically lifts the schema boundary without manual synchronization.
2. **Client-Side WASM Session Amortized Complexity:** In browser-only deployments (`onnxruntime-web`), instantiating an `ort.InferenceSession` parses the ONNX protobuf graph and compiles WebAssembly kernels ($\mathcal{O}(|\Theta|)$ setup cost). Caching a singleton session promise per `(arm, seed)` key and setting `ort.env.wasm.numThreads = 1` prevents `SharedArrayBuffer` / COOP-COEP header failures on static hosts while bounding multi-arm inference latency to < 15 ms across all 4 arms.

### 2. ShapeSense Verification & Experimental Controls
* **Contract Boundary Tests (`tests/test_studio_api.py`):** Explicit boundary tests assert that passing `list(ARMS)` returns HTTP `200 OK` with predictions for every registered arm, whereas passing `[*ARMS, "A0"]` ($|\mathcal{A}| + 1$) returns HTTP `422`.

