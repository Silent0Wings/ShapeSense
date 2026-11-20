# 4_testing - T13: assets icon and banners
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T13 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40248536 + 40253714 / gemini_4_neon + 40248536 + 40253714
- Calibration: `winning-decision (70% tier)`
- Grounding sources: assets/banners/.gitkeep, assets/banners/banner4x3.jpg, assets/icons/.gitkeep, README.md, .gitignore, ShapeSense_Deployed/README.md, ShapeSense_Deployed/web/index.html, ShapeSense_Deployed/web/stage6.html, ShapeSense_Deployed/web/live.html, ShapeSense_Deployed/web/failures.html, ShapeSense_Deployed/web/changes.html, git commit 240ef2f

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T13 (other, stage `deployment (not a course stage)`): assets icon and banners. Propose or assist with the exact implementation, checks, and configuration needed for commit `240ef2f`.

## Response
Add a dedicated top-level `assets/` tree for repository visual media, keeping it cleanly separated from `data_set/`, `artifacts/`, and the future static deployment bundle:

1. **Directory layout and Git tracking**
   - Create `assets/banners/` and `assets/icons/` with empty `.gitkeep` sentinel files (`assets/banners/.gitkeep` and `assets/icons/.gitkeep`) so both asset directories remain tracked in Git even while `assets/icons/` awaits final icon assets.
   - Commit the repository banner image at `assets/banners/banner4x3.jpg` (`2,160,510` bytes, 4:3 aspect ratio).
   - Confirm `.gitignore` does not ignore `assets/` (unlike `data_set/`, `artifacts/*`, `export/model.onnx`, and `ignore/`), and keep `assets/` outside `.importlinter` `root_packages` (`src`, `dashboard`, `demo`, `export`, `studio`) so non-code media never triggers Python import-contract scans.

2. **README integration and web-favicon separation**
   - Point the top header of `README.md` to `assets/banners/banner4x3.jpg` via `<p align="center"><img src="assets/banners/banner4x3.jpg" alt="ShapeSense pipeline banner: hand-drawn shapes passing through a neural network" width="640"></p>`.
   - Keep runtime UI favicons separate from repo-level documentation assets: the Studio / frozen static site pages (`ShapeSense_Deployed/web/index.html`, `stage6.html`, `live.html`, `failures.html`, `changes.html`) link their own `<link rel="icon" type="image/png" href="icon.png">` inside `web/` so the static site bundle (`site/dist/`) stays self-contained under Vercel's size budget without bundling the 2.16 MB README banner.

3. **Pipeline cache safety**
   - Verify no stage `inputs(config)` function hashes `assets/`, ensuring adding or updating banners/icons never invalidates cached `artifacts/stageN/status.json` runs.

## Validation
- Inspected `git show --stat 240ef2f` and filesystem entries under `assets/` to confirm exact paths and byte sizes (`assets/banners/.gitkeep` 0 B, `assets/banners/banner4x3.jpg` 2,160,510 B, `assets/icons/.gitkeep` 0 B).
- Verified `README.md` lines 1-3 reference `assets/banners/banner4x3.jpg` with a valid relative path and descriptive `alt` attribute.
- Ran `python run_pipeline.py --check` (`lint-imports` + `pytest tests/contracts`) to verify `.importlinter` boundaries and contract tests pass with `assets/` committed.

## Our decision
The team committed Gemini 4 Neon's exact `assets/` directory layout, `.gitkeep` placeholders, and `banner4x3.jpg` placement in commit `240ef2f`, keeping `assets/banners/banner4x3.jpg` as the repository `README.md` header while serving lightweight `icon.png` directly inside `web/` for the Studio and deployed static site (`https://shapesense-ten.vercel.app`).

## Measured effect
- **Commit `240ef2f`:** 3 files committed (`assets/banners/.gitkeep`, `assets/banners/banner4x3.jpg` at 2,160,510 bytes, `assets/icons/.gitkeep`; 0 code-line insertions/deletions).
- **Hygiene & build impact:** Zero impact on `.importlinter` contracts, zero invalidation of stage `status.json` input hashes, and zero bloat added to the self-contained `ShapeSense_Deployed` static bundle.

---

## Upgraded & Expanded Technical Analysis (`T13`)

### 1. Three-Way Namespace Isolation (Cache Safety, Import Linting, and Bundle Budget)
Placing repository documentation media under a top-level `assets/` directory enforces three orthogonal engineering invariants:
1. **Stage Cache Invariance (`inputs(config)` Disjointness):** None of Stage 0–6 `inputs(config)` functions include `assets/` in their `CODE_DIRS` or manifest digests. Editing or replacing `assets/banners/banner4x3.jpg` never invalidates `artifacts/stageN/status.json`, avoiding redundant multi-hour training or evaluation reruns after documentation polish.
2. **Documentation Asset vs. Runtime Deployment Budget Split:** `assets/banners/banner4x3.jpg` (`2,160,510` bytes) serves the GitHub/repository `README.md`, whereas the deployed Vercel static bundle (`site/dist/`, governed by the $\le 60\text{ MB}$ total / $\le 25\text{ MB}$ per-file budget in `stages/stage_7.md`) ships only the lightweight `web/icon.png` favicon, keeping documentation media out of visitor downloads.
3. **Architecture Linter Isolation (`.importlinter`):** Excluding `assets` from `root_packages` (`src`, `dashboard`, `demo`, `export`, `studio`) guarantees that non-code media directories are never scanned as Python packages by `lint-imports`.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the non-decision matters. `assets/` is not a Python package and is not in `.importlinter` root packages, so committing media never triggers an import scan. The 2.16 MB banner is for the GitHub README renderer, not the Vercel bundle.

**Changelog:** [1] `assets/` outside the import contracts; [2] banner vs favicon as a size and serving decision; [3] no stage input hashes `assets/`.

**Open questions:** Is there a plan for `assets/icons/`, or will the `.gitkeep` stay as a placeholder? Is the 2.16 MB banner the original or a compressed export?
