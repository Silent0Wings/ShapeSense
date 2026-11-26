# 3_modeling - A06: One learning rate and dropout were shared by every arm.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A06 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage4_train/tuning.py, src/stage4_train/search.py, configs/pipeline.yaml, docs/crisp_dm/iteration_2/search/winners.json, results/phase2_snapshot/winners.json, results/phase2_snapshot/metrics.csv, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/js/pages/stage4.js


## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: One learning rate and dropout were shared by every arm.

## Response
Stage 4 appears to violate per-arm fairness by tuning optimizer and regularization hyperparameters on a single arm and reusing them globally across all arms:

1. In `src/stage4_train/tuning.py` (Decision 7), `run_tuning()` runs the `3 x 2` grid (`lr: [0.0003, 0.001, 0.003]` × `dropout: [0.2, 0.4]`) exclusively on `train.tuning.arm: A1` with `seed = 0` and writes a single global `winner` (`lr: 0.003, dropout: 0.2`) to `artifacts/stage4/tuning.json`.
2. In `configs/pipeline.yaml`, `train.lr` and `train.dropout` explicitly comment `"replaced by the Decision 7 grid winner (artifacts/stage4/tuning.json, A1 seed 0... lr 0.003, dropout 0.2)"`, and `train.tuning.arm` is still set to `A1`.
3. Because `A0` trains on unaugmented real images (`256` clean/step) while `B` and `A2` inject synthetic shapes (`19.8%` - `27.8%` in Iteration 2), sharing `A1`'s `lr = 0.003` and `dropout = 0.2` across every arm risks under-regularizing `A0` (which reaches `99.9%` train accuracy in `docs/crisp_dm/iteration_2/investigation/report.md`) or mis-scaling the step size for mixed real/synthetic arms.

**Recommended fix:** Run the `lr x dropout` grid independently for each arm (`A0`, `A1`, `B`, `A2`) on validation rather than copying `A1`'s `tuning.json` winner to all arms.

## Validation
- Team checked the active Iteration 2 search pipeline (`src/stage4_train/search.py#grid_specs`) and its saved results (`docs/crisp_dm/iteration_2/search/winners.json`) against `src/stage4_train/tuning.py`.
- While Gemini accurately read the **Iteration 1** behavior in `src/stage4_train/tuning.py` and the legacy `train.tuning` comment in `configs/pipeline.yaml` (and correctly noticed that `A1`, `B`, and `A2` all ended up at `lr = 0.003, dropout = 0.2`), it missed that **Iteration 2 had already replaced single-arm sharing with per-arm grid search** in `src/stage4_train/search.py#grid_specs`:
  - `A0` (`grid` 6 trials): `lr = 0.003, dropout = 0.4` scored `94.18` vs `93.91` for `dropout = 0.2` (3-seed confirmation mean `92.61`), so **`A0` actually ran with `dropout = 0.4`** in Iteration 2 (`docs/crisp_dm/iteration_2/search/winners.json`).
  - `A1` (`grid` 6 trials): `lr = 0.003, dropout = 0.2` scored `94.69` vs `93.70` at `0.4` (3-seed mean `94.77`).
  - `B` (`grid` 6 trials): `lr = 0.003, dropout = 0.2` scored `94.36` vs `93.82` at `0.4` (3-seed mean `94.20`).
  - `A2` (`grid` 6 trials): `lr = 0.003, dropout = 0.2` scored `95.31` vs `94.89` at `0.4` (3-seed mean `95.17`).
- Confirmed that `ShapeSense_Deployed/web/js/pages/stage4.js` (`tuningCard`) already documents this exact distinction: *"Iteration 1 tuned once on A1 and froze this for every arm; iteration 2 tuned each arm separately."* (And in Iteration 3's later 60-epoch search, `results/phase2_snapshot/winners.json` again ran a separate 6-point `lr x dropout` grid + 3-fold CV for all five arms, where every arm converged on `lr = 0.003, dropout = 0.2`.)

## Our decision
Verdict: **Does not stand**. Action: **No action**. Every arm was already tuned separately via `src/stage4_train/search.py#grid_specs`; the arms happened to independently select the same learning rate (`0.003`), and `A0`'s dropout winner (`0.4`) differed from `A1`, `B`, and `A2` (`0.2`) in Iteration 2.

## Measured effect
- Zero pipeline changes required (`State: No action` in `results/llm_comparison/gemini_audit.md`).
- Iteration 2 per-arm tuning grids (`6` `lr × dropout` trials per arm, `24` grid trainings total in `docs/crisp_dm/iteration_2/search/winners.json`) independently selected `lr = 0.003` for all four arms and `dropout = 0.4` for `A0` vs `0.2` for `A1`, `B`, and `A2`.

---

## Cross-Arm Hyperparameter Sharing vs. Per-Arm Grid Search (`A06`)

### Claim Metadata

* **Entry ID:** `A06` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `close-to-reality`
* **Grounding Artifacts:** `src/stage4_train/tuning.py`, `src/stage4_train/search.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/search/winners.json`, `results/phase2_snapshot/winners.json`

### Mechanistic & Audit Analysis

Gemini 4 Neon audited `src/stage4_train/tuning.py` (Decision 7) and stale comments in `configs/pipeline.yaml` (`train.tuning.arm: A1`), concluding that Stage 4 tuned $(\text{lr}, \text{dropout})$ exclusively on Arm `A1` ($\text{lr} = 0.003, \text{dropout} = 0.2$) and broadcast those values to `A0`, `B`, and `A2`. Under this premise, unaugmented `A0` (which reaches $99.9\%$ training accuracy) would suffer from under-regularization, while mixed arms `B` and `A2` would use miscalibrated step sizes.

### Verification Against Active Search Pipeline

Codebase inspection confirmed that `src/stage4_train/tuning.py` was a deprecated **Iteration 1** artifact. Beginning in **Iteration 2**, `src/stage4_train/search.py#grid_specs` executed independent $3 \times 2$ grids ($\text{lr} \in \{0.0003, 0.001, 0.003\} \times \text{dropout} \in \{0.2, 0.4\}$, $24$ grid runs total) for each arm individually (`docs/crisp_dm/iteration_2/search/winners.json`):

* **Arm A0:** Selected $\text{lr} = 0.003, \mathbf{\text{dropout} = 0.4}$ ($94.18$ val macro-F1 vs. $93.91$ at $\text{dropout} = 0.2$; 3-seed confirmation mean $92.61$), directly applying higher regularization to the unaugmented arm.
* **Arm A1:** Selected $\text{lr} = 0.003, \text{dropout} = 0.2$ ($94.69$ vs. $93.70$; 3-seed mean $94.77$).
* **Arm B:** Selected $\text{lr} = 0.003, \text{dropout} = 0.2$ ($94.36$ vs. $93.82$; 3-seed mean $94.20$).
* **Arm A2:** Selected $\text{lr} = 0.003, \text{dropout} = 0.2$ ($95.31$ vs. $94.89$; 3-seed mean $95.17$).

In Iteration 3 (`results/phase2_snapshot/winners.json`), a separate 6-point grid plus 3-fold grouped CV was again executed per arm across all five arms, where all arms independently converged on $\text{lr} = 0.003, \text{dropout} = 0.2$.

### Resolution

* **Verdict:** **Does Not Stand** (false premise caused by legacy Iteration 1 module and config comments).
* **Action:** **No action** required on pipeline execution.

