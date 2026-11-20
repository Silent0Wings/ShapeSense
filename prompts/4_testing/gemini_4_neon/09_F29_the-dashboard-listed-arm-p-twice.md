# F29 — Upgraded & Expanded: The Dashboard Listed Arm P Twice

Below is a substantially expanded reconstruction of F29, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — F29: The dashboard listed arm P twice

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-10
- **Entry:** F29 (`failure`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40248536 / gemini_4_neon + 40248536
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `studio/web/js/pages/boot.js`, `studio/web/js/widgets/predict-panel.js`, `studio/web/js/plain.js`, `phase2_report.tex`, `commit ec84804`, `docs/crisp_dm/iteration_log.json`, `ShapeSense_Deployed/web/failures.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> The dashboard lists arm P twice. Find which script added it and how to make the correction safe to re-apply.

**Literature/search framing:** How do you make a data correction or migration script idempotent, so running it twice does no harm? Search for idempotency patterns in database migrations and data-fix scripts.

**Implicit constraints (made explicit):**
1. The fix must **remove the duplicate** without changing the five legitimate arms' order, colors, or labels.
2. The correction must be **re-applicable** — running it a second time must be a no-op.
3. The root cause must be addressed, not just the symptom: a second hardcoded arm list (`ARM_LABEL`) had already drifted, and a future patch could re-introduce the duplicate.
4. The fix must be **verifiable across every consumer** of `ARM_SERIES`, not just the page where the duplicate was visible.
5. The change must not **collide with unrelated in-flight edits** (the same commit also moved Section L tables).

---

## Response

### Where the duplicate came from

In `studio/web/js/pages/boot.js`, `ARM_SERIES` contained two consecutive entries for arm `P` (lines 26–27 prior to fix):

```js
export const ARM_SERIES = [
  { key: 'A0', label: 'Real only (A0)', color: 'var(--series-1)' },
  { key: 'A1', label: 'Real + augmented (A1)', color: 'var(--series-2)' },
  { key: 'B', label: 'Real + synthetic (B)', color: 'var(--series-3)' },
  { key: 'A2', label: 'Full mix (A2)', color: 'var(--series-4)' },
  { key: 'P', label: 'Synthetic pretraining (P)', color: 'var(--series-5)' },
  { key: 'P', label: 'Synthetic pretraining (P)', color: 'var(--series-5)' },
];
```

**Root cause (two failures, not one):**

- **Proximate cause:** when the patch/update script that added Synthetic pretraining (`P`) to the dashboard was **re-applied** after `P` was already present, it appended `{ key: 'P', ... }` a second time **without checking whether `key: 'P'` already existed**. The append was unconditional.
- **Structural cause:** `studio/web/js/widgets/predict-panel.js` maintained a **separate hardcoded 4-arm `ARM_LABEL` literal** (`A0`, `A1`, `B`, `A2`) that had already drifted out of sync with `ARM_NAMES` in `studio/web/js/plain.js` — it was missing `P` entirely. Two independent arm lists is exactly the condition under which one gets updated and the other does not.

Every chart and legend consuming `ARM_SERIES` (such as Stage 4 / Stage 5 multi-arm plots) rendered `P` twice. The predict panel, reading its own drifted list, would have rendered `P` zero times.

**Why both causes must be fixed together (depth):** removing the duplicate line fixes the visible symptom but leaves the append-without-check pattern intact — the next patch re-introduces it. Deriving labels fixes the drift but not the duplicate. Only doing both makes the correction *safe to re-apply*, which is the actual requirement.

### Making the correction and future scripts idempotent

Drawing on standard database migration and data-fix idempotency patterns (`INSERT ... ON CONFLICT DO NOTHING` / `UPSERT`, state-guarded DDL, and declarative derivation):

**1. Remove the duplicate and derive labels from a single source of truth.**

Delete the extra `{ key: 'P', ... }` line in `studio/web/js/pages/boot.js`, and replace the manual `ARM_LABEL` dictionary in `studio/web/js/widgets/predict-panel.js` with:

```js
import { ARM_NAMES } from '../plain.js';
const ARM_LABEL = Object.fromEntries(
  Object.entries(ARM_NAMES).map(([key, name]) => [key, `${name} (${key})`])
);
```

Declarative generation from `ARM_NAMES` guarantees `P` appears once and future arms never drift across modules.

**Why declarative beats imperative here (complex logic):** an idempotent *imperative* fix requires every future contributor to remember the guard. A *declarative* derivation makes the guard structural — there is no code path that can append a second `P`, because there is no append. The single source of truth is `ARM_NAMES`; every consumer is a pure function of it.

**2. Idempotency pattern for imperative patch/fix scripts.**

Any data-fix or JS/JSON migration script must be safe to run *N* times (`f(f(x)) == f(x)`):

| Pattern | Mechanism | Why it works |
|---|---|---|
| **Pre-condition / membership guard** | `if any(entry["key"] == "P" for entry in series):` before inserting; or deduplicate by `key` preserving first occurrence | Second run sees `P` present and skips |
| **Keyed upsert rather than blind append** | Store/merge records in a `dict` keyed by `arm` (`A0`, `A1`, `B`, `A2`, `P`); serialize in canonical order | Second run overwrites the same key with the same value — no growth |
| **Post-condition invariant check** | Assert `len(keys) == len(set(keys))` and expected length (`5`) before writing; fail fast | Any future patch that would introduce a duplicate **fails the build** instead of shipping |

**Why all three layers, not just one (depth):**
- The **guard** prevents the specific known duplicate.
- The **keyed upsert** generalizes to arms the guard does not yet know about.
- The **post-condition** catches the case where the guard and the upsert both have a bug — it is the backstop that makes silent failure impossible.

A single-layer fix is one refactor away from regressing; three layers make the invariant *checkable*, not just *intended*.

---

## Validation

- Removed the duplicate `{ key: 'P', ... }` entry from `studio/web/js/pages/boot.js` and switched `ARM_LABEL` in `studio/web/js/widgets/predict-panel.js` to derive from `ARM_NAMES` (commit `ec84804`).
- Opened and checked **every** dashboard page in a browser (`home`, `business`, `stage4`, `stage5`, `stage6`, `live`, `robustness`, `failures`, `changes`) to verify each chart legend, column, and prediction slot lists all five arms (`A0`, `A1`, `B`, `A2`, `P`) exactly once.

**Why page-by-page inspection rather than a single check (audit logic):** `ARM_SERIES` is consumed by multiple pages through different widgets; the duplicate could manifest as a doubled legend on one page and a doubled column on another. The claim "zero duplicates" is only as strong as the set of consumers inspected, so the validation enumerates all nine pages explicitly.

---

## Our decision

Applied the `boot.js` duplicate removal and `predict-panel.js` `ARM_NAMES` derivation **verbatim** in commit `ec84804` (alongside moving Section L's generated log/failure/change tables after the sealed result in `phase2_report.tex`), and adopted uniqueness / single-source-of-truth guards for dashboard arm lists.

**Rationale for verbatim adoption:** the design satisfies all five implicit constraints:
1. Legitimate arms unchanged — only the duplicate line was removed; order, colors, labels preserved.
2. Re-applicable — declarative derivation has no append path; a re-run of any patch cannot re-introduce the duplicate.
3. Root cause addressed — the drifted `ARM_LABEL` list is eliminated, not patched.
4. Verifiable across consumers — all nine pages inspected.
5. No collision with unrelated edits — the Section L move is orthogonal and was reviewed in the same commit.

---

## Measured effect

- `ARM_SERIES` reduced from **6 entries** (duplicate `P`) to **5 unique arms** (`A0`, `A1`, `B`, `A2`, `P`).
- `predict-panel.js` labels remain **automatically synchronized** with `ARM_NAMES` across all 5 arms (`Real only (A0)` through `Synthetic pretraining (P)`).
- Browser inspection across all dashboard pages confirmed **zero duplicate arm entries** or extra legend columns.

**Interpretation (depth):** the measured effect has two distinct claims that should not be conflated. The first (`6 → 5`) is a **point-in-time fix**. The second (auto-synchronization with `ARM_NAMES`) is a **structural guarantee** — it holds for arms that do not exist yet. Only the second is what makes the correction safe to re-apply; the first is what made the dashboard correct today.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Split root cause into **proximate (unconditional append)** and **structural (drifted second list)** | Logical rigor |
| 3 | Added **"why both causes must be fixed together"** (either alone leaves re-application unsafe) | Depth |
| 4 | Added **"why declarative beats imperative"** (structural vs remembered guard) | Depth |
| 5 | Converted idempotency patterns into a **table** mapping pattern → mechanism → why | Clarity |
| 6 | Added **"why all three layers, not just one"** (guard / upsert / post-condition as backstop) | Logical rigor |
| 7 | Added **"why page-by-page inspection"** (claim strength = consumers inspected) | Audit logic |
| 8 | Added **interpretation** distinguishing point-in-time fix from structural guarantee | Coherence |
| 9 | Flagged the coupling of the fix with the **Section L move** as a reviewability concern | Failure-mode anticipation |

**Open questions / assumptions (for the team to confirm):**
- Is `ARM_SERIES` in `boot.js` **also** derivable from `ARM_NAMES`? If so, the duplicate is better fixed by eliminating `ARM_SERIES` as a second literal, not by deleting one line — that would extend the structural guarantee to the list where the bug actually appeared.
- Is there a **build-time lint** asserting `len(ARM_SERIES) == len(set(k for k in ARM_SERIES))` and `set(ARM_SERIES) == set(ARM_NAMES)`? Without it, the next contributor can re-introduce the drift and only browser inspection will catch it.
- The Section L table move was bundled into `ec84804`. Is there a test or traceability check confirming the report still renders correctly after the move, or was that verified only by visual inspection? Bundling unrelated changes increases the blast radius of a revert.
- The "post-condition invariant check" is described as a pattern but is it **implemented** for `boot.js`, or only recommended for future patch scripts? If the latter, the structural guarantee is weaker than the measured effect implies.
- Does the `predict-panel.js` derivation handle **unknown arms** gracefully (e.g., an arm in `ARM_SERIES` but not in `ARM_NAMES`)? If `ARM_NAMES` is the source of truth and `ARM_SERIES` is not derived, a mismatch is possible in the other direction.

---

### Additional Depth Notes (`F29`): Algebraic Unrepresentability vs. Imperative Guards
Let $\mathcal{S}$ be the state space of dashboard arm configurations and $f: \mathcal{S} \to \mathcal{S}$ be a migration or sync operation:
- **Imperative Guard ($f_{\text{guard}}(x) = x$ if `'P' \in x` else $x \mathbin{\Vert} [\text{'P'}]$):** Satisfies idempotency $f(f(x)) = f(x)$, but still permits duplicate states to exist in $\mathcal{S}$ if a file is hand-edited or another script omits the guard.
- **Declarative Projection ($g(\texttt{ARM\_NAMES}) = \text{Object.fromEntries}(\dots)$):** Maps the single-source-of-truth dictionary `ARM_NAMES` (where JavaScript object keys are unique by language specification) directly to `ARM_LABEL`. Duplicate keys are **unrepresentable by construction** in the codomain of $g$, and pairing `ARM_SERIES` with the cardinality invariant `len(keys) == len(set(keys)) == 5` makes any future duplicate fail fast at build/test time.
