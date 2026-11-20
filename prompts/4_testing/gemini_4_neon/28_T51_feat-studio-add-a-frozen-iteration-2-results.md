# 4_testing - T51: feat(studio): add a frozen Iteration 2 results page
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T51 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40297573 + 40253714 / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: ShapeSense/studio/allowlist.py, ShapeSense/studio/data/pages.py, ShapeSense/studio/web/iteration2.html, ShapeSense/studio/web/js/pages/iteration2.js, ShapeSense/studio/web/js/nav.js, ShapeSense/studio/web/js/glossary.js, ShapeSense/studio/web/js/pages/iteration1.js, ShapeSense/tests/studio/_audit_sweep.py, git commit cd48779, ShapeSense_Deployed/web/iteration2.html, ShapeSense_Deployed/web/iterations.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T51 (built, stage `deployment (not a course stage)`): feat(studio): add a frozen Iteration 2 results page. Propose or assist with the exact implementation, checks, and configuration needed for commit `cd48779`.

## Response
Add a dedicated read-only **Iteration 2 results** page to ShapeSense Studio backed exclusively by the frozen snapshot under `docs/crisp_dm/iteration_2/` so Iteration 3 runs in `artifacts/stage5/` can never overwrite the historical Iteration 2 verdict:

1. **Allow-list frozen Iteration 2 files (`studio/allowlist.py`):**
   - Under `DOCS`, add:
     - `"iter2_status": "docs/crisp_dm/iteration_2/data/stage5_status.json"`
     - `"iter2_per_class": "docs/crisp_dm/iteration_2/data/per_class.csv"`
     - `"iter2_comparisons": "docs/crisp_dm/iteration_2/data/comparisons.csv"`
     - `"iter2_fresh_per_class": "docs/crisp_dm/iteration_2/data/fresh_per_class.csv"`
   - Under `IMAGES`, register `iter2_confusion_{arm}` for `arm in ("A0", "A1", "B", "A2")` pointing to `docs/crisp_dm/iteration_2/figures/confusion_{arm}.png`.

2. **Add the page data builder (`studio/data/pages.py`):**
   - Define `_iteration2()` reading `iter2_status` (defaulting to `{"metrics": {}, "checks": {}}`), `iter2_per_class`, `iter2_comparisons`, and `iter2_fresh_per_class` via `read_json` and `read_csv`.
   - Register `"iteration2": _iteration2` in `BUILDERS`.

3. **Create the HTML page and frontend module:**
   - Add `studio/web/iteration2.html` using the standard Studio shell (`css/base.css`, `css/components.css`, `<aside id="nav"></aside>`, `<main></main>`, `<script type="module" src="js/pages/iteration2.js"></script>`).
   - Add `studio/web/js/pages/iteration2.js` calling `boot('iteration2', ...)` with `SERIES = ARM_SERIES.filter((s) => ['A0', 'A1', 'B', 'A2'].includes(s.key))`. Render:
     - `Iteration 2 verdict` hero card with `m.delta` (`+0.06`), `badge('fail', 'Fail')`, 95% CI (`[-0.69, 0.83]`) on the reused test split, ensemble macro-F1 stats, and `test_reads / test_reads_expected`.
     - `Fresh holdout` hero card with `f.delta` (`+0.08`), `badge('fail', 'Fail')`, 95% CI (`[-0.41, 0.57]`) across `4,500` images, plus `scoreRows` for `fresh_per_class` (`domain: [85, 100]`).
     - `F1 per class` (`scoreRows`), `Comparisons` table (`comparison`, `role`, `delta_macro_f1_points`, `ci`, `p_holm`), and the four `/img/iter2_confusion_${s.key}` confusion matrix tiles.
   - Link `['iteration2.html', 'Iteration 2 results']` in `studio/web/js/nav.js` under the `Overview` group, add glossary entries (`iteration 2 results`, `iteration 2 verdict`) in `studio/web/js/glossary.js`, adjust `studio/web/js/pages/iteration1.js` accordingly, and add `"iteration2"` to the page sweep list in `tests/studio/_audit_sweep.py`.

## Validation
- `40297573` and `40253714` verified that `studio/allowlist.py` resolves all four `iter2_*` docs and four `iter2_confusion_*` images strictly under `docs/crisp_dm/iteration_2/` with zero reads from `artifacts/stage5/` or sealed test manifests.
- `tests/studio/_audit_sweep.py` exercises `GET /api/page/iteration2` without touching any test-split files.
- Subsequent regression checks (`tests/studio/test_frozen_iteration2.py` and `tests/stage6/test_frozen_iteration2.py`) confirm `pages.build("iteration2")["metrics"]` preserves `+0.06` (`[-0.69, 0.83]`) and `+0.08` (`[-0.41, 0.57]`) independently of live Stage 5 metrics, and that `docs/crisp_dm/iteration_2/frozen.sha256` hashes match.

## Our decision
- Adopted Gemini 4 Neon's implementation verbatim across all 8 files in commit `cd48779`. (Later, for the static Vercel deployment in `ShapeSense_Deployed/web/iteration2.html`, `iteration2.html` was kept as a redirect to `iterations.html#2` when Iteration 1, 2, and 3 were consolidated.)

## Measured effect
- Commit `cd48779` modified 8 files (`60 insertions(+), 4 deletions(-)`), exposing the frozen Iteration 2 verdict (`+0.06` CI `[-0.69, 0.83]` on reused test; `+0.08` CI `[-0.41, 0.57]` on `4,500`-image `fresh_holdout`, all arms ~95.2-95.4 macro-F1) in Studio navigation without risk of overwrite by Iteration 3 evaluation runs.

---

## Upgraded & Expanded Technical Analysis (`T51`)

### 1. Allow-List Capability Isolation (`studio/allowlist.py`)
To guarantee that the **Iteration 2 results** page (`iteration2.html`) can never read live Iteration 3 outputs from `artifacts/stage5/`, `studio/allowlist.py` acts as a capability boundary between `studio/data/pages.py` and the filesystem:
- `read_json(key)` and `read_csv(key)` only resolve logical keys registered in `allowlist.DOCS` (and `/img/{key}` only serves keys in `allowlist.IMAGES`).
- Binding `iter2_status`, `iter2_per_class`, `iter2_comparisons`, `iter2_fresh_per_class`, and `iter2_confusion_{A0,A1,B,A2}` exclusively to `docs/crisp_dm/iteration_2/{data,figures}/...` makes it structurally impossible for `_iteration2()` to read mutable `artifacts/stage5/` files.
- **Cryptographic Regression Pin (`frozen.sha256` & `test_frozen_iteration2.py`):** Unit tests in both `tests/studio/test_frozen_iteration2.py` and `tests/stage6/test_frozen_iteration2.py` verify that every file under `docs/crisp_dm/iteration_2/` matches `frozen.sha256` and that `pages.build("iteration2")["metrics"]` returns `+0.06` (`[-0.69, 0.83]`) and `+0.08` (`[-0.41, 0.57]`) regardless of what sits in `artifacts/stage5/`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the allow-list enumerates the files a page may read. A page that tried to read `artifacts/stage5/status.json` fails at the list, not at runtime. This is the same single-reader idea as C28: the boundary is a list, not a convention.

**Changelog:** [1] allow-list as boundary; [2] a fifth confusion arm would need an allow-list update or the page silently omits it; [3] the deployed redirect (`iteration2.html` to `iterations.html#2`) is a different rendering from the studio page.

**Open questions:** Does `_audit_sweep.py` prove the page did not read a sealed split, or only that it did not fail? Is the deployed redirect tested for rendering parity?
