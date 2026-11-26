# 3_modeling - C29: Training budget
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C29 (`change`, `3_modeling`)
- Owner / Proposed by: 40297573 / 40297573
- Calibration: `close-to-reality (30% tier)`
- Grounding sources: ShapeSense/docs/crisp_dm/iteration_3/experiments/budget.json, ShapeSense/docs/crisp_dm/iteration_3/preregistration.md, ShapeSense/src/stage4_train/experiments.py, ShapeSense/src/stage4_train/search.py, ShapeSense/configs/pipeline.yaml, ShapeSense/configs/models/A0.yaml, ShapeSense/configs/models/P.yaml, ShapeSense_Deployed/web/experiments.html


## Prompt
We pre-registered that a longer budget is adopted only if each tested arm gains at least 0.5 validation points. Here are the gains at 60 epochs with no early stopping. Does the rule say we switch, and how do we apply it to every arm?

## Response
Looking at `docs/crisp_dm/iteration_3/experiments/budget.json`, the three tested arms show the following 3-seed mean clean validation macro-F1 gains over the iteration 2 baseline (`e30`, 30 epochs with early stopping):
- **`e60` (with early stopping):** `A0 -3.37`, `A1 -1.53`, `A2 -1.02` (mean epochs run dropped to `12.7`, `21.0`, `27.7` - confirming early stopping fires destructively under high-variance `lr = 0.003` curves).
- **`e30_nostop`:** `A0 +1.76`, `A1 0.00`, `A2 0.00` (fails the `+0.5` rule on `A1` and `A2`).
- **`e60_nostop`:** `A0 +1.99` (`92.61 -> 94.59`), `A1 +0.51` (`94.77 -> 95.28`), `A2 +0.71` (`95.17 -> 95.88`).

### Does the rule say we switch?
Technically, every tested arm cleared `ADOPT_GAIN = 0.5` (`A1` cleared by `+0.006` points: `0.506 >= 0.5`). However, `A1`'s `+0.006` margin is smaller than its 3-seed standard deviation (`0.10` - `0.12` points), and `B` and `P` were not part of `BUDGET_ARMS`. Before locking in `e60_nostop` for all five arms, the prudent step is to run the same `e60_nostop` check on `B` and `P` (or keep `early_stopping_patience` at a safer `20` rather than `999`) to verify `B` and `P` also gain `>= 0.5` points before applying the 2x compute increase across the whole search and final sweep.

### How to apply a shared budget to every arm
Once confirmed, apply it uniformly through `configs/pipeline.yaml#train` (`max_epochs: 60`, `early_stopping_patience: 999`) and `src/stage4_train/search.py#adopted_budget()` (which injects `BUDGET_CHOICES[adopted]` into every search phase's base overrides - `A0`, `A1`, `B`, `A2`, and `P` - while leaving `CV_EPOCHS = 15` fixed for the 3-fold CV stage).

## Validation
`40297573` and the team checked Gemini 4 Neon's caution against the pre-registered contract (`docs/crisp_dm/iteration_3/preregistration.md`) and `src/stage4_train/experiments.py`:
1. **Strict pre-registered threshold check (`experiments.py#L234-L236`):** The pre-registered rule explicitly tested `BUDGET_ARMS = ("A0", "A1", "A2")` with a deterministic cutoff `all(g >= ADOPT_GAIN for g in by_arm.values())` (`ADOPT_GAIN = 0.5`), specifically to prevent post-hoc judgment calls or extra un-registered tests after seeing results. Since `min(1.9895, 0.5061, 0.7132) = 0.5061 >= 0.5`, `budget.json` recorded `"adopted": "e60_nostop"`. Adding an ad-hoc `B`/`P` gate or changing `patience: 999` to `20` would have violated the pre-registration.
2. **Scoring repeatability (commit `52e79e1`):** Scoring all 108 validation experiment trials twice produced byte-identical numbers in `budget.json`, confirming `A1`'s `+0.506` gain was exact and reproducible.
3. **Config propagation (`commit e9fd141`):** `configs/pipeline.yaml` froze `train.max_epochs: 60` and `train.early_stopping_patience: 999`, `configs/models/*.yaml` propagated `early_stopping: false` and `max_epochs: 60` to all five arms (`A0`, `A1`, `B`, `A2`, `P`), and `search.py#adopted_budget()` applied `e60_nostop` to all `5` arms in the search and final `25` main + `15` LOSO runs.

## Our decision
Followed the pre-registered rule strictly: **switched all five arms (`A0`, `A1`, `B`, `A2`, `P`) immediately to `60` epochs with no early stopping (`early_stopping_patience: 999`)** and **rejected** Gemini 4 Neon's suggestion to run an extra `B`/`P` check or lower patience to `20`.

## Measured effect
- **Budget experiment (`budget.json`):** `e60_nostop` gained `+1.99` (`A0`: `92.61 -> 94.59`), `+0.51` (`A1`: `94.77 -> 95.28`), and `+0.71` (`A2`: `95.17 -> 95.88`) clean validation macro-F1 points over `e30`, while `e60` with early stopping lost `-3.37`, `-1.53`, and `-1.02` points.
- **Perturbed validation (`budget.json`):** `A1` (`77.73 -> 78.63`) and `A2` (`80.29 -> 80.58`) also improved on damaged validation, while `A0` (`68.42` at `e30_nostop`, `67.39` at `e60_nostop`) remained weak under damage.
- **Uniform schedule across all 5 final arms (`metrics.csv`, `stage4.html`):** All 25 final seed models and 15 LOSO runs trained for the exact `60` epochs (`2,940` optimizer steps per run), eliminating early-stop variance (`F11`) and lifting 5-seed validation macro-F1 means to `A0 94.33`, `A1 95.27`, `B 95.12`, `A2 95.82`, `P 95.22`.

---

## : Gemini 4 Neon Corpus Synthesis (`C29` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C29` (`change`)
* **Logic Depth:** **High** (applies `C27`'s pre-registered budget gate across `A0`, `A1`, `A2`; constrains `C26` CV horizon and resolves `F11`/`A07`)
* **Risk if Wrong:** **High** (`A1` cleared the `+0.50` bar by `+0.006`, smaller than its 3-seed SD; altering the rule post-hoc would violate pre-registration)
* **Adoption Status:** **Adopted rule strictly (`e60_nostop` for all 5 arms); rejected post-hoc modifications** (rejected Gemini's suggestion to run an extra `B`/`P` check or lower patience to `20` because `BUDGET_ARMS = (A0, A1, A2)` was fixed before execution).

### 2. Group Synthesis: Search Design and the Budget Gate (`C26` $\rightarrow$ `C12` $\rightarrow$ `C25` $\rightarrow$ `C29`, `C27`)

* **`C29`** is the entry where pre-registration stops being a slogan and costs the team an extra check they might otherwise have wanted to run. Under `C27`'s rule, `e60_nostop` gained `A0 +1.99`, `A1 +0.51` (`+0.506` exact), and `A2 +0.71` (`min = 0.506 >= 0.5`), whereas `e60` *with* early stopping active lost `-3.37`, `-1.53`, and `-1.02` points due to the wider cosine LR curve (`A07`).
* Scoring all 108 validation experiment trials twice produced byte-identical numbers, confirming the `+0.506` margin was exact and locking `max_epochs: 60` and `early_stopping_patience: 999` for the entire 191-trial Iteration 3 search and 40-run final retrain.

