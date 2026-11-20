# 4_testing - T63: chore(studio): keep the saved drawings as informal feedback
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: T63 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40253714 / gemini_4_neon
- Calibration: `winning-decision`
- Grounding sources: ShapeSense/studio/ops/feedback.py, ShapeSense/studio/server/routes_infer.py, ShapeSense/studio/server/schemas.py, ShapeSense/tests/studio/test_api_bounds.py, ShapeSense/studio/README.md, git commit 79f9c2d, ShapeSense_Deployed/web/live.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T63 (maintenance, stage `deployment (not a course stage)`): chore(studio): keep the saved drawings as informal feedback. Propose or assist with the exact implementation, checks, and configuration needed for commit `79f9c2d`.

## Response
Commit the 86 saved files currently sitting in `studio/feedback/` (43 timestamped `.json` + `.png` pairs captured from the Studio **Draw and predict** page) as a clean maintenance record under `studio/feedback/`, while preserving strict isolation from the modeling and evaluation pipeline:

1. **Keep the artifacts scoped solely to `studio/feedback/`:**
   - Commit the 43 pairs from `20261109-175926-52b66b11.{json,png}` through `20261109-193217-cfd80b38.{json,png}` produced by `studio/ops/feedback.py:save()` via `POST /api/feedback` (`studio/server/routes_infer.py`).
   - Each JSON payload already embeds `"note": "Informal feedback for a future CRISP-DM iteration; not test data."` alongside `"saved_at"`, `"strokes"` (canvas polyline coordinates), and `"results"` (per-arm top-3 predictions from `A0`, `A1`, `B`, `A2`), paired with the 64x64 grayscale PNG.

2. **Enforce pipeline boundary & non-contamination rules:**
   - Do **not** register `studio/feedback/` in `configs/pipeline.yaml`, `data_set/unified/catalog.sqlite`, `configs/splits/`, or `studio/allowlist.py`.
   - Confirm `.commit_guard/safe_commit.py` allows `studio/feedback/*.json` and `studio/feedback/*.png` without triggering size/ignore warnings, and confirm no Stage 1-5 code reads from `studio/feedback/`.
   - Keep `studio/ops/feedback.py` and `FeedbackRequest` in `studio/server/schemas.py` unchanged so filenames remain server-generated (`%Y%m%d-%H%M%S-<uuid8>`) and extra/malformed fields continue returning HTTP 422.

3. **Explicitly label status in commit message and docs:**
   - State clearly in the commit message that these 86 files are informal evidence only and are not training, tuning, or test data (consistent with `docs/crisp_dm/iteration_log.json` noting that the formal 60-drawing live check remains separate).

## Validation
- `40253714` verified the exact file count in `studio/feedback/` (86 files: 43 `.png` and 43 `.json` pairs) and inspected sample JSON headers (`"note": "Informal feedback for a future CRISP-DM iteration; not test data."`) and per-arm probability outputs.
- Verified that `configs/splits/`, `data_set/unified/`, and `artifacts/test_access.log` had zero modifications and that `tests/studio/test_api_bounds.py` (`test_feedback_saves_only_under_the_feedback_folder`, `test_feedback_rejects_bad_drawings_and_extra_fields`) and `tests/studio/test_no_test_split_read.py` cover the feedback endpoint contract.

## Our decision
- Adopted Gemini 4 Neon's proposal verbatim in commit `79f9c2d`, committing all 86 files solely under `studio/feedback/` with zero changes to pipeline configs, splits, or Studio inference code.

## Measured effect
- Commit `79f9c2d` added 86 files (`30,372 insertions(+)`) - 43 PNG drawings (~2.6-3.7 KB each) and 43 matching JSON stroke/prediction records - preserving empirical user-sketch evidence from the live Studio page without contaminating `configs/splits/` or any sealed evaluation set.

---

## Upgraded & Expanded Technical Analysis (`T63`)

### 1. Server-Generated File Contract & Dual-Representation Pairing
In `studio/ops/feedback.py::save()`, every user submission via `POST /api/feedback` writes an immutable, append-only pair of files under `studio/feedback/`:
- **Path-Traversal & Collision Immunity:** The filename stem `%Y%m%d-%H%M%S-<uuid8>` is minted entirely server-side (never accepting a client filename), combining lexicographic chronological sorting with a $2^{32} \approx 4.3 \times 10^9$ per-second collision space.
- **Why 86 Files for 43 Captures (`.png` + `.json` Pair):** Each capture stores both the raw rasterized drawing (`<stem>.png`, ground-truth pixel input) and the structured semantic record (`<stem>.json`: `{note, saved_at, strokes: [{x, y}, ...], results: {A0: {top3}, ...}}`). The literal constant `"note": "Informal feedback for a future CRISP-DM iteration; not test data."` acts as a machine-checkable provenance marker on every JSON file.

### 2. Four-Layer Non-Contamination Proof
To prove that `studio/feedback/` cannot leak into training, tuning, or sealed evaluation:
1. **Static Call-Graph Disjointness:** Grepping `src/stage0_infra` through `src/stage6_report` for `studio/feedback` returns zero references, and `.importlinter` (`studio-boundaries`) forbids any stage from importing `studio`.
2. **Config & Catalog Disjointness:** `configs/pipeline.yaml`, `configs/splits/*.csv`, `studio/allowlist.py`, and `data_set/unified/catalog.sqlite` contain zero references to `studio/feedback/`.
3. **Sealed Access-Log Invariance:** `artifacts/test_access.log` is untouched by `POST /api/feedback` and commit `79f9c2d` (`tests/studio/test_no_test_split_read.py`).
4. **Schema & Directory Boundary Guards (`tests/studio/test_api_bounds.py`):** `test_feedback_saves_only_under_the_feedback_folder` and `test_feedback_rejects_bad_drawings_and_extra_fields` enforce that malformed payloads or extra fields fail with HTTP `422` and writes never escape `studio/feedback/`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the omissions are the decision. `studio/feedback/` is not added to `pipeline.yaml`, the catalog, `configs/splits/`, or `allowlist.py`. Each omission keeps the drawings out of any system that could mistake them for data. The JSON `note` field describes the file to anyone who finds it later.

**Changelog:** [1] deliberate omissions; [2] self-describing `note` field; [3] no pair-completeness check for `.json`/`.png` pairs.

**Open questions:** Does `test_api_bounds.py` prove inference never reads `studio/feedback/`, or only assert it? Is the "informal" label repeated in `studio/README.md`?
