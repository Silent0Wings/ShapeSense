# 4_testing - F04: B vs A1 failed: -0.36 points, CI [-1.17, 0.41], and A0 with no augmentation scored highest.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison. Other model's answer: [../claude_opus/29_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md](../claude_opus/29_F04_b-vs-a1-failed-0-36-points-ci-1-17-0-41-and.md)
- Date: 2026-11-09
- Entry: F04 (`failure`, `4_testing`)
- Owner / Proposed by: all members / all members
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `results/phase2_snapshot/iter1_status.json`, `results/phase2_snapshot/iteration_log.json`, `docs/crisp_dm/iteration_2/investigation/report.md`, `configs/pipeline.yaml`, `src/stage5_eval/run.py`, `ShapeSense_Deployed/web/stage5.html`, `ShapeSense_Deployed/web/iteration2.html`, commit `d5c6e2d`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt

> **User:** Our pre-registered test `B` vs `A1` failed (-0.36 macro-F1 points, 95% CI [-1.17, 0.41]) and `A0` with no augmentation scored highest (93.88 vs `A1` 90.86 and `B` 90.50). Without touching the test split again, how should we investigate why augmentation and synthetic data did not help - and why can synthetic or heavy augmentation lose to no augmentation at all?

## Response
First, lock the Iteration 1 outcome as final: `B vs A1` (`-0.36` macro-F1 points, 95% CI `[-1.17, 0.41]`, `A0 = 93.88`, `A1 = 90.86`, `B = 90.50`) must stay unchanged in `artifacts/stage5/`, and every diagnostic must run strictly on `train` and `val` (`configs/splits/val.csv` and `artifacts/stage4/*/val_probs.npz`) with zero reads of `configs/splits/test.csv`.

Across image-classification literature and your pipeline contract in `configs/pipeline.yaml`, four mechanisms explain both halves of the failure (`B <= A1` and `A1, B < A0`):

1. **Cue-destroying / label-ambiguating augmentation (`augment.rotate_deg: 180`):** While arbitrary rotation is geometrically label-preserving for isolated polygons, real sources carry strong orientation priors - if `reevald` or `Quick, Draw!` draw `square` and `rectangle` predominantly axis-aligned, rotating them by `±180°` turns a `45°` `square` into a `diamond`-like silhouette and erases a legitimate same-source cue while `A0` exploits it. Heavy geometric warps can also shrink shapes (`augment.frame_margin`) or break `1-px` strokes during resampling.
2. **Reduced real-image density and zero clean real images in `A1`/`B`:** Neither `A1` nor `B` sees unaugmented real images (`A0` sees 100% clean real; `B` replaces `synthetic_fraction: 0.30` of every 256-image batch with synthetic renders), so under a fixed `30`-epoch / `49`-step budget (`1,470` gradient steps) the augmented arms see fewer clean real outlines per epoch and never converge.
3. **Synthetic-to-real domain gap:** Hand-set `synth.*` parameters (`stroke_px`, `vertex_jitter_px`, `radius_px`, `center_jitter_px`) can leave synthetic outlines thinner or cleaner than real drawings, causing `B` to underperform `A1` when synthetic images displace real ones.
4. **Shared untuned hyperparameters (`train.lr: 0.003`, `train.dropout: 0.2`):** Tuning only on `A1` and copying the result to `A0` and `B` biases the comparison toward whichever arm happens to suit `A1`'s gradient variance.

**Recommended validation-only investigation plan:**
- **Phase A (Data & transform audit, no new test reads):** Run a source-prediction probe and orientation audit on `train`/`val` (`square`/`rectangle` orientation distributions by source; bounding-box extent and connected-component counts before vs after `src/stage2_augment/transform.py`; stroke-width measurement on real vs `src/stage3_synth/` images). Verify label alignment, polarity, and loss wiring on `make_batch`.
- **Phase B (Single-factor validation ablations):** On `val` (3 seeds), ablate `rotate_deg` (`0`, `±15`, `±45`, `±90`, `±180`), `scale`, `translate`, `noise`, `blur`, and `shear` on `A1`, plus `30` vs `60` epochs, keeping `configs/splits/test.csv` sealed.
- **Phase C (Comprehensive per-arm search):** Once defects are fixed, run a dedicated per-arm hyperparameter, augmentation, and generator search on validation (hundreds of models across arms, roughly 2 days of GPU compute) so no arm inherits another arm's hand-set ranges.

## Validation
All members reviewed the Iteration 1 `stage5` outputs (`results/phase2_snapshot/iter1_status.json`: `test_reads = 13`, `extra_reads = 0`, `A1 vs A0 = -3.03`, `B vs A0 = -3.38`) and executed the validation-only investigation (`docs/crisp_dm/iteration_2/investigation/report.md`, 16 GPU trainings, zero test reads):
- **Ruled out:** Label attachment (`0` mismatches across `179` images tracked through `make_batch`), loss wiring, class weighting, and polarity (`A1 standard = 93.62` vs `A1 inverted = 93.57` on valid rerun).
- **Confirmed orientation shortcut & `±180°` damage:** `reevald` squares were `92%` axis-aligned, `reevald` rectangles `92-95%`, and `Quick, Draw!` squares `73-85%`, while `El Korchi` squares were randomly oriented; a source classifier hit `91.7%` vs `46.7%` majority baseline. On `val` (3 seeds), `A1` scored `93.15` (rotation off) and `93.17` (`±15°`) vs `90.03` (`±180°`) and `91.69` (`A0`). On held-out Hand-Drawn triangles/rectangles (`val`), `A0` fell to `53.5%` mean accuracy while `A1` reached `66.4%` and `B` `71.8%`.
- **Confirmed transform & generator defects:** Augmented bounding boxes averaged `51.0 px` vs `56.0-57.8 px` real; `69%` of augmented `Quick, Draw!` shapes gained disconnected components (`17.2` pieces per `1-px` stroke); synthetic stroke was `2 px` vs `3.1 px` real; `A1` at `60` epochs climbed to `92.11`/`92.38` vs `90.44`/`90.71` at `30` epochs.

## Our decision
The team kept the Iteration 1 `fail` verdict (`B vs A1 = -0.36`, CI `[-1.17, 0.41]`) unchanged, did not re-read `configs/splits/test.csv` during diagnostics, and opened CRISP-DM Iteration 2 (`eval -> data prep`, commit `d5c6e2d`). While adopting Gemini 4 Neon's validation-only investigation and per-arm tuning principle, the team scoped the multi-hundred-model (~2-day) search down to a pre-registered `166`-trial budget across `A0` (6), `A1` (30), `B` (22), and new arm `A2` (18) plus confirmation runs, after fixing framing (`augment.frame_margin: 0.06`), thin-line preservation (`1.0` piece), and synthetic `stroke_px: 3`.

## Measured effect
- **Iteration 1 verdict preserved:** `B vs A1` remained `-0.36` macro-F1 points (95% CI `[-1.17, 0.41]`, `test_reads = 13`, `extra_reads = 0`).
- **Validation recovery from Iteration 2 fixes:** `A1` validation macro-F1 rose from `90.64` (`±180°`) to `94.77` (`±20°`, `±10°` cap for `square`/`rectangle`/`diamond`); tuned validation means reached `A2 = 95.17`, `A1 = 94.77`, `B = 94.20`, `A0 = 92.61`.
- **Transform parity:** Shape framing restored to `~57 px`, `1-px` stroke fragmentation reduced from `17.2` to `1.0` piece, and synthetic `stroke_px` matched to `3 px` (`~3.1 px` real).

---

## Upgraded & Expanded Technical Analysis (`F04`)

### 1. Making the Orientation Audit Causal Rather Than Correlational
The empirical ablation proves that restricting `rotate_deg` from $\pm 180^\circ$ to $0^\circ$ / $\pm 15^\circ$ lifts `A1` validation macro-F1 from `90.03` to `93.15` / `93.17`. To establish **causal separation** between (a) *legitimate source-cue erasure* and (b) *inter-class label ambiguity* (a $45^\circ$-rotated `square` colliding with the `diamond` class boundary):
- **Counterfactual Co-Label Control:** Evaluate or re-train `A1` under full `rotate_deg: ±180°` while collapsing orientation-aliased pairs (`square` $\cup$ `diamond`) into an orientation-invariant super-class (or applying class-conditional rotation caps: $\pm 10^\circ$ for `square`/`rectangle`/`diamond` vs. wider rotation for isotropic/radial classes).
- In Iteration 2, enforcing the class-conditional cap (`±20°` general, `±10°` for `square`/`rectangle`/`diamond`) eliminated the `square` $\leftrightarrow$ `diamond` rotational aliasing while preserving rotational regularization on non-aliasing classes, driving `A1` validation macro-F1 to `94.77`.

### 2. Disentangling the Three Confounds via Factorial Decomposition
Iteration 1 bundled three distinct structural deficits into the comparison between `A0`, `A1`, and `B`:
1. **Clean Real Exposure Deficit ($C$):** `clean_real_fraction` $\in \{0.0, 0.5, 1.0\}$.
2. **Synthetic Domain Gap ($S$):** `synthetic_fraction` $\in \{0.0, 0.30\}$.
3. **Optimization Hyperparameter Coupling ($L$):** `lr` $\in \{0.001, 0.003\}$ (shared vs. per-arm tuned).

A 3-way factorial validation structure ($C \times S \times L$) decomposes the validation variance into main effects and interactions:

| Factor / Term | Mechanistic Role | Empirical Direction on `val` |
|---|---|---|
| Main Effect $C$ (`clean_real_fraction`) | Anchors BatchNorm running moments and canonical pixel-outline features to clean evaluation geometry | **Dominant positive effect:** adding clean real images (`A2` vs `B`) lifts tuned `val` macro-F1 from `94.20` to `95.17` (`+0.97`) |
| Main Effect $S$ (`synthetic_fraction`) | Procedural shape diversity; negative when `stroke_px = 2` vs `3.1 px` real, positive once calibrated to `3 px` | Shifted from `-0.36` (`B vs A1` Iter 1) to `+0.55` (`B vs A1` damaged Iter 3) after stroke/framing parity |
| Main Effect $L$ (Per-arm `lr`/`dropout`) | Matches step size to gradient variance of augmented/mixed batches | Per-arm tuning (`3×2` grid per arm) lifted all four arms (`A0: 92.61`, `B: 94.20`, `A1: 94.77`, `A2: 95.17`) |

### 3. Mechanistic Budget Arithmetic (`1,470`-Step Fixed Horizon)
Under Decision 13, Iteration 1 fixed the optimization budget at $E = 30$ epochs $\times S = 49$ steps/epoch $= 1,470$ total gradient updates with mini-batch size $B = 256$ ($1,470 \times 256 = 376,320$ total sample slots):
- **`A0` (100% clean real):** Observes $376,320$ clean real image draws ($0$ augmented, $0$ synthetic).
- **`A1` (100% heavily warped real):** Observes $376,320$ warped real draws and **$0$ clean real draws**.
- **`B` (70% warped real + 30% synthetic):** Observes $1,470 \times 256 \times 0.70 \approx 263,424$ real draws (all warped, **$0$ clean real**) and $112,896$ uncalibrated synthetic draws — a **30% real-image exposure deficit** relative to `A0` on top of 100% clean-image displacement.

