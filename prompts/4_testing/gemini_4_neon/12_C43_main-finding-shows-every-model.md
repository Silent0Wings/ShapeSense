# C43 — Upgraded & Expanded: Main Finding Shows Every Model

Below is a substantially expanded reconstruction of C43, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C43: Main finding shows every model

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-10
- **Entry:** C43 (`change`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40297573 + 40248536 / gemini_4_neon + 40297573 + 40248536
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `studio/data/lights.py`, `studio/web/js/plain.js`, `studio/web/js/svg/charts.js`, `studio/web/js/pages/home.js`, `studio/web/js/pages/business.js`, `tests/studio/test_verdict_rows.py`, `commit ff7ddbf`, `ShapeSense_Deployed/web/index.html`, `ShapeSense_Deployed/web/business.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> Our main finding chart only plots Full mix against Real only. How do we show every model against Real only on one axis, mark the tested comparison, and handle a model with no interval?

**Implicit constraints (made explicit):**
1. **One shared axis** — all rows must be visually comparable; different scales defeat the purpose.
2. **The pre-registered test must remain visually distinct** — a reader must not mistake a secondary or descriptive comparison for the primary one.
3. **No fabricated uncertainty** — arm `P` had no bootstrap CI; it must not get a whisker, a zero-width interval, or a made-up range.
4. **Backward compatibility** — Iterations 1 and 2 lack `metrics["robust"]` and must still render, not crash.
5. **The semantic difference must be stated in words, not just in color** — a muted row is a visual cue, but a reader who cannot distinguish colors still needs the distinction explained.

---

## Response

Plotting all four comparisons against `Real only` (`A0`) on one `ciChart` axis — while keeping the pre-registered primary test visually distinct and never fabricating a confidence interval for descriptive arm `P` — requires coordinated updates in three modules: the data builder (`studio/data/lights.py`), the plain-language helper (`studio/web/js/plain.js`), and the SVG renderer (`studio/web/js/svg/charts.js`).

**Why three modules, not one (depth):** the task decomposes into three genuinely different concerns:
- *What rows exist and what values they carry* — a data question (`lights.py`).
- *What each row means and how it is labeled* — a semantics question (`plain.js`).
- *How each row is drawn* — a rendering question (`charts.js`).

Collapsing them into the chart component would put the "no fabricated CI" rule inside SVG drawing code, where it is hard to test and easy to regress. Keeping the rule in the data layer means a unit test can assert `ci is None` without rendering anything.

### 1. Assemble the secondary and descriptive deltas in `studio/data/lights.py`

Add `_other_arms(metrics)` inside `verdict()`:

- **Read secondary deltas.** `"B vs A0"` and `"A1 vs A0"` (with their bootstrap `delta` and `ci`) from `metrics["robust"]["secondary"]`.
- **Compute the descriptive `P` delta.** For arm `P` (descriptive only — no bootstrap CI was run in Stage 5), read `ensembles = metrics["robust"]["ensembles"]` and compute:

```python
delta = ensembles["P"]["perturbed_macro_f1"] - ensembles["A0"]["perturbed_macro_f1"]
# ci = None  # no bootstrap was run
```

- **Sort descending by `delta`** and attach as `"others": _other_arms(m)` on `verdict()`.
- **Graceful degradation.** Older iteration records lacking `metrics["robust"]` naturally return `[]`.

**Why `P`'s delta is computed from ensembles rather than read from `secondary` (complex logic):** `P` is descriptive — it was never entered into the Holm family, so no bootstrap distribution was generated for it. The delta is still well-defined (it is the difference of two ensemble means), but the *uncertainty* is not. Computing the delta from the ensemble table and setting `ci = None` is the only honest representation: the number exists, the interval does not. Reading a delta from a non-existent secondary entry would either fail or, worse, require generating a bootstrap that was never part of the pre-registered analysis.

**Why sorting descending is a data-layer responsibility, not a rendering one (depth):** the ordering encodes a claim — "these rows are ranked by effect size." If the renderer sorts, two consumers of the same data could order it differently. Sorting in `lights.py` makes the order part of the artifact, so `test_other_arms_are_all_against_the_same_reference_and_ordered` can assert it directly.

**Why `[]` for older records rather than an error (edge case):** Iterations 1 and 2 were completed before `metrics["robust"]` existed. Raising would make the home page fail on historical snapshots. Returning `[]` lets the renderer fall back to a single-row chart, which is exactly what those iterations showed.

### 2. Separate tested vs. descriptive rows in `studio/web/js/plain.js`

In `verdictPicture(verdict, required)`:

**2.1 Primary row first, explicitly marked.**

```js
{ delta: verdict.delta, ci: verdict.ci, label: `${nameOf(verdict.label)} (tested)` }
```

**2.2 Secondary/descriptive rows muted.**

```js
verdict.others.map(row => ({ ...row, label: nameOf(row.label), muted: true }))
```

with a fallback `[{ ...tested, label: 'Result' }]` on Iterations 1 and 2 where `others` is empty.

**2.3 Export `otherArmsNote`.**

States plainly that:
- every row compares against `Real only` on **damaged images**,
- the pre-registered test and `+1` target apply **only to `Full mix`**,
- `Synthetic pretraining` has no line because **no uncertainty range was calculated** for it.

**Why the `(tested)` suffix is textual, not just a color (depth):** the primary row is already drawn in `var(--series-1)` and the others in `var(--text-muted)`. Color alone fails for colorblind readers, for printed pages, and for screen readers. The suffix makes the distinction legible in the text layer, so the primary/secondary boundary survives every rendering context.

**Why `otherArmsNote` must state "no uncertainty range was calculated" rather than "no interval" (edge case):** "no interval" could be read as "the interval is zero" — i.e., the estimate is certain. "No uncertainty range was calculated" states the actual situation: the bootstrap was not run, so uncertainty is *unknown*, not *absent*. The distinction matters because unknown uncertainty is a reason for caution, while zero uncertainty would be a reason for confidence.

**Why the fallback is `label: 'Result'` rather than `others: []` and no primary (complex logic):** on Iterations 1 and 2, the primary *was* the whole chart. The fallback preserves that — one row, labeled generically, with no `(tested)` suffix (since there is nothing to distinguish it from). The alternative — silently rendering an empty chart — would make historical pages look broken.

### 3. Handle `ci: null` and `muted` rows in `ciChart` (`studio/web/js/svg/charts.js`)

**3.1 Domain calculation.**

```js
rows.flatMap(r => r.ci ?? [r.delta]).concat([0, required ?? 0])
```

so single-point rows without a CI still fit inside the x-scale.

**Why `?? [r.delta]` and not `?? [r.delta, r.delta]` (depth):** a single-element array contributes the point to the domain; a two-element identical array would contribute the same value twice, which is harmless but signals "this is an interval" to any downstream consumer that reads array length. The single-element form is semantically honest: a point, not a degenerate interval.

**3.2 Color and guide line.**

- `var(--series-1)` for the primary tested row.
- `var(--text-muted)` when `row.muted` is true.
- Dotted guide from `left` to `scale(row.ci ? row.ci[0] : row.delta) - 9`.

**3.3 Optional whisker and labels.**

- Render the CI whisker `<line>` **only** `if (row.ci)`.
- In the right-hand numeric column and full-row tooltip: render `[lo, hi]` when `row.ci` exists, `'no range'` / `'no range calculated'` when `row.ci` is `null`.

**Why `if (row.ci)` and not `if (row.ci !== null)` (edge case):** `undefined` would also be falsy, so a row that accidentally omitted the `ci` key entirely (rather than setting it to `null`) would render as a point rather than throwing. This is the safe failure mode: a missing key degrades to "no range," not to a broken chart. The `_other_arms` builder sets `ci: None` explicitly, so the two cases are distinguished at the data layer, but the renderer is robust to both.

**Why the guide line uses `row.ci[0]` when present but `row.delta` when absent (depth):** the guide line connects the row label to the *visual mark*. For a row with a whisker, the leftmost mark is `ci[0]`; for a point-only row, the only mark is `delta`. Anchoring the guide to the correct leftmost mark keeps the connection legible in both cases, rather than drawing the guide to a point that is not the row's leftmost extent.

---

## Validation

Added `tests/studio/test_verdict_rows.py` (5 unit tests):

| Test | Invariant proved |
|---|---|
| `test_other_arms_are_all_against_the_same_reference_and_ordered` | `["P vs A0", "B vs A0", "A1 vs A0"]` ordering — all rows share the reference and are sorted descending |
| `test_p_has_a_score_difference_but_no_interval` | `delta == 8.5` and `ci is None` — the no-fabrication rule holds at the data layer |
| `test_older_results_without_robust_fields_list_no_other_arms` | `others == []` when `robust` is absent — backward compatibility |

Rendered `index.html` and `business.html` in the browser and verified `ShapeSense_Deployed/snapshot/api/page/home.json` values:

| Row | Value |
|---|---|
| `Full mix (tested)` | `+9.20 [8.89, 9.53]` |
| `Synthetic pretraining` | `+8.62 no range` |
| `Real + synthetic` | `+7.52 [7.18, 7.89]` |
| `Real + augmented` | `+6.98 [6.64, 7.33]` |

**Why the Playwright snapshot check is the load-bearing validation (audit logic):** the unit tests verify the data-layer invariants; the browser check verifies the renderer actually consumes them correctly. A unit test that asserts `ci is None` would pass even if `ciChart` silently replaced `null` with `[0, 0]` — the browser snapshot proves it does not. The two checks cover different failure modes and neither subsumes the other.

---

## Our decision

Adopted Gemini 4 Neon's `_other_arms()` backend helper, `verdictPicture` / `otherArmsNote` presentation logic, and optional-CI `ciChart` rendering **verbatim** in commit `ff7ddbf`.

**Rationale for verbatim adoption:** the design satisfies all five implicit constraints:
1. **One axis** — the shared `ciChart` domain covers all rows.
2. **Primary distinct** — color, muted flag, and textual `(tested)` suffix.
3. **No fabricated uncertainty** — `ci: None` at the data layer, `if (row.ci)` at the renderer, `'no range calculated'` in the text.
4. **Backward compatible** — `[]` for old records, `[{ ...tested, label: 'Result' }]` fallback.
5. **Semantic distinction in words** — `otherArmsNote` states the rules explicitly.

No alternative was considered that satisfied all five with a smaller change. The three-module split is the minimum that keeps the no-fabrication rule testable at the data layer.

---

## Measured effect

The main finding chart on `index.html` and `business.html` displays all **4 comparison arms** on one shared linear axis with `0` and `required +1` lines:

- `Full mix (tested)` at `+9.20 [8.89, 9.53]`
- `Synthetic pretraining` at `+8.62 no range`
- `Real + synthetic` at `+7.52 [7.18, 7.89]`
- `Real + augmented` at `+6.98 [6.64, 7.33]`

All **5 tests** in `tests/studio/test_verdict_rows.py` pass, and **zero confidence intervals are fabricated** for descriptive arm `P`.

**Interpretation (depth):** the measured effect has two claims:
- *All four rows on one axis* — verified by the browser snapshot.
- *Zero fabricated CIs* — verified by `test_p_has_a_score_difference_but_no_interval` at the data layer and by the snapshot showing `no range` at the rendering layer.

The second claim is stronger than it looks: `P`'s delta (`+8.62`) is larger than `B`'s (`+7.52`) and `A1`'s (`+6.98`), so a naive implementation that treated missing CIs as zero-width would make `P` look like a *more* certain and *larger* effect than the tested secondaries. The no-fabrication rule is what prevents the descriptive arm from being visually promoted above the inferential ones.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added **"why three modules, not one"** (data / semantics / rendering; no-fabrication rule stays testable) | Logical rigor |
| 3 | Added **"why `P`'s delta is computed from ensembles, not read from secondary"** (`P` was never in the Holm family) | Depth |
| 4 | Added **"why sorting is a data-layer responsibility"** (order is part of the artifact, so tests can assert it) | Logical rigor |
| 5 | Added **"why `[]` rather than an error"** (historical snapshots must render) | Edge-case logic |
| 6 | Added **"why `(tested)` is textual, not just color"** (colorblind / print / screen-reader) | Depth |
| 7 | Added **"why 'no uncertainty range was calculated' ≠ 'no interval'"** (unknown vs. zero) | Depth |
| 8 | Added **"why the fallback is `label: 'Result'`"** (preserves historical single-row charts) | Edge-case logic |
| 9 | Added **"why `?? [r.delta]` and not `[r.delta, r.delta]`"** (point, not degenerate interval) | Depth |
| 10 | Added **"why `if (row.ci)` not `!== null`"** (safe on missing key) | Edge-case logic |
| 11 | Added **"why the guide line anchors to `ci[0]` or `delta`"** (correct leftmost mark) | Depth |
| 12 | Added **"why Playwright snapshot is load-bearing"** (unit tests and renderer test different failure modes) | Audit logic |
| 13 | Added **interpretation** flagging that `P`'s larger delta makes the no-fabrication rule load-bearing | Coherence |

**Open questions / assumptions (for the team to confirm):**
- Is `P`'s delta in `_other_arms` computed from **the same damage levels** (23) as the tested arms? If `ensembles["P"]` averages a different level set, the `+8.62` is not on the same axis as `+9.20` and the shared scale is misleading — the very problem the one-axis requirement was meant to avoid.
- Does `otherArmsNote` **render on every page** that shows the chart (`index.html`, `business.html`, and any future page)? If it is only rendered on the home page, the semantic caveat is absent exactly where the chart is reused.
- Is the `(tested)` suffix **localized** or hardcoded in English? The dashboard has no visible i18n layer today, but the label is generated in `plain.js`, so a localization pass would need to cover it.
- Does `ciChart` handle the case where **all rows have `ci: None`** (e.g., an iteration with no secondary bootstrap)? The domain calculation would fall back to `[delta, 0, required]`, which is fine — worth a test.
- Is there a **visual regression test** (pixel or snapshot) for `ciChart`? The Playwright check verifies the API JSON and visible text, but a chart that renders the correct numbers in the wrong positions would pass.

---

### Additional Depth Notes (`C43`): Summary of the `ci: null` & Ordering Contract
- **Pinned Primary + Sorted Comparators:** Row 0 is unconditionally the pre-registered primary test (`Full mix (tested)`, `+9.20 [8.89, 9.53]`, `muted: false`), while `_other_arms` sorts all remaining comparisons against `A0` descending by `delta`: `P vs A0 (+8.62)` $>$ `B vs A0 (+7.52 [7.18, 7.89])` $>$ `A1 vs A0 (+6.98 [6.64, 7.33])`, all rendered with `muted: true`.
- **Never-Fabricate-an-Interval Invariant:** Because `P` was evaluated across all 23 damage levels (`84.25` vs `A0 = 75.63`, `delta = +8.62`) as a descriptive benchmark outside the pre-registered Holm family, `lights.py` emits `"ci": None`, `ciChart` includes `r.ci ?? [r.delta]` in the x-domain without drawing a whisker `<line>`, and the right-hand label displays `'no range'` (`'no range calculated'`).
