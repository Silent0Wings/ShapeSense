# 3_modeling - C10: Training arms 

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [33_real_iteration-2-plan-tuning-and-a2.md](33_real_iteration-2-plan-tuning-and-a2.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C10 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 + 40248536 / opus_medium_5.5 + 40256377 + 40248536
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, docs/crisp_dm/iteration_2/investigation/report.md, docs/crisp_dm/iteration_2/preregistration.md, docs/crisp_dm/iteration_2/search/winners.json, docs/crisp_dm/README.md, src/stage4_train/sampling.py, configs/pipeline.yaml, commit 87711f3

> ** from repo, not a saved chat:** No export of the original Claude Opus chat exists. The user prompt and the response below are written from the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
Looking at `src/stage4_train/sampling.py`, every real image in an A1 batch is augmented, and B is the same plus 77 synthetic images out of 256. So neither augmented arm ever sees a clean, standardized real image, which is exactly what validation and test contain. A0 sees only clean images and won on test. Should we add an arm that mixes clean real, augmented real and synthetic images in every batch? How would we split a 256-image batch, and how does it fit the comparison without bending iteration 1's result?

## Response
I think the gap is real and worth an arm. The investigation shows A0 behaves as a template matcher on familiar sources: its accuracy on rotated validation falls from 93.65 at 0° to 60.9 at 45°, while A1 stays at 89 to 91. A1 and B pay for robustness by never training on the image distribution they are scored on. A mixed arm asks the obvious next question: can a model keep A0's fit to clean images and A1's robustness at once?

**Design of the new arm (call it A2).**
- Every batch has three parts: clean real, augmented real, synthetic. The split is per batch, never per epoch, like B's synthetic share today.
- Real images stay class-balanced, as in every other arm, and the step budget stays at 49 steps per epoch. Only the data stream differs.
- Counts come from shares through the same rounding as B: `round(256 * share)`. Add a `clean_fraction` key and a `clean_count` helper next to `batch_composition`.

**How to choose the split.** I would not hand-pick it; hand-set ranges are part of what went wrong in iteration 1. Search it on validation with the other per-arm settings: clean share 0.1 to 0.6, synthetic share 0.1 to 0.4, total at most 0.8 so augmented real images never vanish. Report the frozen shares and the resulting image counts per batch.

| Option | Pro | Con |
|---|---|---|
| Add A2 as a pre-registered arm | Tests the clean-image gap directly | One more arm to train and tune |
| Change A1 to include clean images | No new arm | Breaks the locked iteration 1 definition of A1 |
| Leave arms as they are | Nothing to do | Leaves the clearest open question untested |

**My recommendation is to add A2 and keep A0, A1 and B exactly as defined.** Fairness rules: A2 gets the same seeds, step budget, architecture and its own tuning, like every other arm, A0 included.

**Caution on the comparison.** A2 is designed after a test read, so it cannot rescue iteration 1. Pre-register it before training (A2 vs A0 as the primary test), keep the iteration 1 verdict, and score it on the reused test split and on a fresh holdout that has never been read. If A2 also fails, that is a valid result.

## Validation
- `docs/crisp_dm/iteration_2/preregistration.md` defines A2 as "Clean real + augmented real + synthetic, in each batch" and makes A2 vs A0 the primary comparison.
- `src/stage4_train/sampling.py` has `clean_count` (`round(batch_size * clean_fraction)`) and `batch_composition` for the synthetic count.
- `docs/crisp_dm/iteration_2/search/winners.json` freezes A2 at `clean_fraction` 0.411 and `synthetic_fraction` 0.198, with 18 trials for A2.

## Our decision
Training arms: A0, A1, B -> A0, A1, B, A2. A2 batches hold 105 clean, 100 augmented and 51 synthetic images, because A1 and B saw no clean images during training.

## Measured effect
- Iteration 2 validation macro-F1, three seeds: A2 95.17, A1 94.77, B 94.20, A0 92.61 (`winners.json`).
- Iteration 2 test: A2 vs A0 +0.06, CI [-0.69, 0.83] on the reused test split and +0.08, CI [-0.41, 0.57] on the fresh holdout: fail on both (`iteration_log.json`).
- Iteration 3, damaged images of the never-read fresh holdout 2: A2 vs A0 +9.20 macro-F1 points, CI [8.89, 9.53]: pass (`iteration_log.json`).

---

## Distribution-Shift Mitigation & Experimental Arm `A2` (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `C10` (`change`, `3_modeling`)
* **Date:** `2026-11-09`
* **Owner / Proposed By:** `40256377 + 40248536` / `opus_medium_5.5 + 40256377 + 40248536` (`proposed`)
* **Primary Artifacts:** `src/stage4_train/sampling.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/search/winners.json`, commit `87711f3`

### Diagnostic Premise: The Clean-Manifold Gap

Iteration 1 error analysis revealed a structural dichotomy between training and evaluation distributions:

* **Arm `A0` (Clean Real Only):** Achieved top performance on unperturbed test data by acting as a high-precision template matcher on familiar source geometries (`93.65%` accuracy at $0^\circ$ rotation), but suffered catastrophic degradation under geometric perturbation (`60.9%` at $45^\circ$).
* **Arms `A1` (Augmented Real) & `B` (Augmented Real + Synthetic):** Maintained rotational invariance (`89%–91%` at $45^\circ$), but **100% of real images in every batch underwent stochastic augmentation**. Neither arm ever observed unperturbed standardized real images during gradient updates—creating a training-to-inference distribution mismatch against clean validation/test splits.

### Design & Parameterization of Arm `A2`

Rather than mutating `A1` (which would invalidate Iteration 1 comparability), a fourth pre-registered experimental arm **`A2`** was introduced:

1. **Intra-Batch Tri-Modal Partitioning:** Every 256-image batch is deterministically partitioned into three disjoint strata per step (never epoch-level):

$$N_{\text{clean}} = \operatorname{round}(256 \cdot f_{\text{clean}}), \quad N_{\text{synth}} = \operatorname{round}(256 \cdot f_{\text{synth}}), \quad N_{\text{aug}} = 256 - N_{\text{clean}} - N_{\text{synth}}$$

2. **Invariance Controls:** Preserves exact class balance across real samples, identical backbone architecture, identical `(arm, seed)` PRNG schedule, and the locked **49-step epoch budget**.
3. **Constrained Search Envelope (`preregistration.md`):** To prevent degenerate collapse into `A0` or `B`, validation search bounds were locked prior to execution:
   * $f_{\text{clean}} \in [0.10, 0.60]$
   * $f_{\text{synth}} \in [0.10, 0.40]$
   * $f_{\text{clean}} + f_{\text{synth}} \le 0.80 \implies f_{\text{aug}} \ge 0.20$ (ensuring augmented real examples remain active in every batch)

#### Methodological Guardrail Against Post-Hoc Leakage

Because `A2` was conceived after observing Iteration 1 test metrics, Iteration 1's verdict remained sealed and unaltered. `A2 vs. A0` was pre-registered as the primary hypothesis test in Iteration 2 and evaluated on both the reused test split and **newly collected, never-read fresh holdout splits**.

### Frozen Parameterization & Multi-Iteration Empirical Trajectory

| Evaluation Split / Iteration | `A2` Batch Allocation (`clean / aug / synth`) | `A2` Macro-F1 | `A0` Macro-F1 | $\Delta$ (`A2 - A0`) & 95% CI | Outcome |
| --- | --- | --- | --- | --- | --- |
| **Iter 2 Validation (3 seeds)** | `105 / 100 / 51` (`0.411 / 0.391 / 0.198`) | **95.17** | 92.61 | `+2.56` | Selected winner (18 trials) |
| **Iter 2 Reused Test** | `105 / 100 / 51` | — | — | `+0.06` `[-0.69, +0.83]` | ❌ Fail (statistically indistinguishable) |
| **Iter 2 Fresh Holdout 1** | `105 / 100 / 51` | — | — | `+0.08` `[-0.41, +0.57]` | ❌ Fail (clean holdout ceiling) |
| **Iter 3 Damaged Holdout 2** | `f_synth = 0.12` (re-tuned) | — | — | **`+9.20`** `[+8.89, +9.53]` | **✅ Pass (decisive robustness gain)** |

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |

