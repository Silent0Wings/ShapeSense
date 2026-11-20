# 4_testing - A15: extra_reads is a constant, so that check cannot fail.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A15 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/run.py, src/common/splits.py, tests/stage5/test_iteration3_repairs.py, tests/stage5/test_run.py, results/phase2_snapshot/status5.json, results/phase2_snapshot/iter2_status.json, results/phase2_snapshot/iteration_log.json, docs/crisp_dm/iteration_3/preregistration.md, ShapeSense_Deployed/web/stage5.html, ShapeSense_Deployed/web/changes.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: extra_reads is a constant, so that check cannot fail.

## Response
In `src/stage5_eval/run.py`, inside `analyse_fn(power, ev)`, `extra_reads` is currently hardcoded as a literal constant:

```python
extra_reads = 0  # reads not tied to an evaluated model; must stay 0
```

That value is then passed straight into `test_reads_ok(test_reads, expected, extra_reads)` (`int(test_reads) == int(expected) and int(extra_reads) == 0`) and written into `status.json` under `checks.extra_reads`. Because `extra_reads` is never computed from `artifacts/test_access.log`, the `int(extra_reads) == 0` clause in `test_reads_ok` can never fail under any execution path.

### Why this is a silent audit gap
1. **Intra-stage bypasses go undetected:** `src/common/splits.py` defines `ALLOWED_TEST_READER = "src.stage5_eval"` and `_allowed_test_reader` permits any module whose `__name__` starts with `"src.stage5_eval."` (or runs as `__main__` inside `src/stage5_eval/`). If another module inside `src.stage5_eval` - or a helper added later outside `src.stage5_eval.evaluate` - calls `load_split("test")`, `load_split("fresh_holdout")`, or `load_split("fresh_holdout_2")`, `load_split` appends a line `(iso_timestamp, run_id, caller_module, split, n_rows)` to `artifacts/test_access.log`.
2. **Count mismatch vs. caller identity:** While `count_test_reads(run_id, log_path=d["log"])` counts total lines for `run_id`, `extra_reads` is supposed to verify that *no module other than the evaluator* read a sealed split. Hardcoding `extra_reads = 0` means `checks.extra_reads` in `results/phase2_snapshot/status5.json` (and displayed on `ShapeSense_Deployed/web/stage5.html`) is an unverified assertion rather than a log-derived measurement. If `expected` were miscomputed or an unexpected caller logged a read while another model hit cache, `test_reads == expected` could even pass while hiding an unauthorized caller.

### Recommended fix
1. Add a helper `reads_outside(run_id: str, reader: str, *, log_path: str | Path | None = None) -> int` in `src/common/splits.py` that parses `artifacts/test_access.log` and counts rows where `len(parts) >= 5 and parts[1] == run_id and parts[2] != reader`.
2. Define `READER = "src.stage5_eval.evaluate"` in `src/stage5_eval/run.py` and replace `extra_reads = 0` in `analyse_fn` with:
   ```python
   extra_reads = reads_outside(run_id, READER, log_path=d["log"])
   ```
3. Add a unit test verifying that a sealed read logged under the active `run_id` by any module other than `src.stage5_eval.evaluate` increments `extra_reads` and causes `test_reads_ok` to return `False`, while reads from older `run_id` entries are ignored.

## Validation
- Inspected `src/stage5_eval/run.py` (`READER`, `test_reads_ok`, `analyse_fn`) and `src/common/splits.py` (`load_split`, `count_test_reads`, `reads_outside`).
- Verified the regression test `test_reads_by_another_module_count_as_extra` in `tests/stage5/test_iteration3_repairs.py` (which writes a log containing `src.stage5_eval.evaluate`, `src.other` for the current `run_id`, and `src.other` for an old `run_id`, asserting `reads_outside("run", s5.READER, log_path=log) == 1`) alongside `test_no_unaccounted_gallery_read` in `tests/stage5/test_run.py` (`test_reads_ok(3, 3, 1) is False`).
- Confirmed in the Iteration 3 Stage 5 execution (`results/phase2_snapshot/status5.json`, `run_id` `2026-11-10T05:27:17-05:00/933815`) and the clean-clone rehearsal recorded in `results/phase2_snapshot/iteration_log.json`.

## Our decision
Verdict: **Stands**. Fixed in iteration 3 (commit `4c7cb90`). The team implemented `src.common.splits.reads_outside(run_id, READER, log_path=d["log"])` with `READER = "src.stage5_eval.evaluate"` inside `src/stage5_eval/run.py`, making `checks.extra_reads` genuinely fail-closed against any sealed split read outside `src.stage5_eval.evaluate`.

## Measured effect
- In Iteration 3 (`results/phase2_snapshot/status5.json`), `checks.extra_reads` is dynamically measured as `0`, `checks.test_reads` is `92` of `92` expected (`checks.test_reads_ok: true`), and the earlier 65 `artifacts/test_access.log` entries from iterations 1 and 2 remain intact (`results/phase2_snapshot/iteration_log.json`).
- `ShapeSense_Deployed/web/stage5.html` (`js/pages/stage5.js`) renders `Sealed reads match the plan: 92 of 92` and `Extra reads outside the plan: 0`, and `ShapeSense_Deployed/web/changes.html` records A15 as `Stands` / `Fixed in iteration 3`.

---

## Upgraded Audit Entry (A15)

### Part I — Audit-Gap & Cache-Integrity Cluster Context (`A15`, `A16`, `A18`, `A26`)
Entries `A15`, `A16`, `A18`, and `A26` share one root pathology: **an assertion that looks like a measurement but is actually a constant, or a cache key that is narrower than the thing it claims to fingerprint.** They are the most dangerous class of flaw in a sealed-evaluation pipeline because they produce *green checks that cannot go red*.

### A15 — `extra_reads` is a constant, so that check cannot fail

**Expanded failure-mode trace.** The chain is: `load_split(sealed)` → appends `(iso, run_id, caller_module, split, n_rows)` to `artifacts/test_access.log` → `count_test_reads(run_id)` counts *total* lines → `test_reads_ok(test_reads, expected, extra_reads)` where `extra_reads := 0` is a literal. There are three distinct ways this goes silent:

1. **Intra-package bypass.** `_allowed_test_reader` accepts any `__name__.startswith("src.stage5_eval.")`. A future helper `src.stage5_eval.diagnostics` calling `load_split("fresh_holdout")` logs a line, but `extra_reads` stays `0` — the check is structurally blind to the only caller class it was meant to catch.
2. **Compensating miscounts.** If `expected` over-counts by one (e.g., a model evaluated twice through cache-miss) and an unauthorized caller reads once, `test_reads == expected` can *pass* while a real violation occurred. The constant `extra_reads` makes these two errors cancel invisibly — a classic **masking-by-construction** bug.
3. **Presentation-layer laundering.** `status5.json.checks.extra_reads: 0` and `stage5.html` "Extra reads outside the plan: 0" inherit the constant. The UI renders a *claim*, not a *measurement*, and a reviewer cannot distinguish "verified zero" from "hardcoded zero."

**Deepened fix rationale.** The `reads_outside(run_id, reader, log_path)` helper must (a) be the *single* source of truth, (b) filter strictly on `parts[1] == run_id` so stale-run log lines from iterations 1–2 (the 65 legacy entries) never contaminate, and (c) treat malformed rows as *fail-closed* (a parse error should raise, not be skipped, otherwise a corrupted log line becomes a silent bypass). `READER = "src.stage5_eval.evaluate"` is deliberately narrower than the `_allowed_test_reader` prefix — the log-reader identity and the *permitted* identity differ by design, and that asymmetry is what makes the check meaningful.

**Why it "Stands."** Once `extra_reads` is log-derived, the check becomes genuinely falsifiable: `test_reads_ok(3, 3, 1) is False` is a real assertion with a real counterexample in `test_no_unaccounted_gallery_read`. The measured `0` in `status5.json` is now *earned*, and the 65 intact legacy entries prove the run-id filter works.

### Cross-Cutting Failure Signature: The Green-Constant
Any `checks.X == 0` where `X` is assigned a literal is a *claim*, not a *measurement*. Audit rule: every boolean in `status.json` must trace to a computed value with a failing counterexample in tests.

