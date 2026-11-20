# 3_modeling - A13: Baselines train on 600 real images per class.
- LLM: Gemini 4 Neon 
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09
- Entry: A13 (`claim`, `3_modeling`)
- Owner / Proposed by: team / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: results/llm_comparison/gemini_audit.md, results/llm_comparison/gemini_audit.csv, src/stage4_train/baselines.py, configs/pipeline.yaml, results/phase2_snapshot/split_stats.csv, results/phase2_snapshot/baselines.json, results/phase2_snapshot/metrics.csv, ShapeSense_Deployed/web/stage4.html

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Review the Claude-built ShapeSense pipeline (model stage) for silent flaws, data leakage, statistical validity, and config/implementation mismatches. Specific area under review: Baselines train on 600 real images per class.

## Response
In `configs/pipeline.yaml#train.baselines`, `per_class` is set to `600`, and `src/stage4_train/baselines.py` (`train_baselines`, lines 154-179) calls `balanced_subset(train_labels, per_class, rng)` to sample `min(600, count)` images without replacement per class before fitting `LogisticRegression` on raw pixels (`logreg_pixels`) and `LinearSVC` on HOG features (`svm_hog`). This yields `n_train = 6,000` (`600 x 10` classes, recorded in `results/phase2_snapshot/baselines.json`).

By contrast, the CNN arms (`A0`, `A1`, `B`, `A2`) draw class-balanced batches from the entire training split of `12,405` images (`results/phase2_snapshot/split_stats.csv`), where every class has more than `600` training examples - from `680` (`pentagon`, `mendeley_elkorchi` only) and `700` (`diamond`) up to `2,351` (`triangle`). Thus:
1. The scikit-learn baselines see fewer than half of the available unique training images (`6,000` vs `12,405`), leaving between `80` (`pentagon`) and `1,751` (`triangle`) real training images unused.
2. Any comparison between `logreg_pixels` / `svm_hog` and the CNN arms is not matched on unique training set size, even though both use a class-balanced distribution.

Because linear models on fixed pixel/HOG representations are included as lower-bound sanity-check reference points rather than competitive arms in the primary test, this does not invalidate the CNN experiment, but the `600`-per-class cap (`6,000` total) should be explicitly disclosed next to baseline results.

## Validation
The team checked `src/stage4_train/baselines.py`, `configs/pipeline.yaml`, `results/phase2_snapshot/split_stats.csv`, and `results/phase2_snapshot/baselines.json`:
- Verified per-class counts in `split_stats.csv` (`train` split, total `12,405`): `pentagon: 680`, `diamond: 700`, `ellipse: 701`, `star: 979`, `hexagon: 1,047`, `octagon: 1,048`, `rectangle: 1,399`, `square: 1,749`, `circle: 1,751`, `triangle: 2,351`. Every class indeed has at least `680` training images, so `balanced_subset(..., per_class=600)` always takes `600` per class (`n_train = 6,000`).
- Confirmed in `ShapeSense_Deployed/web/js/pages/stage4.js` (`line 107`) that the baselines card explicitly labels them: `"Reference points only. Macro-F1 in points."`

## Our decision
- **Team verdict: `Stands` (`Disclosed`).** Gemini 4 Neon's observation is correct. The team kept `per_class: 600` unchanged - avoiding an unnecessary retrain of baselines that are purely non-neural reference points - and disclosed that every class has at least `680` training images and that baselines serve as reference points only.

## Measured effect
- **Training sample count:** Baselines train on `6,000` class-balanced real images (`600` per class), vs `12,405` real images available to CNN arms (minimum class size `680` for `pentagon`).
- **Baseline reference scores (`baselines.json` / `metrics.csv`):** `logreg_pixels` (`best_C: 0.01`): `77.74` validation macro-F1, `77.9` test macro-F1 (`78.5%` test accuracy); `svm_hog` (`best_C: 1.0`, `hog_pixels_per_cell: 8`): `82.54` validation macro-F1, `84.3` test macro-F1 (`84.4%` test accuracy) - compared against `95.5-96.2` macro-F1 for the CNN ensembles (`metrics.csv`).

---

## Sample-Size Cap ($n = 600$/Class) in Classical Non-Neural Baselines (`A13`)

### Claim Metadata

* **Entry ID:** `A13` (`claim`, `3_modeling`)
* **Reviewer / Owner:** Gemini 4 Neon / ShapeSense Engineering Team
* **Calibration Tier:** `winning-decision (70% tier)`
* **Grounding Artifacts:** `src/stage4_train/baselines.py`, `configs/pipeline.yaml`, `results/phase2_snapshot/split_stats.csv`, `results/phase2_snapshot/baselines.json`, `results/phase2_snapshot/metrics.csv`, `ShapeSense_Deployed/web/js/pages/stage4.js`

### Mechanistic & Dataset Coverage Analysis

In `src/stage4_train/baselines.py#train_baselines`, `balanced_subset(train_labels, per_class=600, rng)` samples $\min(600, N_c)$ training examples without replacement per class prior to fitting `LogisticRegression` on flattened pixels (`logreg_pixels`) and `LinearSVC` on Histogram of Oriented Gradients (`svm_hog`). Across `split_stats.csv` ($N_{\text{train}} = 12,405$), every class exceeds the $600$-sample threshold:

| Class | Available Train ($N_c$) | Sampled Baseline ($n_c$) | Unused Real Images | Utilization Rate |
| --- | --- | --- | --- | --- |
| **Pentagon** | $680$ | $600$ | $80$ | $88.2\%$ |
| **Diamond** | $700$ | $600$ | $100$ | $85.7\%$ |
| **Ellipse** | $701$ | $600$ | $101$ | $85.6\%$ |
| **Star** | $979$ | $600$ | $379$ | $61.3\%$ |
| **Hexagon** | $1,047$ | $600$ | $447$ | $57.3\%$ |
| **Octagon** | $1,048$ | $600$ | $448$ | $57.3\%$ |
| **Rectangle** | $1,399$ | $600$ | $799$ | $42.9\%$ |
| **Square** | $1,749$ | $600$ | $1,149$ | $34.3\%$ |
| **Circle** | $1,751$ | $600$ | $1,151$ | $34.3\%$ |
| **Triangle** | $2,351$ | $600$ | $1,751$ | $25.5\%$ |
| **Total** | **$12,405$** | **$6,000$** | **$6,405$** | **$48.4\%$** |

While both the linear baselines and the CNN arms train on class-balanced distributions, the baselines utilize only $48.4\%$ ($6,000 / 12,405$) of unique real training images, leaving $6,405$ majority-class examples unused.

### Empirical Performance Context

Because fixed-feature linear classifiers are included solely as non-neural lower-bound sanity checks (`"Reference points only. Macro-F1 in points."` in `stage4.js`) rather than arms in the primary hypothesis tests, the $6,000$-sample cap does not affect experimental validity:

* **`logreg_pixels` (`best_C = 0.01`, $n = 6,000$):** $77.74$ val macro-F1; $77.9$ test macro-F1 ($78.5\%$ accuracy).
* **`svm_hog` (`best_C = 1.0`, `pixels_per_cell = 8`, $n = 6,000$):** $82.54$ val macro-F1; $84.3$ test macro-F1 ($84.4\%$ accuracy).
* **CNN Ensembles ($N = 12,405$):** $95.5$–$96.2$ test macro-F1 ($+11.2$ to $+18.3$ macro-F1 points above classical baselines).

### Resolution

* **Verdict:** **Stands** (`Disclosed`).
* **Action:** Kept `per_class: 600` unchanged to avoid unnecessary retraining of non-neural reference models, explicitly disclosing the $6,000$-image cap alongside baseline metrics.

