# Agent plan: Phase 1 LaTeX report (unified 2D shape classifier)

> This is a plan for an LLM agent. **Do not execute it yet.** It records the resolved decisions, the agent rules, the report structure and the acceptance checks. It is written so that an agent can produce the report after approval. Dataset names are from general knowledge and must be verified by the agent before they are cited.

## 0. Conflicts to resolve before writing

The repo already has results that differ from the plan. The agent must not silently pick one. Flag each item in the report's "Open Items for Approval" section.

| Plan says | Repo says | Where | Action |
|---|---|---|---|
| Synthetic share of the training set: 30-50% | Configured share for arm B is 0.168 and for arm A2 is 0.12 (`configs/pipeline.yaml`). The realized batch shares are 27.8% and 19.8% (`results/` change log, C11) | `configs/pipeline.yaml`, `docs/crisp_dm/iteration_log.json` | Flag. Report the repo's values as the current design. Ask whether to keep them or move to 30-50%. |
| Two test sets: real-only and real plus synthetic | The repo evaluates on real test data only. Synthetic data is in training only. | `configs/splits/test.csv`, `results/README.md` | Flag. The user said "both", so the report describes both, but it must state that the repo currently uses real-only. |
| Reject class `other` (11th class) recommended | The taxonomy has 10 classes and no reject class (`configs/taxonomy.yaml`) | `configs/taxonomy.yaml` | Keep as a recommendation for approval. Do not change the taxonomy. |
| Every statistic is `\TBD{}` | The repo has real counts: 12,405 train, 2,819 validation, 2,776 test; 500 Quick, Draw! diamonds removed by rule | `configs/splits/`, `docs/crisp_dm/iteration_log.json` | Use the repo's real numbers where they exist, and cite the file. Use `\TBD{}` only for numbers the repo does not record, such as dataset file counts and total MB. |
| Dataset list is "to be verified" | `data/README.md` and `docs/source.md` already list four sources with links and licenses | `data/README.md`, `docs/source.md` | Start from those. Verify each license again before citing. |

## 1. Resolved decisions

| Item | Decision |
|---|---|
| Deliverable | One LaTeX report that compiles to PDF. Phase 1 is report only. No code, no generated data, no experiments. Wait for approval afterwards. |
| Style | KISS. Short sections, tables over prose, no page padding. |
| Classes | 10: circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond. |
| Task | Multi-class image classification. Not regression, because the target is a discrete class. |
| Domains | Render (clean digital), sketch (hand-drawn), synthetic. Photographs are excluded. "Photo" here only means an image of a shape. |
| Datasets | Public datasets only. Verify each license. Do not assume any dataset is already downloaded. |
| Synthetic data | A stroke and brush renderer, built both on the CPU and as a GPU shader. Do not name libraries. Write "to be decided during implementation". |
| Test sets | Two: real-only, and real plus synthetic. Report them separately (see conflict above). |
| Image format | 64x64 grayscale as the baseline. 128x128 optional. Chosen because it is the cheapest size that still shows corners. Confirm as "optimal" with the approver. |
| Synthetic share | Moderate. Plan says 30-50% of training. Repo says otherwise (see section 0). |
| Reject class | Recommend an 11th class "other" for non-shapes and ambiguous images. Optional, flagged for approval. |
| Compute | No hard budget. Keep volumes modest. |
| Page limit | None set. Target 6-8 pages, plain article class. |

## 2. Agent rules

1. Write only LaTeX. Do not run experiments. Do not train, generate or download data.
2. Do not name any software library or framework anywhere, including section E. Describe tools by role: "image-processing toolkit", "tabular data toolkit", "deep-learning framework", "shader pipeline".
3. Every unknown number is a clearly marked placeholder, such as `\TBD{}`. Never invent statistics. Where the repo records a number, use it and cite the file.
4. Write all planned work in the future tense ("will be"). The report has no executed results except those already recorded in the repo, which must be marked as recorded results.
5. Confirm each dataset's name, license and size by search before citing it. Cite sources in a bibliography.
6. Keep the report to about 6-8 pages, plain article class, no custom packages beyond what the standard install provides.
7. Stop after delivering the report. Do not start Phase 2.
8. Use plain hyphens. No en or em dashes, in the text or in code comments.

## 3. Report structure

### Title block
Project name, author (Silent), date, phase (Phase 1).

### A. Topic and task
- One paragraph: a single model that recognises 10 shape classes across clean renders, sketches and synthetic stylised images.
- The prediction task: given an image, predict the shape class.
- Classification, and why it is not regression.
- Small table: input (one grayscale image), output (one of 10 classes), metrics (accuracy, macro-F1, per-domain F1), split policy (hold out whole sources, not augmented copies).

### B. Dataset summary
- **ERD (TikZ).** Entities: Source, Image, Label, LabelMapping, AugmentationRecord (self-link to the parent image). Show cardinalities.
- **Planned sources table:** name, domain, license, link, format. Start from `data/README.md` and `docs/source.md`.
- **Statistics table:** number of files, number of tables, number of columns, size in MB, number of classes, per source. Use repo counts where they exist. Use `\TBD{}` elsewhere, with a note that a script will fill them later.

### C. Data integration
- Numbered process: inventory, convert strokes to rasters, map labels, unify size and mode, deduplicate, build master metadata.
- Examples: a label-mapping table (for example "oval" to ellipse, "rhombus" to diamond), plus one conflict case. Use the repo's real case: the Quick, Draw! diamonds, which were excluded by rule (`docs/crisp_dm/iteration_log.json`, change 1).
- Functional dependencies, expected: source_id to domain; source_id to license; image_id to path; (source_id, original_label) to label_id; label_id to label_name. State that mining will verify them and report any violations.

### D. Data preparation
- **Nulls.** Planned audit. Rules: drop unlabelled rows, infer missing size, set license to "unknown" where missing. Two before and after rows, marked as illustrative.
- **Outliers.** Planned features: aspect ratio, foreground ratio, brightness, file size. IQR rule. Example types: blank image, wrong label, tiny image.
- **Transformations.** Resize with padding, grayscale, normalise, label encoding, and augmentation (rotation, scale, noise, blur, warp). Use the repo's real augmentation settings where they exist (`configs/pipeline.yaml`, `docs/crisp_dm/iteration_3/`).
- **Synthetic generation.** Table of stroke styles (pen, marker, pencil, brush, chalk) with the effect each has. State that it will be built both on the CPU and as a shader. State the label-preserving rule: a pentagon keeps five visible corners.

### E. Tools and systems
Role-only table: data handling, image processing, stroke and shader rendering, deduplication, outlier analysis, modelling, experiment tracking, versioning, document typesetting. Add the note "specific tools to be chosen during implementation."

### Closing: Open items for approval
- Reject class "other": yes or no.
- Image size: 64x64 or 128x128.
- Synthetic share: keep the repo's values, or move to 30-50%.
- Test sets: keep real-only as the repo does, or add the real-plus-synthetic test set.

## 4. Acceptance checklist

- [ ] Sections A to E are all present and match the assignment wording.
- [ ] The ERD and at least two tables are included, along with the integration examples.
- [ ] No library or framework names appear anywhere.
- [ ] No photographs are described as a data source.
- [ ] No invented numbers. Every unknown is a placeholder, and every known number has a source.
- [ ] Every conflict in section 0 appears in "Open items for approval".
- [ ] The document compiles cleanly to PDF and stays within about 8 pages.
- [ ] Plain hyphens only.
- [ ] The agent stops after delivering the report and waits for approval.
