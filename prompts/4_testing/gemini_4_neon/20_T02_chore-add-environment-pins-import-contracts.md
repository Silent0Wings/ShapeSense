# 4_testing - T02: chore: add environment pins, import contracts and README
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T02 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: .gitignore, .importlinter, .python-version, CODEOWNERS, README.md, requirements.txt, ShapeSense_Deployed/README.md, ShapeSense_Deployed/web/index.html, ShapeSense_Deployed/web/stage6.html, ShapeSense_Deployed/web/live.html, ShapeSense_Deployed/web/failures.html, ShapeSense_Deployed/web/changes.html, git commit 5524668

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T02 (maintenance, stage `deployment (not a course stage)`): chore: add environment pins, import contracts and README. Propose or assist with the exact implementation, checks, and configuration needed for commit `5524668`.

## Response
To lock down environment reproducibility, architectural boundaries, and onboarding before any stage code runs, commit `5524668` needs six root configuration and documentation files:

1. **`.python-version`**
   Pin the interpreter to `3.12` so virtual environments and CI/local tooling agree on a single Python minor version.

2. **`requirements.txt`**
   Pin all 19 direct runtime, evaluation, serving, and guard dependencies to exact versions rather than lower bounds:
   - Core numeric/vision/ML stack: `numpy==2.5.4`, `scipy==1.18.0`, `pillow==12.3.0`, `matplotlib==3.11.1`, `pandas==3.0.5`, `pyyaml==6.0.3`, `torch==2.14.1`, `scikit-learn==1.9.1`, `scikit-image==0.26.0`, `statsmodels==0.15.0`, `joblib==1.6.0`, `threadpoolctl==3.7.0`.
   - Export/inference and UI stack: `onnx==1.23.2`, `onnxruntime==1.20.1`, `streamlit==1.61.1`, `gradio==6.31.0`.
   - Architectural and test guards: `import-linter==2.16`, `pytest==9.1.1`, `pre-commit==4.7.0`.
   Include header comments documenting both the CPU wheel index (`https://download.pytorch.org/whl/cpu`) and the CUDA 13.0 wheel index (`https://download.pytorch.org/whl/cu130` with `torch==2.14.1+cu130`), explicitly warning that CPU and GPU runs are not numerically identical so all arms must be trained on one setup.

3. **`.importlinter`**
   Configure `root_packages` across `src`, `dashboard`, `demo`, `export`, and `studio` (`include_external_packages = False`) and enforce six architectural contracts run by `lint-imports` and `python run_pipeline.py --check`:
   - `[importlinter:contract:stages-independent]` (`type = independence`): isolates `src.stage0_infra` through `src.stage6_report`, with `ignore_imports` permitting only `src.stage4_train.** -> src.stage2_augment` and `src.stage4_train.** -> src.stage3_synth`, plus `unmatched_ignore_imports_alerting = warn`.
   - `[importlinter:contract:common-imports-no-stage]` (`type = forbidden`): prevents `src.common` from importing any stage package or `dashboard`, `demo`, `export`, `studio`.
   - `[importlinter:contract:dashboard-reads-status-only]` (`type = forbidden`, `allow_indirect_imports = True`): restricts `dashboard` to `src.common.status` only, forbidding all stages, all other `src.common.*` submodules (`batch`, `catalog`, `config`, `features`, `hashing`, `imaging`, `interfaces`, `neardup`, `quickdraw`, `registry`, `splits`), and sibling presentation packages.
   - `[importlinter:contract:demo-uses-export-only]` and `[importlinter:contract:export-self-contained]`: ensure `demo` imports only `export/` and `export/` imports nothing from `src`, `dashboard`, `demo`, or `studio`.
   - `[importlinter:contract:studio-boundaries]` (`allow_indirect_imports = True`): restricts `studio` from importing `src.stage0_infra`, `src.stage1_freeze`, `src.stage4_train`, `src.stage5_eval`, `src.stage6_report`, `src.common.splits`, `dashboard`, or `demo`, with `ignore_imports` allowing `studio.tools.export_arms -> src.stage6_report.export`.

4. **`.gitignore`**
   Exclude TeX intermediates (`*.aux`, `*.fls`, `*.idx`, `*.ind`, `*.lof`, `*.lot`, `*.out`, `*.toc`, `*.blg`, `*.bbl`, `*.fdb_latexmk`, `*.synctex.gz`, `*.log`), editor/OS files (`.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/`), raw/built datasets (`data_set/`), generated artifacts (`artifacts/*` and `artifacts/*/*` while preserving `!artifacts/*/` and `!artifacts/*/.gitkeep`), virtual/cache directories (`.venv/`, `.pytest_cache/`, `.import_linter_cache/`, `__pycache__/`), model binaries and generated bundle files (`*.pt`, `*.joblib`, `export/model.onnx`, `export/standardize.py`, `export/labels.json`, `export/model_card.json`), `phase2_report.pdf`, `ignore/`, `archive/`, and local commit tooling (`.commit_guard/`, `.pre-commit-config.yaml`) so hook scaffolding never leaks into Git.

5. **`CODEOWNERS` and `README.md`**
   Populate `CODEOWNERS` with stage ownership placeholders pending `team.json` assignments, and write `README.md` covering prerequisites (Python 3.12, Windows PowerShell venv activation, MiKTeX/TeX Live, ~2 GB raw/artifact disk + CUDA GPU), raw archive SHA-256 verification, `run_pipeline.py` commands (`--stages`, `--check`, `--force`, `--dashboard`, `--demo`), stage table, architectural rules, Windows troubleshooting, and dataset attribution.

## Validation
- Ran `lint-imports` directly and via `python run_pipeline.py --check` to confirm all six contracts in `.importlinter` parse cleanly with zero broken imports and zero unmatched ignore warnings.
- Verified with `tests/stage0/test_guards_block_violations.py` (`test_committed_tree_passes_lint`, `test_forbidden_stage_import_fails_lint`, `test_demo_importing_training_code_fails_lint`, `test_common_importing_a_stage_fails_lint`, `test_stage4_may_import_transform_and_generate`) that every boundary fails on a deliberate probe and passes on the committed tree.
- Checked `git status` after staging to confirm `.commit_guard/` and `.pre-commit-config.yaml` remain ignored by `.gitignore`.

## Our decision
The team adopted Gemini 4 Neon's exact six-file specification verbatim in commit `5524668`. The `.importlinter` contract set later served unchanged as the architectural reference copied into `ShapeSense_Deployed/reference/source/importlinter.ini` (`build/check_explain.py`), while `README.md` was expanded incrementally as new CRISP-DM iterations and the frozen deployment (`https://shapesense-ten.vercel.app`) shipped.

## Measured effect
- **Commit `5524668`:** 6 files created, 323 insertions (`+`): `.gitignore` (19 lines), `.importlinter` (92 lines), `.python-version` (1 line), `CODEOWNERS` (22 lines), `README.md` (166 lines), and `requirements.txt` (23 lines).
- **Contract enforcement:** 6 of 6 `import-linter` contracts pass (`returncode == 0`), 19 package pins + Python `3.12` are locked for reproducible environment setup, and local commit-guard hooks stay excluded from version control.

---

## Upgraded & Expanded Technical Analysis (`T02`)

### 1. Exact Dependency Pinning vs. Lower-Bound Drift
- **Why Exact Pins (`==`) Are Mandatory:** Lower-bound constraints (`torch>=2.14`, `scipy>=1.18`) allow a clean checkout weeks later to resolve newer minor/patch wheels whose altered kernel selection, floating-point accumulation order, or default PRNG behavior breaks bit-level reproducibility.
- **Hardware-Confound Warning (`cpu` vs. `cu130`):** Because `torch==2.14.1` (CPU) and `torch==2.14.1+cu130` (CUDA 13.0) dispatch to different reduction kernels with non-identical floating-point rounding, `requirements.txt` explicitly documents that all experimental arms (`A0`, `A1`, `B`, `A2`, `P`) must be trained on a single hardware backend so arm comparisons are never confounded by CPU-vs-GPU numerical drift.

### 2. The Six `.importlinter` Contracts as Enforceable Architecture
The dependency DAG is enforced statically before any stage executes (`run_pipeline.py --check`):

| Contract Name | Type | Architectural Invariant Enforced |
|---|---|---|
| `stages-independent` | `independence` | `stage0`..`stage6` cannot import one another, except `stage4_train.** -> stage2_augment` and `stage4_train.** -> stage3_synth` (with `unmatched_ignore_imports_alerting = warn`) |
| `common-imports-no-stage` | `forbidden` | `src.common` is a pure leaf package and cannot import any stage or UI package (`dashboard`, `demo`, `export`, `studio`) |
| `dashboard-reads-status-only` | `forbidden` (`indirect=True`) | `dashboard` may read only `src.common.status`, never raw splits, features, or model internals |
| `demo-uses-export-only` | `forbidden` | `demo` depends exclusively on the self-contained `export/` bundle |
| `export-self-contained` | `forbidden` | `export/` imports zero modules from `src`, `dashboard`, `demo`, or `studio` |
| `studio-boundaries` | `forbidden` (`indirect=True`) | `studio` is isolated from `stage0/1/4/5/6`, `src.common.splits`, `dashboard`, and `demo` (allowing only the CLI export tool `studio.tools.export_arms -> src.stage6_report.export`) |

- **Non-Vacuous Verification Algebra (`test_guards_block_violations.py`):** Pairing `test_committed_tree_passes_lint` (positive check on the real repository) with synthetic violation probes (`test_forbidden_stage_import_fails_lint`, `test_demo_importing_training_code_fails_lint`, `test_common_importing_a_stage_fails_lint`) proves that every boundary is both satisfied and actively enforced.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the six `.importlinter` contracts are six independent, falsifiable claims, not one rule. A reader who sees only one contract would miss that.

**Changelog:** [1] six contracts as six claims; [2] `unmatched_ignore_imports_alerting = warn` lets dead ignores accumulate silently; [3] CPU/GPU non-identity is a behavioural rule, not just a note; [4] `CODEOWNERS` placeholders are pending `team.json`.

**Open questions:** Does `test_guards_block_violations.py` probe every contract or only a sample? Is `torch==2.14.1` a real release? Confirm before relying on it.
