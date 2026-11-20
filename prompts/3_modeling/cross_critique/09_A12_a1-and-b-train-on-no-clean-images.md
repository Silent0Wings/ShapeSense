# 3_modeling - A12: A1 and B train on no clean images.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A12 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/sampling.py, configs/pipeline.yaml, configs/models/A1.yaml, configs/models/B.yaml, configs/models/A2.yaml, ShapeSense_Deployed/web/stage4.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: A1 and B train on no clean images.

## Response
In `src/stage4_train/sampling.py`, `raw_batch` (lines 188-216) decides how many real images remain unaugmented per batch via `clean_count(arm_cfg, batch_size)` (line 97):

```python
return int(round(batch_size * float(arm_cfg.get("clean_fraction", 0.0))))
```

When `arm_cfg["augment"]` is `True`, every image at index `i >= n_clean` - both real and synthetic - is passed through `transform(img, int(lbl), rng)` (lines 210-213), which applies `frame_margin` re-framing, rotation, scaling, shear/non-uniform scale (where allowed), translation, noise, and blur/re-thresholding. Checking `configs/pipeline.yaml#arms` (and `configs/models/A1.yaml`, `B.yaml`, `A2.yaml`):
- **Arm `A0`:** `augment: false, synthetic: false` -> `256` clean real images (`0` augmented).
- **Arm `A1`:** `augment: true, synthetic: false`, `clean_fraction` omitted (`0.0`) -> `n_clean = 0`, so all `256` images per batch are augmented real drawings.
- **Arm `B`:** `augment: true, synthetic: true`, `clean_fraction` omitted (`0.0`) -> `n_clean = 0`, so all `185` real (Iter 2; `213` in Iter 3) and `71` synthetic (Iter 2; `43` in Iter 3) images per batch are augmented.
- **Arm `A2`:** `clean_fraction: 0.411` -> `n_clean = round(256 * 0.411) = 105` clean unaugmented real images per batch.

Because `A1` and `B` never see a single unaugmented, un-reframed real image during training (`real_unchanged: 0`), any distribution shift introduced by `transform` (even mild `frame_margin` re-framing and re-thresholding) is baked into 100% of their training batches. This should be documented clearly as the intentional contrast between `A1`/`B` and `A2`.

## Validation
The team verified `clean_count` and `raw_batch` in `src/stage4_train/sampling.py` alongside `configs/pipeline.yaml` and the exported model cards (`configs/models/A1.yaml`, `B.yaml`, `A2.yaml`):
- Confirmed `A1` and `B` intentionally set `real_unchanged: 0` (`n_clean = 0`), whereas `A2` explicitly adds `clean_fraction: 0.411` (`real_unchanged: 105` of `256` per batch) to test whether retaining clean real examples alongside augmented real and synthetic data improves generalization over `A1` and `B`.
- Cross-checked Iteration 3's validation `preprocess.json` experiment (`iteration_log.json` line 45): running the Stage 2 re-frame/binarise step alone on validation drops `A0` (never trained on re-framed images) by `2.8` macro-F1 points, vs only `0.3` for `A1`, `0.6` for `B`, and `1.1` for `A2`.

## Our decision
- **Team verdict: `Stands` (`Disclosed`).** Gemini 4 Neon's code reading is exact. Having `A1` and `B` train on 0 clean images (`n_clean = 0`) is deliberate by experimental design so `A2` isolates the effect of adding the `41.1%` clean real share (`105` images/batch). Disclosed in `gemini_audit.md` and `configs/models/*.yaml`.

## Measured effect
- **Batch composition (`configs/models/*.yaml`):** `A1` trains on `{real_unchanged: 0, real_augmented: 256, synthetic: 0}`; `B` trains on `{real_unchanged: 0, real_augmented: 185, synthetic: 71}` (Iter 2) / `{213, 43}` (Iter 3); `A2` adds `real_unchanged: 105` (`clean_fraction: 0.411`).
- **Clean vs. damaged outcomes (`fresh_holdout_2`, Iteration 3):** Clean macro-F1 reaches `A0: 97.8`, `A1: 98.3`, `B: 98.0`, `A2: 98.5`; across 23 damage levels, `A2 vs A1` gains `+2.22` (`p = 0.004`, Holm-corrected) and `A2 vs B` gains `+1.68` (`p = 0.004`).

---

## Zero Unaugmented Clean-Image Exposure in Arms A1 and B (`A12`)

### Claim Metadata

* **Entry ID:** `A12` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `winning-decision (70% tier)`
* **Grounding Artifacts:** `src/stage4_train/sampling.py`, `configs/pipeline.yaml`, `configs/models/{A1,B,A2}.yaml`, `results/phase2_snapshot/iteration_log.json`

### Mechanistic & Experimental Design Analysis

In `src/stage4_train/sampling.py#raw_batch`, `clean_count()` computes $n_{\text{clean}} = \text{round}(B \cdot \text{clean\_fraction})$. Every batch slot at index $i \ge n_{\text{clean}}$ passes through `transform(img, lbl, rng)` whenever `arm_cfg["augment"]` is enabled, applying stochastic `frame_margin` re-framing, affine rotation/scaling/shear, translation, additive noise, and blur/re-thresholding. Because `clean_fraction` defaults to $0.0$ in `A1` and `B`, neither arm ever observes an unperturbed real image during gradient updates:

* **Arm A0:** $\{n_{\text{clean}}: 256, n_{\text{aug\_real}}: 0, n_{\text{syn}}: 0\}$
* **Arm A1:** $\{n_{\text{clean}}: 0, n_{\text{aug\_real}}: 256, n_{\text{syn}}: 0\}$
* **Arm B:** $\{n_{\text{clean}}: 0, n_{\text{aug\_real}}: 185\text{ (Iter 2) / }213\text{ (Iter 3)}, n_{\text{syn}}: 71\text{ (Iter 2) / }43\text{ (Iter 3)}\}$
* **Arm A2:** $\{n_{\text{clean}}: 105, n_{\text{aug\_real}}: 100\text{ (Iter 2) / }120\text{ (Iter 3)}, n_{\text{syn}}: 51\text{ (Iter 2) / }31\text{ (Iter 3)}\}$ (`clean_fraction: 0.411`)

### Empirical Isolation & Factorial Role

Setting $n_{\text{clean}} = 0$ in `A1` and `B` is an intentional factorial control rather than an oversight: it isolates the causal contribution of retaining $41.1\%$ unaugmented real anchors ($105$ images/batch) in `A2`. Two empirical findings validate this design:

1. **Preprocessing Sensitivity (`preprocess.json`):** Applying Stage 2 re-framing/binarization alone on validation drops unaugmented `A0` by **$-2.8$ macro-F1 points**, compared to **$-0.3$** (`A1`), **$-0.6$** (`B`), and **$-1.1$** (`A2`), confirming that `transform` alters input manifold statistics.
2. **Holdout Generalization (`fresh_holdout_2`, Iteration 3):** Retaining the $105$ clean real anchors in `A2` achieves the highest clean accuracy (`A2: 98.5` vs. `A1: 98.3`, `B: 98.0`, `A0: 97.8`) while simultaneously delivering statistically significant robustness gains across 23 perturbation levels (`A2 vs. A1`: **$+2.22$ pts**, $p = 0.004$ Holm-corrected; `A2 vs. B`: **$+1.68$ pts**, $p = 0.004$).

### Resolution

* **Verdict:** **Stands** (`Disclosed`).
* **Action:** No code modification; documented `clean_fraction = 0.0` in `A1`/`B` vs. `0.411` in `A2` as the defining factorial contrast.

