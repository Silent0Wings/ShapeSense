# 4_testing - Stage 0 plan: infrastructure, guards and reproducibility

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-06 to 2026-11-08
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Write the owner brief for Stage 0 (infrastructure) and one implementation plan per task, mapped to every brief requirement in a coverage matrix.

## Response (saved output, verbatim)

### `stages/stage_0.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Stage 0 — Infrastructure and reproducibility

> Owner brief. Everything here is about Stage 0 only. The full project
> plan is `../implementation.md`; the issue review is `../plan_issues.md`.

- **Owner:** ______ (Stage 0 is ~0.5 day; this owner takes a full share
  of another stage — Stage 1 is the natural pairing)
- **Code folders:** `src/common/`, `run_pipeline.py`, `tests/contracts/`
- **Depends on:** nothing — day 1, parallel with Stage 1
- **Blocks:** no development work; every stage starts against stub contracts
- **Effort:** ~0.5 day

## Focus

Give all six later stages **one runnable, reproducible skeleton** with
shared configuration, artifact contracts, import boundaries, test-set
guards, environment setup and data sharing. Stage 0 supplies the rails;
it does not implement the experiment.

**The skeleton already exists.** `src/stageN_*/`, `src/common/`,
`configs/pipeline.yaml`, `configs/taxonomy.yaml`, `artifacts/stageN/`
and `run_pipeline.py` are committed. Stage 0 fills in what is missing
and moves the Phase 1 scripts in. It renames nothing — the plan adopted
these names in v4 precisely so that this stage stays small.

## Goals

1. Make the pipeline work end-to-end with stub stages on a clean clone.
2. Move the Phase 1 scripts into `src/stage1_freeze/` and `src/common/`
   **without changing their output**.
3. Make `configs/pipeline.yaml` the only source of shared experimental
   settings, and `configs/taxonomy.yaml` the only source of class
   definitions.
4. Make boundary violations and test-set misuse fail automatically.
5. Let a new teammate install, pull data, run checks and open the
   dashboard from one README.

## Out of scope

- Splitting data, augmentation, generation, training or evaluation.
- Choosing experimental results or changing Phase 1 standardization.
- Building dashboard/demo features (Stage 6 owns those applications).

## Inputs

| Input | Where |
|---|---|
| Existing Phase 1 scripts | `scripts/` |
| Report build command | `build.ps1` |
| Team names | `team.json` |
| Raw/local data | `data_set/` (gitignored) |
| Committed skeleton | `src/`, `configs/`, `run_pipeline.py` |
| Pipeline and interface decisions | `implementation.md` Decisions 4–6, 13–16 |

## Requirements

**Must**
- R1. Add the folders that do not exist yet: `artifacts/stage0/`,
  `tests/contracts/`, `dashboard/`, `demo/`, `export/`. Do **not**
  rename anything that is already committed.
- R2. Before moving any script, record the existing catalog hash, row
  count, class counts and per-(source,label) pHash groups. After the
  move, rerun the build and reproduce all of them exactly; any
  difference fails Stage 0 rather than becoming a silent data change.
  This proves *the move* changed nothing. Decision 15's deliberate
  change to pHash grouping scope happens in Stage 1 and is expected to
  move the numbers — do not confuse the two.
- R3. Remove `sys.path` hacks and private cross-script imports such as
  `audit_dataset.py → build_unified_dataset._qd_loader`
  (`audit_dataset.py:21–22`); `_qd_loader` becomes a public helper in
  `common`.
- R4. Implement config loading with validation and clear errors, for
  both files: `configs/pipeline.yaml` (seed set, split, arms,
  augmentation ranges, synthetic ratio, step budget, training defaults,
  tuning grid, evaluation criterion) and `configs/taxonomy.yaml`
  (classes, ambiguity margins, label-safety rules).
- R5. Replace the hard-coded constants in `src/common/batch.py`
  (`IMAGE_SIZE`, `IMAGE_CHANNELS`, `SYNTHETIC_FRACTION = 0.3`) with
  config reads. Two sources of truth for the synthetic ratio is exactly
  the failure mode the plan forbids.
- R6. Update `src/common/interfaces.py` to the frozen hand-off
  signatures: `TransformFn` gains the `rng` parameter it currently
  lacks, and `GeneratorFn.sample` becomes `generate(label, rng)`.
  Stages 2 and 3 cannot meet their reproducibility requirement without
  this.
- R7. Extend `run_pipeline.py` with `--check`, `--dashboard`, `--demo`,
  `--force`, and the hash-cache skip. Guards run before any stage.
- R8. Implement `common.status` (schema, writer, one `run_id` per
  invocation, input-hash cache) and `common.load_split` (test guard plus
  the append-only `artifacts/test_access.log`, one line per read:
  `iso_timestamp, run_id, caller_module, split, n_rows`). The log is
  never truncated; callers check only lines carrying the current
  `run_id`.
- R9. Add import-linter, pytest contract-test skeletons, pre-commit and
  CODEOWNERS configuration.
- R10. Ship placeholder LaTeX tables from the Stage 5 stub
  (`artifacts/stage5/tables/*.tex`, each containing a dash). `build.ps1`
  runs with `-halt-on-error`, so without them the report cannot compile
  until Stage 5 finishes — and Stage 6 starts its figure work on day 1.
- R11. Pin Python and dependency versions; document CPU-only and GPU
  setup if both are supported.
- R12. Publish the raw archive plus its SHA-256 in the shared folder and
  verify that a second machine retrieves the same hash.
- R13. Write `README.md`: prerequisites, environment creation, data
  pull, all run commands, owner map, artifact layout and troubleshooting.
- R14. `artifacts/`, model checkpoints and `data_set/` stay out of Git.
  The split manifests in `configs/splits/` are the deliberate exception
  (Decision 16) — they are committed.

**Should**
- Provide stub stage entry points that write `not_run` status files.
- Keep the contracts compatible with DVC in case the team adopts it
  later; nothing in this stage should depend on it.
- Document Windows execution-policy and Python-on-PATH fixes.

## Deliverables

- Completed skeleton and migrated public modules.
- Validated `configs/pipeline.yaml` and `configs/taxonomy.yaml`; extended
  `run_pipeline.py`.
- `common.status`, `common.load_split`, `common.hashing`; updated
  `interfaces.py` and `batch.py`.
- Placeholder Stage 5 LaTeX tables so the report compiles on day 1.
- Pinned environment, shared-folder data setup and `README.md`.
- Migration-equivalence report in `artifacts/stage0/`.
- `artifacts/stage0/status.json`.

## Done when

- [ ] A clean clone follows the README and reaches seven stub status
      files **and a compiling report PDF**.
- [ ] A second run skips every unchanged stage.
- [ ] Catalog hash, counts and pHash groups match the pre-move record.
- [ ] A deliberate cross-stage import and a fake test-set read are blocked.
- [ ] A second machine retrieves raw data with an identical SHA-256.
- [ ] All owners can run their contract tests without other stages
      implemented.

## Interfaces you provide

- `common.config`, `common.status`, `common.load_split`.
- Root commands and artifact/status conventions.
- No stage-specific scientific logic.

## Pitfalls

- **Refactoring behavior while moving files** — move first, prove output
  equivalence, then make separately reviewed improvements.
- **Shared SQLite connections across Windows workers** — each training
  worker must open its own read-only connection (benchmarked in Stage 4).
- **Two sources of truth for a number** — the committed `batch.py`
  already duplicates the synthetic ratio from `configs/pipeline.yaml`.
  Find the rest before someone edits one of them.
- **Truncating `test_access.log` to make a check pass** — the check is
  scoped to `run_id` for exactly this reason. Resetting the file
  destroys the audit trail it exists to provide.
- **Stub status looking like success** — stubs must say `not_run`, never
  `passed`.
- **Guard theater** — a configuration file is not enough; the Done-when
  checks require deliberate violations to fail.

## Glossary

- **Reproducible run**: the same code, data and settings produce the same
  outputs. Example: rerunning Stage 1 with seed 42 gives identical manifests.
- **Pipeline DAG**: stages connected by their input/output dependencies.
  Example: Stages 2 and 3 both depend on Stage 1 but not on each other.
- **Caching**: reusing a stage output when none of its inputs changed.
  Example: editing only the report does not retrain the CNN.
- **Contract test**: a test of a public interface rather than its internals.
  Example: `generate()` must always return a 64×64 uint8 image.
- **Pre-commit hook**: a local check run before a commit is accepted.
  Example: import-linter rejects `stage2_augment → stage3_synth`.
- **Shared data folder**: storage for data too large or unsuitable for
  Git, identified by a published hash. Example: a OneDrive folder whose
  archive SHA-256 matches on every machine.
- **Run id**: one identifier minted per pipeline invocation and written
  into every stage's status file. Example: Stage 5 counts the test reads
  carrying today's run id and ignores yesterday's.
- **Migration equivalence**: proof that restructuring code did not change
  its output. Example: the catalog hash is identical before and after.

## Missions

### M1 Identify the boundary violation (recognition)
Prompt: which imports violate the plan?

1. `stage4_train` imports `stage2_augment.transform`.
2. `stage2_augment` imports `stage3_synth.generate` to preview images.
3. `stage1_freeze` imports `common.phash`.
4. `demo` imports `stage4_train.SmallCNN` to rebuild the model.

Expected outcome: 2 and 4 violate the boundaries. 1 and 3 are allowed.
The demo must use the exported bundle, not training code.

### M2 Fail-closed status writer (application)
Prompt: implement a helper that always leaves valid machine-readable
status, including on failure.

```python
def run_stage(name, fn, **metadata):
    started = utc_now()
    try:
        result = fn()
        write_status(name, status="passed", started_at=started,
                     finished_at=utc_now(), **result)
    except Exception as exc:
        write_status(name, status="failed", started_at=started,
                     finished_at=utc_now(), error=str(exc), **metadata)
        raise
```
Expected outcome: a successful stub writes `passed`; a stub that raises
writes `failed` and exits nonzero; neither can silently leave stale
`passed` output from an earlier run.

### M3 One-click clean-clone rehearsal (synthesis)
Prompt: rehearse the whole owner hand-off using stub stages.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pre-commit install
python run_pipeline.py --check
python run_pipeline.py
python run_pipeline.py              # second run: all cached
python run_pipeline.py --dashboard
```
Expected outcome: every command is documented in the README; the first
run creates seven `not_run`/stage-result files and a compiling
`phase2_report.pdf` built from placeholder tables, the second skips
unchanged work, and the dashboard renders missing artifacts without
errors. Temporarily add a forbidden import and verify that the run stops
before Stage 1.
````

### `10_coverage_matrix.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** IN PROGRESS — coverage matrix: every brief requirement → one tracker entry

# Plan 10: Coverage matrix (stage briefs → tracker entries)

**Stage:** all (`stages/stage_0.md` … `stage_6.md`) · **Plan refs:** `implementation.md` v4, Decisions 1–16
**Tracker:** `ignore/todo.md` § "Phase 2 build"

Every **Must** R-number, **Should**, **Done when** box and **Deliverable** in the seven briefs maps
to exactly one entry (`E11` … `E35` = plan `11` … `35`). Status: `open`, `met` (evidence in the
entry's `done` line), `BLOCKED-ON-HUMAN`, or `DEFERRED` (Shoulds only, with reason).
Brief Done-when boxes are **not** ticked in `stages/*.md` (the stage owner owns them); they are
tracked here.

> 2026-11-08 (later): the GPU rerun closed E19, E28, E30, E32, E33 and E35. The note below is history.

> 2026-11-08: E28 (R14), E30, E32, E33 and E35 stay `open` because Stage 4 ended `failed` on the
> Decision 12 LOSO runs (P-61). See `ignore/handoff_phase2.md`.

## Entries

| Entry | Plan | Title |
|---|---|---|
| E11 | [11](11_s0_config_schema.md) | S0 config keys + validated loader |
| E12 | [12](12_s0_batch_interfaces.md) | S0 `batch.py` config reads + frozen interfaces |
| E13 | [13](13_s0_hashing_status.md) | S0 `common.hashing` + `common.status` |
| E14 | [14](14_s0_load_split_guard.md) | S0 `common.load_split` test guard + access log |
| E15 | [15](15_s0_script_migration.md) | S0 Phase 1 script migration + equivalence proof |
| E16 | [16](16_s0_runner.md) | S0 `run_pipeline.py` flags, hash cache, Stage 0 + stubs |
| E17 | [17](17_s0_guards.md) | S0 import-linter, pre-commit, CODEOWNERS, contract tests |
| E18 | [18](18_s0_placeholder_tables.md) | S0 placeholder LaTeX tables + Phase 2 report skeleton |
| E19 | [19](19_s0_env_readme.md) | S0 environment pins, README, data hash, gitignore |
| E20 | [20](20_s1_md5_gemstones.md) | S1 md5 pass, gemstone filter, contact sheet |
| E21 | [21](21_s1_group_split.md) | S1 global pHash groups, group split, leakage asserts, manifests |
| E22 | [22](22_s1_split_stats_fd.md) | S1 split stats, noise bands, FD check on filtered rows |
| E23 | [23](23_s1_source_classifier.md) | S1 source-classifier shortcut check |
| E24 | [24](24_s2_transform.md) | S2 class-safe `transform` + QA |
| E25 | [25](25_s3_generator.md) | S3 `generate` + margins + QA + throughput |
| E26 | [26](26_s4_loader.md) | S4 loader, batch mixer, benchmark |
| E27 | [27](27_s4_baselines.md) | S4 baselines (logreg pixels, linear SVM HOG) |
| E28 | [28](28_s4_cnn_training.md) | S4 CNN, tuning grid, arm × seed sweep, seed disagreement |
| E29 | [29](29_s5_statistics.md) | S5 pure metrics + statistics + verdict |
| E30 | [30](30_s5_evaluation_run.md) | S5 power check, test evaluation, tables, figures, galleries |
| E31 | [31](31_s6_dashboard.md) | S6 read-only dashboard |
| E32 | [32](32_s6_export.md) | S6 ONNX export bundle |
| E33 | [33](33_s6_demo.md) | S6 draw-and-infer demo |
| E34 | [34](34_s6_phase1_report_fixes.md) | S6 Phase 1 report fixes |
| E35 | [35](35_s6_phase2_report.md) | S6 Phase 2 report, traceability, Stage 6 run |

## Matrix

| Stage | ID | Requirement (short) | Kind | Entry | Status |
|---|---|---|---|---|---|
| S0 | R1 | add stage0/, tests/contracts, dashboard/, demo/, export/; rename nothing | Must | E16 | open |
| S0 | R2 | record + reproduce catalog hash, counts, per-(source,label) pHash groups across the move | Must | E15 | open |
| S0 | R3 | remove sys.path hacks + private `_qd_loader` import | Must | E15 | open |
| S0 | R4 | validated config loading for both YAML files | Must | E11 | open |
| S0 | R5 | `batch.py` constants → config reads | Must | E12 | open |
| S0 | R6 | `TransformFn` gains rng; `GeneratorFn.sample` → `generate` | Must | E12 | open |
| S0 | R7 | runner `--check --dashboard --demo --force` + hash-cache skip; guards first | Must | E16 | open |
| S0 | R8 | `common.status` (schema, writer, run_id, cache) + `common.load_split` (guard + log) | Must | E13 + E14 | open |
| S0 | R9 | import-linter, contract-test skeletons, pre-commit, CODEOWNERS | Must | E17 | open |
| S0 | R10 | placeholder `artifacts/stage5/tables/*.tex` | Must | E18 | open |
| S0 | R11 | pin Python + deps; CPU/GPU setup notes | Must | E19 | met |
| S0 | R12 | raw archive + SHA-256 on shared folder, verified on 2nd machine | Must | E19 | open (2nd machine: BLOCKED-ON-HUMAN) |
| S0 | R13 | README: prereqs, env, data pull, commands, owner map, layout, troubleshooting | Must | E19 | met |
| S0 | R14 | artifacts/, checkpoints, data_set/ out of Git; configs/splits committed | Must | E19 | met |
| S0 | Sh1 | stub entry points write `not_run` | Should | E16 | open |
| S0 | Sh2 | contracts DVC-compatible; nothing depends on DVC | Should | E19 | met |
| S0 | Sh3 | Windows execution-policy / PATH docs | Should | E19 | met |
| S0 | D1 | clean clone → README → 7 stub status files + compiling report PDF | Done | E19 | met |
| S0 | D2 | second run skips every unchanged stage | Done | E16 | open |
| S0 | D3 | catalog hash, counts, pHash groups match pre-move record | Done | E15 | open |
| S0 | D4 | deliberate cross-stage import and fake test read are blocked | Done | E17 | open |
| S0 | D5 | second machine retrieves raw data with identical SHA-256 | Done | E19 | BLOCKED-ON-HUMAN |
| S0 | D6 | owners can run contract tests without other stages | Done | E17 | open |
| S0 | Dl | deliverables: migration report, stage0/status.json, validated configs, README | Deliv | E15/E16/E11/E19 | open |
| S1 | R1 | md5 of standardized array, manifest column | Must | E20 | open |
| S1 | R2 | gemstone list matched on md5; fail on 0 or >1 match; count recorded | Must | E20 | open (list itself: BLOCKED-ON-HUMAN) |
| S1 | R3 | pHash groups over ALL images (Hamming ≤ 2) | Must | E21 | open |
| S1 | R4 | every group in exactly one split | Must | E21 | open |
| S1 | R5 | no image_id / md5 in two splits | Must | E21 | open |
| S1 | R6 | ratios from config | Must | E21 | open |
| S1 | R7 | same seed + catalog → byte-identical manifests | Must | E21 | open |
| S1 | R8 | FD check on filtered rows | Must | E22 | open |
| S1 | R9 | R4/R5 failure → status failed, no manifests | Must | E21 | open |
| S1 | R10 | manifest schema `image_id, md5, label_id, source_id, phash_group, split` | Must | E21 | open |
| S1 | R11 | manifests in configs/splits/ and committed | Must | E21 | open (commit: BLOCKED-ON-HUMAN, no git) |
| S1 | R12 | per-class test counts + noise bands → split_stats.csv | Must | E22 | open |
| S1 | R13 | source classifier on ≥2-source classes, train/val only, trigger > 10 pts | Must | E23 | open |
| S1 | R14 | notify Stages 4–6 if trigger fires | Must | E23 | open |
| S1 | Sh1 | stratify by class and source; report source share of test | Should | E21 | open |
| S1 | Sh2 | publish new counts (don't force Phase 1 numbers) | Should | E22 | open |
| S1 | D1 | leakage assertions pass | Done | E21 | open |
| S1 | D2 | every gemstone row matched exactly one md5; count recorded | Done | E20 | BLOCKED-ON-HUMAN (list) |
| S1 | D3 | new counts published + handed to Stage 6 | Done | E22 | open |
| S1 | D4 | seed + catalog hash in status.json inputs | Done | E21 | open |
| S1 | D5 | manifests committed in a PR | Done | E21 | BLOCKED-ON-HUMAN (git) |
| S1 | D6 | manifest contract tests pass | Done | E21 | open |
| S1 | D7 | source-classifier result + shortcut_detected written; owners notified | Done | E23 | open |
| S1 | Dl | split_stats.csv, source_classifier.json, status.json, configs/splits/*.csv | Deliv | E21/E22/E23 | open |
| S2 | R1–R7 | signature; 64×64 uint8 B/W; label unchanged; config disable list; rng only; no disk; no stage imports | Must | E24 | open |
| S2 | Sh1 | shape stays inside frame | Should | E24 | open |
| S2 | Sh2 | noise/blur keep 2-px outlines | Should | E24 | open |
| S2 | D1 | QA sheet: zero label-changing artifacts | Done | E24 | open |
| S2 | D2 | disable rules read from taxonomy.yaml | Done | E24 | open |
| S2 | D3 | transform contract tests pass | Done | E24 | open |
| S2 | Dl | transform, artifacts/stage2/qa/qa_sheet.png, status.json | Deliv | E24 | open |
| S3 | R1–R8 | signature; format; margins; rng; no disk; no stage imports; no literals; ≥ 2,000 img/s | Must | E25 | open |
| S3 | Sh1 | any rotation for every class | Should | E25 | open |
| S3 | Sh2 | star inner ≤ 0.6 × outer | Should | E25 | open |
| S3 | D1–D4 | QA passes; margins tested; throughput met; ranges logged | Done | E25 | open |
| S3 | Dl | generate, param_ranges.json, qa/qa_sheet.png, status.json | Deliv | E25 | open |
| S4 | R1 | one architecture/optimizer/step budget/schedule/batch/early-stop from config | Must | E28 | met |
| S4 | R2 | arms differ only in data stream | Must | E28 | met |
| S4 | R2b | steps_per_epoch frozen once from A0; B real-draw note in status | Must | E28 | met |
| S4 | R3 | same seed list for every arm | Must | E28 | met |
| S4 | R4 | tune once on A1 val, freeze for all | Must | E28 | met |
| S4 | R5 | Decision 8 defaults; selected epoch recorded | Must | E28 | met |
| S4 | R6 | class-balanced real sampling; B synthetic share class-balanced | Must | E26 | open |
| S4 | R7 | B batches 70/30 per batch; synthetic augmented too | Must | E26 | open |
| S4 | R8 | never read test; no log line for this run_id | Must | E28 | met |
| S4 | R9 | reproducible from (arm, seed) incl. workers | Must | E26 | open |
| S4 | R10 | ≥ 100-batch benchmark + per-run and all-run estimates | Must | E26 | open |
| S4 | R11 | seed disagreement → seed_disagreement.json | Must | E28 | met |
| S4 | R12 | save validation softmax probabilities | Must | E28 | met |
| S4 | R13 | both baselines on A0 stream, selected on val, saved loadable | Must | E27 | open |
| S4 | R14 | LOSO Hand-Drawn A1/B if trigger fired | Must | E28 | met (9-class LOSO, P-61 decided) |
| S4 | Sh1 | baselines first | Should | E27 | open |
| S4 | Sh2 | 3 seeds first, 4–5 if budget allows | Should | E28 | met |
| S4 | Sh3 | per-epoch loss/accuracy log | Should | E28 | met |
| S4 | Sh4 | per-worker read-only SQLite connection | Should | E26 | open |
| S4 | D1–D8 | runs + baselines; tuning recorded; steps frozen; selection; probs; benchmark/disagreement; LOSO; clean log | Done | E28 (D6 shared with E26/E27) | open |
| S4 | Dl | <arm>_<seed>/{model.pt,train_log.csv,val_curve.png,val_probs.npz}, baselines/, tuning.json, loader_benchmark.json, seed_disagreement.json, status.json | Deliv | E26/E27/E28 | open |
| S5 | R1 | one test read per model; len(runs)+2; echoed in checks.test_reads | Must | E30 | met |
| S5 | R2 | metrics per seed/ensemble/baseline incl. per-source, per-domain | Must | E29 + E30 | open |
| S5 | R3 | confusion pairs square/diamond, square/rectangle, circle/ellipse | Must | E30 | met |
| S5 | R4 | primary B vs A1 on soft-vote ensembles | Must | E29 | open |
| S5 | R5 | paired bootstrap CI; McNemar supporting; per-seed separately | Must | E29 | open |
| S5 | R6 | Holm on two secondary McNemar p-values | Must | E29 | open |
| S5 | R7 | locked criterion with per-class max(2.0, band) from split_stats.csv | Must | E29 | open |
| S5 | R8 | power check on validation BEFORE first test read | Must | E30 | met |
| S5 | R8b | error galleries for the three pairs | Must | E30 | met |
| S5 | R9 | verdict in metrics.verdict; stage still passed | Must | E30 | met |
| S5 | R10 | per-source tables + LOSO on Hand-Drawn if trigger fired | Must | E30 | met |
| S5 | Sh1 | asterisk pentagon/ellipse if shortcut | Should | E30 | met |
| S5 | Sh2 | "generator adds little" sentence if A1 closes the gap | Should | E30 | open |
| S5 | D1–D8 | power check first; verdict + CIs; read count; thresholds from csv; separation; galleries; LOSO; CSV + LaTeX | Done | E30 | met |
| S5 | Dl | predictions/, tables/{metrics,comparisons}.{csv,tex}, figures/, power_check.json, status.json | Deliv | E30 | met |
| S6 | R1 | Figure 2 TikZ extension, ≥ 0.60\linewidth | Must | E34 | open |
| S6 | R2 | Section A: three arms | Must | E34 | open |
| S6 | R2b | Split paragraph: new counts from Stage 1 | Must | E34 | open |
| S6 | R3 | gemstone filter + removed count in C, D, label table | Must | E34 | open |
| S6 | R4 | typo fixes | Must | E34 | open |
| S6 | R5 | results tables via \input from stage5 tables | Must | E35 | met |
| S6 | R6 | limitations section | Must | E35 | met |
| S6 | R7 | generator parameter ranges from param_ranges.json | Must | E35 | met |
| S6 | R8 | build via `build.ps1 -File phase2_report.tex` | Must | E35 | met |
| S6 | R8b | Decision 13 equal-compute framing | Must | E35 | met |
| S6 | R9–R11 | dashboard read-only, 8 tabs, grey not-run | Must | E31 | open |
| S6 | R12 | ONNX export + predict/standardize/labels + smoke test | Must | E32 | met |
| S6 | R13–R17 | demo canvas, Infer/Clear, export-only, edge cases, informal evidence | Must | E33 | met |
| S6 | R18 | fig:crisp Deployment updated | Must | E34 | open |
| S6 | R19 | same-source vs unseen-source labelling | Must | E35 | met |
| S6 | R20 | rubric checklist | Must | E35 | BLOCKED-ON-HUMAN (rubric) |
| S6 | R21 | attribution in report + export/README; redistribution statement | Must | E32 + E35 | open (license choice: BLOCKED-ON-HUMAN) |
| S6 | Sh1 | ablations (B_equalreal, ratios, per-aug, sketch slice) | Should | E35 | open |
| S6 | Sh2 | error galleries from stage5 figures | Should | E35 | met |
| S6 | D1–D9 | compiles; traceable; framing; claims labelled; export; attribution; rubric; dashboard; demo | Done | E35 (D5 E32, D8 E31, D9 E33, D7 BLOCKED) | open |
| S6 | Dl | phase1 fixes, phase2 PDF, dashboard/app.py, export/, demo/app.py, stage6/status.json, export/README.md | Deliv | E31–E35 | open |

## Unmapped rows
None. (Checked 2026-11-07: every brief R-number, Should, Done-when box and deliverable above has an entry.)
````

### `11_s0_config_schema.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E11 evidence line

# Plan 11: S0 config keys + validated loader

**Stage:** `stages/stage_0.md` R4 (Deliverable: validated configs) · **Plan refs:** `implementation.md` Decisions 3, 6–8, 10, 11, 13, 14; § Shared conventions
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E11) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`configs/pipeline.yaml` lacks `augment`, `synth`, `train` (incl. `steps_per_epoch`, tuning grid), `runs`, `filter_gemstones`, `evaluation`, `split.seed`, `split.phash_hamming_max`. `src/common/config.py` loads YAML with no validation, so a typo surfaces deep inside a stage.

## 2. Root Cause & Investigation
`src/common/config.py:8` is a bare `yaml.safe_load`. Brief S1 reads `seed`/`split`/`filter_gemstones`; S2 `#augment`; S3 `#synth`; S4 `#runs`/`#train`/`#evaluation`; S5 `success_criterion` + `evaluation`. None exist yet.

## 3. Architecture & Modular Design Strategy
Orchestrator-owned shared files. `load_config(path)` returns the pipeline dict with the taxonomy merged under `taxonomy` (path from `paths.taxonomy`). Pure validators `validate_pipeline(d)` / `validate_taxonomy(d)` raise `ConfigError` naming the key path. Values copied verbatim from the Decisions; where a Decision gives no number (augmentation/synthetic ranges) the choice is recorded in §6. `success_criterion` is untouched (Decision 3 lock).

## 4. Proposed Changes by File
- `configs/pipeline.yaml`: add `image_channels`, `filter_gemstones: false`, `split.seed: 42`, `split.phash_hamming_max: 2`, `paths.{taxonomy,metadata,unified_dir,gemstone_ids,test_access_log}`, `augment`, `synth`, `train` (Decision 8 + `steps_per_epoch: null`, `tuning` grid Decision 7), `runs` (arm × seed_set), `evaluation` (n_boot, alpha, shortcut_trigger_points 10, power_halfwidth_limit_points 1.0, bootstrap_seed).
- `src/common/config.py`: `ConfigError`, `validate_pipeline`, `validate_taxonomy`, `load_config` (merge + validate).
- `tests/common/test_config.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_config.py::test_committed_configs_validate`, `::test_missing_key_named_in_error`, `::test_ratios_must_sum_to_one`, `::test_runs_reference_known_arms_and_seed_set`, `::test_unfair_runs_rejected` (S4 M1: per-run epochs/steps/lr overrides or a seed outside seed_set are rejected), `::test_taxonomy_disable_list_names_known_classes`.
- **Break verification**: drop the ratio-sum check → `test_ratios_must_sum_to_one` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Augmentation ranges (no Decision gives numbers): rotation ±180° (taxonomy: any rotation for every class), uniform scale 0.85–1.15, non-uniform extra ±10 %, shear ±12°, noise p 0.3 σ 6 grey levels, blur p 0.3 σ 0.4–0.8 px. Synthetic ranges: radius 16–28 px, stroke 2 px, centre jitter ±4 px, ellipse ratio 1.2–2.5, rectangle ratio 1.2–3.0, diamond acute angle 40–80°, star inner/outer 0.35–0.6.
- `steps_per_epoch: null` until E28 freezes it from A0; `train.lr`/`dropout` start at Decision 8 defaults and are replaced by the Decision 7 grid winner (E28).
- Frozen-file rule: this is the one sanctioned edit (Stage 0 owner); later edits need team review.
````

### `12_s0_batch_interfaces.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E12 evidence line

# Plan 12: S0 batch.py config reads + frozen interfaces

**Stage:** `stages/stage_0.md` R5, R6 · **Plan refs:** `implementation.md` § Shared conventions (Hand-off interfaces); Decision 11
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E12) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`src/common/batch.py` hard-codes `IMAGE_SIZE`, `IMAGE_CHANNELS`, `SYNTHETIC_FRACTION = 0.3` (two sources of truth). `interfaces.py` `TransformFn.__call__(image, label)` lacks `rng`; `GeneratorFn.sample` must become `generate(label, rng)`.

## 2. Root Cause & Investigation
`src/common/batch.py:12-14`; `src/common/interfaces.py:18,30`.

## 3. Architecture & Modular Design Strategy
`batch.py` keeps the `Batch` dataclass plus `validate_batch(batch, image_size, channels)`; constants are gone, sizes come from config. Protocols: `TransformFn(img, label, rng) -> ndarray`, `GeneratorFn(label, rng) -> ndarray` (callables, so plain functions satisfy them), `ModelHandle.predict_proba`. No stage imports.

## 4. Proposed Changes by File
- `src/common/batch.py`, `src/common/interfaces.py`.
- `tests/common/test_batch.py`, `tests/contracts/test_interfaces.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_batch.py::test_no_hardcoded_constants`, `::test_validate_batch_shape_dtype_range`, `::test_validate_batch_rejects_mask_length_mismatch`; `test_interfaces.py::test_transform_protocol_takes_rng`, `::test_generator_protocol_is_generate`.
- **Break verification**: remove the dtype check in `validate_batch` → `test_validate_batch_shape_dtype_range` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Interface change is mandated by S0-R6 (frozen-file exception). Signatures freeze at the Stage 1/2/3 hand-off.
````

### `13_s0_hashing_status.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E13 evidence line

# Plan 13: S0 common.hashing + common.status

**Stage:** `stages/stage_0.md` R8 (status half), Should 1, Mission M2 · **Plan refs:** `implementation.md` Decision 4; § One-click run (Caching); § Shared conventions (status.json)
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E13) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Every stage must write `artifacts/stageN/status.json` through one writer, with one `run_id` per invocation and input hashes so unchanged stages are skipped. Nothing exists yet.

## 2. Root Cause & Investigation
No `src/common/status.py` / `hashing.py`. Brief M2 requires a writer that can never leave a stale `passed`.

## 3. Architecture & Modular Design Strategy
`hashing.py`: `sha256_file`, `sha256_tree(dir)` (sorted relative paths + bytes), `sha256_obj` (canonical JSON), `config_subtree_hash(cfg, dotted)`. `status.py`: `STATUS_VALUES`, `validate_status(d)`, `new_run_id()`, `current_run_id()` (env `SHAPESENSE_RUN_ID`), `write_status(stage, **fields)` (atomic tmp + replace), `read_status(stage)`, `is_cached(stage, inputs)`, `run_stage(stage, fn, inputs, owner)` fail-closed (writes `failed` + re-raises; `NotImplementedError` → `not_run`).

## 4. Proposed Changes by File
- `src/common/hashing.py`, `src/common/status.py`.
- `tests/common/test_hashing.py`, `tests/contracts/test_status_schema.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_status_schema.py::test_passed_status_validates`, `::test_raising_stage_writes_failed_and_reraises` (M2), `::test_not_implemented_writes_not_run`, `::test_stale_passed_overwritten_on_failure`, `::test_cache_hit_only_when_all_inputs_match_and_passed`; `test_hashing.py::test_tree_hash_order_independent_of_listing`, `::test_config_subtree_hash_changes_with_value`.
- **Break verification**: make `run_stage` swallow the exception → `test_raising_stage_writes_failed_and_reraises` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Atomic write so a crash never leaves half a JSON file. `artifacts_dir` comes from config; tests use `tmp_path`.
- A `not_run` or `failed` status is never a cache hit.
````

### `14_s0_load_split_guard.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E14 evidence line

# Plan 14: S0 common.load_split test guard + access log

**Stage:** `stages/stage_0.md` R8 (load_split half), Done-when D4 (fake test read) · **Plan refs:** `implementation.md` § Separation of concerns 2 (Test-set guard)
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E14) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
The test split must be unreadable outside Stage 5 and every read must be logged per `run_id`.

## 2. Root Cause & Investigation
No `src/common/splits.py`. Manifests will live in `configs/splits/{train,val,test}.csv` (Decision 16).

## 3. Architecture & Modular Design Strategy
`splits.py`: `SPLITS`, `load_split(name, *, splits_dir=None, log_path=None)` → list of row dicts; `_caller_module()` walks the stack past `src.common.*`; `name == 'test'` and caller not under `src.stage5_eval` → `TestSplitAccessError`. Each test read appends `iso_timestamp, run_id, caller_module, split, n_rows` (append mode, never truncated). `count_test_reads(run_id, log_path)` for Done-when checks.

## 4. Proposed Changes by File
- `src/common/splits.py`.
- `tests/contracts/test_load_split_guard.py`.

## 5. Test Strategy & Verification Plan
- **Tests** (tmp manifests only, never the real test.csv): `::test_train_read_allowed_anywhere`, `::test_test_read_blocked_outside_stage5` (D4 fake read), `::test_test_read_allowed_from_stage5_module`, `::test_each_test_read_appends_one_line`, `::test_log_never_truncated`, `::test_count_scoped_to_run_id`, `::test_unknown_split_name_rejected`.
- **Break verification**: invert the caller check → `test_test_read_blocked_outside_stage5` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Stack inspection must skip `src.common` frames; tests assert the exact caller recorded.
- Missing manifest → clear error naming the path and telling the user to run Stage 1.
````

### `15_s0_script_migration.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E15 evidence line

# Plan 15: S0 Phase 1 script migration + equivalence proof

**Stage:** `stages/stage_0.md` R2, R3, Done-when D3 · **Plan refs:** `implementation.md` § Stage 0 (Prove migration equivalence); § Separation of concerns 1
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E15) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`scripts/` uses `sys.path.insert` (`build_unified_dataset.py:29`, `audit_dataset.py:21`) and a private cross-script import of `_qd_loader` (`audit_dataset.py:22`). The plan moves the code into `src/` without changing output.

## 2. Root Cause & Investigation
`scripts/taxonomy.py` duplicates `configs/taxonomy.yaml`; `build_unified_dataset.py` hard-codes `OUT = data_set/unified` and `rmtree`s it. `data_set/` is read-only for this work, so the rebuild goes to `artifacts/stage0/rebuild/`.

## 3. Architecture & Modular Design Strategy
Move `standardize.py`, `taxonomy.py`, `build_unified_dataset.py`, `audit_dataset.py`, `check_fds.py`, `discover_fds.py` → `src/stage1_freeze/`. Shared helpers → `src/common/`: `imaging.py` (`md5`, `phash`), `quickdraw.py` (public `quickdraw_loader`), `neardup.py` (`near_dup_groups`), `catalog.py` (read-only SQLite). `taxonomy.py` reads `configs/taxonomy.yaml` (same order → same label ids). Build gains `build(out_dir, data_dir)`. `src/stage0_infra/migration.py` records catalog content hash, row count, class counts and per-(source,label) pHash groups for the pre-move `data_set/unified/` and the rebuild; writes `artifacts/stage0/migration_check.json`.

## 4. Proposed Changes by File
- delete `scripts/*.py` after the move; six modules under `src/stage1_freeze/`.
- `src/common/imaging.py`, `quickdraw.py`, `neardup.py`, `catalog.py`.
- `src/stage0_infra/__init__.py`, `migration.py`.
- `tests/common/test_imaging.py`, `tests/common/test_neardup.py`, `tests/stage0/test_migration_compare.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_neardup.py::test_groups_within_hamming`, `::test_transitive_union`; `test_imaging.py::test_md5_stable`, `::test_phash_known_value`; `test_migration_compare.py::test_identical_records_pass`, `::test_any_count_difference_fails`.
- **Pipeline check**: rebuild into `artifacts/stage0/rebuild/`; `migration_check.json → equal: true`.
- **Break verification**: change the near-dup Hamming default to 3 → compare reports unequal groups.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- If the pre-move catalog came from a different raw snapshot, also run the original `scripts/` code into scratch and compare both (documented in the check file).
- Phase 1 report cites `scripts/...` paths; E34 updates them.
````

### `16_s0_runner.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E16 evidence line

# Plan 16: S0 run_pipeline.py flags, hash cache, Stage 0 + stubs

**Stage:** `stages/stage_0.md` R1, R7, Should 1, Done-when D2 · **Plan refs:** `implementation.md` Decision 4; § One-click run; § Failure behaviour
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E16) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`run_pipeline.py` runs stages 1–6 only, swallows `NotImplementedError`, writes no status and has none of the documented flags.

## 2. Root Cause & Investigation
`run_pipeline.py:39-46`. No Stage 0 entry; no cache.

## 3. Architecture & Modular Design Strategy
Composition root only. Each stage `run.py` exposes `STAGE`, `DEPENDS`, `inputs(config) -> dict` and `run(config) -> dict`. The runner mints one `run_id`, runs guards (`lint-imports` + `pytest tests/contracts`) first (`--check` = guards only), resolves dependencies for `--stages`, skips cached stages unless `--force`, wraps each via `common.status.run_stage`, and stops at the first `failed`. `--dashboard` → `streamlit run dashboard/app.py`; `--demo` → `python -m demo.app`. Stage 0 = `src/stage0_infra/run.py`. Stage source code and `src/common` are hashed inputs.

## 4. Proposed Changes by File
- `run_pipeline.py`; `src/stage0_infra/run.py`; every `src/stageN_*/run.py` gains `STAGE` + `inputs()`.
- create `dashboard/`, `demo/`, `export/`, `artifacts/stage0/` (R1).
- `tests/stage0/test_runner.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `test_runner.py::test_dependency_closure`, `::test_cached_stage_skipped`, `::test_failed_prior_status_not_cached`, `::test_force_ignores_cache`, `::test_failed_stage_stops_pipeline`, `::test_run_id_shared_by_all_stages`.
- **Pipeline**: `python run_pipeline.py` twice → second run reports `cached` for every stage (D2).
- **Break verification**: drop the `status == passed` condition → `test_failed_prior_status_not_cached` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Windows: subprocess calls use `sys.executable -m ...` so the venv is used.
````

### `17_s0_guards.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E17 evidence line

# Plan 17: S0 import-linter, pre-commit, CODEOWNERS, contract tests

**Stage:** `stages/stage_0.md` R9, Done-when D4, D6, Missions M1, M3 · **Plan refs:** `implementation.md` § Separation of concerns 1, 3, 4
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E17) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
Stage independence, the two allowed cross-stage imports, `dashboard → common.status`, `demo → export` must be machine-checked.

## 2. Root Cause & Investigation
No `.importlinter`, `.pre-commit-config.yaml`, `CODEOWNERS` or `tests/contracts/` exist.

## 3. Architecture & Modular Design Strategy
`.importlinter`: independence contract for the six stage packages with the two allowed Stage 4 imports ignored; `src.common` forbidden from importing stages; `dashboard` forbidden from importing `src` except `src.common.status`; `demo` forbidden from `src`. `.pre-commit-config.yaml` local hooks: `lint-imports`, `pytest tests/contracts -q`. `CODEOWNERS` with `team.json` placeholders.

## 4. Proposed Changes by File
- `.importlinter`, `.pre-commit-config.yaml`, `CODEOWNERS`.
- `tests/stage0/test_guards_block_violations.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_forbidden_stage_import_fails_lint` (temporary probe module, removed in `finally`), `::test_demo_importing_src_fails_lint`, `::test_committed_tree_passes_lint`.
- **Pipeline**: with a probe violation present, `python run_pipeline.py` stops before Stage 1 (M3).
- **Break verification**: remove the independence contract → the forbidden-import test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- `pre-commit install` needs `git init`; documented, not run by the agent.
````

### `18_s0_placeholder_tables.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-07):** DONE — verified in tree; see ignore/todo.md E18 evidence line

# Plan 18: S0 placeholder LaTeX tables + Phase 2 report skeleton

**Stage:** `stages/stage_0.md` R10, Done-when D1 (compiling report) · **Plan refs:** `implementation.md` § Stage 0 (placeholder LaTeX tables)
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E18) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
`build.ps1` runs with `-halt-on-error`; `\input{artifacts/stage5/tables/*.tex}` fails until Stage 5 runs.

## 2. Root Cause & Investigation
No `phase2_report.tex`; no Stage 5 tables.

## 3. Architecture & Modular Design Strategy
`src/stage5_eval/placeholders.py` writes dash placeholders for every table name Stage 5 will produce, only when missing; the Stage 5 stub calls it. `phase2_report.tex` skeleton with the section headings and `\input{}` lines.

## 4. Proposed Changes by File
- `src/stage5_eval/placeholders.py`; `phase2_report.tex`.
- `tests/stage5/test_placeholders.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_writes_dash_tables_when_missing`, `::test_never_overwrites_real_table`.
- **Report**: `.\build.ps1 -File phase2_report.tex` compiles.
- **Break verification**: remove the exists-check → `test_never_overwrites_real_table` fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- The Stage 6 traceability check flags any remaining placeholder.
````

### `19_s0_env_readme.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-11-08):** DONE — evidence in `ignore/todo.md`.

# Plan 19: S0 environment pins, README, data hash, gitignore

**Stage:** `stages/stage_0.md` R11–R14, Should 2–3, Done-when D1, D5 · **Plan refs:** `implementation.md` Decision 5; § Risks
**Tracker:** `ignore/todo.md` § "Phase 2 build" (entry E19) · **Coverage:** [10](10_coverage_matrix.md)

---

## 1. Problem Statement / Context
No `requirements.txt`, `.python-version`, `README.md`; `.venv/` not ignored; no published data hash.

## 2. Root Cause & Investigation
Environment: Python 3.12.10, torch 2.14.1+cpu, CPU-only, 14 cores. `streamlit-drawable-canvas` is incompatible with Streamlit 1.61 → the demo uses the plan's Gradio `Sketchpad` fallback.

## 3. Architecture & Modular Design Strategy
`requirements.txt` exact pins. `.python-version` = 3.12. `src/stage0_infra/data_archive.py` computes a deterministic SHA-256 over the raw source tree (`data_set/` minus `unified/`) → `artifacts/stage0/data_archive_sha256.txt`. README: prerequisites, venv, data pull + hash check, every runner mode, owner/artifact map, Windows troubleshooting. `.gitignore`: `.venv/`, checkpoints, `export/model.onnx`.

## 4. Proposed Changes by File
- `requirements.txt`, `.python-version`, `README.md`, `.gitignore`.
- `src/stage0_infra/data_archive.py`; `tests/stage0/test_data_archive.py`.

## 5. Test Strategy & Verification Plan
- **Tests**: `::test_tree_hash_deterministic`, `::test_hash_changes_when_file_changes`.
- **Clean-clone rehearsal** (no git: copy the tracked file set to scratch, follow README) → seven status files + compiling report.
- **Break verification**: include mtimes in the hash → determinism test fails.
- **Regression**: `python -m pytest tests -q`, plus `python run_pipeline.py --check` once E16/E17 land.

## 6. Edge Cases & Risks
- Second-machine verification (R12/D5) is BLOCKED-ON-HUMAN.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each plan's status line records 'verified in tree' (todo E11 to E19).

## Our decision

Validated config, a fail-closed status writer, a test-split guard with an append-only access log, import contracts and a runner.

## Measured effect

The test access log later verified every sealed read (157 reads at the final audit, C56).

---

## Upgraded & Expanded Analysis: Stage 0 Infrastructure & Guardrail Engineering (`E16`, `E17`, `E18`)

### Foundational Invariants Enforced by Stage 0

Stage 0 (`stages/stage_0.md` and modular plans `16_s0_common.md`, `17_s0_guards.md`, `18_s0_runner.md`) establishes the mechanical enforcement layer that makes every downstream testing claim auditable:

| Deliverable | Modules & Artifacts | Core Epistemic / Systems Contract |
|---|---|---|
| **`E16` — Common Helpers & Split Guard** | `src/common/{config,hashing,io,status,splits}.py` | Enforces fail-closed `status.json` writing, content-addressed SHA-256 input hashing, and `load_split("test")` caller verification that appends every sealed read with its `run_id` to `artifacts/test_access.log` (refusing any caller outside `stage5_eval`). |
| **`E17` — Architectural & Schema Guards** | `.importlinter`, `tests/contracts/` | Enforces strict stage-to-stage module isolation (preventing Stages 1–4 or 6 from importing test-evaluation loaders) and validates artifact schemas before downstream consumption. |
| **`E18` — Deterministic Pipeline Runner** | `run_pipeline.py` | Compares recorded `inputs_sha256` against current config/code/artifact hashes so unchanged stages serve from cache without re-reading sealed data (`13 + 52 + 92 = 157` total reads across Iterations 1–3, `C56`). |

