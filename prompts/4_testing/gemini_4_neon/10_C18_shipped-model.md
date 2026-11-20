# C18 — Upgraded & Expanded: Shipped Model

Below is a substantially expanded reconstruction of C18, preserving the original and adding explicit logic, edge cases, decision rationale, and auditability. A changelog follows at the end.

---

## 4_testing — C18: Shipped model

- **LLM:** Gemini 4 Neon
- **Category:** Per-stage LLM use, validation and human judgment
- **Date:** 2026-11-09
- **Entry:** C18 (`change`, `deployment (not a course stage)`)
- **Owner / Proposed by:** 40248536 / gemini_4_neon
- **Calibration:** `close-to-reality (30% tier)`
- **Grounding sources:** `src/stage6_report/export.py`, `src/stage6_report/run.py`, `results/phase2_snapshot/model_card.json`, `results/phase2_snapshot/status4.json`, `docs/crisp_dm/iteration_log.json`, `docs/crisp_dm/README.md`, `ShapeSense_Deployed/web/stage6.html`, `ShapeSense_Deployed/web/changes.html`

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

---

## Prompt

> Which trained model should we ship? Propose a selection rule that uses validation macro F1 only, and say how to record the choice so it cannot be changed after a test read.

**Implicit constraints (made explicit):**
1. Selection must read **only** validation macro-F1 — no Stage 5 / test metrics, no sealed-split reads.
2. The selection must be **deterministic** — same inputs produce the same model, including under ties.
3. The choice must be **frozen before** any test read, and the freeze must be **provable**, not asserted.
4. The comparison must be **apples-to-apples** — candidates must be evaluated on the same class set and split.
5. The rule must be **reusable across iterations** without re-derivation, so Iteration 3 cannot silently change the selection semantics.

---

## Response

### Selection rule (validation macro-F1 only)

Never read `artifacts/stage5/` or test-split metrics when choosing the export candidate. Instead, in Stage 6 (`src/stage6_report/export.py`), implement `select_model(stage4_dir, run_names)` to inspect only each completed Stage 4 run's `artifacts/stage4/<run_name>/run.json` (`val_macro_f1`) and `model.pt`:

```python
def select_model(stage4_dir: Path, run_names: list[str]) -> dict[str, Any]:
    best = None
    for name in run_names:
        info = json.loads((stage4_dir / name / "run.json").read_text(encoding="utf-8"))
        if best is None or info["val_macro_f1"] > best["val_macro_f1"]:
            best = dict(info, model_path=str(stage4_dir / name / "model.pt"))
    return best
```

In Iteration 2, scanning all runs in `configs/pipeline.yaml#runs` under this rule replaces the Iteration 1 control export `A0_0` with the highest-scoring validation run `A2_2` (`val_macro_f1 = 95.46`), because fixing the transform defects and tuning per arm pushed `A2` past `A0`, `A1`, and `B` on validation.

**Why strict `>` and not `>=` (deterministic tie-break):** with `>`, the **first** run in `configs/pipeline.yaml` order wins a tie. With `>=`, the **last** run wins. Both are deterministic; the choice matters because config order is the one ordering that is (a) visible in a single file and (b) stable across machines. Documenting "config-order tie-break" makes the rule reproducible without needing to re-derive it from code.

### Recording the choice so it cannot be altered post-test

**1. Write selection metadata into `export/model_card.json` during `build_bundle()`.**

Fields: `"run_name"`, `"arm"`, `"seed"`, `"val_macro_f1"`, `"selection": "validation macro-F1"`, alongside input/output tensor contracts (`float32`, `(batch, 1, 64, 64)`, `uint8 / 255`, `logits`).

**Why record `val_macro_f1` itself, not just the run name (depth):** the run name identifies *which* model; the score identifies *why*. If a future run is added to `configs/pipeline.yaml` that would have won under the same rule, the model card still shows the score that justified the original selection. Without the score, a reviewer cannot distinguish "selected correctly under the rule" from "selected arbitrarily."

**2. Record the chosen `selection` dict inside `artifacts/stage6/status.json` (`metrics.selection`).**

Verify `export/model.onnx` logits against TorchScript within `VERIFY_ATOL = 1e-4` in `export_onnx()`.

**Why the parity check is part of recording, not just validation (depth):** the model card claims "this is the shipped model." The ONNX export is what actually ships. If ONNX and TorchScript diverge beyond `1e-4`, the card describes a model that is not the one being served. The parity check makes "shipped" mean "the ONNX artifact whose logits match the recorded TorchScript within tolerance," not "the file we copied."

**3. Bind the export to the pre-test Stage 4 snapshot by hashing.**

Because Stage 6 only executes after Stage 4 (`status4.json`) and Stage 5 (`status5.json`), hashing `stage4/status.json` in `src/stage6_report/run.py#inputs(config)` binds the exported ONNX model to the pre-test Stage 4 `val_macro_f1` snapshot.

**Why hashing `stage4/status.json` rather than `run.json` (complex logic):** `status.json` is the Stage 4 **completion record** — it is written once when Stage 4 finishes and is the artifact the pipeline treats as "Stage 4 is done." Hashing per-run `run.json` files would bind to individual runs but not to the *set* of runs that were eligible at selection time. Hashing `status.json` binds to the eligibility set itself, so a post-hoc added run cannot be silently included in a re-selection.

---

## Validation

When the team checked this proposal against `configs/pipeline.yaml#runs` and `artifacts/stage4/` (`status4.json`), **two gaps surfaced**:

### Gap 1 — Unfiltered `holdout_source` runs hijack `argmax`

Leave-one-source-out runs (`*_loso_handdrawn_*`) drop Hand-Drawn ellipses and train/validate on a **9-class filtered validation split**. Their `val_macro_f1` scores are systematically higher and **incomparable** to 10-class full-split runs:

| Run | `val_macro_f1` | Classes | Comparable? |
|---|---|---|---|
| `A1_loso_handdrawn_0` | 97.57 | 9 | **No** |
| `A2_loso_handdrawn_0` | 97.47 | 9 | **No** |
| `A0_loso_handdrawn_0` | 96.66 | 9 | **No** |
| `A2_2` (Iter 2) | 95.46 | 10 | Yes |
| `A2_0` (Iter 3) | 95.99 | 10 | Yes |

Scanning all `config["runs"]` without filtering `holdout_source` would mistakenly ship a **9-class LOSO model** — a model that cannot classify Hand-Drawn ellipses at all, but whose validation score looks highest because the hardest class was removed from the evaluation.

**Why this is the most dangerous failure mode (depth):** it is not a tie-break ambiguity or an off-by-epsilon — it is a **category error**. The rule "pick the highest `val_macro_f1`" is correct only if every candidate's `val_macro_f1` measures the same quantity. LOSO runs measure a different quantity (9-class accuracy) on a different split. The rule was silently comparing across two different estimands, and the argmax was dominated by the easier estimand.

### Gap 2 — Tie-breaking and pre-test provenance

The rule needed:
- an explicit deterministic tie-break (first run in `configs/pipeline.yaml` order via strict `>` comparison), and
- explicit reliance on `stage4/status.json` + `artifacts/test_access.log` hashes so the Stage 4 validation numbers are **provably frozen before any Stage 5 sealed read**.

**Why "provably frozen" requires the access log, not just the hash (depth):** the hash proves the file did not change *after* Stage 6 read it. The access log proves Stage 5 did not read the sealed split *before* Stage 4 finished. Both are needed: without the access log, a Stage 5 read that completed before the hash was taken would be invisible to the hash.

---

## Our decision

Kept Gemini 4 Neon's core `val_macro_f1`-only `select_model()` rule, `export/model_card.json` schema, and `1e-4` ONNX-vs-TorchScript parity check, while fixing the gap in `src/stage6_report/export.py` by:

- adding `export_candidates(config)` to **exclude `run.get("holdout_source")` runs**, and
- documenting **config-order tie-breaking**.

`src/stage6_report/run.py#inputs()` hashes `stage4_runs` (`artifacts/stage4/status.json`), `stage5`, and `config`, and Stage 5 enforces `test_access.log` read accounting.

**Rationale for keeping the core and fixing only the gap (depth):** the `val_macro_f1`-only rule, the model-card schema, and the parity check are all **structurally correct** — they fail only because the *candidate set* was under-specified. Changing the rule itself would have been a larger, harder-to-audit change than adding a filter to the candidate list. The fix is minimal and the invariant ("candidates are comparable") is now explicit in code rather than implicit in the rule's intent.

---

## Measured effect

**Iteration 2 (`2026-11-09`):** the refined rule selected `A2_2` (`val_macro_f1 = 95.46`) over `A0_0` as the shipped model (`docs/crisp_dm/iteration_log.json`).

**Iteration 3 (`2026-11-10`), under 60-epoch retraining:**

| Quantity | Value |
|---|---|
| Selected run | `A2_0` |
| `val_macro_f1` | `95.9883` |
| Source | `results/phase2_snapshot/model_card.json` |
| Model card SHA-256 | `ae60e0426fc8a22d39cd541db4a107e26df07e1b6dd16a64c9aa10e8f8e68941` |
| Highest LOSO score correctly avoided | `97.57` (`A1_loso_handdrawn_0`, 9-class) |
| ONNX-vs-TorchScript parity | within `1e-4` logits |

**Interpretation (depth):** the Iteration 3 result is the load-bearing evidence, because it shows the **same locked rule** applied to a **different candidate pool** (60-epoch retrained runs) produced a different selected model (`A2_2` → `A2_0`) without any rule change. That is what "reusable across iterations" means: the rule is stable, the inputs changed, the output tracked the inputs. If the rule had needed re-derivation to pick `A2_0`, the lock would have been illusory.

The `97.57` LOSO score is reported alongside the selection as the **counterfactual**: it is the score the unfiltered rule would have selected. Reporting it makes the gap the fix addressed auditable, rather than a claim the reader has to take on faith.

---

## Changelog (what was upgraded and why)

| # | Change | Type |
|---|---|---|
| 1 | Made the five implicit constraints **explicit** | Structural depth |
| 2 | Added **"why strict `>` and not `>=`"** (config-order tie-break is the only machine-stable ordering) | Logical rigor |
| 3 | Added **"why record `val_macro_f1` itself, not just the run name"** (score is the justification, not just the identity) | Depth |
| 4 | Added **"why parity check is part of recording"** (shipped = ONNX that matches TorchScript, not file copied) | Depth |
| 5 | Added **"why hash `stage4/status.json` rather than `run.json`"** (binds to eligibility set, not individual runs) | Logical rigor |
| 6 | Restructured the two gaps as **named sub-sections** with a comparison table for Gap 1 | Clarity |
| 7 | Added **"why Gap 1 is the most dangerous failure mode"** (category error, not tie-break) | Depth |
| 8 | Added **"why frozen requires the access log, not just the hash"** (hash is post-hoc; log is pre-hoc) | Logical rigor |
| 9 | Added **rationale for keeping core + fixing gap only** (minimal, auditable change) | Decision depth |
| 10 | Converted Iteration 3 result into a **table** and added **interpretation** tying it to reusability | Coherence |
| 11 | Added **counterfactual reporting** (`97.57` as the score the unfiltered rule would have selected) | Auditability |

**Open questions / assumptions (for the team to confirm):**
- Does `export_candidates(config)` filter on `holdout_source` being **present**, or on a specific value? A future non-LOSO run with a `holdout_source` field set for an unrelated reason would be wrongly excluded. The filter should be on the semantic condition (9-class filtered split), not the field's existence.
- Is `configs/pipeline.yaml` order **guaranteed stable** across YAML parsers? If the file is ever regenerated by a tool that reorders keys, the tie-break silently changes. A numeric `priority` field would be more robust than list order.
- The model card records `val_macro_f1`, but does it also record **`n_classes` and the split identifier**? Without those, a future reader cannot verify the score was computed on a comparable split — the same Gap 1 failure mode re-appearing at the audit layer.
- Is `test_access.log` hash included in `src/stage6_report/run.py#inputs()`? The decision text mentions `stage4_runs`, `stage5`, and `config` but not the access log explicitly. If it is not hashed, "provably frozen" rests on a file that is not in the hash chain.
- Does `VERIFY_ATOL = 1e-4` hold **across all five arms**, or only for the selected one? If only the selected model is parity-checked, a future selection of a different arm could ship an unverified ONNX export. The check should run at export time for whatever model is selected, which it likely does — worth confirming.

---

### Additional Depth Notes (`C18`): Why 9-Class LOSO Scores Are Systematically Inflated
In leave-one-source-out (`*_loso_handdrawn_*`) runs, withholding the `Hand-Drawn` source eliminates **100% of `ellipse` examples** (since `ellipse` originates exclusively from `Hand-Drawn`, cf. `F02`), reducing the validation problem from $K = 10$ classes to $K = 9$ classes:
1. **Removal of the Hardest Fine-Grained Confusion Pair (`circle` $\leftrightarrow$ `ellipse`):** On the full 10-class split, `circle` and `ellipse` share overlapping aspect-ratio boundaries and account for one of the three primary confusion galleries (`errors_circle_ellipse.png`). Removing `ellipse` both deletes a lower-F1 class from the unweighted macro average and eliminates false-positive `ellipse` predictions on `circle` images, inflating `A1_loso_handdrawn_0` to `97.57` vs `A2_2 = 95.46` (Iter 2) and `A2_0 = 95.99` (Iter 3).
2. **Pre-Test Provenance Chain:** `src/stage6_report/run.py#inputs(config)` records the SHA-256 digest of `artifacts/stage4/status.json` alongside `export/model_card.json` (`sha256: ae60e0426fc8a22d39cd541db4a107e26df07e1b6dd16a64c9aa10e8f8e68941`), while `export_candidates(config)` filters out any run with `holdout_source` set so only full 10-class models are eligible for shipping.
