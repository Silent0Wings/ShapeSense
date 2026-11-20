# 4_testing - C19: Live models in the studio
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/39_C19_live-models-in-the-studio.md](../claude_opus/39_C19_live-models-in-the-studio.md)
- Date: 2026-11-09
- Entry: C19 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md#c19, studio/tools/export_arms.py, studio/inference/arms.py, studio/settings.py, studio/README.md, stages/stage_6.md, stages/stage_7.md, commit 22faa35

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** Right now the studio loads `A0` from the Stage 6 `export/` bundle while `A1` and `B` live in `studio/out/arms/`. How should we unify export and loading so all four arms (`A0`, `A1`, `B`, `A2`) are exported to one folder and compared cleanly on the same drawing?

## Response
The current setup mixes two kinds of model file. The Stage 6 bundle in `export/` is the project's deliverable: one model, chosen once, with `predict.py`, `standardize.py` and `labels.json` (`stages/stage_6.md`). The other arms were loaded from wherever they happened to be saved. A live comparison needs something different: one model per arm, chosen by the same rule, in one place the server owns.

I would add a small exporter and a fixed folder:

| Piece | What it does |
|---|---|
| `studio/tools/export_arms.py` | For each arm, picks its best-validation run with the same `select_model` used by `src/stage6_report/export.py`, and writes it with the same `export_onnx` |
| `studio/out/arms/<arm>/model.onnx` | One ONNX file per arm (`ARMS_DIR` in `studio/settings.py`) |
| `studio/out/arms/manifest.json` | Run name, validation macro-F1 and SHA-256 of each exported file, so the page can say which run it is showing |
| `studio/inference/arms.py` | One ONNX Runtime session per arm, opened lazily from that folder; `available()` lists only arms whose file exists |

Why this design:
- **Same rule for every arm.** Selecting on validation scores only keeps the test split out of the choice, and using the Stage 6 helpers means the studio cannot drift from the deliverable's export path.
- **One folder, one manifest.** The live page then asks for "every available arm" instead of knowing file locations. Adding an arm becomes an entry in the export list, not new loading code.
- **Provenance on screen.** `provenance()` reads the manifest, so each live answer can be traced to a run.

Run it once after Stage 4 (`python -m studio.tools.export_arms`), then start the studio. The Stage 6 bundle stays untouched.

Cautions:
- Anything that limits how many arms a request may name must follow the arm list. A hard-coded count will break the page as soon as one more arm is exported.
- Keep `onnxruntime` imported before `torch` in the exporter, as `src/stage6_report/export.py` does.
- `studio/out/` holds generated files; do not treat it as a source of results.

## Validation
`studio/tools/export_arms.py` prints each arm's chosen run and validation macro-F1 as it writes, and records a SHA-256 per file in the manifest. `studio/README.md` lists the export as a one-time step before `python -m studio`. Later, `stages/stage_7.md` names "The bundle written by `studio/tools/export_arms.py`" as the source of the public site's ONNX models.

## Our decision
Adopted: all arms are exported to `studio/out/arms` so every arm can be compared on the same drawing. The export list in `export_arms.py` now holds five arms (`A0`, `A1`, `B`, `A2`, `P`), matching `ARMS` in `studio/settings.py`. Adding the fourth arm exposed a request limit that had not followed the list; that is failure F15, fixed in the same commit.

## Measured effect
No separate measurement recorded. The change is structural: before -> after is "A0 from the bundle, A1 and B separately" -> "All four arms exported to studio/out/arms" (`iteration_log.json`).

---

## Upgraded & Expanded Technical Analysis (`C19`)

### 1. Separating the Single-Model Deliverable (`export/`) from Multi-Arm Comparison (`studio/out/arms/`)
- **Architectural Boundary:** The Stage 6 `export/` bundle (`stages/stage_6.md`) is the standalone single-model deliverable (`model.onnx`, `predict.py`, `standardize.py`, `labels.json`, `model_card.json`). Loading `A0` from `export/` while loading `A1` and `B` from `studio/out/arms/` coupled the multi-arm diagnostic studio to the single-model deliverable and broke as soon as Stage 6 updated `export/model.onnx` from `A0_0` to `A2_2` / `A2_0` (`C18`).
- **Unified Exporter (`studio/tools/export_arms.py`):** Reuses Stage 6's `select_model` (validation macro-F1 only, filtering out `holdout_source` runs) and `export_onnx` (opset 17, `1e-4` TorchScript parity check, importing `onnxruntime` before `torch` to avoid Windows DLL initialization conflicts) across every arm in `studio.settings.ARMS` (`A0`, `A1`, `B`, `A2`, `P`), writing `studio/out/arms/<arm>/model.onnx` and `studio/out/arms/manifest.json` (`run_name`, `val_macro_f1`, `sha256`).

### 2. Lazy Session Registry & Provenance Chain (`studio/inference/arms.py`)
- **Graceful Availability (`available()`):** Inspects `ARMS_DIR` in `ARMS` order and returns only arms whose `model.onnx` file is present on disk, opening each `ort.InferenceSession` lazily on first request and caching it in memory.
- **End-to-End Provenance (`provenance()`):** Exposes `studio/out/arms/manifest.json` to the Studio UI and later serves as the canonical ONNX source for the public static site (`stages/stage_7.md`), ensuring every live browser prediction traces to an exact Stage 4 `run_name`, validation macro-F1 score, and SHA-256 digest (and directly motivating `F15`'s `max_length=len(ARMS)` schema binding).


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the first paragraph draws the distinction the design depends on. The Stage 6 bundle is the deliverable (one model, chosen once). The comparison set is one model per arm, chosen by the same rule, in a place the server owns. The unification separates these two rather than merging them into one folder.

**Changelog:** [1] deliverable vs comparison set as the design core; [2] the request-limit caution is F15 restated, so the design did not prevent that bug and the process caught it; a design that pointed the limit at `len(ARMS)` from the start would have prevented it; [3] sharing the Stage 6 helpers is the drift-prevention argument.

**Open questions:** Does `manifest.json` record which selection rule and export time were used? Without them a reader cannot tell a current manifest from a stale one. `available()` lists only arms whose file exists, so a missing arm yields a shorter card list. Does the page say which arms are missing? A silently short list has the same failure shape as F29's duplicate `P`.
