# 4_testing - A26: One random generator is shared across analyses.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A26 (`claim`, `4_testing`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: ShapeSense/results/llm_comparison/gemini_audit.md, ShapeSense/src/stage5_eval/stats.py, ShapeSense/src/stage5_eval/run.py, ShapeSense/src/stage5_eval/fresh.py, ShapeSense/src/stage5_eval/robust.py, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/tests/stage5/test_iteration3_repairs.py, ShapeSense_Deployed/web/stage5.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (eval stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: One random generator is shared across analyses.

## Response
In `src/stage5_eval/run.py`, a single mutable `np.random.Generator` initialized from `configs/pipeline.yaml#evaluation.bootstrap_seed` (`0`) is threaded sequentially through `power_check()`, the primary comparison (`_compare()`), the secondary comparisons loop, and `fresh.analyse()`.

Sharing one stateful RNG across separate statistical analyses creates hidden order coupling:
- Adding a new secondary comparison (such as `A2 vs A1` for A27), reordering `evaluation.secondary`, or conditionally skipping `fresh_holdout` changes the number of `rng` draws consumed upstream and silently shifts the bootstrap percentile bounds and p-values of every subsequent analysis.
- When `n_boot = 2,000` is near a decision boundary, an order-induced RNG shift can flip a marginal confidence bound across `0` or change a `p_raw` value without any change to the models or predictions.

**Fix:** Replace the shared generator with a deterministic, order-independent generator factory `analysis_rng(seed: int, name: str)` in `src/stage5_eval/stats.py` using `np.random.SeedSequence(seed, spawn_key=(zlib.crc32(name.encode("utf-8")),))`. Every analysis then receives its own isolated stream (e.g., `"power"`, `"test/primary"`, `"test/A1_vs_A0"`, `"fresh/primary"`, `"robust/primary"`, `"robust/primary_by_source"`, `"robust/secondary/..."`, `"robust/clean/..."`).

## Validation
The team implemented `analysis_rng(seed, name)` in `src/stage5_eval/stats.py` (line 229) and updated every call site in `src/stage5_eval/run.py` (`"power"`, `"test/primary"`, `f"test/{cand}_vs_{ref}"`), `src/stage5_eval/fresh.py` (`"fresh/primary"`), and `src/stage5_eval/robust.py` (`"robust/primary"`, `"robust/primary_by_source"`, `f"{scope}/{cand}_vs_{ref}"`). Verified in `pytest` by `tests/stage5/test_iteration3_repairs.py::test_named_generators_do_not_depend_on_the_order_of_analyses`, which confirms that drawing 100 samples from `"something new"` leaves `analysis_rng(0, "secondary/a").random(3)` bit-identical while differing from `"secondary/b"`.

## Our decision
**Verdict: Stands.** Fixed in iteration 3 (`src/stage5_eval/stats.py`, `run.py`, `fresh.py`, `robust.py`, `docs/crisp_dm/iteration_3/preregistration.md`). Every statistical analysis in Stage 5 now spawns its own named generator from `SeedSequence`.

## Measured effect
All Stage 5 bootstrap analyses (`power`, `test/primary`, 4 `test/` secondaries, `fresh/primary`, `robust/primary`, `robust/primary_by_source`, 4 `robust/secondary/*`, and 5 `robust/clean/*`) execute on isolated, order-invariant RNG streams. In the clean-clone rehearsal reported in `iteration_log.json`, all seven stages reproduced every verdict, robustness figure, and results table identically across runs, and `test_named_generators_do_not_depend_on_the_order_of_analyses` passes.

---

## Upgraded Audit Entry (A26)

### Part I — Audit-Gap & Cache-Integrity Cluster Context (`A15`, `A16`, `A18`, `A26`)

### A26 — One RNG shared across analyses

**Expanded failure-mode trace.** A single `np.random.Generator(seed=0)` threaded through `power_check` → `_compare` → secondary loop → `fresh.analyse` means **every analysis's output is a function of every prior analysis's draw count**. Consequences:

1. **Order coupling:** reordering `evaluation.secondary` (an A27-adjacent change!) shifts every downstream percentile. Adding `A2 vs A1` consumes draws, perturbing `fresh/primary`'s CI *even though neither the models nor the data changed*.
2. **Boundary flips:** with `n_boot=2000`, a marginal `ci_lo` near `0` or a `p_raw` near `0.05` can flip verdict purely from RNG bookkeeping — a **non-reproducible-in-principle** result, since it depends on analysis *ordering*, not just the seed.
3. **Silent cross-contamination:** the bug is invisible in any single run (every run is internally consistent); it only surfaces as "reordering the config changed the result," which no unit test naturally catches.

**Deepened fix rationale.** `analysis_rng(seed, name) = default_rng(SeedSequence(seed, spawn_key=(crc32(name),)))` gives each named analysis an **independent, order-invariant** stream. `SeedSequence`'s spawn-key mechanism is specifically designed for this: the child streams are statistically independent and deterministic in `(seed, name)`. The test `test_named_generators_do_not_depend_on_the_order_of_analyses` is exactly the right invariant: drawing from `"something new"` must leave `"secondary/a"` bit-identical. `crc32` (not a hash-based seed) is acceptable because the name space is small and controlled; a reviewer should note that `crc32` collisions across analysis names would alias streams, but the fixed vocabulary (`"power"`, `"test/primary"`, `f"test/{c}_vs_{r}"`, …) makes this a non-issue in practice.

**Coupling insight (`A26` ↔ `A27`).** A26 and A27 are entangled: adding `A2 vs A1` is safe *only because* A26 isolates streams. Had A26 not been fixed, A27's fix would have silently shifted every downstream CI. The audit ordering matters.

