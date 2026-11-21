# 0_data_discovery - Grading Gemini's draft toolset for data visualization
- LLM: Claude Opus 5.5 (`claude-opus-5-5`)
- Category: Two-LLM comparison. Claude Opus 5.5 judges Gemini 4 Neon's answer in [../gemini_4_neon/10_evidence_visualization-tools-draft.md](../gemini_4_neon/10_evidence_visualization-tools-draft.md)
- Date: 2026-11-21

## Prompt

The grading request, as given to this session: judge the Gemini 4 Neon answer in the file above, grade it, and save the result in the matching Claude Opus folder.

The exchange being judged: the task was the user's todo entry "add tools for data visualisation to check the data sets". Gemini answered with Plan 05, a design for a visualization suite: a Streamlit dashboard, a report figure generator, a statistical profiler and a t-SNE / UMAP embedding explorer, plus a new tools table for Section E of `phase1_report.tex`.

The Gemini file is an evidence file, rebuilt from the saved work, not a chat export. Its prompt is the verbatim todo entry, but the exact chat message was not saved. Its response quotes the saved plan file verbatim. I grade the plan as recorded. The status line at its top ("SUPERSEDED by 09") was added later by the team and is not part of the answer.

## Response

### Grade: C (63 / 100)

| Criterion | Score | Reason |
|---|---|---|
| Core explanation is correct | 19 / 25 | The three jobs it gives visualization are right: check that preprocessing does not damage shapes, check class and source balance, and look at the gap between sketches and renders. Before and after grids and per-class counts are the right first tools. |
| Read the question correctly | 12 / 20 | The todo asked for tools to check the data sets. Gemini answered with a four-part suite, including an interactive dashboard and a manifold explorer, and never asked how much setup the project could carry. Plan 09 (`ignore/plan/09_visualization_tools_grounded.md`) says this plan was proposed "without weighing setup cost against project scope". |
| Fit to this project | 10 / 20 | Several parts do not match the project's sources. It lists Mendeley as the "real scan/photo" column, but `phase1_report.tex` (Table 2) marks El Korchi as a render, and the project has no photo domain. It leaves out the Hand-drawn (GitHub) source, the only source of ellipses. Its QA gallery depends on Mistral Vision and OCR, which `ignore/plan/04_mistral_vision_ocr_sanity_check.md` marks "SKIPPED by decision". |
| Actionable advice | 13 / 20 | It names script paths and gives four action items. But it has no order of priority and no cheap first step: the dashboard and the embedding explorer sit beside the figure grid as equals. There is no code and no check for when a figure counts as passing. |
| Accuracy of details | 9 / 15 | Some details hold: the 64 x 64 input matches `image_size: 64` in `configs/pipeline.yaml`, and the train / validation / test split matches its `ratios: [0.70, 0.15, 0.15]`. Others do not. The diagram calls Tool 3 a "Statistical Property Profiler", but section 3.3 makes Tool 3 the manifold explorer, and the profiler never gets a spec. The 10 x 4 grid would have empty cells: `configs/taxonomy.yaml` says pentagon has a single source, and `docs/source.md` lists Quick, Draw! with 7 classes and no ellipse, rectangle or pentagon. |

### What it got right
- Visual checks of the pipeline come first. A before and after grid catches resize, grayscale and padding bugs that no summary number shows. The project built exactly this (`figures/standardization_before_after.png`).
- A class by source count chart is the right way to see balance across merged sources. The project built it too (`figures/unified_class_source_counts.png`).
- It asks whether sketches and renders mix in feature space. That is the right question for a dataset that merges both, even if it was too early to answer it.

### What it got wrong or missed
- **Scope:** a dashboard, Gradio, DVC, pandera and Shapely were all added to the report's tools table. None of them is in the final Section E table of `phase1_report.tex`, which lists Matplotlib as the only visualization and QA tool.
- **Sources:** it describes four domains (render, sketch, synthetic, photo) that are not the project's. The four real sources in `docs/source.md` are two sketch sets and two render sets. Synthetic images are made during training and are not stored, so they are not a fifth source to browse.
- **Dropped decisions:** the QA gallery and the Section E table bring back Mistral Vision and Tesseract OCR, which the project ruled out in plan 04. I could not check from the saved files whether that decision was made before or after this draft. Both carry the same date, 2026-10-19.
- **Missing checks:** it never mentions near-duplicate checks or leakage between splits. The project splits by perceptual hash groups (`group_by: phash` in `configs/pipeline.yaml`), and plan 09 added a dedup safety net for this reason.
- **No guidance on t-SNE use:** it gives no settings or warnings. Plan 09 notes that the scikit-learn docs advise reducing with PCA first and trying several perplexity and seed values.

### What I would have answered for this project
1. Start with what costs nothing new: Matplotlib, which training already needs.
   - A before and after grid per source and class, to check standardization.
   - A count chart of class by source, to check balance and gaps.
   - A width and height scatter and a pixel intensity histogram per source, to check that the merged sources agree.
   - A gallery of the images the cleaning step flags as outliers.
2. Put these in one script that writes PNGs into `figures/`, so the report can use them directly.
3. Leave the dashboard and embedding plots until the dataset is final. Sources were still being corrected at that point.
4. Keep the Section E table to tools that are actually used, and mark planned ones as planned.

This is close to what plan 09 recommended and what was built.

## Validation

- Checked against the Gemini file and `ignore/plan/09_visualization_tools_grounded.md` (the plan that replaced it), `ignore/plan/04_mistral_vision_ocr_sanity_check.md` (OCR and VLM skipped), `configs/pipeline.yaml` (image size 64, split ratios, phash grouping), `configs/taxonomy.yaml` (10 classes, pentagon from one source), `docs/source.md` (the four sources and their classes), `phase1_report.tex` (Table 2 domains, Section E tools table) and the `figures/` folder.
- The Tier 1 script is at `src/stage1_freeze/audit_dataset.py`, not at `scripts/audit_dataset.py` as the status line and `docs/findings.md` say. The figures it makes are listed in `docs/source.md`.
- I did not open the research note that plan 09 cites, so the tool documentation claims in plan 09 were not checked here.
- The grade is my judgment against the criteria in the table. No second grader checked it.

## Our decision

Keep Gemini's answer as the record of the exchange, with this grade beside it. No change to the pipeline or report follows from this grading. Plan 09 had already replaced Plan 05, and only Tier 1 was built.

## Measured effect

None. No change was made.
