# Verification

## How the final results were verified

Every item below already exists in the Phase 2 record. Files are in [`../phase2_snapshot/`](../phase2_snapshot/).

| Check | What it guards against | Evidence |
|---|---|---|
| Pre-registered hypotheses, written before any test read | Choosing the test after seeing the results | `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_3/preregistration.md` |
| Sealed test split and sealed fresh holdouts | Tuning on the test data | `split_stats.csv`, `robust_sealed.json` |
| Import-linter and contract tests | Pipeline stages reading data they should not see | `guards.json` |
| 5 training seeds per arm, mean ± std, and seed disagreement | A result that is luck of one seed | `metrics.csv`, `seed_disagreement.json` |
| 95% confidence intervals, McNemar tests, Holm correction | A difference that is noise | `comparisons.csv`, `power.json`, `noise_bands.csv` |
| Classical baselines (logistic regression, SVM on HOG) | A CNN that is not better than a simple model | `baselines.json` |
| Source classifier and shortcut check | The model learning the source instead of the shape | `source_classifier.json`, `shortcut_notice.md`, `per_source.csv` |
| Functional-dependency checks on the metadata (source to license, original label to class) | Inconsistent labels or licenses after integration | `fd_check.json` |
| Manual QA review sheets | Wrong labels and broken synthetic renders | `qa_review2.md`, `qa_review3.md` |
| Failure log (31 entries) and change log (57 entries) | Silent fixes with no record | `iteration_log.json` |
| External audit by a second LLM (27 claims, each given a verdict by the team) | Trusting one LLM | [`../llm_comparison/gemini_audit.md`](../llm_comparison/gemini_audit.md) |
| Browser models checked against Python (logits within 1e-4) | The published demo differing from the trained models | ShapeSense_Deployed `build/check.py` |

## Dataset-awareness check (course requirement: Claude and Gemini runs 2026-11-20)

Prompts: [`prompts/6_verification/dataset_awareness/`](../../prompts/6_verification/dataset_awareness/).

- **Claude Opus 5.5:** one fresh agent session, no tools, all eight prompts in one session. Full replies and scoring: [`claude_opus/01_four-sources.md`](../../prompts/6_verification/dataset_awareness/claude_opus/01_four-sources.md).
- **Gemini 4 Neon** (configured as Gemini 4, medium effort): one new chat per prompt, web search off, file upload off, no workspace access, as stated by the user. Full replies and scoring: [`gemini_4_neon/01_four-sources.md`](../../prompts/6_verification/dataset_awareness/gemini_4_neon/01_four-sources.md).
- Two supplementary Gemini files are not counted: the Antigravity run with workspace access (`00_`) and the sandboxed CLI replication (`02_`).

| Source | Claude: knew it? | Gemini: knew it? | Evidence |
|---|---|---|---|
| Google QuickDraw | Yes: maker, 345 categories, formats, CC BY 4.0, row field order | Yes: maker, 345 categories, formats, CC BY 4.0, row fields; declined the row's values | `docs/source.md`: CC BY 4.0. The project uses a 7-class subset, which neither reply mentions |
| Kaggle reevald Geometric Shapes | Partly: folder layout and all 8 class names right; declined count, size, format, license | Partly: all 8 class names right, 224 x 224 as typical; declined count, format, license, file names | `docs/source.md`: 20,000 JPG 224 x 224, CC0 |
| Mendeley El Korchi 2D Geometric Shapes | Yes: 9 classes, 90,000 images, 200 x 200 PNG, CC BY 4.0, `Circle_<uuid>.png` names | Yes: 9 classes, 90,000 images, 200 x 200 PNG, CC BY 4.0, `<ClassName>_<UUID>.png` names | `docs/source.md`: 90,000 PNG 200 x 200 RGB, CC BY 4.0. Real file names follow the UUID pattern |
| GitHub frobertpixto Hand-Drawn Shapes | Partly: layout, 4 classes and 70 x 70 right; count and license wrong, marked uncertain | Partly: 4 classes and 70 x 70 PNG right; **format wrong (grayscale; record says RGBA)**; declined count, license, file names | `docs/source.md`: 27,292 PNG 70 x 70 RGBA, CC BY 4.0 data / MIT code |

No confident invention was found in either model. Recalling a description or a file-name convention shows text exposure, not that the models saw the benchmark images.
