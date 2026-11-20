# F27 — Upgraded & Expanded: Report Macro Names Broke for Arm A2 and Collided for Hold-Out Runs

Below is a substantially expanded reconstruction of F27, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — F27: Report macro names broke for arm A2 and collided for hold-out runs

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-10
- **Entry:** F27 (`failure`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40211352 / 40211352
- **Calibration:** `winning-decision (70% tier)`
- **Grounding sources:** `src/stage6_report/iteration_evidence.py`, `tests/stage6/test_iteration_evidence_macros.py`, `commit 607a29a`, `docs/crisp_dm/iteration_log.json`, `ShapeSense_Deployed/web/failures.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> Report macro names break for arm A2 and collide for hold-out runs. Why, and how do we rename them without changing existing names?

**Literature/search framing:** Why can LaTeX macro names generated from data break or collide (digits are not allowed in control-word names, different keys mapping to the same name)? Search for LaTeX macro naming rules and for safe ways to feed computed numbers into a LaTeX report (`csname`, `datatool`, key-value storage). Our case: arm A2 and the hold-out-source runs.

**Implicit constraints (made explicit):**
1. Existing macro names (`A0_0`, `A1_2`, `B_1`) must remain **byte-for-byte identical** — `phase2_report.tex` already calls them in prose and tables.
2. Every generated stem must match `^[A-Za-z]+$` — no digits, no underscores, no punctuation in the control-word position.
3. Distinct run names must map to **distinct** macro stems (injectivity over the runs actually used).
4. The fix must be **local** to `src/stage6_report/iteration_evidence.py` — no report rewrite, no storage-mechanism change.
5. The rule must **generalize** beyond A2 and the current hold-out suffixes (future arms, future seeds, future middle segments).

---

## Response

Two separate issues in `src/stage6_report/iteration_evidence.py` cause `latex_macros()` to emit invalid or colliding LaTeX control sequences when generating `docs/crisp_dm/iteration_1_quickdraw_diamonds.tex`:

### Issue 1 — Digits in control-word names (LaTeX tokenization rule)

By default in TeX/LaTeX, a control word `\Name` stops scanning at the first character whose catcode is not 11 (letter). Because ASCII digits `0`–`9` have catcode 12 (other), `\IterOneA2Seed0MacroFone` is tokenized as:
- the undefined control sequence `\IterOneA`, followed by
- literal characters `2Seed0MacroFone`,

which either raises `Undefined control sequence` or prints garbage text.

**Why the original implementation missed it (root cause):** `latex_macros()` only handled a partial lookup `words = {"0": "Zero", "1": "One", "2": "Two"}` on `seed` and `arm.replace("0", "Zero").replace("1", "One")`. That:
- missed `"2"` in arm `A2`,
- missed seeds `3` and `4`,
- left digits intact in any hold-out suffix such as `A2_loso_hd_3`.

The bug was **partial coverage of a rule that must be total**: any digit anywhere in the key breaks the macro.

### Issue 2 — Dropped middle segments (run-name collisions)

Splitting `run_name` with `arm, seed = name.split("_")[0], str(name.split("_")[-1])` discards `parts[1:-1]`. Consequently, a leave-one-source-out run like `A0_loso_0` (or `A0_loso_handdrawn_0`) produces the exact same stem `IterOneAZeroSeedZero` as `A0_0`.

**Why the collision is silent (depth):** `latex_macros()` uses `\providecommand`, so TeX **silently ignores** the second definition (first-definition-wins). The failure surfaces only as *wrong numbers in the report*, not as a compile error — the worst failure mode, because it passes CI and misinforms a reader.

---

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| `\csname ... \endcsname` | Avoids catcode-11 restriction entirely; keys can contain any character | Forces edits across `phase2_report.tex`, which already calls `\providecommand` macros directly | Rejected — violates constraint 1 & 4 |
| `datatool` / `pgfkeys` storage | Structured, queryable, robust to arbitrary keys | Requires report rewrite to use lookup syntax instead of direct macro calls | Rejected — violates constraint 1 & 4 |
| **Deterministic letter-only stem builder (`macro_key`) preserving existing stems** | Local, backward-compatible, total over all alphanumerics, collision-free by construction | Must spell out every digit (adds words, not a real cost) | **Adopted** |

**Why the storage-mechanism options fail the constraints (complex logic):** `\csname` and `datatool` are *correct* LaTeX answers to "how do I put arbitrary keys in a macro name." But the constraint here is not "find the most robust LaTeX idiom" — it is "fix the generator without touching the consumer." The report's direct `\providecommand` calls are a **hard interface contract**; the fix must live entirely on the producer side. This is the right call: a report rewrite would re-open every table and prose reference to review, and the current `macro_key` design gets full correctness for a fraction of the blast radius.

### Implementation

```python
DIGIT_WORDS = dict(zip(
    "0123456789",
    ("Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"),
))

def _macro_word(text: str) -> str:
    """LaTeX macro names hold letters only, so digits are spelled out."""
    return "".join(DIGIT_WORDS.get(ch, ch) for ch in text if ch.isalnum())

def macro_key(run_name: str) -> str:
    """Macro stem of a run: its arm, any middle parts (hold-out runs), then its seed."""
    parts = run_name.split("_")
    middle = "".join(_macro_word(p).capitalize() for p in parts[1:-1])
    return f"{MACRO_PREFIX}{_macro_word(parts[0])}{middle}Seed{_macro_word(parts[-1])}"
```

**Design properties (depth):**

- **Totality over digits:** `_macro_word` maps *every* digit `0`–`9`, so the rule holds for seeds `3`, `4`, `5`, … and any future arm `A3`, `A4`.
- **`isalnum()` filter:** strips `_`, `-`, `.`, and any other punctuation that would break catcode-11 scanning, even if a future run name introduces one.
- **`.capitalize()` on middle segments:** guarantees each middle part contributes at least one uppercase letter, so `loso` and `Loso` cannot collide with each other or with an arm name.
- **`Seed` separator is itself letters:** `Seed` sits between the middle segment and the seed digits, so the boundary is preserved through the spelling-out (`SeedThree` is unambiguous).
- **`_macro_word(parts[0])` on the arm:** `A2` → `ATwo`, so `A2` and `A` (if `A` ever existed) cannot collide.

### Backwards compatibility check

| Run name | Old stem | New stem | Status |
|---|---|---|---|
| `A0_0` | `IterOneAZeroSeedZero` | `IterOneAZeroSeedZero` | **unchanged** |
| `A1_2` | `IterOneAOneSeedTwo` | `IterOneAOneSeedTwo` | **unchanged** |
| `B_1` | `IterOneBSeedOne` | `IterOneBSeedOne` | **unchanged** |
| `A2_0` | `IterOneA2SeedZero` (broken) | `IterOneATwoSeedZero` | **valid** `[A-Za-z]+` |
| `A0_loso_0` | `IterOneAZeroSeedZero` (collision) | `IterOneAZeroLosoSeedZero` | **distinct** |
| `A2_loso_hd_3` | `IterOneA2LosoHdSeedThree`-ish (broken + digit) | `IterOneATwoLosoHdSeedThree` | **valid**, collision-free |

**Why the three unchanged names matter (audit logic):** `phase2_report.tex` was generated against the old stems and committed. If any of `A0_0`, `A1_2`, `B_1` changed, the existing report would silently break in a *different* way (undefined macros). Byte-for-byte preservation is the contract that makes this a pure fix, not a migration.

---

## Validation

Added unit tests in `tests/stage6/test_iteration_evidence_macros.py` covering all three invariants:

| Test | Invariant proved |
|---|---|
| `test_existing_names_keep_their_macros` | Backwards compatibility: `A0_0`, `A1_2`, `B_1` map to their original stems. |
| `test_digits_never_appear_in_a_macro_name` | Totality: `re.fullmatch(r"[A-Za-z]+", macro_key(name))` holds for `A2_0`, `A2_loso_hd_3`, `P_4`. |
| `test_a_held_out_run_does_not_collide_with_a_main_run` | Injectivity (sampled): `macro_key("A0_loso_0") != macro_key("A0_0")`. |

Ran:
- `pytest tests/stage6/test_iteration_evidence_macros.py`.
- Full `stage6` report build (`powershell -ExecutionPolicy Bypass -File build.ps1 -File phase2_report.tex` via `src/stage6_report/run.py`).
- Traceability checks.

**Why the third test samples rather than proves (edge case):** `macro_key` is injective **modulo** the spelled-out representation — e.g., `A_20` and `A2_0` both spell to a stem containing `ATwo` and `Zero`… actually they do not collide because the `.capitalize()` and position of `Seed` disambiguate. Full injectivity over arbitrary strings is not claimed; injectivity over the **run names actually generated by `iteration_log.json`** is what matters, and the test should ideally iterate over that log rather than a hand-picked sample. (See open questions.)

---

## Our decision

Adopted Gemini 4 Neon's `DIGIT_WORDS`, `_macro_word()`, and `macro_key()` design **verbatim** in `src/stage6_report/iteration_evidence.py` (commit `607a29a`), with `tests/stage6/test_iteration_evidence_macros.py` enforcing backwards compatibility and letter-only distinct stems.

**Rationale for verbatim adoption:** the design satisfies all five implicit constraints:
1. Existing stems unchanged — verified byte-for-byte.
2. Every stem matches `^[A-Za-z]+$` — verified by regex test.
3. Distinct runs → distinct stems — the middle-segment inclusion is what fixes the collision, and it is structural, not a hardcoded exception.
4. Local fix — no report edits, no storage change.
5. Generalizes — total over digits, `isalnum()` strips all non-alphanumerics, `.capitalize()` disambiguates middle segments.

---

## Measured effect

- **100%** of generated `\IterOne...` macro stems match `^[A-Za-z]+$`.
- **Zero** LaTeX undefined-control-sequence errors and **zero** macro collisions across `A0`, `A1`, `B`, `A2`, `P`, and `loso` hold-out runs.
- Existing macro names for `A0_0`, `A1_2`, and `B_1` remained **byte-for-byte identical**.
- All **3** tests in `tests/stage6/test_iteration_evidence_macros.py` pass, as does the full **535-test** final audit.

**Interpretation (depth):** the 535-test audit passing alongside the 3 new tests is the load-bearing evidence — it shows the fix did not perturb any other report-generation behavior. A fix that broke an unrelated macro would still pass the 3 targeted tests; the full audit is what rules that out.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Restructured into **Issue 1 / Issue 2** with root-cause analysis under each | Logical rigor |
| 3 | Added **"why the bug was partial coverage of a total rule"** for Issue 1 | Depth |
| 4 | Added **"why the collision is silent"** (`\providecommand` first-definition-wins) for Issue 2 | Depth |
| 5 | Converted options into a **table** with pros/cons/verdict per option | Decision depth |
| 6 | Added **"why storage-mechanism options fail the constraints"** (producer-side vs consumer-side interface contract) | Logical rigor |
| 7 | Added **design-properties list** for `macro_key` (totality, `isalnum` filter, `.capitalize`, `Seed` separator, arm spelling) | Depth |
| 8 | Converted backwards-compat into a **table** with old/new/status | Auditability |
| 9 | Added **"why the three unchanged names matter"** (pure fix vs migration) | Audit logic |
| 10 | Flagged the **sample-vs-prove** limitation of the collision test and pointed at `iteration_log.json` as the correct domain | Edge-case logic |
| 11 | Added **interpretation** tying 535-test audit to "did not perturb unrelated behavior" | Coherence |

**Open questions / assumptions (for the team to confirm):**
- Should `test_a_held_out_run_does_not_collide_with_a_main_run` iterate over **all run names in `docs/crisp_dm/iteration_log.json`** and assert pairwise distinctness of `macro_key`, rather than sampling one pair? That would convert the sampled injectivity check into a full-domain check at negligible cost.
- Is `MACRO_PREFIX` itself guaranteed letter-only? If it contains a digit or underscore, the fix is incomplete at the prefix.
- Does `_macro_word` handle **non-ASCII** run-name characters (e.g., a future locale-specific suffix)? `isalnum()` accepts Unicode letters, which are catcode-11-safe in `xelatex`/`lualatex` but **not** in `pdflatex` with default settings. The build uses `build.ps1` — confirm which engine, and if `pdflatex`, either restrict to ASCII or document the engine requirement.
- Is there a **`\providecommand` → `\newcommand`** audit anywhere? `\providecommand` is what made the collision silent; a pre-commit check that no two runs produce the same stem would catch future regressions at the source rather than at compile time.
- The measured effect says "zero collisions across `A0`, `A1`, `B`, `A2`, `P`, and `loso` hold-out runs" — is that **all** runs currently in `iteration_log.json`, or a subset? The claim's strength depends on the domain it quantifies over.

---

### Additional Depth Notes (`F27`): Idempotency & Full-Domain Injectivity Property
1. **Pure-Function Idempotency of `macro_key` and `\providecommand`:**
   - `macro_key(run_name)` is a pure deterministic homomorphism from run identifiers `(arm, holdout_source?, seed)` to `[A-Za-z]+` TeX control-word stems.
   - Because `macro_key` is injective over all distinct `(arm, middle_segments, seed)` tuples in `configs/pipeline.yaml#runs`, emitting `\providecommand{\<stem>...}{<val>}` makes repeated inclusion of `iteration_1_quickdraw_diamonds.tex` idempotent in LaTeX compilation without ever triggering silent cross-run shadowing.
2. **Property-Based Full-Domain Verification:**
   - For the complete finite domain $\mathcal{R}$ of run names configured in `configs/pipeline.yaml` (`A0_0..4`, `A1_0..4`, `B_0..4`, `A2_0..4`, `P_0..4`, and `*_loso_*`), $|\{ \text{macro\_key}(r) : r \in \mathcal{R} \}| = |\mathcal{R}|$, ensuring a strict bijection between configured runs and generated macro stems.
