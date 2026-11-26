# 6_verification/dataset_awareness - Cross-critique: Claude Opus 5.5 vs. Gemini 4 Neon dataset awareness
- LLM: Gemini 4 Neon & Claude Opus 5.5 (cross-model comparison and verification review)
- Category: Two-LLM comparison / Pipeline vs. direct LLM prediction (verification)
- Date: 2026-11-20

> **Corrected 2026-11-26.** This comparison first used `gemini_4_neon/01_four-sources.md`, which turned out to be a
> reformatted copy of Gemini's first run, made with access to the project files. The Gemini column, verdicts and
> takeaways below now use the official clean run, [`02_sandboxed-replication.md`](../gemini_4_neon/02_sandboxed-replication.md).

Compare [Claude Opus 5.5](../claude_opus/01_four-sources.md) and [Gemini 4 Neon](../gemini_4_neon/02_sandboxed-replication.md) on the eight blind dataset-awareness prompts in [PROMPT.md](../PROMPT.md), checked against [`docs/source.md`](../../../../docs/source.md) and the 200-image direct-prediction benchmark ([`01_direct-prediction-error-comparison.md`](../../../5_direct_llm_prediction/cross_critique/01_direct-prediction-error-comparison.md)).

## Prompt

> Compare Claude Opus 5.5 and Gemini 4 Neon on the four-source dataset-awareness check (Prompts 1A–1D and 2A–2D). Check both replies against `docs/source.md` for factual errors, hallucinated details, and abstention calibration, and evaluate whether dataset metadata awareness explains either model's performance on the 200-image direct LLM prediction benchmark.

## Side-by-side comparison across the four sources

| Source & ground truth (`docs/source.md`) | Claude Opus 5.5 ([`01_four-sources.md`](../claude_opus/01_four-sources.md)) | Gemini 4 Neon ([`02_sandboxed-replication.md`](../gemini_4_neon/02_sandboxed-replication.md)) | Cross-critique verdict |
|---|---|---|---|
| **1. Google Quick, Draw!**<br>Google Creative Lab, >50M drawings, 345 categories, 4 formats (`.ndjson` raw & simplified, `.bin`, 28×28 `.npy`), CC BY 4.0. Row keys: `word`, `countrycode`, `timestamp`, `recognized`, `key_id`, `drawing`. | **Knows it.** Named maker, ~50M drawings, 345 categories, all 4 formats, CC BY 4.0, and exact remaining field order (`recognized`, `key_id`, `drawing`). Refused to fabricate row values. | **Knows it.** Named maker, >50M drawings, 345 categories, all 4 formats (including 256×256 simplified box and 28×28 `.npy`), CC BY 4.0, and exact remaining field order. Refused to fabricate row values. | **Tie (both know it completely).** Both recall the public specification and schema without inventing row-specific IDs or strokes. |
| **2. Kaggle reevald Geometric Shapes Mathematics**<br>20,000 JPG 224×224 RGB, 8 classes × 2,500 (1,500 train / 500 val / 500 test; `circle-2000.jpg` onward in `test/circle/`), CC0. | **Partial knowledge, no invention.** Knew `train/val/test` layout and all 8 exact class names (`circle`, `kite`, `parallelogram`, `rectangle`, `rhombus`, `square`, `trapezoid`, `triangle`). Abstained on count, resolution, format, license, and `test/circle/` file names. | **Barely knows it, no invention.** A "faint recollection" of the 8 class names, explicitly marked uncertain. Count, resolution, format, license and `test/circle/` file names unknown. | **Claude ahead.** Claude knew the layout and the 8 classes with confidence; Gemini only faintly recalled the classes. Neither guesses the 20,000 count, CC0 license, or `circle-2000.jpg` numbering. |
| **3. Mendeley El Korchi 2D Geometric Shapes**<br>90,000 PNG 200×200 RGB, 9 classes × 10,000 (`Circle`, `Square`, `Triangle`, `Pentagon`, `Hexagon`, `Heptagon`, `Octagon`, `Nonagon`, `Star`), CC BY 4.0, flat `output/` with `<Class>_<uuid>.png`. | **Knows it.** Named Anas El Korchi & Youssef Ghanou, 9 classes, 10,000/class = 90,000 total, 200×200 colour PNG, CC BY 4.0, and `Circle_<uuid>.png` naming (marked slightly uncertain on 2C). | **Knows it.** 90,000 images (10,000/class across all 9 exact classes), 200×200 colour PNG, CC BY 4.0, flat `output/` folder, and `<ClassName>_<uuid>.png` naming. Gave the creator as "El Korchi (possibly Abdeljalil)", marked uncertain and not checked. | **Tie on facts.** Both models know the dataset down to the UUID filename convention. |
| **4. GitHub frobertpixto Hand-Drawn Shapes**<br>27,292 PNG 70×70 RGBA, 4 classes (`ellipse`, `rectangle`, `triangle`, `other`) across 37 `data/user.*/images/` folders (`user.aly/images/` has 220 files named `ellipse.aly.0001.png` etc.), CC BY 4.0 data / MIT code. | **Partial knowledge (2 hedged errors).** Knew `data/user.<name>/` layout, 4 classes, and 70×70 PNG. Guessed "a few thousand" (off by ~10×) and "possibly MIT" (code license, not data license), both explicitly flagged as uncertain. Abstained on 2D count/pattern. | **Does not know it, no invention.** Knew only that the data is organized per user. Classes, count, size, format, license and the `user.aly/images/` pattern all declined as unknown. | **Claude ahead on recall, Gemini stricter on abstention.** Claude knew the layout, 4 classes and 70×70 but offered two hedged guesses that were wrong; Gemini knew almost nothing and guessed nothing. |

## Does dataset awareness explain the 200-image direct prediction benchmark?

Comparing the dataset-awareness results against the per-source direct-prediction accuracy on the 200 blind test images (`results/direct_llm_prediction/summary.json`):

| Source | Dataset-awareness verdict (both LLMs) | n (test sample) | Trained CNN (`A2_0`) | Claude Opus 5.5 | Gemini 4 Neon | Interpretation |
|---|---|---:|---:|---:|---:|---|
| `quickdraw` | **Knows it** (full metadata & NDJSON schema) | 27 | 88.89% | 77.78% | 77.78% | **Highest text awareness, lowest visual score.** Knowing the NDJSON specification does not help classify 64×64 rasterized doodles. |
| `mendeley_elkorchi` | **Knows it** (90k count, 9 classes, 200×200, UUID filenames) | 88 | 100.00% | 98.86% | 100.00% | High score reflects clean synthetic polygon geometry, not filename/metadata recall (all tiles are standardized to 64×64 grayscale with blind IDs `T001`–`T200`). |
| `kaggle_reevald` | **Partial** (Claude: layout & 8 classes; Gemini: classes only faintly) | 46 | 100.00% | 89.13% | 91.30% | Both VLMs miss the same 4 `circle → ellipse` tiles (`T055`, `T103`, `T142`, `T175`) where axis ratio is near the threshold. |
| `github_handdrawn` | **Claude partial, Gemini unknown** (Claude: layout, 4 classes & 70×70; Gemini: per-user folders only) | 39 | 94.87% | 92.31% | 94.87% | Gemini, which did not know this dataset, matches the trained CNN (37/39); Claude, which partly knew it, is 1 tile behind (36/39). Recall does not predict the score. |

### Key takeaways from the cross-critique

1. **Text/metadata exposure is not visual memorization.** Every tile in the 200-image benchmark (`results/direct_llm_prediction/`) was cropped to its ink bounding box, padded with an 8% margin, binarized/standardized to 64×64 black-on-white grayscale (`src/stage1_freeze/standardize.py`), and renamed `T001.png`–`T200.png`. All original resolutions (70×70, 200×200, 224×224), RGB colours, and filenames (`Circle_<uuid>.png`, `ellipse.aly.0001.png`) were stripped before the LLMs saw the tiles.
2. **Inverse rank on `quickdraw` refutes metadata-driven scoring.** The source both LLMs know most thoroughly from public documentation (`quickdraw`) is the exact source where both VLMs score worst (77.78% vs. 88.89% for the CNN).
3. **Same profile on the well-documented sources, Claude ahead on the others.** Both models fully recall Google Quick, Draw! and Mendeley El Korchi. On Kaggle reevald and GitHub frobertpixto, Claude had partial structural recall (folder layout, class list, 70×70), while Gemini, in a sandbox with no project files, only faintly recalled reevald's classes and did not know frobertpixto. Gemini's first run, made with the project files available, reported those details too, which suggests it read them from the workspace.
4. **Zero confident hallucinations.** Both models followed the prompt rule ("If you do not know it, say so instead of guessing"): neither model fabricated a Quick, Draw! `key_id`, file count, or filename pattern.

## Validation

Checked against [`docs/source.md`](../../../../docs/source.md), [`results/verification/README.md`](../../../../results/verification/README.md), and [`results/direct_llm_prediction/summary.json`](../../../../results/direct_llm_prediction/summary.json).

## Our decision

Keep all four sources (as explicitly permitted by the course specification) and report both models' dataset-awareness findings alongside the per-source benchmark breakdown so readers can distinguish documentation recall from visual classification accuracy.

## Measured effect

None. Verification and cross-model comparison only.
