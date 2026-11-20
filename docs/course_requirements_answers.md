# Course requirements: answers and evidence

Each requirement in [course_requirements.md](course_requirements.md) is answered below from this repository and the
deployed copy (`ShapeSense_Deployed`, live at <https://shapesense-ten.vercel.app>). Every number links to its file.
**Status** says whether the requirement is met, partly met, or still needs work. Written 2026-11-20.

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
| Repository and Colab (10%) | Partly met: Colab link and notebook run pending | README has the Colab link, `slides.pdf` is built, the notebook has a section per step. The repo is still **private**, and the notebook has not been run in Colab |
| Presentation (10%) | Met | `slides.pdf`: 8 slides in the course layout, with the repo and Colab links (`slides/build_slides.py`) |

## 1. Stage by stage: what we asked, what the LLM said, how we checked it, what we changed

Every stage keeps its prompts and responses in `prompts/<stage>/{claude_opus,gemini_4_neon,cross_critique}/`, with an
`inferred_prompts.md` index whose entries each have a prompt and an answer. Files named `NN_real_*` are verbatim chat
exports. Others are reconstructions and say so in their header.

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
  plus 32 cross-critique files. Most of these pairs are reconstructions, not original chats, and say so in their header.
- **One critiques the other:** Gemini 4 Neon audited the Claude-built pipeline with web search on: 27 claims
  (`results/llm_comparison/gemini_audit.md`). The team judged 21 to stand, 4 to stand partly and 2 not to stand. As a
  result, 11 were fixed in iteration 3, 9 disclosed and 2 closed by experiment. Example: A01, per-class test counts were never
  checked against the noise bands, and Stage 5 now stops if they don't match. Claude also checked Gemini's reviews
  (`prompts/3_modeling/cross_critique/12_real_*`, `13_real_*`).
- **Did both help?** Yes, measurably in robustness and correctness, not in clean test F1. The audit led to 11 fixes in
  the final pipeline. The two models disagreed on few direct predictions (96% agreement), so a second model added
  little there.
- **Gap:** the original Gemini chats for the audit and for data discovery were not exported. Those files say so,
  and the 7 discovery files carry a labelled stand-in answer, not Gemini's reply.

## 4. Pipeline vs. direct LLM prediction

200 test images (20 per class, seed 0), shown blind to each LLM with 50 labelled training examples. The trained CNN
(A2_0, exported ONNX) was scored on the same images (`results/direct_llm_prediction/summary.json`):

| Model | Correct of 200 | Macro F1 |
|---|---|---|
| Trained CNN (A2_0) | 195 | 97.5 |
| Gemini 4 Neon | 188 | 93.97 |
| Claude Opus 5.5 | 185 | 92.55 |

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

**Dataset awareness** (`prompts/6_verification/dataset_awareness/claude_opus/01_four-sources.md`, `prompts/6_verification/dataset_awareness/gemini_4_neon/01_four-sources.md`, and `prompts/6_verification/dataset_awareness/cross_critique/01_four-sources-cross-critique.md`): Both Claude Opus 5.5 and Gemini 4 Neon, run in fresh zero-tool sessions without web search or file reads, knew Quick, Draw! and El Korchi accurately, down to El Korchi's 90,000 files and `<ClassName>_<UUID>.png` names. Both knew the folder layout and class lists of reevald and frobertpixto (with Gemini also recalling reevald's 224×224 size) while declining to invent unknown counts, licenses, or file names. Neither model made a confident invention. Because both models score lowest on Quick, Draw! (77.78%) despite knowing its metadata best, metadata recall reflects exposure to public documentation rather than memorization of the standardized 64×64 benchmark tiles.

## 6. Deliverables

| Item | Status | Note |
|---|---|---|
| Public GitHub repo: code, prompts and responses, results | **Repo is private** | All material is in the repo once committed and pushed. [Silent0Wings/ShapeSense](https://github.com/Silent0Wings/ShapeSense) must be made public |
| README: team, topic, LLMs, Colab link | Met | Team 14, topic, exact model names, and a Colab link that opens the notebook from GitHub |
| `data/` | Met | `data/README.md` links the sources (`data_set/` is not in Git) |
| `notebooks/` copy of the Colab | Met, not yet run in Colab | `notebooks/shapesense_pipeline.ipynb` has one section per stage, prints the metric after each data preparation step, and scores the baseline, final model and LLMs on the same test images. Every command in it was run locally on 2026-11-20 except the full pipeline rebuild (sections 4 to 7, already recorded) |
| `results/` improvement table and comparisons | Met | `results/improvement_table.csv` and `results/llm_comparison/` complete (§2, §3) |
| `slides.pdf` | Met | 8 slides in the course layout. Rebuild with `python slides/build_slides.py` |
| Colab shared with instructor and TAs, runs top to bottom | Needs the repo public | The GitHub-backed Colab link opens for anyone once the repo is public. Running it needs a GPU runtime and the raw `data_set/` folder from the team's Drive (section 2) |

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
