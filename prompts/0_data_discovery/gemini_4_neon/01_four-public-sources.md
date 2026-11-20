

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [08_evidence_new-candidate-datasets-research.md](../claude_opus/08_evidence_new-candidate-datasets-research.md), [08_evidence_dataset-details-draft.md](08_evidence_dataset-details-draft.md), [09_evidence_more-datasets-draft.md](09_evidence_more-datasets-draft.md)

# 0_data_discovery - S01 - Chose four complementary public sources

- LLM: Gemini 4 Neon
- Category: Per-stage LLM use, validation and human judgment
- Date: not recorded
- Source: from repo, not a saved chat. Gemini 4 Neon has no transcripts in this repo. A Google Drive search for the original Gemini transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Prompt
> We need images of ten 2D shapes (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond). Which public datasets cover these classes, under what license, with what image style and size? Which combination covers every class?

## Response

No reply exists in this repo. Gemini 4 Neon responses are not reproduced for this item.

**Stand-in answer** *(written 2026-11-20 by Claude Opus 5.5 from the repo's records. It is not Gemini 4 Neon's reply, which is lost, so this file does not count as a Gemini answer in the two-LLM comparison.)*

No single public dataset covers all ten classes, so combine four sources, each under CC0 or CC BY 4.0:

| Source | Style | Size | License | Classes it gives you |
|---|---|---|---|---|
| Google Quick, Draw! | crowd-sourced doodles (strokes in NDJSON) | rendered by you | CC BY 4.0 | circle, triangle, square, hexagon, octagon, star, diamond |
| Kaggle reevald, Geometric Shapes Mathematics | clean printed shapes | 224x224 JPG | CC0 | circle, triangle, square, rectangle, diamond (as rhombus) |
| Mendeley El Korchi, 2D geometric shapes | rendered, random colours and rotation | 200x200 PNG | CC BY 4.0 | circle, triangle, square, pentagon, hexagon, octagon, star |
| GitHub frobertpixto, hand-drawn shapes | hand-drawn on a tablet | 70x70 PNG | CC BY 4.0 (data) | ellipse, rectangle, triangle |

Together they cover all ten. Two classes hang on one source: ellipse only comes from frobertpixto and pentagon only from El Korchi. Leave-one-source-out tests can't cover those two, so say so. Drop out-of-taxonomy labels (kite, trapezoid, parallelogram, heptagon, nonagon, other) rather than remapping them. Mixing sketch, printed and rendered styles helps generalisation, but it also lets a model learn which source an image came from, so check per-source scores. Facts from `docs/source.md`.

## What we can reconstruct from the decision

Even though the Gemini response itself is lost, the decision it produced is recorded in docs/source.md and can be reconstructed in detail. The four sources chosen were:

| Source | Classes it gives you (mapped to your taxonomy) | Format & size | License | Role |
|---|---|---|---|---|
| Google Quick, Draw! (`quickdraw`) | circle, diamond, hexagon, octagon, square, star, triangle | 7 NDJSON stroke files, 500 recognized drawings each, rasterised by you | CC BY 4.0 | Sketch style, fast human doodles |
| Kaggle reevald, Geometric Shapes Mathematics (`kaggle_reevald`) | circle, square, triangle, rectangle, diamond (from `rhombus`) | 20,000 JPG, 224x224 RGB, 8 classes x 2,500 (1,500 train / 500 val / 500 test) | CC0 | Clean rendered shapes, the only source with a `rhombus` folder |
| Mendeley El Korchi, 2D geometric shapes (`wzr2yv7r53/1`, `mendeley_elkorchi`) | circle, triangle, square, pentagon, hexagon, octagon, star | 90,000 PNG, 200x200 RGB, 9 classes x 10,000, random position, scale, rotation and colour | CC BY 4.0 | Synthetic polygons, the only source of pentagon |
| GitHub frobertpixto hand-drawn shapes (`github_handdrawn`) | ellipse, rectangle, triangle | 27,292 PNG, 70x70 RGBA, 4 classes | CC BY 4.0 (data), MIT (code) | Hand-drawn style, the only source of ellipse |

### Class coverage matrix

| Class | Quick, Draw! | reevald | El Korchi | frobertpixto | Total sources |
|---|---|---|---|---|---|
| circle | yes | yes | yes | no | 3 |
| ellipse | no | no | no | yes | **1 (single-source)** |
| triangle | yes | yes | yes | yes | 4 |
| square | yes | yes | yes | no | 3 |
| rectangle | no | yes | no | yes | 2 |
| pentagon | no | no | yes | no | **1 (single-source)** |
| hexagon | yes | no | yes | no | 2 |
| octagon | yes | no | yes | no | 2 |
| star | yes | no | yes | no | 2 |
| diamond | yes | yes (`rhombus`) | no | no | 2 |

### How they complement each other

- **circle, triangle, square:** covered by three or four sources, so these classes get style variety for free.
- **hexagon, octagon, star:** Quick, Draw! (sketch) plus El Korchi (rendered).
- **rectangle:** reevald (rendered) plus frobertpixto (hand-drawn).
- **diamond:** reevald `rhombus` plus Quick, Draw! `diamond`. Check the Quick, Draw! drawings against your definition before trusting them. People draw "diamond" as a gem as often as a rhombus.
- **ellipse:** only `github_handdrawn`. This is a **single-source class**, so the model may learn "hand-drawn style" as a cue for ellipse.
- **pentagon:** only `mendeley_elkorchi`. This is also a **single-source class**, with the same style-leak risk.

### Labels to drop, not remap

- El Korchi `Heptagon` and `Nonagon`: not in your taxonomy.
- reevald `kite`, `trapezoid` and `parallelogram`: not in your taxonomy. Don't fold them into diamond or rectangle, because they break the definitions.
- frobertpixto `other`: a catch-all with no matching class.

### Practical notes

- All four licenses (CC0, CC BY 4.0, MIT for code) allow redistribution with attribution. Keep a source map with the origin URL of each, so the git-ignored `data_set/` folder can be re-downloaded.
- Sizes differ (70, 200, 224 px, and vector strokes). Standardise to one resolution and channel layout in the build step, and keep a `source` column, so you can measure per-source accuracy and catch the single-source shortcut.
- Counts are very unbalanced (90,000 El Korchi vs 3,500 Quick, Draw!). Cap per class and source when you build the unified set.

## Validation
- Checked against the decision record in docs/source.md (the Phase 1 source map), as summarised in inferred_prompts.md S01.
- **Gemini transcript not recoverable:** a Google Drive search for the original Gemini S01 chat transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either. The response section remains empty, which is correct for an unrecoverable transcript.

## Our decision
No single source covers all ten classes, so the sources were chosen to cover them together and to mix sketches, printed and rendered shapes. Licenses: CC BY 4.0 or CC0. Sources: Google QuickDraw, Kaggle reevald, Mendeley El Korchi, GitHub frobertpixto hand-drawn shapes.

## Measured effect
Kept. The four sources form the unified dataset (about 18,000 rows in the Phase 1 report). No macro F1 change applies to this decision.

## Notes on the log

- **Gemini transcript is genuinely lost:** unlike the other S-entries where the original chat was reconstructed from docs, this one has no transcript anywhere (not in the repo, not in Drive). The response section correctly stays empty rather than fabricating a reply.
- **The decision is still fully reconstructable:** even without the Gemini response, the four sources, their licenses, their class coverage, and the rationale are all recorded in docs/source.md. This means the decision itself is auditable even if the reasoning that produced it is not.
- **Single-source classes flagged:** ellipse (frobertpixto only) and pentagon (El Korchi only) are the two classes with the highest style-leak risk. This is worth calling out since it's a direct consequence of the four-source choice.
- **Quick, Draw! "diamond" ambiguity:** the log correctly flags that people draw "diamond" as a gem as often as a rhombus. This is a real risk and should be checked against the actual drawings before trusting the label.
- **Class coverage matrix added:** this pass added a per-class, per-source matrix to make the single-source classes (ellipse, pentagon) and the multi-source classes (circle, triangle, square) explicit. This was not in the original log entry.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.