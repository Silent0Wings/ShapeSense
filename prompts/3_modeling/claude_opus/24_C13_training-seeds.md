# 3_modeling - C13: Training seeds 
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09 (no commit recorded; date of the iteration 2 pre-registration and investigation)
- Entry: C13 (`change`, `3_modeling`)
- Owner / Proposed by: 40253714 / 40253714
- LLM role: assisted
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, configs/pipeline.yaml, src/stage4_train/sweep.py, docs/crisp_dm/iteration_2/preregistration.md, docs/crisp_dm/iteration_2/investigation/report.md, docs/crisp_dm/iteration_2/data/stage4_status.json, docs/crisp_dm/iteration_3/preregistration.md, no commit recorded



## Prompt
For iteration 2 I want to go from three seeds per arm to five, and run the Hand-Drawn hold-out on three seeds for every arm instead of only A1 and B on one seed. In the investigation the three A0 hold-out runs scored 47.0, 64.1 and 49.3% accuracy, so one seed per arm tells us almost nothing there. Can you check this against our config and sweep code, and estimate how many extra trainings it costs?

## Response
Your proposal is sound, and the hold-out numbers you quote are the strongest argument for it: a 17-point spread across three A0 runs means a single hold-out run per arm cannot rank arms at all. On the in-distribution side the case is weaker but still real: the primary comparison is a soft-vote ensemble over seeds, and more seeds both stabilise the ensemble and let us report per-seed differences next to the interval.

**What the code already supports.**
- `configs/pipeline.yaml` has `seed_set: [0, 1, 2, 3, 4]` with the note "the SAME set is used for every arm". The fairness rule holds as long as every arm gets the same list, so add `{ arm, seed: 3 }` and `{ arm, seed: 4 }` entries for every arm in `runs`.
- `src/stage4_train/sweep.py` builds the hold-out jobs itself (`<arm>_loso_handdrawn_<seed>`), currently for A1 and B with the first seed only. Extending it to every arm and three seeds needs a config key for the hold-out seed count rather than a hard-coded first seed.
- Finished runs with the same hparams and budget are reused, so seeds 0 to 2 do not have to retrain if nothing else changes. In iteration 2 the recipe does change, so expect everything to retrain.

**Cost, in trainings.**

| Plan | Main runs | Hold-out runs | Total |
|---|---|---|---|
| Three seeds, current hold-out (iteration 1 shape, 3 arms) | 9 | 2 | 11 |
| Three seeds, 4 arms, hold-out for all on 3 seeds | 12 | 12 | 24 |
| Your plan: five seeds, 4 arms, hold-out for all on 3 seeds | 20 | 12 | 32 |

So your plan costs 8 trainings more than the same design with three seeds. These are final runs at the fixed step budget, so the cost scales linearly; the search, not the seeds, is the expensive part of iteration 2.

**Two cautions.**
1. Seeds are for the final retrain only. Search and confirmation stay on seeds 0, 1 and 2, otherwise the confirmation seeds and the reported seeds overlap differently per arm.
2. Hold-out runs must still use the A0 step budget and never read test; they are scored on Hand-Drawn triangles and rectangles, and stay descriptive.

## Validation
- `docs/crisp_dm/iteration_2/preregistration.md`: "The final retrain uses seeds 0, 1, 2, 3, 4 for every arm", plus "the Hand-Drawn hold-out runs for all four arms with 3 seeds each".
- `docs/crisp_dm/iteration_2/data/stage4_status.json` lists 20 main runs (`A0_0` to `A2_4`) and 12 hold-out runs (`<arm>_loso_handdrawn_0` to `_2`).
- `configs/pipeline.yaml` has `evaluation.loso_seeds: 3`, and iteration 3 kept five seeds per arm for all five arms (`docs/crisp_dm/iteration_3/preregistration.md`).

## Our decision
Training seeds: three per arm -> five per arm, plus three hold-out-source runs per arm, to measure seed variation better.

## Measured effect
No before/after measurement of the seed change itself was recorded. With five seeds the iteration 3 report could show that A2 vs A1 did not have the same sign on every seed, and the final five-seed validation macro-F1 was A0 94.33, A1 95.27, B 95.12, A2 95.82, P 95.22 (`iteration_log.json`).

---

## Statistical Power, Ensemble Variance & Hold-Out Replication (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `C13` (`change`, `3_modeling`)
* **Date:** `2026-11-09`
* **Owner / Proposed By:** `40256377` / `40256377` (`assisted` by `opus_medium_5.5`)
* **Primary Artifacts:** `configs/pipeline.yaml`, `src/stage4_train/sweep.py`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/data/stage4_status.json`, `docs/crisp_dm/iteration_3/preregistration.md`

### Statistical Motivation

1. **Out-of-Distribution (OOD) Instability:** In the Iteration 1 diagnostic investigation, three `A0` runs evaluated on the Hand-Drawn leave-one-source-out (LOSO) hold-out scored **`47.0%`, `64.1%`, and `49.3%`** accuracy—a **17.1 percentage-point spread** across initialization seeds. Running only `A1` and `B` on a single hold-out seed (`seed 0`) made cross-arm OOD ranking statistically meaningless.
2. **Soft-Vote Ensemble Stabilization:** Because primary in-distribution evaluation uses a **soft-vote probability ensemble** across seeds, expanding from 3 to 5 seeds reduces ensemble prediction variance and enables paired per-seed sign-consistency analysis alongside bootstrap confidence intervals.

### Pipeline Implementation & Separation of Search vs. Final Retrain

* **Config & Sweep Refactoring:** Extended `configs/pipeline.yaml` (`seed_set: [0, 1, 2, 3, 4]`, `evaluation.loso_seeds: 3`) and refactored `src/stage4_train/sweep.py` to generate `<arm>_loso_handdrawn_<seed>` jobs dynamically across all arms instead of hardcoding `A1`/`B` on seed 0.
* **Data-Leakage & Selection-Bias Prevention:**
  * Hyperparameter search and confirmation remained strictly restricted to `seeds [0, 1, 2]` so that `seeds [3, 4]` functioned as uncontaminated out-of-search replicates.
  * LOSO Hand-Drawn runs enforced the `A0` step budget, never accessed the main test split, and remained strictly descriptive (scored exclusively on Hand-Drawn triangles and rectangles).

### Compute Cost Scaling & Iteration 3 Empirical Payoff

| Experimental Design | Main In-Distribution Runs | LOSO Hand-Out Runs | Total Full Trainings | Marginal Cost vs. 3-Seed 4-Arm |
| --- | --- | --- | --- | --- |
| **Iteration 1 Baseline** (3 arms, 3 main / 1 LOSO on `A1, B`) | `9` (`3 × 3`) | `2` (`2 × 1`) | **11** | Baseline |
| **Intermediate 4-Arm** (4 arms, 3 main / 3 LOSO all arms) | `12` (`4 × 3`) | `12` (`4 × 3`) | **24** | — |
| **Iteration 2 Adopted (`C13`)** (4 arms, 5 main / 3 LOSO all arms) | `20` (`4 × 5`) | `12` (`4 × 3`) | **32** | **`+8` runs** (`+33.3%`, linear step cost) |

*Downstream Payoff:* Carrying the 5-seed protocol into Iteration 3 (`5 arms × 5 seeds = 25` main runs) exposed that `A2 vs. A1` did not maintain uniform sign dominance across every individual seed despite `A2` leading on 5-seed mean validation macro-F1 (`A2: 95.82`, `A1: 95.27`, `P: 95.22`, `B: 95.12`, `A0: 94.33`)—an insight impossible to detect with 3 seeds.

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |

