# 3_modeling - F06: Augmentation and generator ranges were set by hand, and only A1 was tuned.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/17_F06_augmentation-and-generator-ranges-were-set-b.md](../claude_opus/17_F06_augmentation-and-generator-ranges-were-set-b.md)
- Date: 2026-11-09
- Entry: F06 (`failure`, `3_modeling`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/search.py`, `src/stage4_train/tuning.py`, `configs/pipeline.yaml`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/search/winners.json`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage4.html`, `ShapeSense_Deployed/web/experiments.html`, commits `7f356d6`, `87711f3`, `5acfb7c`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt

> **User:** In Iteration 1 we tuned learning rate and dropout on arm A1 only and reused that winner for A0 and B, while setting all augmentation and synthetic generator ranges by hand. Is that a fair comparison given tuning-budget bias (Melis et al. 2018; Bouthillier et al. 2021), and how should we structure a per-arm search on validation only?

## Response
No - tuning hyperparameters on one arm (`A1`) and freezing them across arms with different training distributions is a classic **tuning-budget bias** (Melis et al., 2018; Bouthillier et al., 2021). When `A0` sees only clean real drawings, `A1` sees 100% augmented real drawings, `B` mixes augmented real and synthetic shapes, and `A2` mixes clean real, augmented real, and synthetic shapes, optimal regularization and step sizes differ by data stream. At the same time, blaming *only* the data or *only* the optimizer misses the interaction: in Iteration 1, hand-set `augment.rotate_deg: 180` and uncalibrated `synth.*` parameters crippled `A1` and `B`, while `A0` had no chance to tune `dropout` for unaugmented memorization risk.

To remove tuning bias while keeping every choice strictly off sealed data, design a compute-intensive, **validation-only** per-arm search (`src/stage4_train/search.py`) locked by `docs/crisp_dm/iteration_2/preregistration.md` (fixed seed `20261109`, frozen `steps_per_epoch: 49`):
1. **Staged search spaces per arm (never touching `test.csv` or `fresh_holdout.csv`):**
   - `A1` (`sample_augment`): 24 random trials over `augment.rotate_deg` (`{0, 5, 10, 15, 20, 30, 45, 90, 180}`), `augment.scale`, `augment.nonuniform_scale`, `augment.shear_deg`, `augment.translate_px`, `augment.noise_p`, `augment.blur_p`, and `taxonomy.rotate_limit_deg` for `{square, rectangle, diamond}` (`{None, 0, 5, 10, 15, 30}`), plus the 15-run single-factor ablation (`3 seeds`).
   - `B` (`sample_synth`): 16 random trials over `arms.B.synthetic_fraction` (`[0.1, 0.5]`) and `synth.*` geometry ranges (`radius_px`, `center_jitter_px`, `vertex_jitter_px`, `ellipse_max_axis_ratio`, `rectangle_max_side_ratio`, `diamond_acute_angle_deg`, `star_inner_ratio`, never violating `taxonomy.ambiguity_margins`).
   - `A2` (`sample_shares`): 12 random trials over `clean_fraction` (`[0.1, 0.6]`) and `synthetic_fraction` (`[0.1, 0.4]`) subject to `clean + synthetic <= 0.8`.
2. **Per-arm `(lr, dropout)` grid:** Run the full `3 x 2` grid (`lr` in `[0.0003, 0.001, 0.003]`, `dropout` in `[0.2, 0.4]`) independently for **each** arm (`A0`, `A1`, `B`, `A2` = 24 runs) on its best pipeline configuration.
3. **Multi-seed confirmation:** Re-run each arm's top 5 distinct configurations across `seeds = [0, 1, 2]` (`60` runs), freeze the winner per arm strictly by mean `val_macro_f1`, and disclose the exact `trials_per_arm` in `winners.json`. Expect roughly 160+ models (~1.5-2 GPU-days at the unoptimized single-worker rate before Iteration 3's prep-pool speedup).

## Validation
- Executed the pre-registered validation-only search (`166` trials in Iteration 2) in `src/stage4_train/search.py`, verifying zero test-split reads (`test_access.log` unchanged).
- Recorded every arm's grid and 3-seed confirmation in `docs/crisp_dm/iteration_2/search/winners.json` (`trials_per_arm`: `A0: 6`, `A1: 30`, `B: 22`, `A2: 18` for the arm-specific search + grid phases, with ablation and 3-seed confirmation bringing the total to `166` trials).
- Verified via outside code review (`results/phase2_snapshot/iteration_log.json`) that per-arm `(lr, dropout)` tuning held, while disclosing that `B` and `A2` inherited the augmentation parameters searched on `A1` in Iteration 2 (addressed further in Iteration 3 by also searching `synth_a2` separately and adding 3-fold grouped CV over train+val).

## Our decision
Adopted the full per-arm validation search protocol mediated from Gemini 4 Neon's compute-heavy proposal (`docs/crisp_dm/iteration_2/preregistration.md`, `src/stage4_train/search.py`), settling the team split between data-focused and training-focused hypotheses through empirical per-arm search. In Iteration 3, the team retained the per-arm search structure, added separate `synth_a2` (`16` trials) and `pretrain` (`12` trials for arm `P`) searches plus grouped 3-fold CV confirmation (`191` trained runs + `9` reused = `200`).

## Measured effect
- **Iteration 2 validation macro-F1 (3 seeds, `docs/crisp_dm/iteration_2/search/winners.json`):** `A1` rose from `90.64` (hand-set ranges, `±180°`) to `94.77`; full arm means reached `A2 95.17`, `A1 94.77`, `B 94.20`, `A0 92.61` across `166` validation trials.
- **Iteration 2 tuned winners:** `A1` settled on `rotate_deg: 20` (capped at `±10°` for `square`, `rectangle`, `diamond`), `B` on `synthetic_fraction: 0.278`, `A2` on `clean_fraction: 0.411` / `synthetic_fraction: 0.198`, and `A0` chose `dropout: 0.4` while `A1`, `B`, `A2` chose `dropout: 0.2` (all at `lr: 0.003`).
- **Iteration 3 search (`results/phase2_snapshot/winners.json`):** `191` trainings (`A0: 6`, `A1: 30`, `B: 22`, `A2: 34`, `P: 18` plus CV/confirmation) yielded 3-seed validation macro-F1 of `A0 94.19`, `A1 95.20`, `B 95.06`, `A2 95.80`, `P 95.17`.

---

## Upgraded & Expanded: Gemini 4 Neon Corpus Synthesis (`F06` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F06` (`failure`)
* **Logic Depth:** **High** (tuning-budget bias across data streams, paired with `C11` and `C12`)
* **Risk if Wrong:** **High** (`A1`-only tuning reused for `A0`/`B` is the classic Melis 2018 / Bouthillier 2021 tuning-budget bias)
* **Adoption Status:** **Adopted via mediated staged search** (per-arm validation search of augmentation, generator, shares, and `(lr, dropout)` grid, plus 3-seed confirmation and Iteration 3 separate `synth_a2` + grouped CV).

### 2. Group Synthesis: Tuning Fairness (`C12`, `F06`, `C11`, `T15`, `T23`)

* **`C12`** answers "one shared `(lr, dropout)` or per-arm?" with per-arm, citing Melis 2018 / Bouthillier 2021. The measured separation: `A0` wants `dropout 0.4`; `A1`/`B`/`A2` want `0.2` — all at `lr 0.003`. The outside claim "one LR and dropout were shared" is recorded as **Does not stand**. In Iteration 3, after 3-fold CV and 3-seed confirmation, all five arms converged on `dropout 0.2` (even though `A0` seed 0 alone preferred `0.4`) — a clear example of CV changing a seed-0 conclusion.
* **`F06`** generalizes the same bias to augmentation/generator ranges: `A1`-only tuning reused for `A0`/`B` is the classic bias, and the fix is a staged per-arm search (`A1`: 24 trials; `B`: 16; `A2`: 12; plus per-arm $3 \times 2$ grid and 3-seed confirmation of top-5). It is explicit that `B` and `A2` inherited `A1`'s augmentation in Iteration 2, and that Iteration 3 addresses this with a separate `synth_a2` search plus grouped CV.
* **`C11`** is the reporting discipline for shares: never trust the configured decimal; log both the configured fraction and the realized integer count (`B` configured `0.278`, realized `71/256 = 27.73%`; `A2` `0.198`, realized `51/256 = 19.92%`; Iteration 3 updated `B` to `43/256` and `A2` to `31/256`).
* **`T15` / `T23`** are the low-risk bookkeeping: record the Decision 7 winner (`lr 0.003, dropout 0.2`) as **comment-only** in `pipeline.yaml` so `recipe_fingerprint` and the Stage 4 cache are untouched.

**Depth note:** `C12` and `F06` are the same principle applied at two scales (hyperparameters, then data/augmentation). `C11` and `T15`/`T23` are the **reporting and recording** layer that keeps the first two auditable.

### 3. Corpus Dependency Graph (`3_modeling` Gemini 4 Neon Entries)

```text
F17 (3→4 blocks, 46-px RF, 242,250 params)
 ├── D03 (critique that produced F17's depth change; only depth adopted)
 ├── A14 (model.py default still said 3 blocks → fixed iter 3)
 └── F17's 242k params is the fixed capacity every arm shares

F02 (LOSO: ellipse only in Hand-Drawn → 9-class hold-out)
 ├── T17 (implements excluded_classes in sampling/sweep/eval)
 ├── T22 (seed_disagreement must skip LOSO runs → run_sweep marks holdout_source)
 └── C26 (grouping on source_id would drop classes → must group on phash_group)

C12 (per-arm lr/dropout grid) ──→ T15/T23 (record the winner as a comment)
                                   └── recipe_fingerprint unchanged → no retrain

C11 (per-arm synthetic share) ──→ F06 (augmentation/generator ranges only tuned on A1)
                                   └── both are "tuning-budget bias" fixes

C27 (equal_real, real_fraction, budget) ──→ C29 (budget gate fires)
C29 (e60_nostop adopted) ──→ C26 (CV at 15 epochs to bound cost)
C26 (CV re-ranks top-5) ──→ C12 (per-arm grid feeds top-5)
                         └── C25 (P added as descriptive arm; CV changes 4/5 winners)

F19 (invalid handle) ──→ C30 (eager Pool, _light_children)
C30 (parallel prep) ──→ C31 (optimization stage) ──→ C39 (measured before/after)
F22 (cuDNN halt at 66/191) ──→ relies on C30's atomic result.json resume
F25 (GPU looks idle) ──→ explains C30/C31's CPU-bound pacing
```

### 4. Consolidated Adoption Ledger & Epistemic Rules

* **Adopted verbatim (or close):** `F02`, `F17`, `C12`, `C27`, `C29`, `C30`, `C31`, `C11`, `T15`/`T23`, `T22`.
* **Adopted with correction:** `C26` (`phash_group`, `CV_EPOCHS = 15`), `C25` (continuous cosine schedule, real-phase checkpointing), `C39` (code vs. quieter machine split), `F19` (eager Pool after initial blame disproved), `D03` (depth only).
* **Rejected:** `C12` ("shared LR/dropout" outside claim), `C29` (post-hoc `B`/`P` check), `C25` (LR reset), `C26` (`source_id` grouping), `F22` ("GPU damaged").

