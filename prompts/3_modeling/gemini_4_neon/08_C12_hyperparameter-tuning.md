# 3_modeling - C12: Hyperparameter tuning
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/23_C12_hyperparameter-tuning.md](../claude_opus/23_C12_hyperparameter-tuning.md)
- Date: 2026-11-09
- Entry: C12 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/search.py`, `src/stage4_train/sweep.py`, `src/stage4_train/tuning.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_2/data/stage4_status.json`, `results/phase2_snapshot/winners.json`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage4.html`, commits `87711f3`, `5acfb7c`


## Prompt
In iteration 1 we ran the Decision 7 grid (learning rate 0.0003, 0.001, 0.003 by dropout 0.2, 0.4) on A1 seed 0 only, got lr 0.003 and dropout 0.2 at 90.44 validation macro-F1, and gave that to every arm. Some of us say a single shared setting is the cleanest design, because then only the data differs between arms. Gemini 4 Neon says each arm needs its own tuning, or the arm we tuned on is favoured. Who is right, and if we tune per arm, how do we keep it fair and how do we report the chosen values?

## Response
Reusing `A1`'s Decision 7 grid winner (`lr = 0.003, dropout = 0.2`) across `A0`, `B`, and `A2` violates equal-opportunity hyperparameter tuning (Melis et al., 2018; Bouthillier et al., 2021). In particular, `A0` trains on unchanged real drawings (reaching `99.9%` training accuracy and overfitting faster), whereas `A1`, `B`, and `A2` already receive strong regularization from geometric/pixel augmentation and synthetic variation. Giving every arm its own validation tuning grid prevents `A1`'s optimizer settings from biasing the comparison.

### Per-arm tuning protocol (validation only)
1. **Equal grid per arm (`src/stage4_train/search.py#grid_specs`):** Evaluate the exact same `3 x 2` Cartesian grid - `GRID_LR = (0.0003, 0.001, 0.003)` and `GRID_DROPOUT = (0.2, 0.4)` (`6` runs per arm on seed `0`, frozen `steps_per_epoch = 49`) - independently on each arm's best data/augmentation configuration (`A0`, `A1`, `B`, `A2`, and `P` in Iteration 3).
2. **Strict validation selection:** Select the winning `(lr, dropout)` for each arm exclusively by `val_macro_f1` (never touching `test.csv` or `fresh_holdout*.csv`), then feed each arm's top candidates into the 3-seed confirmation (`seeds = [0, 1, 2]`).
3. **Per-arm config wiring (`configs/pipeline.yaml` & `src/stage4_train/sweep.py`):** Store `hparams: { lr: ..., dropout: ... }` under `configs/pipeline.yaml#arms.<ARM>`, and have `job_specs` resolve `hp_for(arm)` via `config["arms"][arm].get("hparams") or hparams` so every seed of an arm trains with that arm's tuned pair.
4. **Reporting:** Report (a) the full 6-point validation `val_macro_f1` grid per arm (`winners.json#grid`), (b) the total `trials_per_arm`, and (c) each arm's frozen `(lr, dropout)` explicitly in `stage4_status.json#metrics.arm_hparams`, `changes.tex`, and the Stage 4 dashboard table (`ShapeSense_Deployed/web/stage4.html`), explicitly noting whenever two arms independently converge on the same values.

## Validation
- Ran the `6`-point `(lr, dropout)` grid independently for each arm in `src/stage4_train/search.py` (`docs/crisp_dm/iteration_2/search/winners.json`) and verified `sweep.py#job_specs` passed each arm's own `hparams` to all 5 final seeds (`docs/crisp_dm/iteration_2/data/stage4_status.json#metrics.arm_hparams`).
- Verified the per-arm Iteration 2 winners:
  - `A0`: `lr = 0.003, dropout = 0.4` (`94.18` vs `93.91` at `dropout = 0.2`)
  - `A1`: `lr = 0.003, dropout = 0.2` (`94.69` vs `93.70` at `dropout = 0.4`)
  - `B`: `lr = 0.003, dropout = 0.2` (`94.36` vs `93.82` at `dropout = 0.4`)
  - `A2`: `lr = 0.003, dropout = 0.2` (`95.31` vs `94.89` at `dropout = 0.4`)
- Rejected the outside review claim `"One learning rate and dropout were shared by every arm"` (`Does not stand` in `iteration_log.json`), citing the per-arm grid logs and `A0`'s distinct `dropout = 0.4` winner.

## Our decision
Adopted per-arm validation tuning for `lr` and `dropout` across all arms and persisted per-arm `hparams` in `configs/pipeline.yaml` (`train.tuned: true` in `src/stage4_train/run.py`) and `configs/models/*.yaml`. Retained the identical per-arm `3 x 2` grid rule in Iteration 3 (`results/phase2_snapshot/winners.json`).

## Measured effect
- **Iteration 2 (`docs/crisp_dm/iteration_2/search/winners.json`):** Per-arm tuning separated `A0` (`lr = 0.003, dropout = 0.4`, `+0.27` validation macro-F1 over `dropout = 0.2` on seed 0) from `A1`, `B`, and `A2` (`lr = 0.003, dropout = 0.2`), removing tuning-budget bias in `(lr, dropout)` while keeping equal `49`-step training compute across all arms.
- **Iteration 3 (`results/phase2_snapshot/winners.json`, `status4.json`):** Re-tuning every arm at the 60-epoch budget (`A0: 6`, `A1: 30`, `B: 22`, `A2: 34`, `P: 18` search trials) gave `lr = 0.003, dropout = 0.2` for all five arms after 3-fold grouped CV and 3-seed confirmation (even though on `A0` seed 0 alone `dropout = 0.4` scored `94.58` vs `94.14`, CV/confirmation selected `dropout = 0.2` with 3-seed mean `94.19`).

---

## : Gemini 4 Neon Corpus Synthesis (`C12` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C12` (`change`)
* **Logic Depth:** **High** (per-arm $3 \times 2$ `(lr, dropout)` grid, feeds `C26` top-5 grouped CV and refutes `A06`)
* **Risk if Wrong:** **High** (shared hyperparameters tuned on `A1` bias the comparison against unaugmented `A0` and synthetic-mixed `B`/`A2`)
* **Adoption Status:** **Adopted verbatim** (per-arm $3 \times 2$ grid and per-arm `hparams` wiring in `configs/pipeline.yaml`; outside audit claim `A06` that "one LR and dropout were shared" rejected as **Does not stand**).

### 2. Group Synthesis: Tuning Fairness (`C12`, `F06`, `C11`, `T15`, `T23`)

* **`C12`** answers "one shared `(lr, dropout)` or per-arm?" with per-arm, citing Melis 2018 / Bouthillier 2021. In Iteration 2, per-arm tuning separated `A0` (`dropout 0.4`) from `A1`/`B`/`A2` (`dropout 0.2`), all at `lr 0.003`. In Iteration 3, after 3-fold `phash_group` CV (`C26`) and 3-seed confirmation at 60 epochs, all five arms (`A0`, `A1`, `B`, `A2`, `P`) converged on `dropout 0.2` (even though `A0` seed 0 alone preferred `0.4` at `94.58` vs. `94.14`) — showing directly how grouped CV overrides a noisy single-seed grid preference.
* **`F06`** and **`C11`** extend the same equal-procedure fairness rule to data-stream ranges and synthetic batch fractions, while **`T15` / `T23`** preserve the Iteration 1 Decision 7 provenance as comment-only config annotations without invalidating `recipe_fingerprint`.

