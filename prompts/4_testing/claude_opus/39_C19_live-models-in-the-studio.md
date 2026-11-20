# 4_testing - C19: Live models in the studio ()

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [55_real_dashboard-with-onnx-inference.md](55_real_dashboard-with-onnx-inference.md)

- LLM: Opus 5.5 (`opus_medium_5.5`)
- Category: Two-LLM comparison. Gemini 4 Neon answer to the same prompt: [../gemini_4_neon/40_C19_live-models-in-the-studio.md](../gemini_4_neon/40_C19_live-models-in-the-studio.md)
- Date: 2026-11-09
- Worksheet entry: C19 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / opus_medium_5.5
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `studio/tools/export_arms.py`, `studio/inference/arms.py`, `studio/settings.py`, `studio/web/js/widgets/predict-panel.js`, `docs/crisp_dm/iteration_log.json`, commit `22faa35`, `ShapeSense_Deployed/web/live.html`, `ShapeSense_Deployed/web/stage6.html`, `ShapeSense_Deployed/web/changes.html`

> **This is a reconstruction, not the original exchange.** It was written afterwards grounded in the repository records (`ShapeSense` and `ShapeSense_Deployed`). It is not evidence that Opus 5.5 said these exact words.

## Prompt ()

> **User:** Right now the studio loads `A0` from the Stage 6 `export/` bundle while `A1` and `B` live in `studio/out/arms/`. How should we unify export and loading so all four arms (`A0`, `A1`, `B`, `A2`) are exported to one folder and compared cleanly on the same drawing?

## Response ()

> **Opus 5.5:** Export all comparison arms through one uniform path under `studio/out/arms/` and remove the `export/` special case from `studio/inference/arms.py`:
>
> - **Single export target:** In `studio/tools/export_arms.py`, expand `ARMS_TO_EXPORT` to include `"A0"` alongside `"A1"`, `"B"`, and `"A2"` (and later `"P"`). Write every arm's best-validation model to `studio/out/arms/<arm>/model.onnx` and record `run`, `val_macro_f1`, and `sha256` in `studio/out/arms/manifest.json`.
> - **Uniform inference loader:** In `studio/inference/arms.py`, drop the `if arm == "A0": return REPO_ROOT / "export" / "model.onnx"` branch and the `export/model_card.json` provenance merge so `model_path(arm)` and `provenance()` read solely from `ARMS_DIR` and `ARMS_MANIFEST`.
> - **Clean Stage 6 separation:** Leave `export/` as the standalone single-model shipped bundle (`A2_2` in Iteration 2, `A2_0` in Iteration 3) while `studio/out/arms/` serves side-by-side multi-arm comparison.
>
> | Option | Effect | Recommendation |
> |---|---|---|
> | Keep `A0` pointing at `export/model.onnx` | `A0` breaks or silently compares the shipped `A2` bundle once `export/` switches winner | Skip |
> | Export all arms uniformly to `studio/out/arms/` with one `manifest.json` | Guarantees every arm comes from the same run selection rule and stage | **Do this** |
>
> This also maps 1-to-1 onto the static site (`ShapeSense_Deployed`), where `web/models/manifest.json` lists every arm's `.onnx` file under one `models/` folder for ONNX Runtime Web.

## Why this reading fits

Commit `22faa35` updates `studio/tools/export_arms.py` (`ARMS_TO_EXPORT = ("A0", "A1", "B", "A2")`) and simplifies `studio/inference/arms.py` by removing the `REPO_ROOT / "export"` fallback, matching `iteration_log.json` (`C19`). When arm `P` was added in `4091dab`, extending `ARMS_TO_EXPORT` by one entry and freezing `web/models/` in `ShapeSense_Deployed` worked without structural changes.

## Validation

- Ran `python -m studio.tools.export_arms`, verifying `studio/out/arms/<arm>/model.onnx` and `studio/out/arms/manifest.json` are generated uniformly for all active arms using validation scores only.
- Verified `ShapeSense_Deployed` parity via `build/check.py` (browser ONNX Runtime Web logits within `1e-4` of Python across all exported arms on `live.html`).

## Our decision

Removed the `export/` special case from `studio/inference/arms.py`, exported all arms (`A0`, `A1`, `B`, `A2`, and later `P`) uniformly to `studio/out/arms/` with a single `manifest.json`, and carried the same unified `models/` layout into `ShapeSense_Deployed`.

## Measured effect

Every live model on `live.html` loads from one uniform directory and manifest (`A0`, `A1`, `B`, `A2` in Iteration 2; all 5 arms `A0`, `A1`, `B`, `A2`, `P` in Iteration 3), preventing `export/` bundle updates (`A2_2` / `A2_0`) from colliding with `A0` during live drawing comparisons.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C19`)

### The latent bug (not just ugliness)

`A0` previously loaded from `export/model.onnx`, which is the **shipped single-model bundle** — in Iteration 2 that was `A2_2`, in Iteration 3 `A2_0`. Once `export/` switched winner, `A0` would silently load the *`A2`* model and label it `A0`. The comparison "`A0` vs `A2`" would compare `A2` against itself — a **silent mislabeling** that would corrupt every live comparison.

### The uniform-export invariant

**Invariant:** every arm's `model_path(arm)` is a pure function of `ARMS_DIR` and `ARMS_MANIFEST`, with no per-arm special cases ($\text{model\_path}: \text{Arm} \rightarrow \text{Path}$ is total and case-free). `manifest.json` records `{run, val_macro_f1, sha256}` per arm, so provenance is uniform and the selected run is auditable.

### Role-based directory separation & scaling proof

`export/` is the *shipped single model* (what a downstream consumer downloads); `studio/out/arms/` is the *comparison set* (what the studio loads). Separating them by role meant that adding `P` in `4091dab` required extending `ARMS_TO_EXPORT` by one entry and freezing `web/models/` — **zero structural changes**.

