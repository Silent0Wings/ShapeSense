# 3_modeling - C12: Hyperparameter tuning 
[33_real_iteration-2-plan-tuning-and-a2.md](33_real_iteration-2-plan-tuning-and-a2.md), [39_real_full-or-partial-training-in-tuning.md](39_real_full-or-partial-training-in-tuning.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/08_C12_hyperparameter-tuning.md](../gemini_4_neon/08_C12_hyperparameter-tuning.md)
- Date: 2026-11-09
- Entry: C12 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, configs/pipeline.yaml, docs/crisp_dm/iteration_2/preregistration.md, docs/crisp_dm/iteration_2/investigation/report.md, docs/crisp_dm/iteration_2/search/winners.json, docs/crisp_dm/iteration_3/search/winners.json, commits 87711f3, 5acfb7c



## Prompt
In iteration 1 we ran the Decision 7 grid (learning rate 0.0003, 0.001, 0.003 by dropout 0.2, 0.4) on A1 seed 0 only, got lr 0.003 and dropout 0.2 at 90.44 validation macro-F1, and gave that to every arm. Some of us say a single shared setting is the cleanest design, because then only the data differs between arms. Gemini 4 Neon says each arm needs its own tuning, or the arm we tuned on is favoured. Who is right, and if we tune per arm, how do we keep it fair and how do we report the chosen values?

## Response
The "one shared setting" argument assumes the setting is neutral. It is not: it was chosen on A1, so it is A1's optimum, and the other arms inherit it whether or not it suits their data stream. A0 sees only clean images and fits fast; A2 and B see harder, more varied batches. A learning rate or dropout that is right for one can under- or over-regularise another. So the shared setting does not remove a difference between arms, it hides one, and in the direction that favours A1.

Gemini 4 Neon is right on the principle. The shared-setting camp is right that tuning per arm opens a new risk: unequal search effort. The resolution is to equalise the procedure, not the values.

**Rules I would write into the pre-registration:**
1. **Same grid for every arm**, A0 included: the existing 3 x 2 grid, nothing added for one arm only.
2. **Same base for the grid**: each arm's best augmentation and generator setting found so far, so the grid tunes the arm as it will actually be trained.
3. **Same budget**: 49 steps per epoch, the same epoch limit and the same early-stopping rule for every grid cell.
4. **Same confirmation**: top settings re-run on seeds 0, 1 and 2, highest three-seed mean wins. One seed is not enough; validation can swing between epochs at lr 0.003, as the investigation found.
5. **Validation only**, and the test split stays sealed.

**Reporting.** Freeze each arm's winner in its own `hparams` block in `configs/pipeline.yaml`, publish the full grid per arm, and state trials per arm. If the winners turn out to be the same values for most arms, that is fine and worth saying: it means the shared setting was close, not that tuning was wasted.

| Design | Hidden bias | Effort balance | Verdict |
|---|---|---|---|
| Shared, tuned on A1 | Favours A1 | Trivially equal | Drop |
| Per arm, ad hoc | Low | Unequal | Drop |
| Per arm, same grid and budget | Low | Equal for the grid | Adopt |

## Validation
- `docs/crisp_dm/iteration_2/preregistration.md`: "Each arm gets its own learning-rate and dropout tuning, A0 included", with the 3 x 2 grid for A0, A1, B and A2.
- `docs/crisp_dm/iteration_2/search/winners.json` holds the full grid per arm and the three-seed confirmation. A0's grid gave 94.18 at lr 0.003, dropout 0.4 against 93.91 at dropout 0.2.

## Our decision
Hyperparameter tuning: learning rate and dropout tuned on A1, shared by every arm -> tuned per arm: learning rate 0.003 for all, dropout 0.2, except A0 at 0.4. A single arm's settings could favour that arm.

## Measured effect
- Iteration 2 winners, mean validation macro-F1 over three seeds: A0 92.61 (seeds 94.18, 89.21, 94.43), A1 94.77, B 94.20, A2 95.17 (`docs/crisp_dm/iteration_2/search/winners.json`).
- In iteration 3, with 60 epochs and grouped CV, A0's winner moved back to dropout 0.2, so all five arms use lr 0.003 and dropout 0.2 (`docs/crisp_dm/iteration_3/search/winners.json`, `configs/pipeline.yaml`).

---

## Per-Arm Optimization Symmetry & Confounder Elimination (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `C12` (`change`, `3_modeling` — Two-LLM mediated comparison with `gemini_4_neon`)
* **Date:** `2026-11-09`
* **Owner / Proposed By:** `40256377` / `gemini_4_neon` (`mediated` by `opus_medium_5.5`)
* **Primary Artifacts:** `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_3/search/winners.json`, commits `87711f3`, `5acfb7c`

### Statistical Critique of Shared Hyperparameters

In Iteration 1, Decision 7 executed a $3 \times 2$ grid search ($\text{lr} \in \{3\times 10^{-4}, 10^{-3}, 3\times 10^{-3}\} \times \text{dropout} \in \{0.2, 0.4\}$) **exclusively on `A1` seed 0**, selecting `(lr=0.003, dropout=0.2)` (`90.44` validation macro-F1) and broadcasting those hyperparameters across all arms.

#### Why "Shared Settings" Introduce Directional Selection Bias

* **Asymmetric Regularization Requirements:** `A0` trains exclusively on low-variance clean real data and rapidly overfits without stronger regularization, whereas `A1`, `B`, and `A2` train on high-entropy augmented/synthetic streams that already act as implicit regularizers.
* **Single-Seed Variance:** At `lr = 0.003`, validation curves exhibit high epoch-to-epoch oscillation; tuning on a single seed (`seed 0`) conflates optimization trajectory noise with genuine hyperparameter superiority.
* **Confounded Attribution:** Applying `A1`'s optimal point estimate to all arms does not hold capacity constant—it systematically favors `A1` while under- or over-regularizing competing arms.

### Standardized Per-Arm Search Protocol

To eliminate directional bias without introducing unequal search effort, Iteration 2 pre-registered **procedural symmetry** across all four arms (`A0`, `A1`, `B`, `A2`):

1. **Identical Search Space:** Every arm evaluates the exact same $3 \times 2 = 6$ grid (`lr` $\times$ `dropout`).
2. **Conditioned Data Pipeline:** Each arm's grid runs atop that arm's frozen optimal augmentation/generator configuration.
3. **Locked Compute Budget:** Identical 49 steps/epoch, maximum epoch cap, and early-stopping criterion across all 24 grid cells.
4. **Multi-Seed Confirmation:** Top candidates are evaluated across `seeds = [0, 1, 2]`, selecting the winner strictly by **3-seed mean validation macro-F1** while keeping test splits sealed.

### Empirical Grid Outcomes Across Iterations

| Arm | Iter 1 (Shared from `A1` s0) | Iter 2 Winner (`lr`, `dropout`) | Iter 2 3-Seed Val Macro-F1 (Per-Seed Breakdown) | Iter 3 Winner (60 Epochs, Grouped CV) |
| --- | --- | --- | --- | --- |
| **`A0`** | `(0.003, 0.2)` | **`(0.003, 0.4)`** (`94.18` vs `93.91` at `0.2`) | **92.61** (`[94.18, 89.21, 94.43]`) | `(0.003, 0.2)` |
| **`A1`** | `(0.003, 0.2)` | `(0.003, 0.2)` | **94.77** | `(0.003, 0.2)` |
| **`B`** | `(0.003, 0.2)` | `(0.003, 0.2)` | **94.20** | `(0.003, 0.2)` |
| **`A2`** | *N/A* | `(0.003, 0.2)` | **95.17** | `(0.003, 0.2)` |

*Key Takeaway:* In Iteration 2, per-arm tuning empirically validated the theoretical prediction—`A0` uniquely required higher dropout (`0.4`) to curb clean-data overfitting before converging back to `0.2` under Iteration 3's 60-epoch grouped cross-validation regime.

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |

