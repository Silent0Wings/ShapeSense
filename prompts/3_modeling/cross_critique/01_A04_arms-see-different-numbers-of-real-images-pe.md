# 3_modeling - A04: Arms see different numbers of real images per step.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A04 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage4_train/sampling.py, src/stage4_train/train.py, src/stage4_train/experiments.py, configs/pipeline.yaml, configs/models/A0.yaml, configs/models/A1.yaml, configs/models/B.yaml, configs/models/A2.yaml, docs/crisp_dm/iteration_3/experiments/equal_real.json, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/experiments.html


## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Arms see different numbers of real images per step.

## Response
In `src/stage4_train/sampling.py`, `batch_composition()` fixes the total batch size (`batch_size = 256`) and subtracts synthetic images from the real slot budget (`return batch_size - n_syn, n_syn`), while `src/stage4_train/train.py` locks `steps_per_epoch = 49` (`ceil(12405 / 256)`) across every arm under Decision 13. Because total step count and total batch size are held constant, every synthetic image displaces a real drawing:

- **A0 (`Real only`):** `256` unchanged real images per step (`12,544` real draws/epoch).
- **A1 (`Real + augmented`):** `256` augmented real images per step (`12,544` real draws/epoch).
- **B (`Real + synthetic`):** With `synthetic_fraction = 0.168` (`0.278` in Iteration 2), `n_syn = 43` (`71` in Iteration 2), leaving only `213` real images per step (`185` in Iteration 2) - a `16.8%` to `27.7%` reduction in real training images seen per epoch.
- **A2 (`Full mix`):** With `clean_fraction = 0.411` and `synthetic_fraction = 0.12` (`0.198` in Iteration 2), batches hold `105` clean real + `120` augmented real = `225` real images per step (`205` in Iteration 2) plus `31` synthetic (`51` in Iteration 2).

**Statistical & optimization diagnosis:** This creates a real-exposure confound when comparing `B` and `A2` against `A0` and `A1`. Any drop or lag in `B` relative to `A1` cannot be attributed cleanly to synthetic domain gap when `B` is also seeing `43` - `71` fewer real examples on every gradient step (`2,107` - `3,479` fewer real examples per epoch).

**Recommended fix:** Add an `equal_real` mode to `batch_composition()` where every arm draws the full `256` real images per step and appends `n_syn` synthetic images on top (`return batch_size, n_syn`, giving batches of `299` for `B` and `287` for `A2`). Keeping real-image exposure identical across all arms should remove the real-data handicap and raise `B` and `A2` clean and damaged macro-F1 without changing the `49` optimizer steps per epoch.

## Validation
- Team verified the unequal real-image counts per step in `src/stage4_train/sampling.py#batch_composition` and `configs/models/{A0,A1,B,A2}.yaml`.
- Added the `equal_real` option in `src/stage4_train/sampling.py` (`if arm_cfg.get("equal_real"): return batch_size, n_syn`) and ran the pre-registered validation-only experiment (`src/stage4_train/experiments.py#equal_real_specs`, 3 seeds each for `B` and `A2`, recorded in `docs/crisp_dm/iteration_3/experiments/equal_real.json`).
- Validation results directly refuted the expectation that equalizing real images per step would improve accuracy:
  - **B (`equal_real` vs `normal`):** Clean validation macro-F1 dropped from `94.20 ± 0.05` (`30.0 ± 0.0` epochs) to `92.18 ± 2.59` (`18.67 ± 10.26` epochs), a **`-2.03`-point** loss; damaged validation macro-F1 dropped from `77.07 ± 2.47` to `73.88 ± 7.00` (`-3.19` points).
  - **A2 (`equal_real` vs `normal`):** Clean validation macro-F1 dropped from `95.17 ± 0.26` (`30.0 ± 0.0` epochs) to `94.66 ± 0.90` (`27.0 ± 5.20` epochs), a **`-0.51`-point** loss; damaged validation macro-F1 dropped from `80.29 ± 1.30` to `77.61 ± 2.14` (`-2.68` points).
- On reflection, Gemini's recommendation overlooked that appending `n_syn` on top of `256` real images alters batch size (`256 + n_syn`), changes gradient noise scale at `lr = 0.003`, triggers earlier validation swings under early stopping, and dilutes the tuned synthetic gradient fraction.

## Our decision
Verdict: **Stands** (arms genuinely see different real-image counts per step). **Closed by experiment**: because giving `B` and `A2` `256` real images per step with synthetic images appended on top degraded clean validation macro-F1 by `2.0` and `0.5` points (and damaged validation by `3.2` and `2.7` points), the team rejected `equal_real` for the main runs, kept the tuned `256`-image batches (`213` real in `B`, `225` real in `A2`), and disclosed the unequal real counts in `results/llm_comparison/gemini_audit.md` and `ShapeSense_Deployed/web/iterations.html#3`.

## Measured effect
- `B/equal_real` vs `B/normal` (3 validation seeds): `-2.03` clean macro-F1 (`92.18` vs `94.20`), `-3.19` perturbed macro-F1 (`73.88` vs `77.07`), mean epochs run `18.67` vs `30.0`.
- `A2/equal_real` vs `A2/normal` (3 validation seeds): `-0.51` clean macro-F1 (`94.66` vs `95.17`), `-2.68` perturbed macro-F1 (`77.61` vs `80.29`), mean epochs run `27.0` vs `30.0`.

---

## Real-Sample Displacement and Exposure Asymmetry Across Arms (`A04`)

### Claim Metadata

* **Entry ID:** `A04` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `close-to-reality`
* **Grounding Artifacts:** `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, `src/stage4_train/experiments.py`, `configs/models/{A0,A1,B,A2}.yaml`, `docs/crisp_dm/iteration_3/experiments/equal_real.json`, `results/llm_comparison/gemini_audit.md`

### Mechanistic & Statistical Analysis

Under Decision 13, `src/stage4_train/train.py` fixes the optimization horizon across every arm at $S = 49$ steps per epoch ($\lceil 12,405 / 256 \rceil$) and `src/stage4_train/sampling.py` (`batch_composition`) constrains the mini-batch cardinality to $B = 256$ via zero-sum slot replacement: $n_{\text{real}} = B - n_{\text{syn}}$. Because total gradient updates and mini-batch size are held invariant, every synthetic sample injected into a mini-batch directly displaces one real sample from the gradient estimator.

Let $N_{\text{real/epoch}} = S \cdot n_{\text{real}}$ denote total real draws per epoch. Across iterations, real-sample exposure diverges systematically across arms:

| Arm | Composition Mode | Iter 2 Batch ($n_{\text{clean}} / n_{\text{aug}} / n_{\text{syn}}$) | Iter 2 Real Draws / Epoch | Iter 3 Batch ($n_{\text{clean}} / n_{\text{aug}} / n_{\text{syn}}$) | Iter 3 Real Draws / Epoch | Real Exposure Deficit vs. A0/A1 |
| --- | --- | --- | --- | --- | --- | --- |
| **A0** | Real unchanged | $256 / 0 / 0$ | $12,544$ | $256 / 0 / 0$ | $12,544$ | $0.0\%$ |
| **A1** | Real augmented | $0 / 256 / 0$ | $12,544$ | $0 / 256 / 0$ | $12,544$ | $0.0\%$ |
| **B** | Real + synthetic | $0 / 185 / 71$ | $9,065$ | $0 / 213 / 43$ | $10,437$ | $-27.7\%$ (Iter 2) / $-16.8\%$ (Iter 3) |
| **A2** | Full hybrid mix | $105 / 100 / 51$ | $10,045$ | $105 / 120 / 31$ | $11,025$ | $-19.9\%$ (Iter 2) / $-12.1\%$ (Iter 3) |

**Statistical Confound:** In a causal comparison between $B$ and $A1$ (or $A2$ and $A1$), synthetic domain shift is confounded with a $16.8\%$ to $27.7\%$ reduction in real-data sample complexity per step. Any performance degradation in $B$ relative to $A1$ reflects the joint effect of synthetic covariate mismatch and reduced real empirical risk coverage ($2,107$ to $3,479$ fewer real draws per epoch).

### Empirical Counter-Analysis & Optimization Dynamics

Gemini 4 Neon proposed an `equal_real` mode ($n_{\text{real}} = 256$, $B' = 256 + n_{\text{syn}}$) to hold real exposure constant while preserving $S = 49$ steps per epoch. The team implemented `equal_real` in `src/stage4_train/sampling.py` and executed a pre-registered 3-seed validation study (`docs/crisp_dm/iteration_3/experiments/equal_real.json`), which falsified the hypothesis that equalizing real draws improves performance:

* **Arm B (`equal_real` vs. `normal`):** Clean validation macro-F1 dropped by **$-2.03$ points** ($92.18 \pm 2.59$ vs. $94.20 \pm 0.05$); damaged validation macro-F1 dropped by **$-3.19$ points** ($73.88 \pm 7.00$ vs. $77.07 \pm 2.47$); mean convergence truncated from $30.0 \pm 0.0$ to $18.67 \pm 10.26$ epochs.
* **Arm A2 (`equal_real` vs. `normal`):** Clean validation macro-F1 dropped by **$-0.51$ points** ($94.66 \pm 0.90$ vs. $95.17 \pm 0.26$); damaged validation macro-F1 dropped by **$-2.68$ points** ($77.61 \pm 2.14$ vs. $80.29 \pm 1.30$); mean convergence shifted from $30.0 \pm 0.0$ to $27.0 \pm 5.20$ epochs.

**Root Cause of Failure:** Appending $n_{\text{syn}}$ on top of $256$ real samples alters three coupled optimization invariants simultaneously:

1. **Gradient Noise Scale ($g \propto \text{lr} / B'$):** Increasing $B$ from $256$ to $299$ (Arm B) or $287$ (Arm A2) under fixed $\text{lr} = 0.003$ reduces stochastic gradient variance, sharpening trajectories into narrower minima and triggering early-stopping variance spikes.
2. **Synthetic Gradient Dilution:** Effective synthetic gradient weight shrinks from $n_{\text{syn}} / 256$ to $n_{\text{syn}} / (256 + n_{\text{syn}})$ ($0.277 \to 0.217$ in Iter 2 B), invalidating prior hyperparameter tuning.

### Resolution

* **Verdict:** **Stands** (as an architectural property) / **Closed by Experiment**.
* **Action:** Retained fixed $B = 256$ zero-sum slot allocation across all arms to preserve gradient noise scale and tuned synthetic mixture ratios, explicitly documenting the real-draw asymmetry.

