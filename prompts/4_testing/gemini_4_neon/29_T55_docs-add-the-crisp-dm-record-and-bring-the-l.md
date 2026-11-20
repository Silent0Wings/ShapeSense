# 4_testing - T55: docs: add the CRISP-DM record and bring the living docs up to date
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T55 (`task`, `all stages (CRISP-DM record)`)
- Owner / Proposed by: 40297573 / 40297573
- Calibration: `winning-decision`
- Grounding sources: ShapeSense/README.md, ShapeSense/docs/crisp_dm/README.md, ShapeSense/docs/crisp_dm/iteration_log.json, ShapeSense/studio/README.md, ShapeSense/stages/stage_0.md, ShapeSense/stages/stage_6.md, git commit 9b298b9, ShapeSense_Deployed/web/index.html, ShapeSense_Deployed/web/stage0.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T55 (documented, stage `all stages (CRISP-DM record)`): docs: add the CRISP-DM record and bring the living docs up to date. Propose or assist with the exact implementation, checks, and configuration needed for commit `9b298b9`.

## Response
To consolidate the project's CRISP-DM history and align every living document with the in-progress Iteration 3 state without altering closed Iteration 1 or Iteration 2 records:

1. **Create `docs/crisp_dm/README.md` (146 lines) as the human-readable CRISP-DM index:**
   - State the precedence rule upfront: `docs/crisp_dm/iteration_log.json` feeds the dashboard and wins if any prose diverges, and closed iterations are never rewritten.
   - Summarize all five arms (`A0`, `A1`, `B`, `A2`, plus Iteration 3's `P` pretrained on synthetic shapes and fine-tuned on real images), the closed Iteration 1 (`B vs A1`: `-0.36`, CI `[-1.17, 0.41]`) and Iteration 2 (`A2 vs A0`: `+0.06` CI `[-0.69, 0.83]` reused test; `+0.08` CI `[-0.41, 0.57]` fresh holdout) verdicts, and the pre-registered Iteration 3 status (`docs/crisp_dm/iteration_3/preregistration.md`, evaluating `A2 vs A0` across 23 damage levels on the never-read 4,500-image `fresh_holdout_2`).
   - Document the standing decisions by category (Evidence and evaluation, Modeling, Process and record-keeping, Deployment) and note the two remaining outside-review points open until experiments finish (unequal real images per step and BatchNorm statistics in `B` and `A2`).

2. **Update `docs/crisp_dm/iteration_log.json` incrementally:**
   - Leave the closed Iteration 1 and Iteration 2 entries unchanged.
   - Add the Iteration 3 entry (`"id": 3`, `"status": "open"`, route `"Evaluation → Business Understanding"`) and record Iteration 3 failures `F18` (500-second timeout during `fresh_holdout_2` build leaving a partial folder without manifest), `F19` (worker pool invalid-handle crash from editing training code during worker start-up), and `F20` (108-trial run hanging silently after 6 trials at 12:11 until detected at 14:28, motivating the 5-minute stall watcher).
   - Append the Iteration 3 `changes` entries for `model` (Arm `P`, grouped 3-fold CV top-5 re-scoring at 15 epochs, equal-real/real-fraction/training-length options) and `eval` (moving robustness into Stage 5 with single-build hashed perturbed copies).

3. **Synchronize `README.md`, `studio/README.md`, `implementation.md`, `docs/findings.md`, `docs/source.md`, `export/README.md`, and `stages/stage_0.md` - `stages/stage_6.md`:**
   - Update `README.md` to add Arm `P`, link directly to `docs/crisp_dm/README.md`, document `.\scripts\run_studio.bat` / `python -m studio`, and clarify that sealed data (`test` and both fresh holdouts) raises on `common.load_split` outside `src.stage5_eval`.
   - Add a `> **Current state (2026-11-09).**` callout block at the top of `stages/stage_0.md` through `stages/stage_6.md`, `implementation.md`, `docs/findings.md`, `docs/source.md`, and `export/README.md` so original Phase 1/2 specs stay intact while pointing readers to `docs/crisp_dm/README.md`.
   - Update `studio/README.md` to list the new Studio pages (`Iteration 1 and 2 results`, `Failure timeline`, `Changes by CRISP-DM step`, `Robustness check`) and note that saved drawings write only to `studio/feedback/`.

## Validation
- `40297573` verified via `git diff` that closed records under `docs/crisp_dm/iteration_1/` and `docs/crisp_dm/iteration_2/` and the Iteration 1/2 objects in `docs/crisp_dm/iteration_log.json` remained byte-identical.
- Checked JSON validity of `docs/crisp_dm/iteration_log.json` and confirmed all internal Markdown links between `README.md`, `docs/crisp_dm/README.md`, and `stages/stage_*.md` resolve cleanly.

## Our decision
- Adopted Gemini 4 Neon's structure and per-file updates across all 15 files in commit `9b298b9`.

## Measured effect
- Commit `9b298b9` updated 15 files (`361 insertions(+), 20 deletions(-)`), creating the 146-line `docs/crisp_dm/README.md`, appending `118` lines to `docs/crisp_dm/iteration_log.json` (adding Iteration 3 open tracking, `F18` - `F20`, and 4 `changes` items), and adding current-state banners across all 7 stage briefs (`stages/stage_0.md` - `stage_6.md`) plus root/module READMEs.

---

## Upgraded & Expanded Technical Analysis (`T55`)

### 1. Single-Source Precedence & Append-Only Audit Algebra
- **Machine-Readable Precedence Rule:** `docs/crisp_dm/README.md` codifies that `docs/crisp_dm/iteration_log.json` is the authoritative state backing both the Studio dashboard and Stage 6 report tables; if any prose summary diverges, `iteration_log.json` wins.
- **Non-Destructive Append-Only History:** Closed iterations (`"id": 1` and `"id": 2` in `iteration_log.json`, plus `docs/crisp_dm/iteration_1/` and `docs/crisp_dm/iteration_2/`) are treated as immutable ledger entries (verified byte-identical via `git diff`). Iteration 3 is opened strictly by appending `"id": 3`, failures `F18`–`F20`, and new `changes` records.
- **Banner-Over-Rewrite Pattern for Phase 1/2 Specs:** Rather than editing historical requirements inside `stages/stage_0.md`–`stage_6.md`, `implementation.md`, `docs/findings.md`, `docs/source.md`, and `export/README.md` (which would obscure the original Phase 1/2 design baseline), prepending a `> **Current state (2026-11-09).**` callout block preserves the original specification text verbatim while routing readers directly to `docs/crisp_dm/README.md` for Iteration 2/3 changes.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the precedence rule (`iteration_log.json` wins if prose diverges) is stated first, which is where a governance rule has to sit to be followed.

**Changelog:** [1] precedence rule first; [2] "never rewritten" is a policy enforced by review, not by a check; [3] banners over rewrites preserve historical specs.

**Open questions:** Should the iteration 1 and 2 folders get a `frozen.sha256` check, as T51 does for iteration 2? Are F18 to F20 surfaced on a failures page, or only in the JSON?
