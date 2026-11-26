# 3_modeling - C11: Synthetic share of a batch
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/22_C11_synthetic-share-of-a-batch.md](../claude_opus/22_C11_synthetic-share-of-a-batch.md)
- Date: 2026-11-09
- Entry: C11 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/sampling.py`, `src/stage4_train/search.py`, `src/stage4_train/train.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_2/data/stage4_status.json`, `docs/crisp_dm/iteration_2/report/changes.tex`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage4.html`, commits `87711f3`, `5acfb7c`


## Prompt
Follow-up on the iteration 2 search. B has used `synthetic_fraction: 0.3` since the Phase 1 plan, and the new A2 arm also needs a synthetic share. Part of the team wants to keep 30% for B so it stays the arm we pre-registered in iteration 1; Gemini 4 Neon wants the share searched on validation per arm, together with the generator ranges. Which should we do, and how do we report the share so nobody misreads it?

## Response
Do **not** lock `synthetic_fraction` at the Iteration 1 hand-picked `0.3` (`30%`) for `B` and `A2`. Because `B` replaces augmented real images directly with synthetic images while `A2` splits each 256-image batch three ways (`clean real` + `augmented real` + `synthetic`), a single fixed share will favor one mix over the other and conflates architecture/pipeline differences with an arbitrary mixing ratio.

### 1. Search the synthetic share per arm on validation
In `src/stage4_train/search.py`, keep `steps_per_epoch = 49` and `batch_size = 256` identical across all arms, and search the shares independently on validation:
- **Arm `B` (`sample_synth`):** Search `arms.B.synthetic_fraction` over `[0.1, 0.5]` alongside the Stage 3 generator parameters (`16` trials).
- **Arm `A2` (`sample_shares`):** Search `(arms.A2.clean_fraction, arms.A2.synthetic_fraction)` over `clean` in `[0.1, 0.6]` and `synthetic` in `[0.1, 0.4]` subject to `clean + synthetic <= 0.8` (`12` trials), ensuring at least `20%` of every `A2` batch remains augmented real images.
- Confirm the top 5 settings per arm over 3 validation seeds (`[0, 1, 2]`) and freeze the winners in `configs/pipeline.yaml#arms`.

### 2. Report both configured shares and realized integer batch counts
In `src/stage4_train/sampling.py`, `batch_composition(arm_cfg, batch_size, synthetic_fraction)` computes:
```python
n_syn = int(round(batch_size * share))
n_real = batch_size - n_syn
```
and `clean_count(arm_cfg, batch_size)` computes `n_clean = int(round(batch_size * clean_fraction))`. Because `round(256 * share)` snaps to an integer image count per batch, the realized fraction (`n_syn / 256`) differs slightly from the configured decimal (e.g., `0.278 * 256 = 71.168 -> 71`, which is `71 / 256 = 0.27734375`). Report **both**:
1. The exact configured fractions (`arms.<ARM>.synthetic_fraction`, `arms.A2.clean_fraction`), and
2. The realized integer image counts per 256-image batch (`n_clean`, `n_real - n_clean`, `n_syn`) plus `realized_synthetic_share` logged by `train_one` in `run.json`.

## Validation
- Verified in `src/stage4_train/sampling.py` (`batch_composition`, `clean_count`, `raw_batch`) and `src/stage4_train/train.py` (`train_one` logging `realized_synthetic_share`, `real_draws_per_step`, `clean_per_step`, `synthetic_per_step`) that every batch matches `n_clean + (n_real - n_clean) + n_syn == 256` and `n_syn / 256` matches `run.json`.
- Inspected `docs/crisp_dm/iteration_2/search/winners.json` and `docs/crisp_dm/iteration_2/data/stage4_status.json`:
  - Arm `B` winner: configured `synthetic_fraction: 0.278` (`27.8%`), realized `71` synthetic + `185` augmented real of `256` (`realized_synthetic_share = 0.27734375` = `27.73%`).
  - Arm `A2` winner: configured `clean_fraction: 0.411` and `synthetic_fraction: 0.198` (`19.8%`), realized `105` clean real + `100` augmented real + `51` synthetic of `256` (`realized_synthetic_share = 0.19921875` = `19.92%`).
- Checked the outside review point (`results/phase2_snapshot/iteration_log.json`, `Synthetic shares are rounded differently from the real batch`), confirming the configured vs realized rounding distinction is accurately disclosed.

## Our decision
Replaced the fixed `30%` share with per-arm validation search and adopted the dual reporting convention (configured percentage plus realized integer count out of `256` images) across `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/report/changes.tex`, `iteration_log.json`, and `ShapeSense_Deployed/web/stage4.html` (`recipeBars`). Kept the same per-arm search rule in Iteration 3.

## Measured effect
- **Iteration 2 (`docs/crisp_dm/iteration_2/search/winners.json`):** `B` shifted from `30%` (`77 / 256`) to **71 of 256** (`27.8%` configured, `27.73%` realized, val macro-F1 `94.20`); `A2` settled at **105 clean + 100 augmented + 51 synthetic of 256** (`19.8%` synthetic configured, `19.92%` realized, val macro-F1 `95.17`).
- **Iteration 3 (`configs/pipeline.yaml`, `configs/models/B.yaml`, `configs/models/A2.yaml`):** Re-running the per-arm validation search at 60 epochs with grouped 3-fold CV updated the shares to **B: 43 of 256** (`0.168` configured, `0.16796875` realized) and **A2: 105 clean + 120 augmented + 31 synthetic of 256** (`0.12` synthetic configured), with `A2` achieving `+9.20` damaged macro-F1 over `A0` (`95% CI [8.89, 9.53]`).

---

## : Gemini 4 Neon Corpus Synthesis (`C11` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `C11` (`change`)
* **Logic Depth:** **Medium** (per-arm synthetic share search + dual continuous/integer reporting, coupled with `F06` and `A10`)
* **Risk if Wrong:** **Medium** (configured vs. realized rounding: `71/256 = 27.73%`, not `27.8%`; `51/256 = 19.92%`, not `19.8%`)
* **Adoption Status:** **Adopted verbatim** (per-arm share search on validation + dual reporting of configured decimal and realized integer count out of `256`).

### 2. Group Synthesis: Tuning Fairness (`C12`, `F06`, `C11`, `T15`, `T23`)

* **`C11`** establishes the reporting discipline for batch mixture shares: never trust the configured decimal alone; log both the configured fraction and the realized integer count out of `256` (`round(256 * share)`). Its worked example matches the precision check in `A10` and `12_real`: Iteration 2 `B` configured `0.278` $\rightarrow$ realized `71/256 = 27.73%`; `A2` configured `0.198` $\rightarrow$ realized `51/256 = 19.92%`. Iteration 3 updated `B` to `43/256` (`0.168`) and `A2` to `31/256` (`0.120`).
* Paired with **`C12`** (per-arm `lr`/`dropout` grid) and **`F06`** (staged per-arm augmentation/generator search), `C11` removes the arbitrary `30%` Iteration 1 hand-set constraint while keeping every arm's batch composition auditable in `configs/models/*.yaml` and `stage4.html` (`recipeBars`).

