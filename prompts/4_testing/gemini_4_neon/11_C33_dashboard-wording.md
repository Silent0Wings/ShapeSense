# C33 — Upgraded & Expanded: Dashboard Wording

Below is a substantially expanded reconstruction of C33, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C33: Dashboard wording

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-10
- **Entry:** C33 (`change`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40253714 / gemini_4_neon
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `studio/web/js/plain.js`, `studio/web/js/pages/home.js`, `studio/data/pages.py`, `studio/web/js/svg/charts.js`, `commit f6117b3`, `docs/crisp_dm/iteration_log.json`, `ShapeSense_Deployed/web/index.html`, `ShapeSense_Deployed/web/changes.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> A new reader of our dashboard home page cannot tell what the project does or what it found: it shows arm codes, a bare FAIL and a process title. Rewrite it in plain words, generated from the stored results.

**Implicit constraints (made explicit):**
1. **No hardcoded metrics** — every number on the page must be read from stored artifacts (`configs/pipeline.yaml`, `status*.json`, `model_card.json`).
2. **Separation of concerns** — plain-language translation, page layout, and data loading must be separate modules, so a wording change does not touch a chart and a data-schema change does not touch prose.
3. **Codes are replaced, not removed** — `A0`/`A1`/`B`/`A2`/`P` must still resolve to a consistent readable name on every page that uses them.
4. **The verdict must be legible without a statistician** — `PASS`/`FAIL` replaced by plain outcomes, with the CI explained visually, not just numerically.
5. **The rewrite must generalize to other pages** (`business`, `iteration1`, `iteration2`, `stage5`) — the home page is the first reader, not the only one.

---

## Response

To make `index.html` intelligible to a first-time visitor without hardcoding any numbers, **separate plain-language translation from page layout** and feed the locked `success_criterion` from `studio/data/pages.py` alongside `lights.verdict()`.

**Why separation is the architectural move (depth):** the current home page conflates three responsibilities — *what the project is*, *what the result means*, and *how the result is drawn*. A wording change today requires editing the page module, which also owns layout, which also calls the chart. The fix is to split:

| Responsibility | Module | Reads from |
|---|---|---|
| Translation (codes → words, verdict → sentence) | `studio/web/js/plain.js` | `verdict`, `criterion`, `ARM_NAMES` |
| Data (verdict, criterion, classes) | `studio/data/pages.py` | `configs/pipeline.yaml`, stored JSON |
| Drawing (CI chart) | `studio/web/js/svg/charts.js` | rows passed in |
| Layout | `studio/web/js/pages/home.js` | the three above |

### 1. Expose the locked criterion in `studio/data/pages.py`

Update `_home()`, `_iteration1()`, and `_iteration2()` to include:

```python
"criterion": config()["success_criterion"]
```

so every page that displays a verdict receives `macro_f1_min_gain_points` (`1.0`) **directly from `configs/pipeline.yaml`**.

**Why the criterion must be injected, not inferred from the verdict (complex logic):** a `PASS` is only meaningful relative to a pre-registered threshold. If the page infers the threshold from the verdict (e.g., "PASS means delta > 0"), it silently re-defines success as "any positive delta" — the exact failure the pre-registration exists to prevent. Injecting the locked `1.0` makes the page display *the criterion the experiment was run against*, not *a criterion reconstructed from the outcome*.

### 2. Create `studio/web/js/plain.js` for generated copy and verdict graphics

**2.1 Arm-name mapping.**

```js
ARM_NAMES = { A0: 'Real only', A1: 'Real + augmented', B: 'Real + synthetic',
              A2: 'Full mix', P: 'Synthetic pretraining' }
armName(key)          // 'A0' -> 'Real only'
nameArms(label)       // /\b(A0|A1|A2|B|P)\b/g -> replace codes in free text
```

**Why a word-boundary regex, not string replace (edge case):** a naive `.replace("A0", "Real only")` would corrupt `A01`, `SA0`, or a future `A0x` arm. `\b` anchors the match to whole tokens, so the translation is total over the codes actually used and inert over anything that merely contains them.

**2.2 Verdict headline replacing bare `PASS`/`FAIL`.**

```js
headline(verdict):
  if verdict.verdict === 'pass'           -> 'Clear gain'
  else if spansZero(verdict.ci)           -> 'No clear gain'
  else                                    -> 'Target not met'
```

**Why three outcomes, not two (depth):** `PASS`/`FAIL` collapses two distinct failure modes into one word. "No clear gain" means *the experiment was inconclusive* (CI includes zero); "Target not met" means *the experiment was conclusive but below threshold* (CI excludes zero, delta < 1.0). These imply different next actions — collect more data vs. revise the approach — and a reader cannot act on `FAIL` without knowing which one occurred.

**2.3 Generated summary sentence.**

```js
finding(verdict):
  "<Candidate> scored <delta> points higher/lower than <Reference>."
  + " The uncertainty range includes no difference at all."   // if CI crosses 0
  + " It [did/did not] meet the pre-registered success rule."
```

built from `verdict.label`, `verdict.delta`, `verdict.ci`, `verdict.verdict`.

**Why generate from fields rather than templating a fixed sentence (depth):** a fixed sentence would hardcode the reference arm, the direction, and the threshold. Generating from `label`/`delta`/`ci`/`verdict` means the same code produces a correct sentence for Iteration 3, for a future negative result, and for a different reference arm — no prose edit required.

**2.4 Visual confidence-interval plot.**

`verdictPicture(verdict, required)` calls `ciChart({ label, required, rows })` in `studio/web/js/svg/charts.js`, plotting:
- the point-estimate dot,
- the 95% CI whisker,
- a vertical `0` line,
- a dashed `required +1` target line.

**Why the `0` line and the `required` line are both needed (depth):** the `0` line answers "is there any effect?" (CI excluded or included). The `required` line answers "is the effect big enough?" (delta ≥ 1.0). A reader who sees only the CI whisker cannot tell whether a CI that clears `0` but sits at `+0.4` is a success — the dashed line makes the criterion visible in the same picture as the estimate.

### 3. Rewrite `studio/web/js/pages/home.js`

**3.1 Header.** Replace the process-centric header (`"Shape classification project / From business question to a live model"`) with:
- `"ShapeSense"`
- `"Draw a shape, and a small AI model names it"`
- a one-sentence summary of the ten-shape recognition task.

**3.2 "The ten shapes" card.** Via `shapeRow(meta.classes)`, fetching one real training image per class from `/api/samples?label=${label}&split=train&n=1`, with a `"Try drawing a shape"` CTA linking to `live.html`.

**3.3 "The main finding" card.** Displays `finding(data.verdict)`, `verdictPicture(data.verdict, data.criterion.macro_f1_min_gain_points)`, and a caption explaining the dot, whisker, dashed target line, and `Real only` vs `Full mix`.

**Why the CTA and the sample tiles belong above the finding (reader-order logic):** a first-time visitor needs three things in order — *what is this*, *can I try it*, *what did it find*. The original page led with the process title and a FAIL badge, which answers none of those. The rewrite reorders to match the reader's questions, not the pipeline's stages.

---

## Validation

Committed the changes in `f6117b3` across `studio/web/js/plain.js`, `studio/web/js/pages/home.js`, `studio/data/pages.py`, `studio/web/js/svg/charts.js`, `business.js`, `iteration1.js`, `iteration2.js`, `stage5.js`, and `crisp-cycle.js`, plus tests in `tests/stage2/test_transform_internals.py` and `tests/stage4/test_train.py`.

Inspected `index.html`, `business.html`, `iteration1.html`, `iteration2.html`, and `stage5.html` in a browser (and verified static parity in `ShapeSense_Deployed` Playwright checks) to confirm all displayed text, CI bounds, and `required +1` lines **match the stored JSON records with zero hardcoded metrics**.

**Why Playwright static-parity checks matter here (audit logic):** the deployed site is a static snapshot. A browser check on the live server verifies the *dev* pages; the Playwright parity check verifies the *deployed* pages match the same JSON. Without it, "zero hardcoded metrics" would be a claim about the source tree, not about what a visitor actually sees.

---

## Our decision

Adopted Gemini 4 Neon's `plain.js` module, `pages.py` `criterion` injection, `home.js` plain-language opening (`The ten shapes` + `The main finding` + `ciChart`), and `ARM_NAMES` mapping **verbatim** in commit `f6117b3` (later refined in `9d24f95` to pass `{ damaged: true }` on Iteration 3 pages so clean-image context appears right after the damaged-image verdict).

**Rationale for verbatim adoption:** the design satisfies all five implicit constraints:
1. No hardcoded metrics — every value flows from `pages.py` ← stored JSON / `configs/pipeline.yaml`.
2. Separation of concerns — translation, data, drawing, and layout are four modules.
3. Codes replaced consistently — `ARM_NAMES` + `nameArms()` applied across all pages.
4. Verdict legible — three plain outcomes plus a visual CI with both reference lines.
5. Generalizes — the same `plain.js` / `ciChart` / `criterion` machinery was applied to `business`, `iteration1`, `iteration2`, `stage5`, and `crisp-cycle` in the same commit.

**The `9d24f95` refinement is the interesting one (depth):** passing `{ damaged: true }` on Iteration 3 pages means the clean-image context appears *right after* the damaged-image verdict, not before. This is a reader-order fix that the original C33 did not anticipate — it emerged once Iteration 3 had two verdicts on the same page. That the fix was a **parameter**, not a rewrite, is evidence the separation held.

---

## Measured effect

The home page now:

- introduces the project in **plain language**,
- displays all **10 shape classes** as `72px` sample tiles with a direct `live.html` CTA,
- names all **5 arms** without raw codes,
- renders an **SVG `ciChart`** for every verdict (`index.html`, `business.html`, `iteration1.html`, `iteration2.html`) strictly from stored artifacts.

All automated tests pass after commit `f6117b3` and through the final **535-test audit**.

**Interpretation (depth):** the measured effect has three distinct guarantees that should not be conflated:
- *Plain language* — a first-time reader can state what the project does (testable by reader study, not by CI).
- *No raw codes* — `A0` etc. never appear in prose (testable by grep / Playwright).
- *No hardcoded metrics* — every number matches stored JSON (testable by Playwright parity).

Only the last two are machine-checked. The first — the actual goal of the entry — is asserted but not measured. That is the honest limit of the evidence.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added **responsibility table** (translation / data / drawing / layout) and the *why separation* argument | Structural depth |
| 3 | Added **"why criterion must be injected, not inferred"** (otherwise success is re-defined from the outcome) | Logical rigor |
| 4 | Added **"why word-boundary regex"** edge case (`A01`, `SA0`, `A0x`) | Edge-case logic |
| 5 | Added **"why three outcomes, not two"** (inconclusive vs. conclusive-below-threshold imply different actions) | Depth |
| 6 | Added **"why generate from fields, not template"** (same code for negative results, future arms, different references) | Depth |
| 7 | Added **"why both `0` and `required` lines"** (any-effect vs. big-enough are different questions) | Depth |
| 8 | Added **reader-order logic** for header → CTA → finding | Coherence |
| 9 | Added **"why Playwright static-parity"** (claim is about deployed pages, not source tree) | Audit logic |
| 10 | Added **`9d24f95` refinement** as evidence the separation held (parameter, not rewrite) | Depth |
| 11 | Added **interpretation** distinguishing the three guarantees and flagging that "plain language" is asserted, not measured | Honest limits |

**Open questions / assumptions (for the team to confirm):**
- Is "plain language" **tested at all** — e.g., a short reader study, a readability score (Flesch–Kincaid), or a screenshot review by someone outside the team? The entry's stated goal is comprehension, and the current validation checks codes and numbers but not comprehension.
- Does `nameArms()` apply to **titles and captions** as well as body prose, or only to the generated `finding()` sentence? A code appearing in a chart caption would still confuse a first-time reader.
- The `criterion` injection is added to `_home()`, `_iteration1()`, `_iteration2()` — does it also cover `_stage5()` and `_crisp_cycle()`? The decision text says the machinery was applied to those pages, but the enumerated functions do not include them.
- Does `ciChart` handle **CI that extends beyond the axis range** (e.g., `[8.89, 9.53]` with a required line at `1.0` and a zero line at `0`)? The axis must span all three references, or the chart will clip a meaningful line.
- Is `ARM_NAMES` **also** the source of truth for `ARM_SERIES` in `boot.js` (F29)? If not, the two lists can drift again, and `plain.js` would translate an arm that the chart does not draw — or vice versa.

---

### Additional Depth Notes (`C33`): Three-Branch `spansZero` Decision Table & Zero-Literal Pipeline
Every numerical value and badge rendered by `plain.js` flows from `configs/pipeline.yaml` $\to$ `studio/data/pages.py` (`criterion` + `verdict`) $\to$ `plain.js` (`headline`, `finding`, `verdictPicture`) $\to$ `charts.js` (`ciChart`), with `spansZero(ci) = (ci[0] <= 0 && ci[1] >= 0)` partitioning outcomes into three mutually exclusive badges:

| Branch Condition | `headline(verdict)` Badge | Generated `finding(verdict)` Clause | ShapeSense Instance |
|---|---|---|---|
| `verdict.verdict === 'pass'` | `'Clear gain'` | Reports point gain, 95% CI, and pass against locked $+1.0$ target | **Iter 3 (`A2 vs A0` damaged):** `+9.20`, CI `[8.89, 9.53]` |
| `verdict.verdict !== 'pass'` **and** `spansZero(verdict.ci)` | `'No clear gain'` | Appends `"The uncertainty range includes no difference at all."` | **Iter 1 (`B vs A1`):** `-0.36`, CI `[-1.17, 0.41]`; **Iter 2 (`A2 vs A0`):** `+0.06`, CI `[-0.69, 0.83]` |
| `verdict.verdict !== 'pass'` **and** `!spansZero(verdict.ci)` | `'Target not met'` | Statistically nonzero CI that remained below the $+1.0$-point MPID (or failed per-class harm) | Clean `fresh_holdout_2` (`+0.64`, CI `[0.19, 1.07]`) |
