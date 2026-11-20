# 3_modeling - A10: Synthetic shares are rounded differently from the real batch.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A10 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/sampling.py, src/stage4_train/train.py, docs/crisp_dm/iteration_2/search/winners.json, docs/crisp_dm/iteration_2/data/stage4_status.json, configs/pipeline.yaml, ShapeSense_Deployed/web/stage4.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Synthetic shares are rounded differently from the real batch.

## Response
In `src/stage4_train/sampling.py`, `batch_composition(arm_cfg, batch_size, synthetic_fraction)` (lines 78-94) converts each arm's configured `synthetic_fraction` into a fixed integer count per `256`-image batch via Python's `round`:

```python
n_syn = int(round(batch_size * share)) if arm_cfg["synthetic"] else 0
return batch_size - n_syn, n_syn
```

Because `batch_size = 256` is discrete, the tuned Iteration 2 percentages (`arms.B.synthetic_fraction: 0.278` = 27.8% and `arms.A2.synthetic_fraction: 0.198` = 19.8% in `docs/crisp_dm/iteration_2/search/winners.json`) do not map cleanly to exact integers:
- **Arm B:** `256 * 0.278 = 71.168`, which rounds to `n_syn = 71` and `n_real = 185`. The actual batch share is `71 / 256 = 0.27734375` (`27.73%`, or `27.7%` to one decimal place), not `27.8%`.
- **Arm A2:** `256 * 0.198 = 50.688`, which rounds to `n_syn = 51` and `n_real = 205`. The actual batch share is `51 / 256 = 0.19921875` (`19.92%`, or `19.9%` to one decimal place), not `19.8%`.

Because `train_one` logs `realized_synthetic_share = syn_total / img_total` (`0.27734375` for B and `0.19921875` for A2), reporting only the configured `27.8%` and `19.8%` values creates a visible mismatch against the per-batch integer counts (`71/256` and `51/256`) and the run logs. Both the configured target shares and the realized batch counts/shares should be recorded side by side.

## Validation
The team cross-checked `src/stage4_train/sampling.py` (`batch_composition`), `docs/crisp_dm/iteration_2/search/winners.json`, and `docs/crisp_dm/iteration_2/data/stage4_status.json`:
- Confirmed `batch_composition` computes `n_syn = 71` (`n_real = 185`) for Iteration 2 arm `B` and `n_syn = 51` (`n_real = 205`) for Iteration 2 arm `A2`.
- Confirmed `stage4_status.json` records `real_draws_per_step: {"B": 185, "A2": 205}`, `synthetic_per_step: {"B": 71, "A2": 51}`, and `realized_synthetic_share: 0.27734375` (27.73%) across all `B` runs and `0.19921875` (19.92%) across all `A2` runs.
- Note that the same discrete rounding occurs in Iteration 3 (`configs/pipeline.yaml` / `status4.json`): configured `0.168` (`B`) -> `43/256 = 0.16796875`, and `0.12` (`A2`) -> `31/256 = 0.12109375`.

## Our decision
- **Team verdict: `Stands` (`Fixed in this record`).** No training code was altered, because per-batch integer rounding (`round(batch_size * share)`) is deterministic and intentional (Decision 11 / R7). The team fixed the documentation discrepancy directly in the audit record (`gemini_audit.md`), reporting both the configured shares (`27.8%`, `19.8%`) and the realized batch counts and percentages (`71/256 = 27.7%`, `27.73%` logged; `51/256 = 19.9%`, `19.92%` logged).

## Measured effect
- **Arm B (Iteration 2):** Configured `27.8%` (`0.278`) -> `71` synthetic + `185` real per `256`-image batch (`27.7%`, logged mean `27.734375%`).
- **Arm A2 (Iteration 2):** Configured `19.8%` (`0.198`) -> `51` synthetic + `205` real per `256`-image batch (`19.9%`, logged mean `19.921875%`).

---

## Discrete Mini-Batch Quantization of Continuous Synthetic Mixture Ratios (`A10`)

### Claim Metadata

* **Entry ID:** `A10` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `winning-decision (70% tier)`
* **Grounding Artifacts:** `src/stage4_train/sampling.py`, `src/stage4_train/train.py`, `docs/crisp_dm/iteration_2/search/winners.json`, `docs/crisp_dm/iteration_2/data/stage4_status.json`, `results/phase2_snapshot/status4.json`

### Mechanistic & Numerical Analysis

`batch_composition()` converts continuous hyperparameter shares $p_{\text{syn}} \in [0, 1]$ into deterministic per-batch integer slot counts via half-to-even rounding: $n_{\text{syn}} = \text{round}(256 \cdot p_{\text{syn}})$ and $n_{\text{real}} = 256 - n_{\text{syn}}$. Because $B = 256 = 2^8$, exact representation requires $p_{\text{syn}}$ to be an integer multiple of $2^{-8} = 0.00390625$ ($0.390625\%$). Configured search winners exhibit minor quantization offsets:

| Iteration & Arm | Configured Share ($p_{\text{syn}}$) | Exact Product ($256 \cdot p_{\text{syn}}$) | Quantized Batch Counts ($n_{\text{syn}} / n_{\text{real}}$) | Realized Share ($n_{\text{syn}} / 256$) | Quantization Error ($\Delta p$) |
| --- | --- | --- | --- | --- | --- |
| **Iter 2 — Arm B** | $0.278$ ($27.80\%$) | $71.168$ | $71 / 185$ | $0.27734375$ ($27.73\%$) | $-0.0656\%$ |
| **Iter 2 — Arm A2** | $0.198$ ($19.80\%$) | $50.688$ | $51 / 205$ | $0.19921875$ ($19.92\%$) | $+0.1219\%$ |
| **Iter 3 — Arm B** | $0.168$ ($16.80\%$) | $43.008$ | $43 / 213$ | $0.16796875$ ($16.80\%$) | $-0.0031\%$ |
| **Iter 3 — Arm A2** | $0.120$ ($12.00\%$) | $30.720$ | $31 / 225$ | $0.12109375$ ($12.11\%$) | $+0.1094\%$ |

While `train_one` logs the exact realized ratio (`syn_total / img_total`), prose summaries citing only configured values (`27.8%`, `19.8%`) diverge from the logged integer counts (`71/256`, `51/256`).

### Resolution

* **Verdict:** **Stands** (`Fixed in this record`).
* **Action:** Retained deterministic integer slot allocation (Decision 11 / R7) and updated audit tables to report both configured targets and realized integer batch ratios side by side.

