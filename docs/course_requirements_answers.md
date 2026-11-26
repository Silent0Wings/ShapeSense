# Course requirements: answers and evidence

Each requirement in [course_requirements.md](course_requirements.md) is answered below from this repository and the
deployed copy (`ShapeSense_Deployed`, live at <https://shapesense-ten.vercel.app>). Every number links to its file.
**Status** says whether the requirement is met, partly met, or still needs work. Written 2026-11-20, updated
2026-11-26 (repo public, notebook run in Colab).

Main metric everywhere: **macro F1** over 10 classes, in points (0 to 100), on the sealed test split of 2,776 images
unless a row says otherwise.

## Summary

| Requirement (weight) | Status | Main evidence |
|---|---|---|
| Per-stage LLM use, validation and human judgment (30%) | Met | `prompts/<stage>/`, `results/llm_comparison/attribution_worksheet.csv` (101 entries) |
| Baseline and improvement table (part of the 30%) | Met | `results/improvement_table.csv`, `results/README.md` §1 |
| Verification and dataset awareness (20%) | Met (Claude and Gemini runs complete) | `results/verification/README.md`, `prompts/6_verification/dataset_awareness/` |
| Two-LLM comparison (15%) | Met | `results/llm_comparison/`, `prompts/*/cross_critique/` |
| Pipeline vs. direct LLM prediction (15%) | Met | `results/direct_llm_prediction/summary.json` |
| Repository and Colab (10%) | Mostly met: sharing pending | The repo is **public**. The notebook ran top to bottom in Colab on a T4 GPU on 2026-11-24 with every stage passing, and `notebooks/shapesense_pipeline.ipynb` is that run, saved with its outputs (print: `jupyter runs clean.pdf`). Still to do: share view access with the instructor and TAs |
| Presentation (10%) | Met | `slides.pdf`: 8 slides in the course layout, with the repo and Colab links (`slides/build_slides.py`) |

## 1. Stage by stage: what we asked, what the LLM said, how we checked it, what we changed

Every stage keeps its prompts and responses in `prompts/<stage>/{claude_opus,gemini_4_neon,cross_critique}/`, with an
`inferred_prompts.md` index whose entries each have a prompt and an answer. Files named `NN_real_*` are verbatim chat
exports. 
| Stage | What the LLM proposed (examples) | How we validated it | What the team changed, and why |
|---|---|---|---|
| 0. Data discovery | Four public sources covering all ten classes. Reject four other candidates | Licenses and counts checked on disk (`docs/source.md`). MD5 of every file before deleting duplicates | Excluded Kaggle dinesh (license "Unknown", no new class). Removed 4 duplicate folders |
| 1. Data integration | Label map, MD5 identity, global pHash near-duplicate groups, group-aware split, sealed holdouts | Functional-dependency checks (`results/phase2_snapshot/fd_check.json`), fail-closed leakage guards (`guards.json`) | Found that images reveal their source (F05): a source classifier and per-source scores were added (`source_classifier.json`, `per_source.csv`) |
| 2a. Cleaning | Drop, relabel or keep the Quick, Draw! diamonds | Review sheets. Quick, Draw! diamond recall on validation was 59% | Excluded all 500 by a written rule before any test read. Split re-frozen at 12,405 / 2,819 / 2,776 (F01, C01) |
| 2b. Transformation | Class-safe augmentation. Synthetic shape generator | Rotation ablation (`docs/crisp_dm/iteration_2/search/phase_ablation.json`). Framing and stroke checks | Rotation ±180° hurt square, rectangle and diamond, so it was searched: ±20°, capped at ±10° for those three (F07). Framing fixed (F08), thin-line path (F09), synthetic stroke width matched to real (F10) |
| 2c. Feature selection | Input representation: crop, resolution, hand-made features | HOG + SVM and pixels + logistic regression baselines (`baselines.json`). Reframing check (`exp_preprocess.json`). Resolution search on validation | Chose a 48 px input on validation, which scored +0.48 over 64 px on test. Caught a GPU resize bug first (F32). See §2 |
| 3. Modeling | CNN arms A0, A1, B, A2, P. Per-arm search of augmentation, generator and hyperparameters | 166-trial validation search. 5 seeds per arm | Moved to four conv blocks, because three gave a 22-px receptive field (F17). Training made about 5x faster with identical scores (F21) |
| 4. Testing | Pre-registered comparisons, bootstrap CIs, McNemar with Holm correction | `comparisons.csv`, `power.json`, `noise_bands.csv` | Reported failed hypotheses as failed: A2 vs A0 +0.5, CI [-0.2, 1.2] (F04, F14). Robustness test on damaged images: A2 vs A0 +9.20, CI [8.89, 9.53] (`robust_sealed.json`) |

The full log is 31 failures and 57 changes, each with its cause and how it was handled
(`docs/crisp_dm/iteration_log.json`), mirrored with decisions in the attribution worksheet. Of the 101 worksheet
entries, the LLM proposed 52 and assisted, mediated, reviewed, inspected, implemented or critiqued 27 more. In 13 no
LLM was involved, and the team caught 8 problems itself.

Each failure was also restated as a research question (`prompts/failure_search_prompts.md`). The cited web answers are
saved in each stage's `claude_opus/` folder as `NN_Fnn_*-search.md`.

## 2. Baseline and improvement table: met (run 2026-11-20)

Same CNN, same settings, seeds 0 to 4. Each row adds one step and retrains, and every row is scored on the same 2,776
test images (`results/improvement_table.csv`, built by `scripts/improvement_table.py`):

| Data preparation step | Baseline score | New score | Delta (New - Baseline) |
|---|---|---|---|
| Cleaning | 89.13 ± 0.43 | 89.63 ± 0.74 | +0.50 |
| Transformation | 89.13 ± 0.43 | 95.83 ± 0.31 | +6.70 |
| Feature selection | 89.13 ± 0.43 | 96.31 ± 0.13 | +7.19 |

- **Baseline:** raw images, only decoded and resized to 64x64, including the 372 items cleaning removes.
- **Cleaning:** its gain is within the seed spread. Its purpose was label correctness.
- **Transformation:** standardization alone gives +5.51 (arm A0), and augmentation plus synthetic shapes take it to
  +6.70 (arm A2).
- **Feature selection:** a 48 px input, chosen on validation, gives +7.19. It was higher than 64 px on 4 of 5 seeds,
  but its validation margin was within noise.
- **Caveats** (in `results/README.md` §1): this test split had been read in earlier iterations (F13). The first
  feature-selection attempt hit a GPU resize bug (F32) and was rerun.

## 3. Compare two LLMs (Claude Opus 5.5 and Gemini 4 Neon)

- **Per stage:** 25 entries have a Claude and a Gemini answer to the same prompt, word for word, each file linking to
  the other model's answer (`prompts/*/claude_opus/` and `prompts/*/gemini_4_neon/`, category "Two-LLM comparison"),
  plus 32 cross-critique files. 
- **One critiques the other:** Gemini 4 Neon audited the Claude-built pipeline with web search on: 27 claims
  (`results/llm_comparison/gemini_audit.md`). The team judged 21 to stand, 4 to stand partly and 2 not to stand. As a
  result, 11 were fixed in iteration 3, 9 disclosed and 2 closed by experiment. Example: A01, per-class test counts were never
  checked against the noise bands, and Stage 5 now stops if they don't match. Claude also checked Gemini's reviews
  (`prompts/3_modeling/cross_critique/12_real_*`, `13_real_*`).
- **Did both help?** Yes, measurably in robustness and correctness, not in clean test F1. The audit led to 11 fixes in
  the final pipeline. The two models disagreed on few direct predictions (96% agreement), so a second model added
  little there.


## 4. Pipeline vs. direct LLM prediction

200 test images (20 per class, seed 0), shown blind to each LLM with 50 labelled training examples. The trained CNN
(A2_0, exported ONNX) was scored on the same images (`results/direct_llm_prediction/summary.json`):

| Model | Correct of 200 | Macro F1 |
|---|---|---|
| Trained CNN (A2_0) | 195 | 97.5 |
| Gemini 4 Neon | 188 | 93.97 |
| Claude Opus 5.5 | 185 | 92.55 |

**Rerun with one command** (`scripts\llm_classify.bat`, 2026-11-26): each model fills in an unlabelled CSV for the
same 200 images through its CLI. Claude 92.97 and Gemini 92.48 macro F1 against 97.50 for the CNN; the CNN still
leads by about 5 points, and the two LLMs are within noise of each other (`results/direct_llm_prediction/README.md`).

**Why the difference:** both LLMs make the same errors: circle called ellipse (4 each) and hexagon called octagon
(4 each). These are exactly the pairs whose definitions hinge on axis ratio or corner count at 64x64. The CNN learned
those boundaries from 12,405 training images. The gap is largest on Quick, Draw! sketches: the CNN got 24 of 27 and
each LLM 21 of 27. The CNN's 5 errors are mostly hard sketches that the LLMs also miss. Only one or two images went the
other way, for example T154, a hand-drawn ellipse the CNN called a triangle. Analysis:
`prompts/5_direct_llm_prediction/cross_critique/01_direct-prediction-error-comparison.md`.

## 5. Verification

**Process:**
- Hypotheses pre-registered before any test read.
- Sealed test split and two sealed fresh holdouts.
- Import-linter and contract tests that stop stages reading data they shouldn't see.
- 5 seeds per arm.
- Bootstrap CIs, McNemar tests with Holm correction.
- Classical baselines and a source-shortcut check.
- Functional-dependency checks on the metadata.
- Manual QA sheets.
- The 27-claim external audit.
- Browser models checked against Python, with logits within 1e-4 (`ShapeSense_Deployed/build/check.py`).

The full table is in `results/verification/README.md`.

**Dataset awareness** (`prompts/6_verification/dataset_awareness/claude_opus/01_four-sources.md`, `prompts/6_verification/dataset_awareness/gemini_4_neon/02_sandboxed-replication.md`, and `prompts/6_verification/dataset_awareness/cross_critique/01_four-sources-cross-critique.md`): Claude Opus 5.5 ran in a fresh zero-tool session, and Gemini 4 Neon in the Antigravity CLI in an empty sandbox folder with no project files and tools forbidden. Both knew Quick, Draw! and El Korchi accurately, down to El Korchi's 90,000 files and `<ClassName>_<uuid>.png` names. Claude also knew the folder layout and class lists of reevald and frobertpixto. Gemini only faintly recalled reevald's classes and did not know frobertpixto. Gemini's first run, made by hand in Antigravity with access to the project files, reported more, and is not counted (`gemini_4_neon/00_`; `01_` is the same reply, reformatted). Neither model made a confident invention. Because both models score lowest on Quick, Draw! (77.78%) despite knowing its metadata best, metadata recall reflects exposure to public documentation rather than memorization of the standardized 64×64 benchmark tiles.

## 6. Deliverables

| Item | Status | Note |
|---|---|---|
| Public GitHub repo: code, prompts and responses, results | Met | [Silent0Wings/ShapeSense](https://github.com/Silent0Wings/ShapeSense) is public and all commits are pushed |
| README: team, topic, LLMs, Colab link | Met | Team 14, topic, exact model names, and a Colab link that opens the notebook from GitHub |
| `data/` | Met | `data/README.md` links the sources (`data_set/` is not in Git) |
| `notebooks/` copy of the Colab | Met | `notebooks/shapesense_pipeline.ipynb` has one section per stage, prints the metric after each data preparation step, and scores the baseline, final model and LLMs on the same test images. It is the 2026-11-24 Colab run (T4 GPU), saved with all its outputs |
| `results/` improvement table and comparisons | Met | `results/improvement_table.csv` and `results/llm_comparison/` complete (§2, §3) |
| `slides.pdf` | Met | 8 slides in the course layout. Rebuild with `python slides/build_slides.py` |
| Colab shared with instructor and TAs, runs top to bottom | Runs: met. Sharing: pending | Ran top to bottom without errors on 2026-11-24 (T4 GPU). The GitHub-backed Colab link opens for anyone now that the repo is public. View access to the run copy still has to be shared with the instructor and the TAs. On the T4 the scores differ slightly from the recorded local run (RTX 3080): baseline 89.26 vs 89.13, final 96.18 vs 96.31, with every step still improving in the same order. Side-by-side table in `results/README.md` §1 |

## 7. Slide layout (about 8 slides, 10 minutes)

1. Topic and dataset: 10 shape classes, 4 public sources (`docs/source.md`).
2. The two LLMs and dataset awareness: §3 and §5.
3. Where the LLM helped and where we corrected it: F01, F07, F17, A01 (§1).
4. Improvement table: §2.
5. Two-LLM comparison: the audit, 27 claims, 11 fixes (§3).
6. Pipeline vs. direct LLM: 97.5 vs 94.0 vs 92.6 (§4).
7. Verification process (§5).
8. Lessons learned:
   - LLM numbers were wrong when unmeasured. Converting pixels on the GPU, as an outside report recommended, would have changed every result (F24).
   - Both LLMs share blind spots.
   - Pre-registration kept us honest when hypotheses failed.
