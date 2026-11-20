# 4_testing - F26: Stage 6 could pass with a failed report check
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/36_F26_stage-6-could-pass-with-a-failed-report-chec.md](../claude_opus/36_F26_stage-6-could-pass-with-a-failed-report-chec.md)
- Date: 2026-11-09
- Entry: F26 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40253714 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, src/stage6_report/run.py, src/stage6_report/traceability.py, tests/stage6/test_run_status.py, stages/stage_7.md, commit 69dcb02

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** Can Stage 6 report `passed` even when a report check fails? Please audit `src/stage6_report/run.py`'s pass logic and its cache keys in `inputs(config)`.

## Response
I found two separate problems: one in the pass logic and one in the cache key.

**1. A failed check did not fail the stage.** Stage 6 runs four checks: the report builds, the export smoke test predicts the expected class, every number in the report is traceable, and source attribution is present in the report and the export README. The traceability and attribution results were written into the status as `checks`, but only the build and smoke test decided `status`. So a report with a hand-typed number, or with the dataset credits missing, could still come out as `passed`. That matters beyond Stage 6: Stage 7 gate G1 reads "every stage has status `passed`", so a soft check here would let an unverified report through to publication.

Fix: collect every failing check into one list and fail the stage if the list is not empty, with a readable reason for each.

```python
if not checks["traceable"]:
    problems.append(f"{trace['n_failing']} report numbers failed the traceability check")
if not checks["attribution_present"]:
    problems.append("source attribution is missing from the report or export README")
if problems:
    result["status"] = "failed"
```

**2. The cache key missed inputs.** The stage is skipped when its input hashes match the last run. The key covered only part of the config and did not include the preprocessing code or the Stage 3 generator status, although the report quotes numbers that depend on them. Changing a config value outside the hashed part, or `standardize.py`, would reuse a stale report. Fix: hash the whole config, `src/stage1_freeze/standardize.py` and `artifacts/stage3/status.json` alongside the existing inputs.

| Change | Risk if left | Cost |
|---|---|---|
| Failed check fails the stage | Unverified report marked passed | None; the checks already run |
| Whole config in the key | Stale report after a config edit | More cache misses after any config edit |
| Preprocessing code and generator status in the key | Stale numbers after a preprocessing or generator change | Same |

The extra cache misses are the right trade: a rebuild of the report is cheap compared with publishing a stale number.

This touches no evaluation rule or sealed data. It only makes Stage 6 report what its own checks found.

Tests I would add: one where all checks pass and no failure is set, a parametrised one where each failing check alone fails the stage, one where any config change changes the key, and one for the preprocessing code and the generator status.

## Validation
`tests/stage6/test_run_status.py` holds the four tests: `test_all_checks_passing_sets_no_failure`, `test_a_failing_report_check_fails_the_stage`, `test_any_config_change_invalidates_the_cache` and `test_cache_tracks_preprocessing_and_generator_status`. The current `inputs()` in `src/stage6_report/run.py` hashes the full `config`, `standardize` and `stage3_status`.

## Our decision
A failed check now fails the stage, and the cache tracks the whole config, the preprocessing code and the generator status (commit 69dcb02). State: Overcome.

## Measured effect
Before: a failed traceability or attribution check -> stage still passed. After: the same check -> stage fails. No count of affected runs is recorded.

---

## Upgraded & Expanded Technical Analysis (`F26`)

### 1. Trust-Boundary Closure ("Ran Without Crashing" vs. "Verified")
Stage 6 (`src/stage6_report/run.py`) evaluates four boolean verification invariants in `checks`:
$$C_{\text{stage6}} = \{\texttt{report\_built}, \; \texttt{smoke\_test}, \; \texttt{traceable}, \; \texttt{attribution\_present}\}$$
- **The Soft-Check Vulnerability:** Prior to commit `69dcb02`, `checks["traceable"]` (`src/stage6_report/traceability.py`) and `checks["attribution_present"]` were recorded inside `status.json` but omitted from the failure gate. Because Stage 7 Gate G1 checks `all(stage.status == "passed")`, a soft check in Stage 6 created a trust-boundary leak allowing an unverified report (with untraceable hand-typed numbers or missing dataset credits) to pass into deployment.
- **Conjunctive Fail-Closed Gate:** Appending human-readable diagnostics to `problems` whenever `not checks["traceable"]` or `not checks["attribution_present"]` and setting `result["status"] = "failed"` when `problems` is non-empty makes `status == "passed"` a strict logical conjunction over all four checks (`test_a_failing_report_check_fails_the_stage` parametrized over each check individually).

### 2. Merkle Cache-Key Completeness in `inputs(config)`
- **Eliminating Partial-Config Blind Spots:** Hashing only a subset of `config` keys alongside Stage 4/5 outputs left Stage 6 blind to edits in `src/stage1_freeze/standardize.py`, `artifacts/stage3/status.json` (which supplies the Stage 3 generator throughput and fidelity facts quoted in the report), and unhashed `configs/pipeline.yaml` sections.
- **Full-Dependency Digest:** Including the full `config` digest, `standardize.py`, and `artifacts/stage3/status.json` in `src/stage6_report/run.py#inputs(config)` trades cheap report-rebuild cache misses for a strict guarantee that `phase2_report.pdf` can never be served from a stale cache after any upstream config, preprocessing, or generator change (`test_any_config_change_invalidates_the_cache`, `test_cache_tracks_preprocessing_and_generator_status`).


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the opening sentence, "two separate problems: one in the pass logic and one in the cache key," is the teaching structure. The problems are independent. Fixing only the pass logic leaves stale reports after a config change; fixing only the key leaves a failing report marked passed. Two fixes, two test groups, two rows in the trade-off table.

**Changelog:** [1] two independent problems; [2] the failure message should name the failing numbers, not only count them; [3] on failure, is the reason recorded in `checks` or only the top-level status?; [4] coarse keying is the conservative choice for a report read by external reviewers.

**Open questions:** Does `inputs()` hash the whole config as raw bytes or a parsed, canonical form? Raw bytes make a whitespace-only edit invalidate the cache. Is `test_a_failing_report_check_fails_the_stage` parametrized over all failing checks? A single-case test does not guarantee "every failing check fails the stage," which is the claim being made.
