# 4_testing - C17: Robustness check
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-09
- Entry: C17 (`change`, `4_testing`)
- Owner / Proposed by: team / team
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `robustness/perturb.py`, `robustness/run.py`, `tests/robustness/test_perturb.py`, `docs/crisp_dm/iteration_2/robustness/results.json`, `results/phase2_snapshot/robustness.json`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/robustness.html`, commit `0f8a702`


## Prompt
Clean accuracy does not show which model survives damaged images. Design a robustness check: fixed perturbed copies of validation, which damage types and levels, and how all 20 models are scored. It must stay descriptive and change no verdict.

## Response
To measure degradation under image damage without touching `configs/splits/test.csv` or `configs/splits/fresh_holdout.csv`, build a standalone, deterministic, validation-only robustness suite (`robustness/perturb.py` and `robustness/run.py`) that generates fixed perturbed copies of `configs/splits/val.csv` (`n = 2,819` images) once and scores all `20` Iteration 2 models (`A0`, `A1`, `B`, `A2` × seeds `0..4`) on identical inputs.

### 1. Fixed perturbed copies of validation
- **Single deterministic build:** Use fixed RNG seed `20261109` (`val` split only) so every model across all four arms is evaluated on the exact same pixel arrays, eliminating Monte Carlo noise between arms.
- **No label-breaking distortions:** Keep every perturbation geometry- and class-safe (no aspect-ratio stretching or shear that turns `circle` into `ellipse` or `square` into `rectangle`), and store the resulting dataset note in `docs/crisp_dm/iteration_2/robustness/results.json` explicitly marked descriptive.

### 2. Perturbation families and levels (`32` sets = `clean` + `31` levels)
Cover `8` distinct corruption families spanning mild-to-severe deployment damage:
- **Rotation (`rot0` control + 6 angles):** `0°`, `15°`, `30°`, `45°`, `90°`, `135°`, `180°` (tests whether `A0` relies on axis-aligned orientation shortcuts).
- **Gaussian noise (`4` levels):** `σ ∈ {0.02, 0.05, 0.1, 0.2}`.
- **Salt-and-pepper noise (`4` levels):** `1%`, `5%`, `10%`, `20%` pixel flips.
- **Gaussian blur (`3` levels):** `radius ∈ {1, 2, 3}` px.
- **JPEG compression (`3` levels):** `quality ∈ {90, 50, 20}`.
- **Brightness shift (`4` levels):** `-0.4`, `-0.2`, `+0.2`, `+0.4`.
- **Contrast reduction (`3` levels):** `×0.75`, `×0.5`, `×0.25`.
- **Square occlusion (`3` levels):** `8`, `16`, `24` px patches.

### 3. Scoring all `20` models and enforcing the descriptive boundary
- Score every individual seed model (`A0_0..4`, `A1_0..4`, `B_0..4`, `A2_0..4`) across all `32` sets; aggregate per `(arm, set)` as mean and std of `accuracy`, `macro_f1`, and `drop` (`clean - perturbed`), plus `families` summaries, `per_class` breakdowns, and seed-summed confusion matrices.
- Keep `src/stage4_train/` and `src/stage5_eval/` untouched, run no bootstrap hypothesis test or `success_criterion` check here, and state clearly on `studio/web/robustness.html` (`ShapeSense_Deployed/web/robustness.html`) that the check is descriptive only and alters neither Iteration 1 nor Iteration 2 verdicts.

## Validation
The team implemented `robustness/perturb.py`, `robustness/run.py`, `tests/robustness/test_perturb.py`, and the `studio/web/robustness.html` view in commit `0f8a702` (`Stage 4 and 5 code is unchanged`). Unit tests in `tests/robustness/test_perturb.py` verified determinism under seed `20261109`, output shape/dtype bounds, and all `32` set definitions. Running `robustness/run.py` on `val` (`2,819` images × `32` sets × `20` models) completed without touching any sealed split (`test_access.log` unchanged).

## Our decision
Adopted the full `32`-set (`8`-family) validation robustness design turned from the team's class-survival idea (`0f8a702`), keeping it strictly descriptive and isolated from Stage 5 verdicts. Because this validation sweep showed every arm falling below `30%` on the `7` harshest levels (`saltpepper0.1`, `saltpepper0.2`, `blur2`, `blur3`, `bright-0.4`, `contrast0.5`, `contrast0.25`), the team later used those findings to prune Iteration 3's pre-registered test suite down to `23` non-degenerate levels.

## Measured effect
- **Validation clean vs 30-level damaged mean macro-F1 (`results/phase2_snapshot/robustness.json`):**
  - `A0`: `93.17` clean → `52.80` damaged mean
  - `A1`: `94.16` clean → `59.85` damaged mean
  - `B`: `94.22` clean → `60.65` damaged mean
  - `A2`: `95.13` clean → `62.18` damaged mean (`+9.38` points over `A0` under damage, despite clean parity on `test.csv`)
- **Zero verdict mutation:** Iteration 1 and Iteration 2 verdicts remained `fail`; `test_access.log` stayed clean.

---

##  Technical Analysis (`C17`)

### 1. Why Descriptive-Only on Validation Is a Logical Necessity
Restricting `robustness/run.py` in Iteration 2 to descriptive summary statistics (with zero bootstrap p-values or verdict changes) is not merely conservative reporting — it is an **epistemic necessity**:
1. **In-Sample Selection Contamination (cf. `A11`, `A25`):** The validation split (`configs/splits/val.csv`, $n = 2,819$) was already used across `166` hyperparameter/augmentation/generator trials and best-epoch checkpoint selection (`val_macro_f1`). Running an inferential hypothesis test on perturbed copies of the same validation images would inherit selection optimism.
2. **Post-Hoc Hypothesis Formation:** The corruption hypothesis was formulated *after* observing clean saturation on `test.csv` and `fresh_holdout.csv` (`+0.06` and `+0.08`). Under scientific pre-registration rules, an exploratory sweep on `val` can **generate** the Iteration 3 hypothesis and calibrate the corruption levels, while the binding inferential test must move into Stage 5 on a never-read holdout (`fresh_holdout_2.csv`, see `C23` and `C28`).

### 2. Formal Degeneracy Detection Rule (`max_arm_mean < 30.0%`)
To prevent catastrophic signal-destroying corruptions from injecting pure chance noise into Iteration 3's primary estimand, a perturbation level $\ell$ is classified as **degenerate** on validation if even the best-performing arm collapses below $30.0\%$ macro-F1 ($3\times$ the $10\%$ uniform random-guessing baseline for 10 classes):
$$\text{Degenerate}(\ell) \iff \max_{a \in \{\text{A0}, \text{A1}, \text{B}, \text{A2}\}} \overline{\text{F1}}_{\text{val}}(a, \ell) < 30.0\%$$

Applying this rule to `docs/crisp_dm/iteration_2/robustness/results.json` partitions the `30` damaged validation levels (excluding `clean` and `rot0`) into `7` degenerate levels and `23` informative levels:

| Partition | Perturbation Levels | Count | Validation Behavior ($\max_a \overline{\text{F1}}_{\text{val}}$) | Action for Iteration 3 Pre-Registration |
|---|---|---|---|---|
| **Dropped (Degenerate)** | `saltpepper0.1`, `saltpepper0.2`, `blur2`, `blur3`, `bright-0.4`, `contrast0.5`, `contrast0.25` | `7` | `< 30.0%` across every arm (total outline erasure / binarization collapse) | Excluded **before** reading `fresh_holdout_2.csv` (`ff1f269`) |
| **Kept (Informative)** | `rot15..180` (6), `gauss0.02..0.2` (4), `saltpepper0.01..0.05` (2), `blur1` (1), `jpeg90..20` (3), `bright-0.2..+0.4` (3), `contrast0.75` (1), `occlude8..24` (3) | `23` | $\ge 30.0\%$ (shapes remain human-recognizable; separates shortcut reliance from structural invariance) | Locked as `evaluation.robust.levels` in `configs/pipeline.yaml` |

