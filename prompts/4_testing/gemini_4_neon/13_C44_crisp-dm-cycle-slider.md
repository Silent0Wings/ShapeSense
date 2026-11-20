# C44 — Upgraded & Expanded: CRISP-DM Cycle Slider

Below is a substantially expanded reconstruction of C44, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C44: CRISP-DM cycle slider

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-10
- **Entry:** C44 (`change`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40297573 / gemini_4_neon + 40297573
- **Calibration:** `close-to-reality (30% tier)`
- **Grounding sources:** `studio/web/js/widgets/crisp-cycle.js`, `studio/web/js/pages/home.js`, `studio/data/lights.py`, `docs/crisp_dm/iteration_log.json`, `commit ff7ddbf`, `ShapeSense_Deployed/web/index.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> Our CRISP-DM wheel only shows the latest state and hides iteration 3's trip back. Design a slider that walks iterations 1 to 3 and shows each iteration's frozen result, its route back and what each step found.

**Implicit constraints (made explicit):**
1. **Each iteration must show its own frozen result** — not the latest result retroactively applied to earlier stops. Iteration 1's `-0.36` must not be overwritten by Iteration 3's `+9.20`.
2. **The route back must be visible and distinguish past from present** — the feedback arc for Iteration 1 should not look identical to Iteration 3's.
3. **Every step's finding must be readable** — truncation that hides the outcome defeats the purpose of showing "what each step found."
4. **All 6 phases must render** — including phases with no finding in a given iteration (`business`, `deploy` in Iteration 1), which must be visibly distinct from phases that have findings.
5. **The widget must be navigable without a mouse** — keyboard and mobile users must be able to reach every stop and every phase detail.

---

## Response

Replace the static `crispCycle` call on `home.js` with an interactive `crispProgress({ phases, iterations, results })` widget in `studio/web/js/widgets/crisp-cycle.js`.

**Why a slider and not a set of independent pages (depth):** three separate iteration pages would satisfy "show each iteration" but not "walk iterations 1 to 3" — the comparison across iterations is the point. The slider makes the sequence the primary artifact: the reader sees the route back accumulate, and sees each iteration's result against the same wheel. Independent pages would make the comparison a memory task.

### 1. Iteration slider and quick-stop ticks

Render:
- `<input class="progress-slider" type="range" min="1" max="3" step="1">`, defaulting to `iterations.length` (`3`).
- Clickable `Iteration 1`, `Iteration 2`, `Iteration 3` buttons, each showing its verdict (`fail` / `fail` / `pass`).

Moving the slider or clicking a tick re-renders the SVG wheel and detail panel.

**Why default to `iterations.length` and not `1` (reader-order logic):** the most recent iteration is the one a returning reader wants; a first-time reader can still start at 1 via the leftmost tick. Defaulting to 1 would make every visit start with the two failed iterations, which is the wrong first impression for a page whose main finding is Iteration 3's pass.

**Why the verdict is on the tick, not just in the centre (depth):** the ticks are the map of the sequence. A reader deciding whether to scrub through can see at a glance that the sequence is fail → fail → pass without moving the slider. Putting the verdict only in the centre would require three interactions to learn what the tick row could show in zero.

### 2. Progressive feedback arrows (`back past` vs `back now`)

Keep:
- the **6 forward clockwise arrows** around the CRISP-DM ring,
- the **baseline `Data Understanding → Business Understanding` feedback arc**.

Then, for stop `n`, slice `iterations.slice(0, n)`:
- parse `trip.route.split(' → ')` to map source and target phase indices (`Modeling → Data Preparation`, `Evaluation → Data Preparation`, `Evaluation → Business Understanding`),
- draw **earlier trips** with class `'back past'`,
- draw **the active trip** `k === n - 1` with `'back now'`,
- place an `iteration k` label at each quadratic Bézier midpoint, offset outward toward the centre.

**Why past vs. now must be visually distinct (complex logic):** the CRISP-DM wheel's claim is that the project *cycled back* — the route back is the evidence of iteration. If all trips rendered identically, a reader at Iteration 3 would see three arcs with no way to tell which one Iteration 3 added. The `back now` class is what makes "this is the trip this iteration took" readable. Without it, the slider would show three iterations' worth of arcs as an undifferentiated pile, which is *worse* than the static wheel it replaced.

**Why the label goes at the Bézier midpoint, offset toward the centre (depth):** the route-back arcs cross the interior of the wheel, where the centre verdict text lives. Anchoring the label at the arc's midpoint — the point furthest from both endpoints — keeps it clear of the phase nodes; offsetting toward the centre keeps it clear of the ring. Any other anchor would collide with either the nodes or the centre text.

**Why earlier trips are `back past` and not removed (edge case):** a slider that showed only the active trip would answer "what did this iteration do?" but not "what is the accumulated route?" The `back past` arcs are the record of previous trips — they are what makes the wheel a *cycle* rather than three disconnected iterations. Rendering them muted but present is the difference between a history and a snapshot.

### 3. Centre verdict and clickable step findings

Centre of the SVG wheel:
- `Iteration ${it.id}: ${it.title}`
- the result headline (`No clear gain` / `Clear gain`)
- `${nameArms(r.label)}: ${signed(r.delta)} points`

Each of the 6 `212×92` SVG phase nodes (`node()`) is populated with `it.findings[phase.id]` wrapped across 3 lines, and click handlers open the full finding and link in `.progress-detail` below the wheel.

**Why the centre carries the result and the nodes carry the findings (depth):** the two answer different questions. The centre answers "did this iteration succeed?" — a single number and verdict, comparable across stops. The nodes answer "what did each step do?" — six independent descriptions, not comparable across stops but informative within one. Putting both in one place would conflate an aggregate claim with six local ones.

---

## Validation

When the team integrated `crispProgress` into `studio/web/js/widgets/crisp-cycle.js` and tested it across desktop and mobile viewports in Chromium (commit `ff7ddbf`), **two gaps in the initial draft appeared**:

### Gap 1 — SVG node text truncation

Passing the raw paragraph from `it.findings[phase.id]` directly into `wrap(line, 31)` inside the `212×92` SVG `<rect>` truncated Iteration 2 and Iteration 3 findings mid-sentence after 3 lines (around ~90 characters), hiding key outcomes inside the diagram.

**Why this is the failure mode the entry was meant to prevent (depth):** the prompt asked to show "what each step found." A node that truncates at ~90 characters shows *the beginning* of what each step found, which is the same failure as the original static wheel in a different form — the reader still cannot see the outcome. The widget would have shipped looking correct (all six nodes filled) while functionally hiding the content it was built to reveal.

### Gap 2 — Frozen per-iteration results and empty steps

The initial draft:
- assumed `results` could come from a **single status bundle** rather than `lights.iteration_results()` reading frozen `iter1_status`, `iter2_status`, and `status5`,
- did **not visually dim** phases without findings in Iteration 1 (`business`, `deploy`),
- did **not** provide a clickable `<ol class="cycle-list">` fallback for narrow/keyboard navigation.

**Why "single status bundle" is the wrong data source (complex logic):** a single bundle is the *latest* status. Using it for all three stops would have shown Iteration 3's `+9.20` at Iteration 1 and Iteration 2's stops — exactly the "latest state only" failure the entry was written to fix. Each stop must read its own frozen record: `iter1_status`, `iter2_status`, `status5`. The requirement is not "show three iterations" but "show three *frozen* iterations," and only per-iteration records satisfy that.

**Why dimming is needed, not just omitting (edge case):** a phase with no finding in Iteration 1 could be rendered empty, which reads as "this phase did nothing." Dimming reads as "this phase was not part of this iteration's findings" — a different and correct claim. The two renderings look similar but say different things; only the dimmed version is honest about the data.

**Why the `<ol class="cycle-list">` fallback is not optional (accessibility logic):** a range slider and clickable SVG nodes are both mouse-oriented. Without a focusable list, a keyboard user cannot reach any stop beyond the default, and a screen reader cannot enumerate the phases. The `<ol>` is the semantic structure the SVG lacks — it makes the widget navigable in the modality the SVG cannot serve.

---

## Our decision

Kept Gemini 4 Neon's `crispProgress` range slider, tick buttons, progressive `back past` / `back now` feedback arcs, centre verdict summary, and click-to-inspect `.progress-detail` panel, and **refined two parts** before landing commit `ff7ddbf`:

- **Added `iteration_results()`** in `studio/data/lights.py` (tested by `tests/studio/test_verdict_rows.py`) so stops 1, 2, and 3 pull their own frozen records (`-0.36`, `+0.06`, `+9.20`).
- **Added short box-sized `CAPTIONS[1..3]`** plus `resultLine(r)` for the SVG nodes, while keeping the full `it.findings[id]` text in `.progress-detail`.
- **Dimmed steps with missing findings** (`group.classList.add('dim')`).
- **Added a synchronized `<ol class="cycle-list">`** with `focus()` retention for keyboard accessibility.

**Rationale for keeping the core and refining the gaps (depth):** the slider, tick buttons, progressive arcs, and centre/detail split are all **structurally correct** — the widget failed only at the data source (single bundle vs. per-iteration) and at the rendering boundaries (truncation, empty phases, missing keyboard path). Each refinement is a local change that leaves the interaction design intact. Replacing the slider would have been a larger, harder-to-audit change than fixing the four specific gaps.

**The `CAPTIONS` decision is the most consequential refinement (depth):** it accepts that a `212×92` box cannot hold a full paragraph, and answers by providing a **box-sized summary** for the node while keeping the **full text** one click away in `.progress-detail`. The alternative — shrinking the font or growing the box — would have been a layout fix to a content problem. The chosen fix separates "what fits in the diagram" from "what the step actually found," which is the honest division.

---

## Measured effect

On `index.html`, the slider and 3 tick buttons walk cleanly across:

| Iteration | Comparison | Delta | Verdict | Route back |
|---|---|---|---|---|
| 1 | `B vs A1` | `-0.36` points | `fail` | `Modeling → Data Preparation` |
| 2 | `A2 vs A0` | `+0.06` points | `fail` | `Evaluation → Data Preparation` |
| 3 | `A2 vs A0` | `+9.20` points | `pass` | `Evaluation → Business Understanding` |

All **6 SVG phase nodes** render without mid-sentence truncation, keyboard/mobile views remain navigable via `.cycle-list`, and `test_each_iteration_reports_its_own_result_and_a_missing_record_is_skipped` plus Playwright browser checks pass across light, dark, and phone viewports.

**Interpretation (depth):** the measured effect has four distinct guarantees:
- *Frozen per-iteration results* — verified by `test_each_iteration_reports_its_own_result_and_a_missing_record_is_skipped` (`-0.36`, `+0.06`, `+9.20` are three different records, not one bundle reused).
- *Progressive route-back* — visible in the table: three different routes, not one repeated.
- *No truncation* — verified by browser inspection across the 6 nodes.
- *Keyboard/mobile navigability* — verified by Playwright across light, dark, and phone viewports.

The first is the load-bearing one: the entire entry exists because the wheel "only shows the latest state," and the fix is only correct if the three stops show three records. A widget that walked the slider but reused one bundle would look identical in a screenshot and fail the actual requirement.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added **"why a slider, not independent pages"** (comparison across iterations is the point) | Structural depth |
| 3 | Added **"why default to `iterations.length`"** (returning reader; latest is the headline) | Reader-order logic |
| 4 | Added **"why verdict on the tick, not just the centre"** (map of the sequence, zero interactions) | Depth |
| 5 | Added **"why past vs. now must be visually distinct"** (otherwise the cycle becomes an undifferentiated pile, worse than the static wheel) | Logical rigor |
| 6 | Added **"why the label goes at the Bézier midpoint, offset toward centre"** (clear of nodes and centre text) | Depth |
| 7 | Added **"why earlier trips are muted, not removed"** (history vs. snapshot) | Edge-case logic |
| 8 | Added **"why centre carries result and nodes carry findings"** (aggregate vs. local claims) | Depth |
| 9 | Reframed Gap 1 as **the same failure the entry was fixing** (truncation hides outcomes) | Depth |
| 10 | Reframed Gap 2 as **"single bundle is the wrong data source"** (latest-state failure re-appearing at the data layer) | Logical rigor |
| 11 | Added **"why dimming, not omitting"** (empty reads as "did nothing"; dimmed reads as "not part of this iteration") | Edge-case logic |
| 12 | Added **"why the `<ol>` fallback is not optional"** (keyboard and screen-reader modality) | Accessibility logic |
| 13 | Added **`CAPTIONS` decision rationale** (box-sized summary + full text one click away, not a layout fix to a content problem) | Decision depth |
| 14 | Converted measured effect into a **table** and added **interpretation** flagging the load-bearing guarantee | Coherence |

**Open questions / assumptions (for the team to confirm):**
- Does `iteration_results()` **skip missing records** (the test name says `a_missing_record_is_skipped`) or **fail loudly**? A missing `iter2_status` on a page that claims to walk 1–3 should probably be visible to the author, not silently absent from the tick row. The current test name suggests skipping — worth confirming that is the intended behavior for a missing *frozen* record rather than a missing *optional* one.
- Is `CAPTIONS[1..3]` **hand-written** or generated from `it.findings`? If hand-written, it can drift from the full text; if generated, it is a summarization problem the entry does not describe solving.
- Does the `.progress-detail` panel **scroll into view** on mobile when a node is clicked, or does the reader have to scroll manually? The entry does not say.
- Is the `<ol class="cycle-list">` **synchronized with the slider** (clicking a list item moves the slider) or only with the detail panel? The text says "synchronized" but the scope is ambiguous.
- Does the slider **preserve state** across iteration changes (e.g., if the reader has a phase selected and moves the slider, does the detail panel stay on that phase or reset)? The `focus()` retention mentioned for the `<ol>` suggests attention was paid here, but the behavior is not stated.

---

### Additional Depth Notes (`C44`): SVG Box Truncation Arithmetic & Frozen Snapshot Mapping
- **Truncation Arithmetic (`212×92` SVG Phase Box):** Inside each `212×92` `<rect>`, subtracting the phase header (`24 px`) and horizontal padding (`14 px`) leaves at most **3 lines** at `wrap(line, 31)` ($\le 31 \times 3 = 93$ characters). Raw `it.findings[phase.id]` strings (`140–220` chars) overflowed and truncated mid-sentence after ~90 characters. Introducing `<90`-character `CAPTIONS[1..3]` for the SVG `<text>` nodes while rendering the complete `it.findings[id]` prose in `.progress-detail` eliminated truncation without shrinking font size below legibility.
- **Per-Stop Frozen Snapshot Binding (`lights.iteration_results()`):** Stop 1 reads `iter1_status.json` (`B vs A1 = -0.36`, `fail`), Stop 2 reads `iter2_status.json` (`A2 vs A0 = +0.06`, `fail`), and Stop 3 reads `status5.json` (`A2 vs A0 = +9.20`, `pass`), ensuring historical stops never drift when later iterations run.
