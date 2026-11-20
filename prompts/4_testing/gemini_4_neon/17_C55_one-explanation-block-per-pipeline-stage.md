# 4_testing - C55: One explanation block per pipeline stage
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/46_C55_one-explanation-block-per-pipeline-stage.md](../claude_opus/46_C55_one-explanation-block-per-pipeline-stage.md)
- Date: 2026-11-10
- Entry: C55 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 / 40248536
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `studio/web/js/widgets/stage-brief.js`, `studio/data/pages.py`, `studio/web/js/pages/stage0.js`, `studio/web/js/pages/stage1.js`, `studio/web/js/pages/stage2.js`, `studio/web/js/pages/stage3.js`, `studio/web/js/pages/stage4.js`, `studio/web/js/pages/stage5.js`, `studio/web/js/pages/stage6.js`, `studio/web/css/components.css`, commit `7719006`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Every stage page of the dashboard shows its tools and tables in its own way, and most of them never say what the stage is for. I want each stage to open with the same block: its job, what goes in, what it does, what comes out, the key finding, and the checks that show it worked, all read from stored results, with links to the previous and next stage. Can you review this design and tell me what to change? Gemini is reviewing it too.

## Response
Create a single shared widget (`stageBrief` and `stageNav` in `studio/web/js/widgets/stage-brief.js`) rendered immediately after `pageHead` on all seven stage pages (`stage0.js` through `stage6.js`), backed by stored `status*.json` checks exposed through `studio/data/pages.py`:

1. **Uniform `stageBrief({ job, input, process, output, finding, checks })` structure:**
   - Top sentence (`.brief-job`): states the stage's single-sentence purpose in plain language.
   - Three-step data-flow strip (`.brief-flow`): `Goes in` → `What it does` → `Comes out`, formatted consistently (`tidy()` capitalizes the first letter and trims any trailing period).
   - Two-column notes row (`.brief-notes`): left column **Key finding** (what actually mattered or went wrong in this stage); right column **How we know it worked** rendering `checks` as a list where each `{ label, ok }` gets a semantic badge via `checkBadge(ok)`: `Passed` (`good` when `ok === true`), `Failed` (`bad` when `ok === false`), or `Recorded` (`info` when `ok === null`, e.g., informational warnings such as Stage 1's source shortcut).
2. **Ground checks in stored artifacts (`studio/data/pages.py`):** Ensure `_stage1()` through `_stage6()` include `"checks": (read_json("statusN") or {}).get("checks", {})` alongside `_stage0()`'s `guards` and `access` summary, so pages never hard-code pass/fail booleans. For example:
   - `stage1.js`: checks `fd` (`every(r => r.holds)`), `d.checks.no_phash_group_spans`, and the informational source-shortcut warning (`ok: null`), and moves `Frozen split` immediately below the brief.
   - `stage2.js` & `stage3.js`: map `d.checks` dynamically via `checkRows(d.checks)`, and on `stage3.js` add a `Real against generated` card above the controls fetching `/api/samples?label=${label}&split=train&n=1` next to the first generated image so new readers immediately see what real vs. synthetic shapes look like.
   - `stage4.js`: compute `Key finding` dynamically from `d.winners.winners` (highest vs. lowest mean validation macro-F1), enforce `no_test_reads` first in `checks`, and keep `Run setup` directly beneath the brief.
   - `stage5.js`: lead with `finding(v, { damaged: true })`, verify `v.verdict === 'pass'`, `test_reads === test_reads_expected`, `extra_reads === 0`, and `harmful_classes.length === 0`, and place the `Verdict` card at the top.
3. **Sequential navigation (`stageNav(stage)`):** Render `Previous: <n-1> · <name>` and `Next: <n+1> · <name>` at the bottom of every stage (`stage === 6` links onward to `live.html`: `Next: Draw and predict`).

**Review note on the paired draft:** Aligning the check labels across `stage0` - `stage6` with `status*.json` keys avoids drift between the brief and the detailed tables below; keeping `ok: null` for non-gating warnings (`Source shortcut found, recorded as a warning`) prevents false-red badges while still surfacing critical caveats.

## Validation
- Student `40248536` and the team reviewed both versions, wired `checks` in `studio/data/pages.py`, applied `stageBrief` and `stageNav` across `stage0.js` - `stage6.js` plus the `Real against generated` card on `stage3.js` and top-of-page key result placement on Stages 1, 4, and 5, and verified all 7 stage pages in Studio and via `pytest`.
- In `ShapeSense_Deployed`, `tests/browser_checks.mjs` verified `stage0.html` - `stage6.html` render cleanly with zero missing checks or error text in light, dark, and phone views.

## Our decision
- Adopted the shared `stageBrief` + `stageNav` widget (`studio/web/js/widgets/stage-brief.js`), artifact-backed `checks` in `studio/data/pages.py`, higher placement of key results on Stages 1, 4, and 5, and the `Real against generated` preview on Stage 3 in commit `7719006`.

## Measured effect
- All 7 pipeline stage pages (`stage0.html` - `stage6.html`) open with the identical 6-part structured explanation block (`job`, `Goes in` → `What it does` → `Comes out`, `Key finding`, `How we know it worked` badges) and end with `stageNav` links through `live.html`.
- Every check badge is driven directly by stored `status*.json` / `guards` artifacts with zero hard-coded pass states.

---

## Upgraded & Expanded Technical Analysis (`C55`)

### 1. The Typed `stageBrief` Contract & Tri-State Badge Semantics
```js
stageBrief({ job, input, process, output, finding, checks })
// checks: Array<{ label: string, ok: true | false | null }>
```
The tri-state `ok` domain (`true | false | null`) in `checkBadge(ok)` is a load-bearing epistemic distinction:
- `ok === true` $\to$ `Passed` (`good` / green): a mandatory gating invariant held.
- `ok === false` $\to$ `Failed` (`bad` / red): a mandatory gating invariant was violated.
- `ok === null` $\to$ `Recorded` (`info` / neutral): an empirical diagnostic finding or non-blocking domain warning that **must be surfaced** without triggering a false-red stage failure (e.g., Stage 1's `"Source shortcut found, recorded as a warning"`).

### 2. Artifact-Backed Check Invariants & Computed Key Findings
- **Zero Hard-Coded Pass States:** `studio/data/pages.py` injects `"checks": (read_json("statusN") or {}).get("checks", {})` for Stages 1–6 (and `guards` + `access` for Stage 0). Because `stage2.js` and `stage3.js` map `d.checks` dynamically via `checkRows(d.checks)` and Stages 1, 4, 5, and 6 bind directly to `d.checks.*` keys, adding or failing a check in `status*.json` automatically updates the brief.
- **Computed "Key Finding" Column:**
  - **Stage 3 (`stage3.js`):** Renders the `Real against generated` side-by-side comparison card above the interactive controls (fetching `/api/samples?label=${label}&split=train&n=1` beside the first synthetic render) so the domain gap is visually inspectable rather than asserted in prose.
  - **Stage 4 (`stage4.js`):** Computes the key finding dynamically from `d.winners.winners` (comparing argmax vs. argmin mean validation macro-F1 across arms) and pins `no_test_reads` as the first verification badge.
  - **Stage 5 (`stage5.js`):** Derives the key finding from `finding(v, { damaged: true })` and verifies the 4-part gating conjunction: `v.verdict === 'pass'`, `test_reads === test_reads_expected`, `extra_reads === 0`, and `harmful_classes.length === 0`.
- **Sequential Chain Navigation (`stageNav(stage)`):** Links `stage - 1` and `stage + 1` with explicit stage titles, terminating at `stage === 6` with an onward link to `live.html` (`Next: Draw and predict`).


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the `ok: null` to "Recorded" badge is a third state. Some checks are observations, not pass/fail claims, and colouring a caveat red would train readers to ignore red.

**Changelog:** [1] three-state badge (observation vs claim); [2] `tidy()` can mutate labels that are already capitalized or punctuated; [3] `stage6` to `live.html` is an intentional special case; [4] labels are aligned with `status*.json` keys to prevent drift.

**Open questions:** Do `status*.json` checks carry a reason for failures, or only a boolean? Is `stageNav` specified for `stage0`, which has no previous stage?
