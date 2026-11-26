# 3_modeling - A07: Early stopping can end runs before the schedule finishes.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A07 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/train.py, configs/pipeline.yaml, docs/crisp_dm/iteration_2/data/stage4_status.json, docs/crisp_dm/iteration_3/experiments/budget.json, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/failures.html


## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Early stopping can end runs before the schedule finishes.

## Response
In `src/stage4_train/train.py`, `train_one` constructs a single `CosineAnnealingLR` schedule tied to the full epoch budget (`T_max = max_epochs * steps_per_epoch`, stepping once per optimizer step), while simultaneously tracking validation macro-F1 (`val_macro_f1`) and breaking out of the training loop whenever `wait >= patience` (`early_stopping_patience`). This creates two coupled failure modes:

1. **Schedule truncation and unequal effective training horizons.** When early stopping triggers before `max_epochs` (30 epochs in the current sweep, 49 steps/epoch), the run halts mid-schedule while the cosine learning rate is still elevated, rather than decaying smoothly to zero. Worse, different seeds and arms can stop at very different epochs (`epochs_run` varies per run), which breaks the equal-compute symmetry intended by Decision 13 (`steps_per_epoch = 49` frozen across arms).
2. **High-variance validation swings at `lr = 0.003`.** Under `AdamW` at `lr = 0.003`, single-epoch validation macro-F1 fluctuates sharply early in training before BatchNorm statistics and weights settle. A brief early spike at epoch 5-8 sets a high `best_score` threshold, causing `wait` to exhaust patience during the normal consolidation dip and terminating runs around epochs 10-15 - well before the cosine schedule finishes.

Because this affects runs stochastically across seeds and arms, early stopping is likely truncating a large share of runs across the sweep and distorting arm means. I recommend setting `train.early_stopping_patience` to disable early stopping immediately (or decoupling `T_max` and lowering the trigger frequency) so every arm completes the full cosine trajectory.

## Validation
The team audited `src/stage4_train/train.py` (`train_one`, lines 376-480) alongside the recorded Iteration 2 run logs in `docs/crisp_dm/iteration_2/data/stage4_status.json` and `docs/crisp_dm/iteration_2/investigation/report.md`:
- Across the 20 main runs (`A0`, `A1`, `B`, `A2` across seeds `0..4`), **17 of 20 runs used all 30 epochs**. Only 3 main runs stopped early: `A0_1` (`best_epoch: 5`, `epochs_run: 10`, `val_macro_f1: 89.21`), `A1_4` (`best_epoch: 8`, `epochs_run: 13`, `val_macro_f1: 92.03`), and `B_3` (`best_epoch: 24`, `epochs_run: 29`, `val_macro_f1: 94.56`).
- All 5 runs of `A2` and 4 of 5 runs for each of `A0`, `A1`, and `B` completed the full 30-epoch schedule (`1,470` optimizer steps), so the claim that truncation was pervasive across most main runs only held **partly** (though leave-one-source-out runs stopped early more frequently, and `A0_1` / `A1_4` clearly suffered from the `lr = 0.003` validation swing).
- Later, in Iteration 3 (`src/stage4_train/experiments.py` and `docs/crisp_dm/iteration_3/experiments/budget.json`), the team ran a controlled 27-run validation experiment comparing 30 epochs, 60 epochs with early stopping (`e60`), and 60 epochs with early stopping disabled (`e60_nostop`, `early_stopping_patience: 999`).

## Our decision
- **Iteration 2 verdict: `Partly` (`Disclosed`).** The team confirmed the mechanism Gemini 4 Neon flagged (`wait >= patience` halting `CosineAnnealingLR` mid-schedule, notably on `A0_1` and `A1_4`), while noting that Gemini overstated its prevalence on the main sweep (17 of 20 main runs reached epoch 30, and every arm shared the same stopping rule). Iteration 2 results were kept intact and the 3 early-stopped main runs were disclosed.
- **Iteration 3 follow-up:** Informed by this finding and the `budget.json` experiment, Iteration 3 pre-registered the `0.5`-point adoption rule and moved `configs/pipeline.yaml#train` to `max_epochs: 60` and `early_stopping_patience: 999` (no early stopping).

## Measured effect
- **Iteration 2 main sweep (`stage4_status.json`):** 17/20 main runs ran 30 epochs; 3 stopped early (`A0` seed 1: 10 epochs, 89.21 val macro-F1; `A1` seed 4: 13 epochs, 92.03; `B` seed 3: 29 epochs, 94.56).
- **Iteration 3 validation budget test (`budget.json`, 3 seeds per arm):** Keeping early stopping at 60 epochs (`e60`) *dropped* clean val macro-F1 vs `e30` (`A0: -3.37`, `A1: -1.53`, `A2: -1.02` points), whereas `e60_nostop` gained `+1.99` (`A0`), `+0.51` (`A1`), and `+0.71` (`A2`) points - all clearing the `0.5`-point adoption threshold. Every Iteration 3 run completed all 60 epochs (`2,940` steps).

---

## Coupling Between Early Stopping and Cosine Annealing Horizon ($T_{\max}$) (`A07`)

### Claim Metadata

* **Entry ID:** `A07` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `close-to-reality (30% tier)`
* **Grounding Artifacts:** `src/stage4_train/train.py`, `docs/crisp_dm/iteration_2/data/stage4_status.json`, `docs/crisp_dm/iteration_3/experiments/budget.json`, `configs/pipeline.yaml`

### Mechanistic & Optimization Analysis

In `src/stage4_train/train.py#train_one`, `CosineAnnealingLR` is parameterized with $T_{\max} = E_{\max} \cdot S$ ($30 \times 49 = 1,470$ steps in Iteration 2):

$$\eta_t = \eta_{\min} + \frac{1}{2}(\eta_0 - \eta_{\min})\left(1 + \cos\left(\frac{\pi t}{T_{\max}}\right)\right)$$

Simultaneously, an early-stopping monitor checks validation macro-F1 every epoch and halts training when `wait >= early_stopping_patience`. This coupling introduces two failure modes:

1. **Elevated-LR Termination:** When early stopping triggers at step $t_{\text{stop}} \ll T_{\max}$, optimization aborts while $\eta_t$ remains near $\eta_0 = 0.003$, preventing fine-grained convergence in the cosine decay tail and breaking equal-compute symmetry ($S \cdot E_{\max}$) across seeds.
2. **Transient Spike Lock-In:** High initial step size ($\eta_0 = 0.003$) induces high-variance validation oscillations during early BatchNorm stabilization (epochs $5$–$8$). A transient validation spike sets an artificially high `best_score` threshold, exhausting `patience` during normal weight consolidation and terminating runs prematurely.

### Empirical Validation & Iteration 3 Redesign

1. **Iteration 2 Audit (`stage4_status.json`):** Across 20 main sweep runs ($4 \text{ arms} \times 5 \text{ seeds}$), $17/20$ completed all 30 epochs ($1,470$ steps). However, $3$ runs suffered premature truncation: `A0_1` (`best_epoch: 5`, `epochs_run: 10`, val macro-F1 $89.21$), `A1_4` (`best_epoch: 8`, `epochs_run: 13`, val macro-F1 $92.03$), and `B_3` (`best_epoch: 24`, `epochs_run: 29`, val macro-F1 $94.56$).
2. **Iteration 3 Controlled Budget Experiment (`budget.json`, 27 runs):** Comparing 30 epochs (`e30`), 60 epochs with early stopping (`e60`), and 60 epochs without early stopping (`e60_nostop`, `patience = 999`) revealed that extending $T_{\max}$ to 60 epochs *with* early stopping degraded validation macro-F1 because a wider cosine curve stayed at high $\eta_t$ longer, amplifying early validation spikes:
   * `e60` (early stopping active) vs. `e30`: **A0: $-3.37$ pts**, **A1: $-1.53$ pts**, **A2: $-1.02$ pts**.
   * `e60_nostop` (full cosine trajectory) vs. `e30`: **A0: $+1.99$ pts**, **A1: $+0.51$ pts**, **A2: $+0.71$ pts** (all exceeding the pre-registered $+0.50$-point adoption threshold).

### Resolution

* **Verdict:** **Partly** (mechanism confirmed; Iteration 2 sweep prevalence was limited to $3/20$ runs, though severe on `A0_1` and `A1_4`).
* **Action:** Iteration 2 records were disclosed as-is; Iteration 3 updated `configs/pipeline.yaml` to `max_epochs: 60` and `early_stopping_patience: 999` so every run completes all $2,940$ optimizer steps.

