# 4_testing - F26: Stage 6 could pass with a failed report check. ()

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/37_F26_stage-6-could-pass-with-a.md](../gemini_4_neon/37_F26_stage-6-could-pass-with-a.md)
- Date: 2026-11-09
- Worksheet entry: F26 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40253714 / opus_medium_5.5
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage6_report/run.py`, `tests/stage6/test_run_status.py`, `docs/crisp_dm/iteration_log.json`, commit `69dcb02`, `ShapeSense_Deployed/web/stage6.html`, `ShapeSense_Deployed/web/failures.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Can Stage 6 report `passed` even when a report check fails? Please audit `src/stage6_report/run.py`'s pass logic and its cache keys in `inputs(config)`.

## Response ()

> **Opus 5.5:** Yes - right now Stage 6 is fail-open on two report checks and under-hashes its cache inputs, so stale or broken reports can silently pass:
>
> - **Ignored check failures in `run()`:** `src/stage6_report/run.py` computes `trace = check_report(...)` and `attribution = attribution_present(...)` and records them in `checks`, but the failure gate only inspects `checks["report_built"]` and `checks["export_smoke_test"]`. If numbers fail traceability or dataset source attribution is missing, `result["status"]` is never set to `"failed"`.
> - **Incomplete cache keys in `inputs(config)`:** The cache hashes only `config_subtree_hash(config, "runs")` instead of the full config, and omits both `src/stage1_freeze/standardize.py` and `artifacts/stage3/status.json`. Edits to non-`runs` config keys (such as `image_size` or arm settings), preprocessing code, or Stage 3 generator status can serve a stale Stage 6 cache hit.
>
> | Area | Current gap | Fix |
> |---|---|---|
> | Gate logic in `run()` | Only checks `report_built` and `export_smoke_test` | Fail stage when `traceable` or `attribution_present` is `False` |
> | Cache key `config` | Hashes only `config["runs"]` subtree | Hash full config via `sha256_obj(config)` |
> | Cache key upstream inputs | Misses preprocessing & Stage 3 status | Add `standardize` (`standardize.py`) and `stage3_status` (`stage3/status.json`) |
>
> Collect all four gate failures into `problems` before setting `result["status"] = "failed"` and `result["error"] = " | ".join(problems)`, and add unit tests in `tests/stage6/test_run_status.py` covering both failing gates and cache invalidation.

## Why this reading fits

Commit `69dcb02` applies these exact fixes to `src/stage6_report/run.py` (`problems` checks for `traceable` and `attribution_present`, `sha256_obj(config)`, `stage3_status`, and `standardize` in `inputs()`) and introduces `tests/stage6/test_run_status.py`. This matches `iteration_log.json` (`F26`) word for word on both the fail-closed gate and the expanded cache inputs.

## Validation

- Added `tests/stage6/test_run_status.py` with four tests:
  - `test_all_checks_passing_sets_no_failure`
  - `test_a_failing_report_check_fails_the_stage` (parametrized over `traceable=False` and `attribution=False`)
  - `test_any_config_change_invalidates_the_cache` (changing `config["image_size"]` from `64` to `32`)
  - `test_cache_tracks_preprocessing_and_generator_status` (verifying `"standardize"` and `"stage3_status"` keys in `stage6.inputs(config)`).

## Our decision

Made Stage 6 fail-closed on all four checks (`report_built`, `export_smoke_test`, `traceable`, `attribution_present`) and updated `stage6_report.run.inputs()` to hash the full `config` object alongside `src/stage1_freeze/standardize.py` and `artifacts/stage3/status.json`.

## Measured effect

All 4 regression tests in `tests/stage6/test_run_status.py` enforce that any traceability or attribution failure sets `status == "failed"` with a diagnostic `error` message, and any change to `config`, preprocessing code, or Stage 3 generator status invalidates the Stage 6 cache (all checks surfaced cleanly on `ShapeSense_Deployed/web/stage6.html`).

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`F26`)

### Gate completeness (the fail-open derivation)

A stage's status is a function of its checks: $\text{status} = f(\text{checks})$. The bug is that $f$ ignores two of four inputs (`traceable` and `attribution_present`). Formally, $f$ is **not injective on the check vector** — two distinct check vectors (one with `traceable=False`) map to the same `"passed"`. The fix collects all failures into `problems` and sets `"failed"` if `problems` is non-empty, making $f$ **surjective onto `{"passed", "failed"}` and fail-closed on every check it claims to run.** A check that is computed but not gated is worse than no check — it creates false confidence.

### Cache-key completeness invariant

The cache key is $H(\text{inputs})$. The invariant: **if any input that affects the output changes, the key must change.** The bug: `inputs()` hashed `config["runs"]` (not full config), omitted `standardize.py` (preprocessing), and omitted `stage3/status.json` (generator status). So three classes of change — non-`runs` config (e.g., `image_size`), preprocessing code, and generator status — produced **stale cache hits**.

The fix adds `sha256_obj(config)` (full config), `standardize.py`, and `stage3_status`. The four regression tests are **one per class of omission**:
1. all-passing $\rightarrow$ no failure;
2. failing traceability/attribution $\rightarrow$ failure (parametrized over both gates);
3. config change (`image_size` $64 \rightarrow 32$) $\rightarrow$ cache invalidated (changing a *non-`runs`* key that the old `config_subtree_hash(config, "runs")` missed);
4. preprocessing/generator status $\rightarrow$ cache tracks both.

