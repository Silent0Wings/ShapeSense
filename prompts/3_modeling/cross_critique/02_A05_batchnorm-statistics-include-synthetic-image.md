# 3_modeling - A05: BatchNorm statistics include synthetic images in B and A2.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A05 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `close-to-reality`
- Grounding sources: results/llm_comparison/gemini_audit.md, src/stage4_train/model.py, src/stage4_train/bn.py, src/stage4_train/train.py, src/stage4_train/experiments.py, configs/pipeline.yaml, docs/crisp_dm/iteration_3/experiments/batchnorm.json, tests/stage4/test_iteration3.py, ShapeSense_Deployed/web/stage4.html, ShapeSense_Deployed/web/experiments.html


## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: BatchNorm statistics include synthetic images in B and A2.

## Response
Every block of `SmallCNN` in `src/stage4_train/model.py` uses `nn.BatchNorm2d(c_out)` across the four convolutional stages (`[32, 64, 128, 128]`). In arms **B** (`43/256` synthetic in Iteration 3; `71/256` in Iteration 2) and **A2** (`31/256` synthetic in Iteration 3; `51/256` in Iteration 2), each training forward pass feeds a mixed batch of real and synthetic images through `self.features`, so the `BatchNorm2d` `running_mean` and `running_var` buffers track a mixture of real hand-drawn/rendered sketches and Stage 3 geometric renders.

**Why this is a potential domain-shift flaw:** Synthetic images have uniform `stroke_px: 3` anti-aliased outlines rendered at `2x` supersample, exact background `255`, and no source-specific noise or sketch irregularities. At test time (`model.eval()`), `SmallCNN` evaluates 100% real images using running moments partially pulled toward synthetic activation statistics - which can systematically shift pre-ReLU feature thresholds and hurt both `B` and `A2` relative to real-only `A0` and `A1`.

**Recommended fix:** Add a post-training BatchNorm recalibration pass on real training images only (`images_u8` from `train` split, leaving all `Conv2d` and `Linear` weights frozen). Specifically: load `model.pt`, call `norm.reset_running_stats()`, set `norm.momentum = None` (exact cumulative mean/variance) and `norm.train()`, run one `torch.no_grad()` pass over `train.images` (`12,405` real images), and return `model.eval()`. Removing synthetic bias from the normalization buffers should improve real-image validation and test macro-F1 for `B` and `A2`.

## Validation
- Implemented `src/stage4_train/bn.py#recalibrated` (`CHUNK = 256`, `norm.reset_running_stats()`, `norm.momentum = None`, `norm.train()`, `torch.no_grad()` forward pass over `train.images`) and verified via `tests/stage4/test_iteration3.py::test_batchnorm_recalibration_changes_only_the_averages` that only BatchNorm running stats change while all weights stay identical.
- Evaluated the 3 saved `exp_scarcity` `f100` models for `B` and `A2` on validation (`src/stage4_train/experiments.py`, logged in `docs/crisp_dm/iteration_3/experiments/batchnorm.json`):
  - **B (`recalibrated` vs `saved`):** Clean validation macro-F1 fell from `94.20 ± 0.05` (`94.204`) to `93.55 ± 0.12` (`93.545`), a **`-0.66`-point** drop; damaged validation macro-F1 fell from `77.07 ± 2.47` (`77.068`) to `76.54 ± 1.95` (`76.536`), a `-0.53`-point drop.
  - **A2 (`recalibrated` vs `saved`):** Clean validation macro-F1 fell from `95.17 ± 0.26` (`95.169`) to `94.39 ± 0.25` (`94.394`), a **`-0.78`-point** drop; damaged validation macro-F1 fell from `80.29 ± 1.30` (`80.292`) to `79.75 ± 1.23` (`79.746`), a `-0.55`-point drop.
- Gemini's hypothesis missed that the `Conv2d` weights, BatchNorm affine `weight`/`bias`, and `Linear` head co-adapted to the mixed-batch BatchNorm statistics during training; resetting `running_mean`/`running_var` post-hoc without fine-tuning miscalibrates the downstream classifier.

## Our decision
Verdict: **Stands** (BatchNorm buffers in `B` and `A2` do include synthetic images). **Closed by experiment**: post-training BatchNorm recalibration on real images consistently reduced clean macro-F1 (`-0.7` points for `B`, `-0.8` points for `A2`) and damaged macro-F1 (`-0.5` points for both), so the team rejected recalibration and kept the saved training BatchNorm statistics.

## Measured effect
- `B/recalibrated` vs `B/saved` (3 validation seeds): `-0.66` clean macro-F1 (`93.55` vs `94.20`), `-0.53` damaged macro-F1 (`76.54` vs `77.07`).
- `A2/recalibrated` vs `A2/saved` (3 validation seeds): `-0.78` clean macro-F1 (`94.39` vs `95.17`), `-0.55` damaged macro-F1 (`79.75` vs `80.29`).

---

## Covariate Shift in BatchNorm Population Statistics Under Mixed-Domain Training (`A05`)

### Claim Metadata

* **Entry ID:** `A05` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `close-to-reality`
* **Grounding Artifacts:** `src/stage4_train/model.py`, `src/stage4_train/bn.py`, `src/stage4_train/experiments.py`, `docs/crisp_dm/iteration_3/experiments/batchnorm.json`, `tests/stage4/test_iteration3.py`

### Mechanistic & Statistical Analysis

`SmallCNN` (`src/stage4_train/model.py`) applies `nn.BatchNorm2d(c_out)` after every convolutional layer across channels $[32, 64, 128, 128]$. During training in arms **B** ($16.8\%$–$27.7\%$ synthetic) and **A2** ($12.1\%$–$19.9\%$ synthetic), exponential moving average (EMA) buffers ($\hat{\mu}_{\text{EMA}}, \hat{\sigma}^2_{\text{EMA}}$) accumulate first- and second-order moments over mixed mini-batches:

$$\hat{\mu}_{\text{mix}} = (1 - \alpha)\mu_{\text{real}} + \alpha\mu_{\text{syn}}, \quad \hat{\sigma}^2_{\text{mix}} = (1 - \alpha)\sigma^2_{\text{real}} + \alpha\sigma^2_{\text{syn}} + \alpha(1 - \alpha)(\mu_{\text{real}} - \mu_{\text{syn}})^2$$

where $\alpha = n_{\text{syn}} / 256$. Because Stage 3 synthetic renders possess uniform anti-aliased outlines (`stroke_px: 3`, $2\times$ supersampled) and noise-free background values ($255$), their pre-activation distributions exhibit lower spatial variance and shifted means compared to heterogeneous real sketches. At inference (`model.eval()`), 100% real test images ($\alpha = 0$) are normalized using $\hat{\mu}_{\text{mix}}$ and $\hat{\sigma}^2_{\text{mix}}$, inducing a systematic pre-ReLU activation offset relative to real-only arms (`A0`, `A1`).

### Empirical Counter-Analysis & Co-Adaptation Dynamics

To test whether removing synthetic moment contamination improves inference on real data, the team implemented exact post-hoc BatchNorm recalibration (`src/stage4_train/bn.py#recalibrated`):

1. Froze all `Conv2d` and `Linear` parameters as well as BatchNorm affine parameters ($\gamma, \beta$).
2. Reset running buffers (`norm.reset_running_stats()`) and switched to cumulative moving average (`norm.momentum = None`).
3. Executed a single `torch.no_grad()` forward pass over all $12,405$ real training images (`CHUNK = 256`), verified by unit test `test_batchnorm_recalibration_changes_only_the_averages`.

Evaluation across 3 saved `exp_scarcity` (`f100`) seeds (`docs/crisp_dm/iteration_3/experiments/batchnorm.json`) demonstrated uniform degradation:

| Arm & Evaluation Regime | Saved Mixed-Batch BN (Macro-F1) | Recalibrated Real-Only BN (Macro-F1) | Net Delta ($\Delta$) |
| --- | --- | --- | --- |
| **Arm B (Clean Val)** | $94.204 \pm 0.05$ | $93.545 \pm 0.12$ | **$-0.66$ pts** |
| **Arm B (Damaged Val)** | $77.068 \pm 2.47$ | $76.536 \pm 1.95$ | **$-0.53$ pts** |
| **Arm A2 (Clean Val)** | $95.169 \pm 0.26$ | $94.394 \pm 0.25$ | **$-0.78$ pts** |
| **Arm A2 (Damaged Val)** | $80.292 \pm 1.30$ | $79.746 \pm 1.23$ | **$-0.55$ pts** |

**Root Cause of Failure:** During gradient descent, convolutional filters $W$ and affine parameters $(\gamma, \beta)$ co-adapt specifically to the mixed-batch normalization coordinate frame $(\hat{\mu}_{\text{mix}}, \hat{\sigma}_{\text{mix}})$. Substituting $(\mu_{\text{real}}, \sigma_{\text{real}})$ post-hoc without fine-tuning shifts decision boundaries relative to the frozen linear classifier head.

### Resolution

* **Verdict:** **Stands** (running buffers do incorporate synthetic moments) / **Closed by Experiment**.
* **Action:** Rejected post-hoc BatchNorm recalibration; preserved training-time EMA statistics.

