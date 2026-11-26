# 3_modeling - C11: Synthetic share of a batch 
- LLM: Claude Opus 5.5, medium effort 
- Category: Two-LLM comparison. Other model's answer: [../gemini_4_neon/07_C11_synthetic-share-of-a-batch.md](../gemini_4_neon/07_C11_synthetic-share-of-a-batch.md)
- Date: 2026-11-09
- Entry: C11 (`change`, `3_modeling`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/3_modeling/inferred_prompts.md, configs/pipeline.yaml, src/stage4_train/sampling.py, docs/crisp_dm/iteration_2/preregistration.md, docs/crisp_dm/iteration_2/investigation/report.md, docs/crisp_dm/iteration_2/search/winners.json, commits 87711f3, 5acfb7c



## Prompt
Follow-up on the iteration 2 search. B has used `synthetic_fraction: 0.3` since the Phase 1 plan, and the new A2 arm also needs a synthetic share. Part of the team wants to keep 30% for B so it stays the arm we pre-registered in iteration 1; Gemini 4 Neon wants the share searched on validation per arm, together with the generator ranges. Which should we do, and how do we report the share so nobody misreads it?

## Response
Both positions protect something real, so I would separate what each one protects.

**The case for keeping 30%.** It keeps B recognisable as the iteration 1 arm, and it removes one degree of freedom from the search. That matters: every searched knob is one more way to fit validation.

**The case for searching it.** 30% was never chosen on evidence; like the augmentation ranges, it was set by hand. The investigation also found the synthetic stroke at 2 px against 3.1 px for real outlines, so the generator was off in a way that interacts with how much synthetic data each batch holds. Holding the share fixed while searching everything else would tune B around an arbitrary constraint, and A2 has no prior value at all.

**Resolution.** Search the share, but under the same rules as every other setting:
1. Iteration 1 is closed. Its B result at 30% stands and is not re-scored. Iteration 2 B is a re-tuned arm, reported as such.
2. Put the share inside the generator search for B and the batch-share search for A2, with ranges written down before training (A2: clean 0.1 to 0.6, synthetic 0.1 to 0.4, total at most 0.8). Report how many trials each arm received.
3. Select on validation macro-F1 only. Test stays sealed.

**Reporting.** A fraction hides rounding. The sampler takes `round(256 * share)`, so 30% is really 77 of 256 images. Report both: the configured share and the actual count per 256-image batch, for B and for A2. That also makes A2's three-way split readable as image counts.

| Choice | Fair to B | Fair to A2 | Search risk |
|---|---|---|---|
| Keep B at 30%, search A2 only | No, B gets one knob fewer | Yes | Lower |
| Search both, same rules | Yes | Yes | Bounded by the pre-registered limits |

I would take the second row. The fairness argument wins as long as the limits are fixed in advance.

## Validation
- `docs/crisp_dm/iteration_2/preregistration.md` lists the generator search on B (16 trials) and the A2 batch-share search (12 trials) before any iteration 2 training.
- `docs/crisp_dm/iteration_2/search/winners.json` freezes `arms.B.synthetic_fraction` 0.278 and `arms.A2.synthetic_fraction` 0.198, chosen on three-seed validation means.
- `src/stage4_train/sampling.py` documents the rounding (`256 * 0.3 = 76.8 -> 77`).

## Our decision
Synthetic share of a batch: B 30% -> B 71 of 256 images (configured 27.8%), A2 51 of 256 (configured 19.8%). Chosen by the validation search.

## Measured effect
No separate measurement of the share alone was recorded. The B winner scored 94.20 mean validation macro-F1 over three seeds and the A2 winner 95.17 (`winners.json`). In iteration 3 the search moved them again, to `synthetic_fraction` 0.168 for B and 0.12 for A2 (`configs/pipeline.yaml`).

---

## Synthetic Mixture Optimization & Discretization Reporting (Deep-Dive)

### Metadata & Lineage

* **Entry ID / Type:** `C11` (`change`, `3_modeling` — Two-LLM mediated comparison with `gemini_4_neon`)
* **Date:** `2026-11-09`
* **Owner / Proposed By:** `40256377` / `gemini_4_neon` (`mediated` by `opus_medium_5.5`)
* **Primary Artifacts:** `configs/pipeline.yaml`, `src/stage4_train/sampling.py`, `docs/crisp_dm/iteration_2/preregistration.md`, `docs/crisp_dm/iteration_2/search/winners.json`, commits `87711f3`, `5acfb7c`

### Methodological Conflict & Resolution

* **Position A (Freeze `B` at `0.30`):** Preserves strict continuity with Iteration 1's Phase 1 specification and avoids adding a degree of freedom that increases validation overfitting risk.
* **Position B (Search `synthetic_fraction` per arm):** `0.30` was an arbitrary heuristic rather than an empirical optimum. Furthermore, Iteration 2's investigation discovered a systematic domain gap in synthetic stroke width (`2.0 px` synthetic vs. `3.1 px` real outlines). Because synthetic fidelity interacts directly with optimal mixture ratio, holding `synthetic_fraction` fixed while tuning generator parameters would force `B` to optimize around an artificial bottleneck, while `A2` had no prior baseline at all.

#### Mediated Governance Protocol

1. **Strict Iteration Boundary:** Iteration 1's `B` benchmark at `0.30` remains closed and unamended; Iteration 2 `B` is explicitly reported as a re-tuned successor.
2. **Pre-Registered Budget & Bounds:** `synthetic_fraction` was jointly optimized inside `B`'s generator search (16 trials) and `A2`'s batch-share search (12 trials) under pre-registered bounds (`A2`: $f_{\text{clean}} \in [0.1, 0.6]$, $f_{\text{synth}} \in [0.1, 0.4]$, sum $\le 0.8$), selecting strictly on 3-seed validation macro-F1.
3. **Dual Continuous-Discrete Reporting:** Because `sampling.py` discretizes shares via `round(256 * share)` (e.g., $256 \times 0.30 = 76.8 \rightarrow 77$ images), reporting percentages alone obscures quantization step boundaries. All configs and reports mandate publishing **both** the continuous float parameter and exact integer image count per 256-image batch.

### Parameter Evolution Across Iterations

| Arm | Iteration 1 (Heuristic) | Iteration 2 (Validation Search) | Iteration 3 (60-Epoch Grouped CV) |
| --- | --- | --- | --- |
| **Arm `B`** | `0.300` $\rightarrow$ **77 / 256** (`30.1%`) | `0.278` $\rightarrow$ **71 / 256** (`27.7%`, Val F1: `94.20`) | `0.168` $\rightarrow$ **43 / 256** (`16.8%`) |
| **Arm `A2`** | *Not defined* | `0.198` $\rightarrow$ **51 / 256** (`19.9%`, Val F1: `95.17`) | `0.120` $\rightarrow$ **31 / 256** (`12.1%`) |

### Cross-Entry Systems Synthesis (Iteration 1 $\rightarrow$ Iteration 3)

| Entry | Layer | Core Bottleneck Addressed | Downstream Architectural Coupling |
| --- | --- | --- | --- |
| **`C14`** | Hardware / CUDA Runtime | Parent benchmark context + 3 workers = 4 CUDA tenants exceeding 8 GB VRAM (`F03`) | Capped `parallel_runs` at `2` in Iter 2, then `1` in Iter 3 to accommodate `BatchPool` (`F23`) |
| **`F23`** | IPC / OS Multiprocessing | File locks, cache key reuse, and unguarded teardown in persistent `spawn` pool | Cut per-trial runtime by `~25%` (`220 s` $\rightarrow$ `163–176 s`), enabling 191-trial Iter 3 search |
| **`C10`** | Data Manifold / Sampling | `A1` & `B` never saw clean real images; `A0` lacked rotational robustness | Introduced tri-modal `A2` batches; yielded `+9.20` macro-F1 on damaged hold-out in Iter 3 |
| **`C11`** | Mixture Parameterization | Arbitrary `0.30` synthetic share interacted with `2.0 px` vs `3.1 px` stroke gap | Validated dual float/integer batch reporting and per-arm fraction optimization |
| **`C12`** | Optimization Symmetry | Shared `(lr, dropout)` from `A1` seed 0 introduced directional arm bias | Exposed `A0`'s higher dropout need (`0.4`) in Iter 2 via equal-budget $3 \times 2$ grids |
| **`C13`** | Statistical Inference | `17.1 pt` OOD seed spread invalidated single-seed hold-out comparisons | Expanded to 5 main seeds + 3 LOSO seeds/arm, quantifying seed-level sign variance |

