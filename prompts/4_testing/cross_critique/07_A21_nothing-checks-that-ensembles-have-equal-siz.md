# 4_testing - A21: Nothing checks that ensembles have equal size.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A21 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage5_eval/evaluate.py, src/stage5_eval/run.py, src/stage5_eval/stats.py, src/stage5_eval/robust.py, tests/stage5/test_stats.py, results/phase2_snapshot/metrics.csv, results/phase2_snapshot/status5.json, ShapeSense_Deployed/web/changes.html


## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Nothing checks that ensembles have equal size.

## Response
In `src/stage5_eval/evaluate.py`, `ensemble(records)` accepts an arbitrary non-empty `Sequence[dict]` of per-seed prediction records and computes the soft-vote average:

```python
probs = soft_vote(np.stack(stack, axis=0))
```

Looking at `ensemble(records)` and its callers in `src/stage5_eval/run.py` (lines 573-592):

```python
ens: dict[str, dict] = {}
for arm in arms:
    members = [models[s.name] for s in specs if _arm_of(s) == arm]
    rec = evaluate.ensemble(members)
    ...
for needed in (reference, candidate):
    if needed not in ens:
        raise ValueError(f"arm {needed} has no runs; the primary comparison needs it")
```

Neither `evaluate.ensemble` nor that ensemble-building loop checks that `len(members)` is equal across `reference` and `candidate` (or across all compared arms).

### Potential risk
If `configs/pipeline.yaml` accidentally omits a seed for one arm (e.g., 4 seeds in `A0` vs. 5 seeds in `A2`), `evaluate.ensemble` will silently average a 4-model ensemble against a 5-model ensemble. Because larger ensembles achieve lower prediction variance and slightly higher macro-F1, an unequal ensemble size could bias the soft-vote comparison in favor of the arm with more seeds.

### Recommended fix
Add an explicit length/member-count assertion before comparing `ens[reference]` and `ens[candidate]` in `src/stage5_eval/run.py` (and `robust.py` / `fresh.py`), raising `ValueError` if the compared arms do not contain the same number of ensemble members.

## Validation
- Inspected `src/stage5_eval/evaluate.py::ensemble`, `src/stage5_eval/run.py::analyse_fn`, `src/stage5_eval/robust.py::analyse`, `src/stage5_eval/stats.py::per_seed_differences`, and `tests/stage5/test_stats.py::test_per_seed_requires_matching_seeds`.
- Found that Gemini's inspection of `evaluate.ensemble()` in isolation missed the downstream guard already executed for every comparison in both `run.py` (line 621) and `robust.py` (line 126): `per_seed_differences(scores_by_arm[ref], scores_by_arm[cand])` explicitly checks:
  ```python
  if set(scores_a) != set(scores_b):
      raise ValueError(
          f"seed sets differ: {sorted(scores_a)} vs {sorted(scores_b)}"
      )
  ```
- Because `is_arm_member(run)` keeps only plain `{arm, seed}` runs with unique integer seeds per arm and `missing_upstream` aborts Stage 5 if any configured run's `model.pt` is missing, any mismatch in ensemble size - or even different seed IDs of the same count, such as `{0, 1, 2}` vs `{0, 1, 3}` - immediately raises `ValueError` during comparison.
- Verified in `tests/stage5/test_stats.py::test_per_seed_requires_matching_seeds` and in `results/phase2_snapshot/metrics.csv` / `status5.json` that all 5 arms (`A0`, `A1`, `B`, `A2`, `P`) have identical seed sets `[0, 1, 2, 3, 4]`.

## Our decision
Verdict: **Does not stand**. State: **No action**. While `evaluate.ensemble()` does not compare two arms' sizes by itself, Stage 5 (`run.py` and `robust.py`) runs `per_seed_differences` on every primary and secondary comparison, which requires exact equality of the two arms' seed sets (`set(scores_a) == set(scores_b)`) and raises `ValueError` otherwise - a stricter invariant than equal size alone.

## Measured effect
- No code change required (`State: No action`); the invariant is already enforced by `src/stage5_eval/stats.py::per_seed_differences` and guarded by `tests/stage5/test_stats.py::test_per_seed_requires_matching_seeds`.
- All 5 evaluated ensembles in Iteration 3 (`A0`, `A1`, `B`, `A2`, `P` in `results/phase2_snapshot/metrics.csv` and `status5.json`) combine the exact same 5 seeds `[0, 1, 2, 3, 4]`. `ShapeSense_Deployed/web/changes.html` records A21 as `Does not stand` / `No action`.

---

## Upgraded Audit Entry (A21)

### Part IV — Comparability & Coverage Cluster Context (`A21`, `A27`)

### A21 — Nothing checks ensembles have equal size

**Expanded reasoning — the "partial inspection" trap.** `evaluate.ensemble(records)` in isolation does not compare arm sizes, so the critique is locally plausible. But the *downstream* `per_seed_differences` in `run.py` and `robust.py` enforces `set(scores_a) == set(scores_b)` → `ValueError` on mismatch. This is **strictly stronger than equal size**: it also catches `{0,1,2}` vs `{0,1,3}` (same count, different seed identity) — the exact bias case the critique worried about (4 vs 5 seeds) is a strict subset. `is_arm_member` + `missing_upstream` further guarantee no arm silently drops a seed.

**Deepened verdict.** "Does not stand / No action" is correct and the reasoning is a good example of *evaluating the whole call path, not one function*. The measured invariant: all 5 arms (`A0,A1,B,A2,P`) have seeds `[0,1,2,3,4]` in `metrics.csv`/`status5.json`, pinned by `test_per_seed_requires_matching_seeds`. Residual note: the *error message* comes from the comparison layer, not `ensemble()` itself, so a future direct `ensemble()` caller bypassing `per_seed_differences` would be unprotected — worth a defensive assertion in `ensemble()` for robustness, though not currently exploitable.

