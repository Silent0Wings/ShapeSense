# Stage map: course stages, CRISP-DM phases and ShapeSense stages

The course asks for five stages. ShapeSense was built as seven pipeline stages and recorded with CRISP-DM
phases. This table links the three, and points to the evidence for each.

Live pages: <https://shapesense-ten.vercel.app> (the stage pages are `stage0.html` to `stage6.html`).
Worksheet rows: [`llm_comparison/attribution_worksheet.csv`](llm_comparison/attribution_worksheet.csv), column
`course_stage`.

| Course stage | CRISP-DM phase | ShapeSense stage | Repository evidence | Live page | Worksheet rows |
|---|---|---|---|---|---|
| 0. Data discovery (optional) | Business understanding, Data understanding | Phase 1 source search | [`docs/source.md`](../docs/source.md), [`docs/data_sets.md`](../docs/data_sets.md), [`phase1_report.pdf`](../phase1_report.pdf) | `business.html` | 7 decisions (S01 to S07) |
| 1. Data integration | Data understanding, Data preparation | Stage 1 data freeze | [`stages/stage_1.md`](../stages/stage_1.md), `src/stage1_freeze/` | `stage1.html` | 2 failures, 3 changes |
| 2. Data preparation: cleaning | Data preparation | Stage 1 data freeze | [`docs/crisp_dm/iteration_1_quickdraw_diamonds.json`](../docs/crisp_dm/iteration_1_quickdraw_diamonds.json) | `stage1.html`, `iteration1.html` | 1 failure, 1 change |
| 2. Data preparation: transformation | Data preparation | Stage 2 augmentation, Stage 3 synthetic generator | [`stages/stage_2.md`](../stages/stage_2.md), [`stages/stage_3.md`](../stages/stage_3.md), `docs/crisp_dm/iteration_2/investigation/` | `stage2.html`, `stage3.html` | 4 failures, 7 changes |
| 2. Data preparation: feature selection | Data preparation | Input representation & 48 px resolution search (`scripts/improvement_table.py fs`) | [`results/improvement_table.csv`](improvement_table.csv), [`prompts/2_data_preparation/feature_selection/`](../prompts/2_data_preparation/feature_selection/) | `stage1.html`, `experiments.html` | 1 failure (F32), 2 changes |
| 3. Modeling | Modeling | Stage 4 training | [`stages/stage_4.md`](../stages/stage_4.md), `docs/crisp_dm/iteration_2/search/`, `docs/crisp_dm/iteration_3/search/` | `stage4.html`, `experiments.html` | 13 failures, 18 changes |
| 4. Testing | Evaluation | Stage 5 evaluation | [`stages/stage_5.md`](../stages/stage_5.md), `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_3/preregistration.md` | `stage5.html`, `robustness.html` | 3 failures, 10 changes |
| (not a course stage) | Deployment | Stage 6 report and export, Stage 7 site | [`stages/stage_6.md`](../stages/stage_6.md), [`stages/stage_7.md`](../stages/stage_7.md) | `stage6.html` | 8 failures, 18 changes |
| (supports Testing and Verification) | - | Stage 0 infrastructure: guards, hash cache, code migration check | [`stages/stage_0.md`](../stages/stage_0.md), `src/stage0_infra/` | `stage0.html` | - |

The three CRISP-DM iterations cut across the stages: [`docs/crisp_dm/README.md`](../docs/crisp_dm/README.md),
`iterations.html`, `iteration1.html`, `iteration2.html`, `experiments.html`.

## Key findings per stage

Copied from the conclusions on the live stage pages, each read from that page's numbers.

**1. Data integration (Stage 1)**
- The data is frozen into about 70% train, 15% validation and 15% test, and the test images are never shown.
- An image's source almost gives away its class, so training on one source and testing on another became mandatory.
- Every rule the catalog must satisfy holds, with zero violations.
- No single source covers every class, and ellipses and pentagons each come from one source only.
- Some near-copies come in groups of over 200 images, and each group is kept inside a single split.

**2. Data preparation: cleaning (Stage 1, CRISP-DM iteration 1)**
- Most Quick, Draw! "diamonds" were not rhombi, so they were removed before the split.

**2. Data preparation: transformation (Stages 2 and 3)**
- Each training drawing becomes many varied copies that still show the same shape.
- Augmentation only ever touches training images, after the split.
- A generated shape now looks like a clean version of a real drawing of the same class.
- Generated ellipses, rectangles and diamonds always stay clearly away from circles and squares.

**3. Modeling (Stage 4)**
- All five models use the same small network of 242,250 learned numbers.
- Each model got its own tuning, and all five settled on the same learning rate and dropout.
- Two seeds of the same model disagree on only about 2% of validation images.
- Without a neural network, the best baseline reaches 82.5, more than ten points below every model.

**4. Testing (Stage 5)**
- On damaged images the full mix beats real-only training by 9.20 points, which passes the locked rule.
- On clean images the gains are under one point, so the clear win is on damaged images.
- Most classes score above 90 for every model; ellipse and octagon are the hardest.
- On a source never seen in training every model drops sharply, and Full mix drops least.
- Rendered sources are almost always right; hand-drawn and Quick, Draw! sketches are where the models miss.
- Validation showed the test was big enough to detect a one-point gain before any test image was read.

## Gaps against the course PDF

- **Feature selection** has no Phase 2 step. It needs a new run (see [`prompts/2_data_preparation/PROMPT.md`](../prompts/2_data_preparation/PROMPT.md)).
- **Baseline before any data preparation**: the Phase 2 baselines (logistic regression, SVM on HOG) were trained
  on the prepared 64x64 images, so they are not the course baseline.
- **Deployment** (26 worksheet rows) is not graded as a stage, but it can support the presentation.
